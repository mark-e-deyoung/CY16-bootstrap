# CY16 container and developer-environment strategy

This document is the authoritative container/DX contract for CY16-bootstrap.
The canonical cross-platform path is a disposable Linux container so the same
compiler/test environment can be used from Windows and Linux hosts without
installing a native C toolchain on every machine.

## Host contract

Normal development host prerequisites are deliberately small:

- Git;
- Python 3.10+ for the repo launcher and agent preflight;
- Docker Engine on Linux or Docker Desktop on Windows;
- GitHub CLI when doing agent/GitHub workflow work.

The repository does not silently install privileged system packages. A fresh
machine runs `scripts/dev.py doctor`, installs only the missing host basics, then
runs `scripts/dev.py bootstrap`.

## Build stages

The single `Dockerfile` has three roles:

### `builder`

Contains only build/test dependencies:

- GCC + libc development headers;
- make;
- Python + pip/setuptools/wheel;
- pytest and pycparser.

It installs the CY16 Python package, builds the chibicc-derived C binary, and
stages only runtime Python files under `/runtime-root`.

### `test`

Extends `builder` and runs the isolated validation ladder:

- `pytest -q`;
- assemble/disassemble/simulate the setup stub;
- wrap/decode the setup-stub SCAN artifact;
- compile `write_memctl.c` with the chibicc-derived binary;
- assemble/simulate the resulting CY16 assembly.

Canonical isolated validation:

```text
python scripts/dev.py test
```

or directly:

```text
docker build --target test -t cy16-bootstrap:local-test .
```

No running test container is retained.

### `runtime`

Contains only:

- `python3-minimal`;
- Debian's `python3-pycparser`;
- installed CY16 Python package/console scripts;
- the compiled chibicc-derived binary under the unambiguous name
  `cy16-chibicc`.

The final image does **not** contain GCC, make, libc development headers, pip,
pytest, the repository checkout, tests, docs, or patch artifacts. It has no
`VOLUME` declaration and runs as a numeric non-root user by default.

The Python `cy16-cc` console entrypoint and compiled `cy16-chibicc` binary are
intentionally distinct. They are different implementation paths and must not
silently overwrite one another in the image.

## Build context

`.dockerignore` is default-deny. Only the files actually consumed by the build
or test target are sent to Docker. Tracked object files and `.orig`/`.rej`
artifacts are excluded even inside included source directories.

## Stateless runtime

`scripts/dev.py tool ...` launches a new container for every invocation with:

```text
container root filesystem      read-only
runtime network                disabled
Linux capabilities             all dropped
no-new-privileges              enabled
/tmp                            disposable tmpfs
repository                     /work read-only
host build directory           /work/build read-write
container lifetime             one command (--rm)
```

On Linux the wrapper uses the invoking non-root UID/GID so generated files in
`build/` remain owned by the developer. On Docker Desktop the image's non-root
identity is used.

The only intended persistent state is explicit host output under `build/`.
There is no named/anonymous Docker volume, background service, or follow-on
`docker exec` workflow.

## Portable commands

Windows PowerShell:

```powershell
.\scripts\dev.ps1 doctor
.\scripts\dev.ps1 bootstrap
.\scripts\dev.ps1 test
.\scripts\dev.ps1 tool cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000
```

Linux/POSIX shell:

```bash
./scripts/dev.sh doctor
./scripts/dev.sh bootstrap
./scripts/dev.sh test
./scripts/dev.sh tool cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000
```

Direct Python is equivalent on either platform:

```text
python scripts/dev.py bootstrap
```

Compatibility wrappers `scripts/bootstrap.ps1` and `scripts/bootstrap.sh`
delegate to the same portable bootstrap. `scripts/run_docker.ps1` delegates to
the locked-down `cy16-cc` runtime path.

## Native development

A native Python venv remains possible for contributors who deliberately want it:

```text
python -m venv .venv
python -m pip install -e . pytest pycparser
```

But the native full validation ladder also needs a compatible C compiler and
`make`. That is straightforward on Linux, variable on Windows, and unnecessary
for normal cross-machine use. The container path is authoritative for portable
validation.

## Platform support

| Capability | Windows | Linux | macOS (future) |
|---|---|---|---|
| Source/agent work | first-class | first-class | expected; not validated here |
| Canonical Docker build/test/runtime | first-class | first-class | expected through Docker Desktop; not validated here |
| Native Python-only tools | supported | supported | expected |
| Native full C compiler ladder | optional; environment-dependent | supported with GCC/make | not validated |

No macOS success claim is made because there is no Mac available for project
validation. The architecture intentionally avoids Windows/Linux-specific paths
so a future Mac should require only wrapper/volume verification rather than a
new toolchain design.

## Reproducibility boundary

The container removes host-OS variance, but the current Debian base tag is still
a mutable upstream tag. Before publishing a long-lived shared GHCR runtime image,
pin the reviewed multi-architecture base digest and record the image provenance.
Do not invent or copy a digest without validating it against the local Docker
builder/target platforms.

Container changes must not alter CY16 ISA/ABI, assembler, simulator, SCAN, or
compiler semantics merely to make image construction convenient.
