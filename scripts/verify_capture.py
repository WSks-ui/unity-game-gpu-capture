#!/usr/bin/env python3
"""Verify saved capture file integrity: read stability, byte size, SHA256 digest, and NewCapture completion event."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys


def stat_key(stat):
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


def verify(args):
    capture = Path(args.capture).expanduser().resolve(strict=True)
    if not capture.is_file():
        raise ValueError("Capture path must point to an existing file")
    if args.expected_bytes is not None and args.expected_bytes <= 0:
        raise ValueError("Expected byte size must be greater than 0")
    expected_hash = args.expected_sha256.lower() if args.expected_sha256 else None
    if expected_hash and not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError("Expected SHA256 must be a 64-character hexadecimal string")

    digest = hashlib.sha256()
    length = 0
    header = b""
    with capture.open("rb") as stream:
        before = os.fstat(stream.fileno())
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            if not header:
                header = block[:16]
            digest.update(block)
            length += len(block)
        after = os.fstat(stream.fileno())
    final = capture.stat()
    stable = stat_key(before) == stat_key(after) == stat_key(final) and length == after.st_size
    actual_hash = digest.hexdigest()
    errors = []
    if not stable:
        errors.append("File mutated or path was replaced during read; digest is not valid for completion verification")
    if length == 0:
        errors.append("Capture file is empty")
    if args.expected_bytes is not None and length != args.expected_bytes:
        errors.append("Actual byte size does not match --expected-bytes")
    if expected_hash and actual_hash != expected_hash:
        errors.append("Actual SHA256 digest does not match --expected-sha256")

    event = None
    if args.new_capture:
        payload = json.loads(Path(args.new_capture).read_text(encoding="utf-8-sig"))
        events = payload.get("events") if isinstance(payload, dict) else payload
        if not isinstance(events, list):
            raise ValueError("Completion message file must be a JSON event list or an object containing an 'events' list")
        candidates = [item for item in events if isinstance(item, dict) and item.get("type") == "new_capture"]
        if args.capture_id is not None:
            candidates = [item for item in candidates if item.get("capture_id") == args.capture_id]
        if len(candidates) != 1:
            raise ValueError("NewCapture record is missing or ambiguous; specify --capture-id when multiple records exist")
        event = candidates[0]
        if event.get("message_complete") is not True:
            errors.append("NewCapture message is not marked complete (message_complete != true)")
        if type(event.get("byte_size")) is not int or event["byte_size"] != length:
            errors.append("NewCapture byte_size is missing or does not match actual file size")

    return {
        "schema": "capture_file_integrity_receipt_v1",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "capture": str(capture),
        "size_bytes": length,
        "sha256": actual_hash,
        "header_first_16_bytes_hex": header.hex(),
        "file_stable_during_read": stable,
        "expected_size_supplied": args.expected_bytes,
        "expected_sha256_supplied": expected_hash,
        "new_capture": event,
        "file_checks_passed": not errors,
        "errors": errors,
        "checks_performed": ["file_read_stability", "size", "sha256", "new_capture_consistency" if event else "no_new_capture_supplied"],
        "limit": "Verifies on-disk file integrity and completion metadata only; does not parse internal capture commands.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, help="Path to the saved capture file")
    parser.add_argument("--expected-bytes", type=int, help="Optional expected byte size")
    parser.add_argument("--expected-sha256", help="Optional expected 64-char hex SHA256 digest")
    parser.add_argument("--new-capture", help="Optional JSON file containing complete NewCapture event records")
    parser.add_argument("--capture-id", type=int, help="Target capture_id when multiple NewCapture events exist")
    parser.add_argument("--output", help="Optional path for a new JSON receipt file (refuses to overwrite)")
    args = parser.parse_args()
    if args.capture_id is not None and not args.new_capture:
        parser.error("--capture-id requires --new-capture")
    try:
        output = Path(args.output).expanduser().absolute() if args.output else None
        if output and output.exists():
            raise ValueError("Output receipt path already exists; refusing to overwrite")
        receipt = verify(args)
        text = json.dumps(receipt, ensure_ascii=False, indent=2)
        if output:
            # Write receipt as a standalone new file without modifying capture or event logs.
            with output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text + "\n")
        print(text)
        return 0 if receipt["file_checks_passed"] else 2
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
