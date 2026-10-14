"""Disposable, no-hardware controller-plan tests."""
from pathlib import Path
import importlib.util

MODULE = Path(__file__).with_name("plan.py")
spec = importlib.util.spec_from_file_location("wyse_plan", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_empty_os_root_has_safe_plan(tmp_path):
    observed = mod.inventory(tmp_path)
    result = mod.plan(observed)
    assert result["mode"] == "read-only"
    assert result["schema"] == "cy16-lab-plan-v1"
    assert all(not item["automatic"] for item in result["actions"] if item["name"] in ("install-os", "configure-instruments", "hpi-ram-write"))

def test_offline_inventory_reads_fixture(tmp_path):
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/os-release").write_text("ID=ubuntu\\nVERSION_ID=22.04\\n")
    observed = mod.inventory(tmp_path)
    assert "ID=ubuntu" in observed["os_release"]
    assert isinstance(observed["tools"], dict)
