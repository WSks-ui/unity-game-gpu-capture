#!/usr/bin/env python3
"""Generate a per-application Vulkan candidate profile from an official manifest without modifying system settings or launching processes."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def absolute_file(value, label):
    path = Path(value).expanduser()
    if not path.is_absolute() or not path.is_file():
        raise ValueError(f"{label} must be an absolute path to an existing file: {value}")
    return path


def write_json(path, value):
    # Exclusive creation prevents overwriting candidates, receipts, or concurrent user edits.
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def build(args):
    source = absolute_file(args.source_manifest, "Source manifest")
    raw = json.loads(source.read_text(encoding="utf-8-sig"))
    layer = raw.get("layer")
    if not isinstance(layer, dict) or layer.get("name") != "VK_LAYER_RENDERDOC_Capture":
        raise ValueError("Source file must be a single-layer RenderDoc manifest from the installed release")
    if not raw.get("file_format_version") or not isinstance(layer.get("library_path"), str):
        raise ValueError("Manifest is missing file_format_version or library_path")
    for field in ("name", "type", "api_version", "implementation_version"):
        if field not in layer:
            raise ValueError(f"Manifest is missing required field: {field}")
    source_library = Path(layer["library_path"])
    if not source_library.is_absolute():
        source_library = source.parent / source_library
    source_library = absolute_file(str(source_library), "Source library")
    library = absolute_file(args.library, "Candidate library") if args.library else source_library
    source_hash = sha256(source_library)
    library_hash = sha256(library)
    if source_hash != library_hash:
        raise ValueError("Candidate library bytes differ from source DLL; cross-build compatibility is not inferred")

    apps = []
    for value in args.app:
        # Preserve caller-supplied case and path semantics without resolving symlinks/junctions.
        path = absolute_file(value, "Target app")
        if path.suffix.lower() != ".exe":
            raise ValueError(f"Target app must be a Windows executable (.exe): {value}")
        name = str(path)
        if name not in apps:
            apps.append(name)

    out = Path(args.out).expanduser()
    if not out.is_absolute():
        raise ValueError("Output directory must be an absolute path")
    if out.exists():
        raise ValueError("Output directory already exists; choose a new directory for each run")
    manifest_path = out / "capture_layer.json"
    settings_path = out / "vk_loader_settings.json"
    candidate = copy.deepcopy(raw)
    candidate["layer"]["library_path"] = str(library)
    # Remove enable_environment only on this scoped copy; reference strictly via app_keys.
    removed_enable = candidate["layer"].pop("enable_environment", None)
    settings = {
        "file_format_version": "1.0.0",
        "settings_array": [{
            "app_keys": apps,
            "layers": [
                {"name": layer["name"], "path": str(manifest_path), "control": "on", "treat_as_implicit_manifest": True},
                {"control": "unordered_layer_location"},
            ],
        }],
    }
    # Create output directory only after all inputs validate; no registry, service, or DLL side effects.
    out.mkdir(parents=True, exist_ok=False)
    write_json(manifest_path, candidate)
    write_json(settings_path, settings)
    receipt = {
        "schema": "renderdoc_app_profile_preparation_v1",
        "prepared_only": True,
        "system_configuration_modified": False,
        "runtime_validated": False,
        "source_manifest": str(source),
        "source_manifest_sha256": sha256(source),
        "source_library": str(source_library),
        "candidate_library": str(library),
        "library_sha256": library_hash,
        "candidate_library_matches_source_bytes": True,
        "app_keys": apps,
        "removed_enable_environment": removed_enable,
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "settings": {"path": str(settings_path), "sha256": sha256(settings_path)},
        "limits": [
            "Verify that the target Vulkan loader supports this LoaderSettings schema under matching elevation",
            "Changing DLL filename or directory can alter internal module resolution and helper lookup paths despite identical bytes",
            "Scoped strictly to exact app_keys; do not register capture_layer.json globally",
        ],
    }
    write_json(out / "profile_manifest.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", required=True, help="Absolute path to the installed official RenderDoc layer manifest")
    parser.add_argument("--app", action="append", required=True, help="Exact absolute path to a target .exe (repeatable)")
    parser.add_argument("--library", help="Optional: absolute path to an existing byte-identical DLL copy")
    parser.add_argument("--out", required=True, help="Absolute path to a non-existent output directory")
    args = parser.parse_args()
    try:
        receipt = build(args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
