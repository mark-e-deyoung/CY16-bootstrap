# Claude Code project instructions

@docs/AGENT_HANDOFF.md

These rules apply even when Claude Code is started with `--dangerously-skip-permissions`.

- Treat current repository files/tests and current GitHub issues/PRs as authoritative. Prior chat/session claims are not evidence unless reproduced in Git.
- Never commit directly to `main`.
- Use one independently actionable issue/integration step -> one `agent/...` branch -> one worktree -> one draft PR.
- Do not force-push, delete another branch/worktree, merge a GitHub PR, or rewrite another active PR branch unless the active integration instruction explicitly authorizes it.
- Run baseline validation before edits and affected/full validation afterward. Do not weaken negative tests merely to make CI pass.
- Preserve source/provenance/licensing boundaries. A valid artifact manifest is not a signature or execution authorization.
- Do not publish private local-media paths or recovered proprietary bytes.
- Do not infer unresolved DE2-115 SCAN JUMP/INT behavior while resolving CY16 code.
