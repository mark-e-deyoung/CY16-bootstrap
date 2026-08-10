#!/usr/bin/env python3
"""Portable host wrapper for CY16-bootstrap.

The canonical cross-platform path is containerized. This launcher performs no
privileged host installation and never starts a persistent container.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
DEFAULT_IMAGE = "cy16-bootstrap:local"
TOOLS = (
    "cy16-cc",
    "cy16-chibicc",
    "cy16-as",
    "cy16-dis",
    "cy16-sim",
    "cy16-scanwrap",
    "cy16-scan-decode",
)


class DevError(RuntimeError):
    pass


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    shown = subprocess.list2cmdline(cmd) if os.name == "nt" else " ".join(cmd)
    print(f"+ {shown}")
    proc = subprocess.run(cmd, cwd=cwd or ROOT)
    if proc.returncode:
        raise DevError(f"command failed with exit code {proc.returncode}: {shown}")


def command(name: str) -> str | None:
    return shutil.which(name)


def doctor(_: argparse.Namespace) -> None:
    print(f"Repository: {ROOT}")
    print(f"Host: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {platform.python_version()}")
    missing = []
    for name in ("git", "docker"):
        found = command(name)
        print(f"[{'OK' if found else 'MISSING'}] {name}: {found or 'not found'}")
        if not found:
            missing.append(name)
    gh = command("gh")
    print(f"[{'OK' if gh else 'OPTIONAL'}] gh: {gh or 'not found'}")
    if missing:
        print("\nThis repo does not install privileged host packages automatically.")
        raise DevError("doctor found missing required capabilities: " + ", ".join(missing))
    print("\nHost is ready for the canonical containerized CY16 workflow.")
    if sys.platform == "darwin":
        print("macOS is not validated by this project yet; Docker/source workflow is the intended future path.")


def image_name(args: argparse.Namespace) -> str:
    return args.image or os.environ.get("CY16_IMAGE", DEFAULT_IMAGE)


def test(args: argparse.Namespace) -> None:
    run(["docker", "build", "--target", "test", "-t", f"{image_name(args)}-test", "."])


def image(args: argparse.Namespace) -> None:
    run(["docker", "build", "--target", "runtime", "-t", image_name(args), "."])


def bootstrap(args: argparse.Namespace) -> None:
    doctor(args)
    if not args.no_test:
        test(args)
    image(args)
    print(f"\nCY16 runtime image ready: {image_name(args)}")


def linux_user_args() -> list[str]:
    if os.name != "nt" and hasattr(os, "getuid") and hasattr(os, "getgid"):
        uid, gid = os.getuid(), os.getgid()
        if uid != 0:
            return ["--user", f"{uid}:{gid}"]
    return []


def tool(args: argparse.Namespace) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    root = str(ROOT.resolve())
    build = str(BUILD.resolve())
    docker_cmd = [
        "docker", "run", "--rm",
        "--read-only",
        "--network", "none",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m",
        *linux_user_args(),
        "-e", "HOME=/tmp",
        "-v", f"{root}:/work:ro",
        "-v", f"{build}:/work/build:rw",
        "-w", "/work",
        "--entrypoint", args.tool,
        image_name(args),
        *args.tool_args,
    ]
    run(docker_cmd)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Portable CY16-bootstrap developer wrapper")
    p.add_argument("--image", help=f"local runtime image tag (default: {DEFAULT_IMAGE})")
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("doctor", help="diagnose host prerequisites")
    d.set_defaults(func=doctor)

    b = sub.add_parser("bootstrap", help="validate and build the local runtime image")
    b.add_argument("--no-test", action="store_true", help="skip isolated test-stage build")
    b.set_defaults(func=bootstrap)

    t = sub.add_parser("test", help="build the isolated Docker test target")
    t.set_defaults(func=test)

    i = sub.add_parser("image", help="build the minimal runtime image")
    i.set_defaults(func=image)

    x = sub.add_parser("tool", help="run one CY16 CLI in a locked-down disposable container")
    x.add_argument("tool", choices=TOOLS)
    x.add_argument("tool_args", nargs=argparse.REMAINDER)
    x.set_defaults(func=tool)
    return p


def main() -> int:
    try:
        args = parser().parse_args()
        args.func(args)
        return 0
    except DevError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
