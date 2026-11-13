---
name: game-gpu-capture
description: "Capture and save complete GPU frame captures (.rdc) for Windows Unity games. Covers Unity client and graphics backend identification, RenderDoc integration, per-application Vulkan layer loading, capture triggering, file integrity verification, and temporary configuration cleanup (not needed for standard screenshots or screen recordings)."
---

# Unity Game GPU Capture

Acquire a complete RenderDoc capture file (`.rdc`) from a Windows Unity game client, verify on-disk integrity, and restore temporary system configurations.

## Route Selection

1. **Environment Discovery**: Identify the Unity client and engine version via `UnityPlayer.dll` properties, `*_Data\boot.config`, `Player.log` initialization logs, and loaded graphics modules. Record the actual EXE path, graphics API (`D3D11` / `D3D12` / `Vulkan`), architecture, process elevation, launcher parent-child chain, and active graphics loader.
2. **Standard Integration**: Use RenderDoc's supported capture entry points when sufficient, preserving the client's native graphics backend, launch arguments, working directory, and required parent launcher chain.
3. **Per-Application Vulkan Loading**: When both the launcher and the game create Vulkan instances, or when layer loading must be scoped strictly to the game process, follow [Windows Vulkan Configuration](references/windows-vulkan.md).
4. **Conflict & Protection Triage**: When encountering access denied errors (`Error 5`), ACE anti-cheat alerts, or helper process interference, follow [Conflict Triage & ACE Branches](references/conflict-triage.md).
5. **Triggering & Verification**: Follow [Capture Completion & Verification](references/capture-completion.md) to trigger, stream-save, and validate captures; see [Anonymous Unity Case](references/acquisition-case.md) for a verified configuration baseline.

## Execution Workflow

Operate within the session's authorized targets, network scope, and system modification boundaries; handle UAC prompts according to active tool rules.

1. **Isolate Run & Back Up State**: Create a dedicated output directory per run. Record the target EXE path, process creation time, tool versions, candidate configurations, and original system state. Scope temporary changes strictly to the target object.
2. **Validate Custom Loading with a Probe**: For unverified injection or layer-loading setups, validate first with an independent graphics probe matching the target's architecture, elevation, and loader. Use standard verified paths directly.
3. **Bind Identity & Trigger on Scene Ready**: Bind the game process and control port strictly by EXE path, PID, and creation time. Wait until the target in-game rendering scene is active before requesting a single frame (skip launchers, login screens, and loading screens).
4. **Stream-Save & Verify Integrity**: Use official APIs or a version-matched protocol client. Wait for a complete `NewCapture` signal, then stream-save the file and compute its SHA256 hash, verifying that `NewCapture.byte_size` matches the actual file size on disk. Connect only to the control port owned by the target game PID without preempting existing control sessions.
5. **Deliver & Restore Baseline**: Report the final file path, byte size, SHA256, and target process/frame metadata; conclude the run once a valid capture is secured. Revert temporary changes item-by-item and read back to confirm, preserving concurrent external modifications and separate historical receipts. Allow the target process to exit cleanly so the injected DLL unloads and a clean baseline is restored.

## Bundled Scripts

Run with Python 3 (standard library only; pass `--help` for CLI options):

- `scripts/build_renderdoc_profile.py`: Generates a per-application Vulkan profile bound to exact EXE paths from an official layer manifest, writing only to a new directory. `--library` validates and points to a byte-identical DLL copy (module resolution and helper lookup paths must still be verified for the target RenderDoc version).
- `scripts/verify_capture.py`: Streams a saved capture file to verify read stability (`fstat` consistency), byte size, SHA256, and optional `NewCapture` event consistency, writing a standalone JSON receipt.
