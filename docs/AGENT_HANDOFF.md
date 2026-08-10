# Local Agent Handoff

This is the durable entrypoint for a fresh local agent. Mutable project state lives in GitHub; refresh it at session start rather than relying on prior chat.

## Bootstrap state

The normal bootstrap is a **clean, current `main` checkout containing root `CLAUDE.md`**. Launch Claude from that bootstrap/control worktree, run the fail-closed preflight there, and let the agent create or use dedicated sibling worktrees for integration/task branches.

Older stacked task branches predate the handoff files and may not contain `CLAUDE.md`. Do **not** launch a fresh unrestricted Claude session directly from one of those older branches and assume the project contract will be discovered. Keep the Claude session anchored in current `main` while implementation happens in the dedicated issue worktree.

Do not copy handoff files manually into older task branches merely to make them visible; keep bootstrap state separate from implementation semantics.

## Start here

1. Run:

   ```bash
   python scripts/agent_handoff_preflight.py
   ```

   A non-zero result is a hard stop. Resolve every reported error before implementation.

2. Read GitHub issue **#8**, the canonical integration controller.
3. Refresh open PR/issue state with `gh`.
4. Take only the first integration step whose dependencies are satisfied.
5. Use a dedicated worktree and integration/issue branch. Open or update a draft PR early.

## Authority order

When information conflicts:

1. current repository files/tests at the active branch;
2. current GitHub issue/PR body and latest corrective comments;
3. immutable commit/workflow/test evidence recorded there;
4. source/provenance records;
5. prior chat/session summaries are non-authoritative unless reproduced in Git.

## Current durable stack

The canonical dependency map is issue **#8**. Current principal branches are:

- **PR #2** — parent source/provenance, AN048 fixture, simulator corrections, SCAN `WRITE_CONFIG` structural work.
- **PR #11** — parent review fixes: strict SCAN parser/builders, bounded 64 KiB simulator load, AN048/error/provenance fixes.
- **PR #13** — parent byte-layout correction: byte directives remain contiguous raw bytes; instructions/`.word`/`.short` must start on an even address.
- **PR #4** — relative branches, INT, macros, control-flow conformance; must be reconciled after the parent corrections.
- **PR #6 / PR #15** — SCAN artifact manifest producer plus metadata-only self-consistency hardening.
- **PR #9 / PR #17** — legacy artifact scanner plus symlink containment/archive budgets.
- **#18** — later wraparound regression/model decision. A prior session described equivalent work as completed, but no durable issue/PR/branch/commit existed; #18 is the authoritative recovery point.
- **PR #20 / PR #22** — merged repository handoff and fail-closed preflight hardening now present on `main`.
- **#23** — hosted-CI budget/path-filter policy; full validation remains available manually.

Cross-repository source gates remain in `SemperSupra/DE2-115`: SCAN JUMP issue #48 and SCAN INT issue #51. Do not infer either behavior during CY16 conflict resolution.

## First local task: integrate PR #11 and PR #13 safely

Issue #8 says the parent corrections must be incorporated before PR #2 can progress. A dedicated integration branch is reserved so a fresh agent does not rewrite the existing parent branch as its first action:

```text
agent/issue-8-parent-integration
base: PR #2 head 32da72aa1ec59c6f5f9490df534a125f7f5a247d
```

Recommended worktree flow:

```bash
git fetch --all --prune
git worktree add ../CY16-bootstrap-issue-8 agent/issue-8-parent-integration
```

Keep the unrestricted Claude session launched from the clean/current `main` bootstrap. It may operate on the sibling integration worktree, but the older integration branch itself is not the project-memory bootstrap.

Before integrating anything, reproduce the parent validation ladder locally. The PR #2 workflow currently requires:

```bash
python -m pip install --upgrade pip
pip install pytest pycparser
pip install -e .
make clean
make CC=gcc
pytest -q
mkdir -p build
cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000 --lst build/setup_stub.lst --map build/setup_stub.map
cy16-dis build/setup_stub.bin --base 0x1000
cy16-sim build/setup_stub.bin --base 0x1000 --pc 0x1000 --dump 0xc03a
cy16-scanwrap build/setup_stub.bin build/setup_stub.scan 0x1000
cy16-scan-decode build/setup_stub.scan
./chibicc examples/c/write_memctl.c -S > build/write_memctl.s
cy16-as build/write_memctl.s -o build/write_memctl.bin --base 0x1000
cy16-sim build/write_memctl.bin --base 0x1000 --pc 0x1000 --dump 0xc03a
```

Then integrate/reconcile the two child branches on the integration branch. Preserve semantics, not merely whichever side wins a textual conflict.

