#!/usr/bin/env python3
"""Read-only Wyse lab-controller discovery and desired-state planner."""
import argparse
import json
import platform
import shutil
from pathlib import Path

TOOLS = ("podman", "systemctl", "quartus_sh", "jtagconfig", "lsusb", "udevadm", "python3")

def inventory(root=Path("/")):
    release = root / "etc/os-release"
    os_release = release.read_text() if release.is_file() else ""
    return {
        "os_release": os_release,
        "machine": platform.machine(),
        "tools": {name: shutil.which(name) for name in TOOLS},
        "serial_by_id": sorted(p.name for p in (root / "dev/serial/by-id").iterdir())
        if (root / "dev/serial/by-id").is_dir() else [],
    }

def plan(observed):
    return {
        "schema": "cy16-lab-plan-v1",
        "mode": "read-only",
        "target": "wyse5070-ubuntu-22.04-x86_64",
        "observed": observed,
        "actions": [
            {"name": "verify-host-identity", "automatic": True, "destructive": False},
            {"name": "install-os", "automatic": False, "reason": "blank disk; requires physical boot or qualified PXE"},
            {"name": "configure-instruments", "automatic": False, "reason": "USB identity and safe pinout unverified"},
            {"name": "hpi-ram-write", "automatic": False, "reason": "S04 safety gate closed"},
        ],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = plan(inventory(args.root))
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded)

if __name__ == "__main__":
    main()
