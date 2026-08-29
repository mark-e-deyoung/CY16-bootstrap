import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import flywheel  # noqa: E402


@pytest.fixture
def policy():
    return json.loads((ROOT / "flywheel" / "tasks.json").read_text(encoding="utf-8"))


def snapshot(**observations):
    return {"observations": observations}


def by_id(resolved):
    return {task["id"]: task for task in resolved}


def test_repository_policy_is_valid(policy):
    flywheel.validate_policy(policy)


def test_parent_integration_is_first_actionable_task(policy):
    state = snapshot(
        **{
            "pr:2:state": "open",
            "pr:11:validation": "success",
            "pr:13:validation": "success",
        }
    )
    resolved = flywheel.resolve(policy, state)
    tasks = by_id(resolved)

    parent = tasks["issue-8-parent-integration"]
    assert parent["state"] == "actionable"
    assert parent["eligible_executors"] == ["webui", "local-agent"]
    assert parent["required_validators"] == ["github-actions"]
    assert tasks["issue-8-control-flow-reconciliation"]["state"] == "blocked"


def test_completed_parent_unlocks_multiple_real_tranches(policy):
    state = snapshot(
        **{
            "pr:2:contains-pr-11": True,
            "pr:2:contains-pr-13": True,
            "pr:2:validation": "success",
            "pr:4:state": "open",
            "pr:6:state": "open",
            "pr:15:validation": "success",
            "pr:9:state": "open",
            "pr:17:validation": "success",
        }
    )
    tasks = by_id(flywheel.resolve(policy, state))

    assert tasks["issue-8-parent-integration"]["state"] == "completed"
    assert tasks["issue-8-control-flow-reconciliation"]["state"] == "actionable"
    assert tasks["issue-8-scan-manifest-reconciliation"]["state"] == "actionable"
    assert tasks["issue-8-legacy-scanner-reconciliation"]["state"] == "actionable"


def test_missing_evidence_fails_closed(policy):
    tasks = by_id(flywheel.resolve(policy, snapshot()))
    parent = tasks["issue-8-parent-integration"]

    assert parent["state"] == "blocked"
    assert any(
        blocker["type"] == "evidence" and blocker["reason"] == "missing"
        for blocker in parent["blockers"]
    )


def test_failed_validation_blocks_progress(policy):
    state = snapshot(
        **{
            "pr:2:state": "open",
            "pr:11:validation": "failure",
            "pr:13:validation": "success",
        }
    )
    parent = by_id(flywheel.resolve(policy, state))["issue-8-parent-integration"]

    assert parent["state"] == "blocked"
    assert any(
        blocker.get("key") == "pr:11:validation"
        and blocker.get("observed") == "failure"
        for blocker in parent["blockers"]
    )


def test_hil_task_routes_only_to_hardware_executor(policy):
    state = snapshot(
        **{
            "pr:2:contains-pr-11": True,
            "pr:2:contains-pr-13": True,
            "pr:2:validation": "success",
            "pr:6:contains-pr-15": True,
            "pr:6:validation": "success",
            "de2:scan-hil-gate": "ready",
        }
    )
    task = by_id(flywheel.resolve(policy, state))["de2-scan-hil-validation"]

    assert task["state"] == "actionable"
    assert task["eligible_executors"] == ["hil"]


def test_unknown_capability_is_rejected(policy):
    broken = copy.deepcopy(policy)
    broken["tasks"][0]["required_capabilities"].append("telepathy")

    with pytest.raises(flywheel.PolicyError, match="unknown capabilities"):
        flywheel.validate_policy(broken)


def test_dependency_cycle_is_rejected(policy):
    broken = copy.deepcopy(policy)
    broken["tasks"][0]["depends_on"] = ["issue-8-control-flow-reconciliation"]

    with pytest.raises(flywheel.PolicyError, match="dependency cycle"):
        flywheel.validate_policy(broken)
