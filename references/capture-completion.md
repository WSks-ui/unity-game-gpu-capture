# Acquiring and Verifying Complete Capture Files

## Integration & Triggering

1. **Standard Entry**: Configure RenderDoc for the Unity client's active graphics API, preserving the target EXE, working directory, launch arguments, and required parent launcher chain.
2. **Per-App Vulkan Layer Entry**: After registering temporary settings per [Per-Application Vulkan Configuration](windows-vulkan.md), enter the target in-game scene and trigger a single frame using the active capture hotkey (read local hotkey settings first), official capture API, or TargetControl.
3. **Connection Acceptance**: Verify that the control port owner, handshake PID, EXE path, and creation time match the current game instance. Connect only to the port owned by the current game PID and preserve existing control sessions.
4. **Completion Acceptance**: Wait for a complete `NewCapture` message and record the target process, frame number, capture ID, reported path, and byte size. Runs ending with only `progress` updates, early connection resets, or process exit without `NewCapture` are incomplete.

## Saving & Integrity Verification

- **Streaming & Read Stability**: After receiving the completion signal, stream-save the file in chunks and compute its SHA256 digest, creating the destination file exclusively (`x`). Verify file size, modification time, and file identity stability across pre-read `fstat`, post-read `fstat`, and final path `stat`.
- **Size & Path Matching**: Confirm `NewCapture.byte_size` equals the actual disk byte length. When copying from a tool temporary directory to a persistent location, record both source and final paths along with their SHA256 digests.

Populate the variables below with absolute paths for the current run:

```powershell
$skillRoot = 'ABSOLUTE_SKILL_DIRECTORY'
$captureFile = 'ABSOLUTE_CAPTURE_FILE_PATH'
$completionMessages = 'ABSOLUTE_COMPLETION_MESSAGES_PATH'
$newReceipt = 'ABSOLUTE_NEW_RECEIPT_PATH'

python (Join-Path $skillRoot 'scripts/verify_capture.py') `
  --capture $captureFile `
  --new-capture $completionMessages `
  --output $newReceipt
```

Add `--expected-bytes` and `--expected-sha256` when expected values are known, and use `--capture-id` when the event log contains multiple `NewCapture` records. The script accepts either a JSON object containing an `events` list or a top-level event list, outputting a standalone integrity receipt.

## Protocol Baseline

Prefer official capture APIs. Custom TargetControl clients must align with the installed RenderDoc version; the validated RenderDoc `1.47` baseline uses protocol `v9`, `64`-byte chunk alignment, and `NewCapture` trailing fields. Mark `message_complete` true only after all fields are parsed; leave partial packets marked incomplete.

## Delivery & Cleanup

Deliver the final file path, actual byte size, SHA256 digest, target process/frame number, and configuration restoration results. Revert temporary registrations item-by-item and read back to confirm, preserving unrelated original settings; allow target processes to exit cleanly so loaded capture DLLs unload from memory.
