#!/usr/bin/env python3
"""Deterministic CY16 flywheel resolver.

This tool derives task state from stable policy plus an ephemeral observation
snapshot. It does not persist workflow state and is not an authority over live
GitHub state.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "flywheel" / "tasks.json"


class PolicyError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise PolicyError(f"{path}: top-level JSON value must be an object")
    return value


def _task_map(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = policy.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise PolicyError("policy.tasks must be a non-empty list")
    result: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise PolicyError("every task must be an object")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise PolicyError("every task must have a non-empty string id")
        if task_id in result:
            raise PolicyError(f"duplicate task id: {task_id}")
        result[task_id] = task
    return result


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise PolicyError("unsupported schema_version; expected 1")
    if policy.get("authority") != "github-live-state":
        raise PolicyError("authority must be github-live-state")

    executors = policy.get("executors")
    if not isinstance(executors, dict) or not executors:
        raise PolicyError("policy.executors must be a non-empty object")

    executor_caps: set[str] = set()
    for name, spec in executors.items():
        if not isinstance(name, str) or not isinstance(spec, dict):
            raise PolicyError("invalid executor declaration")
        caps = spec.get("capabilities")
        if not isinstance(caps, list) or not all(isinstance(c, str) for c in caps):
            raise PolicyError(f"executor {name}: capabilities must be a list of strings")
        executor_caps.update(caps)

    tasks = _task_map(policy)
    for task_id, task in tasks.items():
        for field in ("depends_on", "prerequisites", "completion_evidence", "required_capabilities"):
            if field not in task:
                raise PolicyError(f"task {task_id}: missing {field}")
        dependencies = task["depends_on"]
        if not isinstance(dependencies, list) or not all(isinstance(x, str) for x in dependencies):
            raise PolicyError(f"task {task_id}: depends_on must be a list of task ids")
        for dependency in dependencies:
            if dependency not in tasks:
                raise PolicyError(f"task {task_id}: unknown dependency {dependency}")

        for predicate_field in ("prerequisites", "completion_evidence"):
            predicates = task[predicate_field]
            if not isinstance(predicates, list):
                raise PolicyError(f"task {task_id}: {predicate_field} must be a list")
            for predicate in predicates:
                if not isinstance(predicate, dict) or set(predicate) != {"key", "equals"}:
                    raise PolicyError(
                        f"task {task_id}: predicates must contain exactly key and equals"
                    )
                if not isinstance(predicate["key"], str) or not predicate["key"]:
                    raise PolicyError(f"task {task_id}: predicate key must be non-empty")

        required_caps = task["required_capabilities"]
        if not isinstance(required_caps, list) or not all(isinstance(c, str) for c in required_caps):
            raise PolicyError(f"task {task_id}: required_capabilities must be strings")
        unknown = sorted(set(required_caps) - executor_caps)
        if unknown:
            raise PolicyError(f"task {task_id}: unknown capabilities: {', '.join(unknown)}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise PolicyError(f"dependency cycle detected at {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in tasks[task_id]["depends_on"]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in tasks:
        visit(task_id)


def _predicate_failures(predicates: list[dict[str, Any]], observations: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for predicate in predicates:
        key = predicate["key"]
        expected = predicate["equals"]
        if key not in observations:
            failures.append({"key": key, "expected": expected, "observed": None, "reason": "missing"})
        elif observations[key] != expected:
            failures.append(
                {
                    "key": key,
                    "expected": expected,
                    "observed": observations[key],
                    "reason": "mismatch",
                }
            )
    return failures


def resolve(policy: dict[str, Any], snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    validate_policy(policy)
    observations = snapshot.get("observations")
    if not isinstance(observations, dict):
        raise PolicyError("snapshot.observations must be an object")

    tasks = _task_map(policy)
    executors = policy["executors"]
    resolved: dict[str, dict[str, Any]] = {}

    def task_state(task_id: str) -> dict[str, Any]:
        if task_id in resolved:
            return resolved[task_id]
        task = tasks[task_id]

        completion_failures = _predicate_failures(task["completion_evidence"], observations)
        if not completion_failures:
            result = {
                "id": task_id,
                "title": task.get("title", task_id),
                "priority": task.get("priority", 1000),
                "state": "completed",
                "eligible_executors": [],
                "required_validators": task.get("required_validators", []),
                "blockers": [],
                "refs": task.get("refs", []),
                "escalate_if": task.get("escalate_if", []),
            }
            resolved[task_id] = result
            return result

        dependency_blockers = []
        for dependency in task["depends_on"]:
            dependency_state = task_state(dependency)
            if dependency_state["state"] != "completed":
                dependency_blockers.append(
                    {"dependency": dependency, "state": dependency_state["state"]}
                )

        prerequisite_failures = _predicate_failures(task["prerequisites"], observations)
        blockers: list[dict[str, Any]] = []
        blockers.extend({"type": "dependency", **item} for item in dependency_blockers)
        blockers.extend({"type": "evidence", **item} for item in prerequisite_failures)

        required_caps = set(task["required_capabilities"])
        eligible = []
        for executor_name, executor in executors.items():
            if required_caps.issubset(set(executor["capabilities"])):
                eligible.append(executor_name)

        if blockers:
            state = "blocked"
        elif not eligible:
            state = "blocked"
            blockers.append(
                {
                    "type": "capability",
                    "reason": "no executor satisfies required capabilities",
                    "required_capabilities": sorted(required_caps),
                }
            )
        else:
            state = "actionable"

        result = {
            "id": task_id,
            "title": task.get("title", task_id),
            "priority": task.get("priority", 1000),
            "state": state,
            "eligible_executors": eligible,
            "required_validators": task.get("required_validators", []),
            "required_capabilities": sorted(required_caps),
            "blockers": blockers,
            "completion_evidence_missing_or_mismatched": completion_failures,
            "refs": task.get("refs", []),
            "escalate_if": task.get("escalate_if", []),
        }
        resolved[task_id] = result
        return result

    output = [task_state(task_id) for task_id in tasks]
    return sorted(output, key=lambda item: (item["priority"], item["id"]))


def cmd_check_policy(args: argparse.Namespace) -> int:
    policy = load_json(args.policy)
    validate_policy(policy)
    print(json.dumps({"valid": True, "policy": str(args.policy)}, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    policy = load_json(args.policy)
    snapshot = load_json(args.snapshot)
    print(json.dumps({"tasks": resolve(policy, snapshot)}, indent=2, sort_keys=True))
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    policy = load_json(args.policy)
    snapshot = load_json(args.snapshot)
    tasks = resolve(policy, snapshot)
    actionable = [task for task in tasks if task["state"] == "actionable"]
    if not actionable:
        print(json.dumps({"next": None, "reason": "no-actionable-task"}, indent=2))
        return 2
    print(json.dumps({"next": actionable[0]}, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check-policy", help="validate stable task policy")
    check.set_defaults(func=cmd_check_policy)

    status = subparsers.add_parser("status", help="derive all task states from a snapshot")
    status.add_argument("--snapshot", type=Path, required=True)
    status.set_defaults(func=cmd_status)

    next_cmd = subparsers.add_parser("next", help="derive the highest-priority actionable task")
    next_cmd.add_argument("--snapshot", type=Path, required=True)
    next_cmd.set_defaults(func=cmd_next)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, json.JSONDecodeError, PolicyError) as exc:
        print(f"flywheel: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
