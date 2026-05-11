# CY16 Session Handoff

Date: 2026-05-11

## Repository state

- Repository: `mark-e-deyoung/CY16-bootstrap`
- Branch: `main`
- Green baseline commit: `e8414ff208d7384368ebd7baa684e75b5732e17a`
- Green GitHub Actions baseline before this handoff: `25635202946`
- Latest green local validation: `docker build -t cy16-ladder .` with `23 passed`
- Local dirty file intentionally left untouched: `test.c`

## Completed in the last working session

- Fixed the compiler validation ladder blockers in `src/cy16cc/cy16_codegen.c`.
- Added or completed backend handling for expression cases seen in the Phase 9 ladder, including comma expressions, memory zeroing, logical/bitwise not, conditionals, multiplication constants, local offset assignment, pointer arithmetic scaling, and null expression stack behavior.
- Scoped pytest discovery through `pyproject.toml`.
- Updated CI to run a clean build and the corrected simulator invocation.
- Merged PR #1 and confirmed the `main` push workflow passed.
- Integrated the Phase 10 assembler/disassembler compatibility subset after review, covering `%rN` register spelling, stack forms, string directives, `.space`/`.skip`, `.bss`, `cy16-dis --gnupro`, docs, and tests.
- Reimplemented the useful Phase 9 switch/case follow-on locally, rejected the generated `chibicc` binary patch, and fixed parameter register spilling so later parameter reads survive earlier expression codegen.

## Delegation state

GitHub CLI works when proxy environment variables are cleared for the process. Jules also works with the same proxy cleanup.

Use this prefix before remote `git`, `gh`, or `jules` commands when the local environment still points proxy variables at `127.0.0.1:9`:

```powershell
$env:HTTP_PROXY=''; $env:HTTPS_PROXY=''; $env:ALL_PROXY=''; $env:GIT_HTTP_PROXY=''; $env:GIT_HTTPS_PROXY='';
```

Active Jules results:

- Phase 10 assembler/disassembler compatibility: session `2129117754108276796`, completed. Compatible subset integrated locally and validated with Docker.
- Phase 9 compiler follow-on: session `12196061178148043562`, awaiting user feedback. Patch was pulled for review only and not applied because it includes a generated `chibicc` binary change. Switch/case was reimplemented locally instead.

## Recommended next steps

1. Keep `main` as the green baseline.
2. Push and confirm GitHub Actions for the Phase 10 integration before moving to compiler changes.
3. Continue Phase 9 with static locals, function pointers, interrupt attributes, inline assembly, and peephole cleanup as separate changes.
4. After local Docker and CI are green again, generate SCAN examples and resume DE2-115 HPI readback validation.

## Useful commands

```powershell
git status --short --branch
docker build -t cy16-ladder .
$env:HTTP_PROXY=''; $env:HTTPS_PROXY=''; $env:ALL_PROXY=''; $env:GIT_HTTP_PROXY=''; $env:GIT_HTTPS_PROXY=''; gh run list --branch main --limit 5
$env:HTTP_PROXY=''; $env:HTTPS_PROXY=''; $env:ALL_PROXY=''; $env:GIT_HTTP_PROXY=''; $env:GIT_HTTPS_PROXY=''; jules remote list --session
```
