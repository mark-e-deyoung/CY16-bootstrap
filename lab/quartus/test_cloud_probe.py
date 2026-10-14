import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "cloud_probe", Path(__file__).with_name("cloud_probe.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_schema():
    result = module.probe()
    assert result["schema"] == "quartus-cloud-preflight/v1"
    assert result["classification"] in ("NO_QUARTUS", "READY_FOR_DEVICE_CHECK")
    assert isinstance(result["tools"]["quartus_sh"], bool)
    assert result["memory_mib"] is None or result["memory_mib"] > 0
