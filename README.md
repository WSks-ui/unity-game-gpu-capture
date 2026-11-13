# Unity Game GPU Capture

An Agent Skill dedicated to acquiring complete GPU frame captures (`.rdc`) from Windows Unity games. Covers capture tool integration, target process selection, capture triggering, completion verification, and temporary configuration cleanup.

## Capabilities

- Identify Unity client builds, versions, active graphics APIs (`D3D11` / `D3D12` / `Vulkan`), executable paths, and launcher parent-child chains.
- Integrate RenderDoc capture entry points, including per-application Vulkan layer loading via `LoaderSettings`.
- Triage capture blockers caused by ACE anti-cheat components, helper processes, permission boundaries, and delayed runtime alerts.
- Wait for complete capture signals, verify file size and SHA256 integrity, and restore temporary system settings.

ACE troubleshooting guidance includes stage-isolation methods and verified candidate combinations; exact parameters must match the target game and tool versions.

## Installation & Invocation

In Codex, place the `game-gpu-capture` directory in one of the following locations:

- Project-scoped: `.agents/skills/game-gpu-capture/`
- User-scoped: `~/.agents/skills/game-gpu-capture/`

Preserve the directory layout so `SKILL.md` sits at the root of the skill folder. For other Agent runtimes, load the directory according to their skill conventions. See the [Codex Skills Documentation](https://developers.openai.com/codex/skills) for discovery rules.

Example prompt:

```text
Use $game-gpu-capture to acquire a complete GPU frame capture from the target Windows Unity game.
Verify the executable path and graphics API first, select the appropriate capture route, and restore temporary configurations after saving.
```

Provide the Unity client launch method, target executable, and desired in-game scene; see [SKILL.md](SKILL.md) for execution details.

## Bundled Scripts

Scripts require Python 3 and use only the standard library. Run from this directory:

```shell
python scripts/build_renderdoc_profile.py --help
python scripts/verify_capture.py --help
```

| Script | Purpose |
| --- | --- |
| `build_renderdoc_profile.py` | Generates per-application Vulkan candidate configs from an official layer manifest; writes files only without modifying the registry or launching processes |
| `verify_capture.py` | Verifies read stability, byte size, SHA256 digest, and optional `NewCapture` event consistency for saved capture files |

Capture tools and target game clients must be prepared in the target environment. Confirm tool versions, elevation, and system configuration permissions before execution.

## Documentation Index

| Document | Contents |
| --- | --- |
| [Windows Vulkan](references/windows-vulkan.md) | Per-application layer loading, loader baselines, and configuration contracts |
| [Conflict Triage](references/conflict-triage.md) | Permission checks, helper processes, and ACE triage branches |
| [Capture Completion](references/capture-completion.md) | Triggering, completion signals, streaming save, and cleanup |
| [Acquisition Case](references/acquisition-case.md) | Verified conditions affecting capture outcomes and applicability boundaries |

This public package includes skill documentation, UI metadata, and two helper scripts. `.gitignore` excludes local captures, logs, credentials, and generated configuration receipts.
