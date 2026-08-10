# CY16 container and developer-environment strategy

This document is the authoritative container/DX contract for CY16-bootstrap.
The canonical cross-platform path is a disposable Linux container so the same
compiler/test environment can be used from Windows, Linux, and eventually macOS
hosts without installing a native C toolchain on every machine.

## Host contract

Normal development host prerequisites are deliberately small:

- Git;
- Python 3.10+ for the repo launcher and agent preflight;
- Docker Engine on Linux or Docker Desktop on Windows/macOS;
- GitHub CLI when doing agent/GitHub workflow work.

The repository does not silently install privileged system packages. A fresh
machine runs `scripts/dev.py doctor`, installs only the missing host basics, then
runs `scripts/dev.py bootstrap` once a supported container runtime is available.

### Optional shared workstation bootstrap

The reusable host-prerequisite layer is being developed in
`SupraShellScripts/stateless-dev-tooling` issue #10 / PR #11. CY16-bootstrap does
not depend on that repository and remains independently bootstrappable.

When the shared tooling repository is present in the development workspace, the
CY16 host profile is simply:

```text
base + container
```

The shared helper owns only host prerequisite/package-manager and container
runtime discovery. CY16-bootstrap continues to own the compiler/test/runtime
image, exact tool behavior, validation ladder, generated artifacts, and CY16
semantics. Do not copy shared package-manager logic into this repository.

## Build stages

The single `Dockerfile` has three roles:

### `builder`

Contains only build/test dependencies:

- GCC + libc development headers;
- make;
- Python + pip/setuptools/wheel;
- pytest and pycparser.

It builds one CY16 Python wheel, installs that exact wheel into the builder for
validation, stages the same wheel under `/runtime-root`, and builds the
chibicc-derived C binary.

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

Linux/macOS POSIX shell:

```bash
./scripts/dev.sh doctor
./scripts/dev.sh bootstrap
./scripts/dev.sh test
./scripts/dev.sh tool cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000
```

Direct Python is equivalent on each source host:

```text
python scripts/dev.py bootstrap
```

Compatibility wrappers `scripts/bootstrap.ps1` and `scripts/bootstrap.sh`
delegate to the same portable bootstrap. `scripts/run_docker.ps1` delegates to
the locked-down `cy16-cc` runtime path.

Linux container execution is validated. The Windows and macOS launchers are
validated, but Docker Desktop project-container execution on those two OSes is a
local-machine gate.

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

| Capability | Windows | Linux | macOS |
|---|---|---|---|
| Source/agent launcher | validated PowerShell/Python surface | validated | validated POSIX/Python surface on hosted Mac |
| Canonical Docker build/test/runtime | first-class design; Docker Desktop execution still needs local validation | validated on Ubuntu 24.04 CI | intended through Docker Desktop; project-container execution still needs local validation |
| Native Python-only tools | supported | supported | launcher/import surface expected from same Python package |
| Native full C compiler ladder | optional; environment-dependent | supported with GCC/make | not required or validated |

A hosted Mac now validates the project POSIX/Python launcher and diagnostic
surface. No separate macOS compiler/toolchain design is planned; the remaining
macOS work is container-runtime/volume behavior on an actual development Mac.

## Reproducibility boundary

The Docker base is pinned to the reviewed Debian manifest digest used by the
successful Linux validation run:

```text
debian:trixie-slim@sha256:3a39a0592364683e6bab97937b72cad5a8fa6dcbbee90edb3bb48c7f8e94f258
```

GitHub Actions dependencies are also commit-pinned. The validated Linux runtime
image was 109.4 MiB, defaulted to a non-root user, declared no persistent volume,
and passed the locked-down portable-wrapper smoke test.

This is reproducible at the base-image/source level, but it is not yet a
bit-for-bit hermetic package build: `apt-get` still resolves Debian packages from
the active Trixie repositories at image-build time. If byte-for-byte rebuilds
become necessary, add an explicit Debian snapshot/package lock rather than
silently depending on current repository state. Linux amd64 is the fully
validated container target today; Windows/macOS Docker behavior and other CPU
architectures are not yet claimed.

Container changes must not alter CY16 ISA/ABI, assembler, simulator, SCAN, or
compiler semantics merely to make image construction convenient.