### PR #11 invariants

- strict SCAN suffix/terminator/known-record validation;
- unknown records require explicit archaeology opt-in;
- record builders reject out-of-range/truncated values rather than masking them;
- `CPU.load()` cannot extend the machine beyond 64 KiB;
- `sim.py` remains the bounded public API/CLI wrapper;
- AN048 acceptance fails on `ERROR:` traces;
- unverified source revisions remain explicitly unknown.

### PR #13 invariants

Authoritative byte-layout policy:

```text
.byte/.ascii/.asciz/.space/.skip -> contiguous raw bytes
byte-data labels                 -> may be odd
instruction/.word/.short start   -> even address required
alignment                        -> explicit source pad byte
final storage zero pad           -> representation detail, not source layout
```

Do not restore the rejected per-directive automatic-padding experiment.

After both sets of changes are present, run the complete parent suite plus PR #13's focused layout tests. Inspect the reduced diff. Open a draft integration PR targeting `agent/cy16-source-conformance-and-an048`; do not merge the GitHub PR unless explicitly authorized by the active integration task.

## Hosted Actions budget

Current operator constraint, recorded **2026-08-10**: hosted GitHub Actions minutes are exhausted for the remainder of August on the current free-tier budget.

Until that constraint is explicitly cleared:

- local validation is authoritative for agent work;
- do not intentionally dispatch hosted workflows merely to prove a change;
- when an issue or PR says “rerun CI/workflow,” reproduce the workflow commands locally and record exact commands/results in the draft PR;
- the main `CY16 Validation Ladder` is path-filtered so documentation/project-memory changes do not launch the full ladder, while source/build/test inputs still do;
- `workflow_dispatch` remains available for deliberate later runs;
- before relying on hosted Actions in a later session, verify the current budget rather than assuming this dated constraint is still active.

## Next tasks after the parent integration is accepted

Follow issue #8, not this document, for the exact live order. Expected sequence:

1. reconcile PR #4 against the integrated parent:
   - port instruction execution changes into `sim_core.py`;
   - keep `sim.py` as bounded wrapper;
   - preserve PR #13 raw-byte/even-word-start policy;
   - run control-flow + parent + layout tests together;
2. only after that, resolve issue #18's wraparound model/test decision;
3. incorporate PR #15 into PR #6 and retarget the manifest producer;
4. incorporate PR #17 into PR #9 and retarget the recovery scanner;
5. coordinate the reviewed producer fixture with DE2-115 PR #23/#47.

## Trust and provenance boundaries

- A manifest proves internal consistency/integrity binding, not signer identity or execution authorization.
- The DE2-115 consumer must remain an independent parser/policy boundary.
- Linux/Stierlitz GPL sources are behavioral references; do not copy implementation text into MIT code without an explicit licensing decision.
- Retained vendor PDFs/source and recovered CY3663/CY4640 material require separate provenance/redistribution classification.
- Raw local-media scanner reports can expose private paths; do not commit/publicly post them without sanitization.
- Recovered proprietary bytes are not normal source artifacts.

## Cross-repository boundary

When work crosses into `SemperSupra/DE2-115`:

- stop treating CY16 state as authoritative for the DE2 consumer;
- enter DE2-115 through a clean/current `main` bootstrap and run its own preflight;
- follow DE2 issue #26 for integration/consumer order;
- preserve independent producer and consumer parsing/policy boundaries;
- return to CY16 issue #8 for producer/toolchain integration decisions.

## Git/worktree discipline

Before editing:

```bash
git fetch --all --prune
git status --short --branch
git worktree list
gh auth status
gh issue view 8 --repo mark-e-deyoung/CY16-bootstrap
gh pr list --repo mark-e-deyoung/CY16-bootstrap --state open --limit 100
```

Never reuse another agent's dirty worktree. Before pushing:

- fetch the assigned remote branch and verify its head has not moved unexpectedly;
- inspect `git diff --check` and the complete issue-scoped diff;
- run affected and inherited validation locally;
- inspect generated/private/proprietary files;
- push only the assigned branch.

Never use `reset --hard`, `git clean`, dropped stashes, destructive worktree removal, rebase/force-push, or silent branch retargeting to make local state convenient.

Draft PR handoff must state:

- base/dependencies;
- exact semantic conflicts resolved;
- validation commands/results;
- exact head SHA;
- provenance/licensing impact;
- remaining blocker and next safe action.

## Session completion

Do not leave important findings only in the terminal transcript. Update the issue/PR, push the branch, record exact validation, and leave no unexplained local-only edits.
