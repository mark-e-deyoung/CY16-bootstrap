#!/usr/bin/env python3
"""Read-only preflight for a fresh local CY16 agent session.

No files, refs, worktrees, issues, or PRs are modified by this script.
Unsafe or unverifiable bootstrap state exits non-zero.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "mark-e-deyoung/CY16-bootstrap"
CONTROL_ISSUE = 8
RECOVERY_ISSUE = 18
EXPECTED_ORIGIN_SUFFIX = "mark-e-deyoung/CY16-bootstrap.git"


def run(*args: str) -> tuple[int, str]:
    proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.strip()


def section(title: str) -> None:
    print(f"\n== {title} ==")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    section("repository")
    rc, root = run("git", "rev-parse", "--show-toplevel")
    if rc != 0:
        print(root)
        print("ERROR: not inside a Git worktree")
        return 2
    root_path = Path(root).resolve()
    print(f"root: {root_path}")

    rc, branch = run("git", "branch", "--show-current")
    print(f"branch: {branch or '(detached)'}")
    if rc != 0 or not branch:
        errors.append("detached HEAD or branch could not be determined")
    elif branch == "main":
        warnings.append("bootstrap is on main; create/use the assigned integration worktree before editing")

    rc, status = run("git", "status", "--short", "--branch")
    print(status)
    if rc != 0:
        errors.append("git status failed")
    rc, porcelain = run("git", "status", "--porcelain")
    if rc != 0:
        errors.append("could not determine worktree cleanliness")
    elif porcelain:
        errors.append("worktree is dirty; preserve/reconcile local changes before allowing an agent to edit")

    rc, origin = run("git", "remote", "get-url", "origin")
    print(f"origin: {origin if rc == 0 else '(missing)'}")
    if rc != 0:
        errors.append("origin remote is missing")
    elif EXPECTED_ORIGIN_SUFFIX not in origin.replace("\\", "/"):
        errors.append(f"origin does not identify expected repository {REPO}")

    section("worktrees")
    rc, worktrees = run("git", "worktree", "list", "--porcelain")
    print(worktrees if rc == 0 else "unable to list worktrees")
    if rc != 0:
        errors.append("git worktree list failed")

    section("handoff files")
    for rel in ("CLAUDE.md", "docs/AGENT_HANDOFF.md", "scripts/agent_handoff_preflight.py"):
        present = (root_path / rel).is_file()
        print(f"{rel}: {'present' if present else 'MISSING'}")
        if not present:
            errors.append(f"required handoff file missing: {rel}")

    section("GitHub")
    gh = shutil.which("gh")
    if not gh:
        print("gh: unavailable")
        errors.append("gh CLI is required to refresh mutable issue/PR state")
    else:
        print(f"gh: {gh}")
        rc, auth = run(gh, "auth", "status")
        if rc != 0:
            print(auth)
            errors.append("gh authentication is not usable; do not proceed with mutable GitHub state unknown")

        for number, label in ((CONTROL_ISSUE, "integration controller"), (RECOVERY_ISSUE, "later wraparound recovery")):
            rc, output = run(
                gh,
                "issue",
                "view",
                str(number),
                "--repo",
                REPO,
                "--json",
                "number,title,state,url",
            )
            if rc != 0:
                print(output)
                errors.append(f"could not refresh GitHub issue #{number}")
                continue
            try:
                item = json.loads(output)
                print(f"{label}: #{item['number']} [{item['state']}] {item['title']} {item['url']}")
            except (json.JSONDecodeError, KeyError):
                print(output)
                errors.append(f"unexpected gh JSON for issue #{number}")

        rc, output = run(
            gh,
            "pr",
            "list",
            "--repo",
            REPO,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            "number,title,headRefName,baseRefName,isDraft,url",
        )
        if rc != 0:
            print(output)
            errors.append("could not refresh open PR list")
        else:
            try:
                prs = json.loads(output)
                print(f"open PRs: {len(prs)}")
                for pr in prs:
                    draft = "draft" if pr.get("isDraft") else "ready"
                    print(f"  #{pr['number']} {draft}: {pr['headRefName']} -> {pr['baseRefName']} | {pr['title']}")
            except (json.JSONDecodeError, KeyError):
                print(output)
                errors.append("unexpected gh JSON for PR list")

        if branch == "main":
            rc, local_head = run("git", "rev-parse", "HEAD")
            if rc != 0:
                errors.append("could not determine local main HEAD")
            rc, remote_head = run(gh, "api", f"repos/{REPO}/commits/main", "--jq", ".sha")
            if rc != 0:
                print(remote_head)
                errors.append("could not read current remote main SHA through GitHub API")
            elif local_head != remote_head:
                print(f"local main:  {local_head}")
                print(f"remote main: {remote_head}")
                errors.append("local main is not current; stop and fast-forward it safely before starting agent work")
            else:
                print(f"main freshness: current at {local_head}")

    section("result")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARN: {item}")
    if errors:
        print("Preflight FAILED. Do not begin implementation until every ERROR is resolved.")
        return 2
    print("Preflight PASSED.")
    print("Next: read issue #8 and use agent/issue-8-parent-integration for the first parent-reconciliation task.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
