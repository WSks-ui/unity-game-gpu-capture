# Unity / Vulkan Capture Acquisition Case

An anonymized, verified acquisition record preserving key environmental conditions. Re-verify graphics API, loader version, and launch chain when adapting to other games or versions.

## Environment & Completion Criteria

- **Environment**: Windows Unity client, Vulkan loader supporting `app_keys`, and RenderDoc (see [Configuration Baseline](windows-vulkan.md)).
- **Completion**: Complete `NewCapture` event, matching reported and on-disk byte sizes, and passing independent SHA256 verification.

## Acquisition Workflow

1. Verify Unity client build, process elevation, active graphics API, parent launcher, and loader version; configure `app_keys` strictly for the game and probe.
2. Run an elevation-matched probe comparison, recording loaded DLL paths, instance creation, helper identity, and port ownership.
3. Launch the game normally, refresh EXE path, PID, and creation time, and request a single frame once the target scene is active.
4. Stream-save the capture after receiving the complete `NewCapture` signal, verifying byte length and SHA256.
5. Revert temporary settings, read back to confirm, and archive completion and restoration receipts.

## Condition Comparison

| Configuration | Observed Outcome |
| --- | --- |
| Global capture layer | Layer loads into parent launcher first; control port belongs to parent process |
| Exact `app_keys` profile | Parent launcher remains clean; game process establishes an isolated capture connection |
| Temporary service disable | Launch chain reverts service configuration, invalidating the test condition |
| Private original-name DLL without co-located helper | Capture is interrupted after trigger; no complete file produced |
| Byte-identical DLL copy in isolated directory & filename | Complete capture file acquired under these combined filename, directory, and internal helper lookup conditions |

Record exact alert text, error codes, and failure stages on any unsuccessful run; see [ACE Triage Branches](conflict-triage.md) for follow-up actions.
