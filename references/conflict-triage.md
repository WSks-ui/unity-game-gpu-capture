# Capture Conflict Triage & Resolution

Isolate failures by lifecycle stage: **Process Creation → Layer Loading → Graphics Instance Creation → Login / In-Game Entry → Capture Trigger → File Save Completion**.

## Signal Interpretation

| Observation | Stage Meaning | Next Check |
| --- | --- | --- |
| `OpenService` returns Error 5 | The requested service access was denied | Access mask, elevated query result, actual service state, and DACL |
| Service `STOPPED`, Driver `RUNNING` | User-mode service and kernel driver lifecycles are independent | Driver state and the component originating the alert |
| Window owned by `csrss` | Identifies the owning thread/process of the window | Original requester, source session, and dialog API |
| Module snapshot returns Error 5 | Module enumeration call denied under current token | Elevation differences, native wait points, and pre/post-entry states |
| DLL/driver load not observed | Missing from current sampling window | Transient loads, name variants, sibling processes, and sampling coverage |
| Control port open or `APIUse supported` | Control channel or API probe stage succeeded | Complete frame capture and file-completion messages |
| No new process after UI click | Expected launch not yet observed | Refresh UI/process state; ask user to complete manual click if needed |

## Minimal Experiment Prerequisites

- **Comparable Probe**: Match elevation, architecture, loader, candidate config, and observation window to the target game; record full helper paths, arguments, and parent creation times.
- **Scoped Config Changes**: Operate within authorized scope and back up raw bytes or full value types/data. Record multi-factor changes as combined experiments, and conclude once a complete capture file is obtained.
- **Candidate DLL Contract**: Verify module resolution, embedded resources, and helper lookup rules for the tool version before testing renamed or relocated DLLs on a probe.

## ACE & Anti-Cheat Triage Branches

Preserve exact alert text, error codes, and failure stages, then execute the matching branch:

| Condition | Action | Acceptance Criteria |
| --- | --- | --- |
| Global layer enters parent launcher first | Switch to [per-application Vulkan config](windows-vulkan.md) targeting only the game and probe; revert global registration | Parent launcher stays clean, game gets an isolated connection, and normal layer discovery is preserved |
| No tool GUI, but `renderdoccmd` child process appears | Bind helper path, arguments, and parent creation time; inspect crash-handler and private DLL directory conditions | Active background processes and helper lookup paths are explicitly identified |
| Delayed alert after scene entry or trigger | Align timestamps for trigger, `progress`, alert, exit, and file flush | Complete `NewCapture` matches on-disk file; mark candidates without completion signals incomplete |
| Process/service query returns Error 5 | Run authorized elevated query to inspect caller privileges, target identity, service DACL, and runtime stage | Clearly distinguish permission boundaries from compatibility conflicts |
| Alert persists while user-mode service is stopped | Query related kernel driver states and load events concurrently | Service and driver states are accurately recorded; attribute alert source only with direct evidence |
| Suspected service startup condition (within scope) | Back up service config, run a reversible A/B check, and monitor whether the launch chain reverts it | Condition holds and game launches normally; abort and restore immediately if reverted or launch fails |

Reuse prior findings directly if removing the client ACE directory still triggers alerts or if service changes are automatically reverted by the launch chain. Track service checks separately from capture candidates; when a debug build, config flag, or sanctioned capture channel exists, follow its documented contract.

### Verified Capture-Capable Candidate Combination

**Per-application layer loading + byte-identical private copy of the official DLL + verified internal module/helper lookup path + single-frame trigger after entering the target scene**. This successful configuration left ACE services, drivers, and game files untouched (whereas using the original DLL filename in a private directory without a co-located helper failed).

Steps to reproduce a comparable candidate:
1. Copy the official capture DLL into a new private directory under a distinct filename (preserving the original installation) and verify identical SHA256 digests.
2. Inspect the target RenderDoc version's basename, module resolution, and embedded resource contracts, noting any helper lookup fallback to the EXE directory.
3. Generate a manifest copy pointing `library_path` to the candidate DLL while preserving layer name, exports, extensions, and `pre_instance_functions` (via `build_renderdoc_profile.py --library`).
4. Validate on an elevation- and loader-matched probe: confirm only the candidate DLL loads, the original DLL is absent, graphics instance creation succeeds, and helper paths match expectations.
5. Launch the Unity game normally, re-bind process identity and control port, enter the target scene, and request one frame, and wait for a complete `NewCapture` and the saved file.
6. Restore temporary settings after the run and adjust variables for any subsequent round. Because DLL name, directory, and internal helper lookup paths changed together, record the outcome as "a complete capture was obtained under these combined conditions"; single-variable attribution is unnecessary.

## Telemetry Sampling & State Restoration

- **Sampling**: Schedule window, service, and port monitors independently so slow module enumeration does not skew timestamps; compute actual intervals from timestamps and record maxima.
- **Win32 Calls**: Declare explicit `argtypes` and `restype` on `ctypes` Win32 bindings (preventing 64-bit handle truncation); prefer structured port APIs over localized `netstat` text parsing.
- **Restoration**: Restore exact modified items in `finally` blocks or standalone cleanup routines; save and reconcile concurrent external changes while preserving third-party layers. Read back to verify, allow target processes to exit cleanly, and retain historical or failed receipts separately.
