# Per-Application Vulkan Capture Layer on Windows (Unity)

Applicable when a Unity client runs on Vulkan and requires isolated layer configurations between the parent launcher and the game process. Inspect the actual `vulkan-1.dll` path and version loaded by the target first (validated against System32 loader `1.4.341.0`; private app-bundled loaders require separate verification).

## Configuration Contract

- **Exact Path Matching (`app_keys`)**: `vk_loader_settings.json` selects profiles via `settings_array[].app_keys` using exact, case-sensitive full EXE paths matching the actual launch path (basenames, wildcards, and shortcuts are not matched).
- **Registry Path & Elevation**: Under this baseline, elevated (Administrator) processes ignore `HKCU` and read `HKLM\SOFTWARE\Khronos\Vulkan\LoaderSettings` (value name = absolute path to `vk_loader_settings.json`, type `REG_DWORD`, data `0`). Back up the key/value's prior existence, type, and data; inspect precedence and override behavior if settings already exist.
- **Configuration Chain**: Registry points to `vk_loader_settings.json` → references layer manifest (`capture_layer.json`) → `library_path` points to the capture DLL.
- **Implicit Layer Semantics**: Configure the layer entry with `"control": "on"` and `"treat_as_implicit_manifest": true`, preserving the official manifest's `pre_instance_functions`, export mappings, and extension fields (loading as a pure explicit layer caused initialization crashes in this baseline).
- **Preserve Layer Discovery**: Append `{"control": "unordered_layer_location"}` to the layer array to preserve the normal discovery mechanism for existing layers.
- **Scoped Activation**: The manifest copy with `enable_environment` removed is referenced exclusively by the per-app settings file while preserving `disable_environment`. Keep global `ImplicitLayers` untouched.

## Generating Candidate Profiles

Populate the variables below with absolute paths for the current run:

```powershell
$skillRoot = 'ABSOLUTE_SKILL_DIRECTORY'
$layerManifest = 'ABSOLUTE_RENDERDOC_MANIFEST_PATH'
$gameExe = 'ABSOLUTE_GAME_EXECUTABLE_PATH'
$probeExe = 'ABSOLUTE_CAPTURE_PROBE_PATH'
$newRun = 'ABSOLUTE_NEW_RUN_DIRECTORY'

python (Join-Path $skillRoot 'scripts/build_renderdoc_profile.py') `
  --source-manifest $layerManifest `
  --app $gameExe `
  --app $probeExe `
  --out $newRun
```

The script preserves the official manifest structure, API version, and export names while recording `enable_environment` removal in `profile_manifest.json`. If the layer does not activate, inspect the target process environment for `disable_environment` variables alongside actual DLL paths and loader logs.

`--library` points to an existing DLL copy whose SHA256 matches the source DLL; the script validates the digest and updates the manifest path without copying or renaming files. Verify the target RenderDoc version's module resolution and helper lookup rules before changing DLL names or directories.

## Minimal Runtime Verification

For unverified layer setups, run an elevated-matched **"Clean Probe → Matched Probe → Clean Probe"** sequence:

1. Verify self-reported EXE, loader, capture DLL paths, and Vulkan instance creation across probes so only the matched path loads the candidate layer.
2. Record full helper process identities and control port ownership, confirming the parent launcher and unrelated apps remain clean.
3. Once verified, launch the Unity client through its normal startup chain and re-bind process identity; track control port readiness and final capture file completion separately.

## Upstream Baselines

* **Vulkan-Loader**: commit `32fcb949e253cbeb40cda7ea76122b492db579ae` ([LoaderSettings Docs](https://github.com/KhronosGroup/Vulkan-Loader/blob/32fcb949e253cbeb40cda7ea76122b492db579ae/docs/LoaderSettingsFile.md), [settings.c](https://github.com/KhronosGroup/Vulkan-Loader/blob/32fcb949e253cbeb40cda7ea76122b492db579ae/loader/settings.c), [loader_windows.c](https://github.com/KhronosGroup/Vulkan-Loader/blob/32fcb949e253cbeb40cda7ea76122b492db579ae/loader/loader_windows.c)).
* **RenderDoc**: official `v1.47`, commit `b0e1370309f7d7bf986a73830446ca39d9b8c1fd` (read `api_version` and `implementation_version` directly from the local release manifest).
