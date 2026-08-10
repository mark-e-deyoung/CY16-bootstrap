# Local Agent Handoff

This is the durable entrypoint for a fresh local agent. Mutable project state lives in GitHub; refresh it at session start rather than relying on prior chat.

## Start here

1. Run:

   ```bash
   python scripts/agent_handoff_preflight.py
   ```

2. Read GitHub issue **#8**, the canonical integration controller.
3. Refresh open PR/issue state with `gh`.
4. Take only the first integration step whose dependencies are satisfied.
5. Use a dedicated worktree and integration/issue branch. Open/update a draft PR early.

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
- **#19** — this handoff preparation.

Cross-repository source gates remain in `SemperSupra/DE2-115`: SCAN JUMP issue #48 and SCAN INT issue #51. Do not infer either behavior during CY16 conflict resolution.

## First local task: integrate PR #11 and PR #13 safely

Issue #8 says the parent corrections must be incorporated before PR #2 can progress. A dedicated integration branch is reserved so a fresh agent does not rewrite the existing parent branch as its first action:

```text
agent/issue-8-parent-integration
base: PR #2 head 32da72aa1ec59c6f5f9490df534a125f7f5a247d
```

Recommended worktree flow:

```bash
git fetch --all
git worktree add ../CY16-bootstrap-issue-8 agent/issue-8-parent-integration
cd ../CY16-bootstrap-issue-8
```

Before integrating anything, reproduce the parent validation ladder. The PR #2 workflow currently requires:

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

After both sets of changes are present, run the complete parent suite plus PR #13's focused layout tests. Inspect the reduced diff. Open a draft integration PR targeting `agent/cy16-source-conformance-and-an048`; do not merge the GitHub PR unless explicitly authorized.

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

## Git/worktree discipline

Before editing:

```bash
git fetch --all
git status --short --branch
git worktree list
gh auth status
gh issue view 8 --repo mark-e-deyoung/CY16-bootstrap
gh pr list --repo mark-e-deyoung/CY16-bootstrap --state open --limit 100
```

Never reuse another agent's dirty worktree. Before pushing, inspect `git diff --check`, complete issue-scoped diff, tests, generated/private files, and branch ownership.

Draft PR handoff must state:

- base/dependencies;
- exact semantic conflicts resolved;
- validation commands/results;
- exact head SHA;
- provenance/licensing impact;
- remaining blocker and next safe action.

## Session completion

Do not leave important findings only in the terminal transcript. Update the issue/PR, push the branch, record exact validation, and leave no unexplained local-only edits.
