# CY16 WebUI Flywheel Contract

Status: experimental  
Tracking issue: #29

## Purpose

This document is the public CY16 entrypoint for an interactive WebUI executor. It complements, but does not replace, `docs/AGENT_HANDOFF.md`, which remains the local-agent bootstrap for work requiring a checkout, local/private evidence, specialized tools, or hardware access.

The experiment asks whether a fresh WebUI session can reconstruct actionable CY16 work from durable GitHub evidence without relying on prior chat/session state.

## Authority order

Use this order when reconstructing current work:

1. current repository files and tests;
2. current GitHub issues, pull requests, checks, reviews, and branch relationships;
3. immutable commit/workflow/artifact evidence;
4. source/provenance records;
5. prior chat summaries only when reproduced into durable GitHub state.

Computed flywheel output is advisory/derived. It is not a second task database and never overrides live GitHub state or the governing issue.

## Executor classes

### `webui`

Use for GitHub-native reasoning, review, issue/PR/documentation work, repository edits through available GitHub interfaces, and public-source research.

### `github-actions`

Use as the independent deterministic software validator for build/test/static/provenance/reproducibility work covered by repository workflows.

### `local-agent`

Escalate only when the task actually requires a capability unavailable to WebUI/hosted CI, such as private/local filesystem evidence, specialized installed tools, or a materially useful interactive local execution loop. Generate a bounded handoff using the existing repository/local-agent contract; do not invent a parallel workflow authority.

### `hil`

Use for physical DE2-115, USB-Blaster, CY7C67200 runtime, or other device-level measurement.

## Resume loop

A fresh WebUI session should:

1. read this document, `CLAUDE.md`, `docs/AGENT_HANDOFF.md`, and the governing issue(s) for the selected work;
2. refresh live GitHub issue/PR/check state;
3. construct or obtain an ephemeral observation snapshot matching `flywheel/tasks.json` evidence keys;
4. run or reason equivalently to `python scripts/flywheel.py next --snapshot <snapshot.json>`;
5. take the highest-priority actionable task that is within current authority and available capabilities;
6. preserve the task's stated validators and guarded boundaries;
7. submit project changes through normal branch/PR review and hosted validation;
8. record durable evidence in the owning issue/PR rather than in chat;
9. refresh GitHub state and derive the next task;
10. stop at a genuine local/HIL/owner/privileged gate rather than silently broadening authority.

## What the resolver is allowed to know

`flywheel/tasks.json` contains stable project policy only: task identifiers, priority, evidence predicates, capability requirements, validators, and escalation boundaries. It must not be maintained as a shadow copy of whether PRs are currently open/merged/green.

The snapshot is ephemeral observed state. It may be generated from GitHub by a WebUI session, local tool, or future read-only adapter. It is evidence input, not durable workflow authority.

## Failure discipline

- Missing required evidence fails closed.
- Unknown capabilities fail closed.
- Dependency cycles are invalid policy.
- A failed validator blocks dependent progression until corrected or explicitly reclassified.
- Repeated identical failure should become diagnosis/escalation rather than an unbounded retry loop.
- Implementation failure does not authorize weakening tests, provenance claims, authoritative fixtures, independent-consumer rules, or hardware expectations.
- Validator-semantic changes require guarded review.

## Current first experiment

Issue #29 is the experiment track. The first real workload is the current stacked integration governed by issue #8. The resolver should help reconstruct which integration tranche is actionable, but issue #8 and live PR/check state remain authoritative.

The first success criterion is not full autonomy. It is a clean WebUI -> GitHub Actions cycle where a fresh session can explain:

- what is actionable;
- why prerequisites are satisfied;
- which executors are eligible;
- which independent validation is required;
- which conditions require escalation;
- which exact GitHub evidence proves the result.

Do not generalize the mechanism beyond CY16 until repeated evidence justifies it.