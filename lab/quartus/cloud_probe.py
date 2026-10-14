#!/usr/bin/env python3
"""Read-only Quartus cloud executor preflight; emits sanitized JSON."""
import argparse
import json
import platform
import shutil
import subprocess
from pathlib import Path


def run(args, timeout=15):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return {
            "status": "ok" if p.returncode == 0 else "failed",
            "exit_code": p.returncode,
            "output": (p.stdout + p.stderr)[:2000],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unavailable", "error": type(exc).__name__}


def probe():
    mem_kib = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                mem_kib = int(line.split()[1])
                break
    except OSError:
        pass
    disk = shutil.disk_usage("/tmp")
    names = ("quartus_sh", "quartus_map", "quartus_fit", "quartus_asm",
             "quartus_sta", "docker", "podman", "qemu-system-x86_64")
    tools = {name: shutil.which(name) is not None for name in names}
    return {
        "schema": "quartus-cloud-preflight/v1",
        "architecture": platform.machine(),
        "os": platform.system(),
        "memory_mib": mem_kib // 1024 if mem_kib else None,
        "tmp_free_gib": round(disk.free / 1024**3, 2),
        "tools": tools,
        "quartus": run(["quartus_sh", "--version"]) if tools["quartus_sh"] else {"status": "unavailable"},
        "classification": "READY_FOR_DEVICE_CHECK" if tools["quartus_sh"] else "NO_QUARTUS",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = json.dumps(probe(), sort_keys=True, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload)
    else:
        print(payload, end="")
