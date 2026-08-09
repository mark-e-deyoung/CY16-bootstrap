# Canonical SCAN artifact v1 example

This example regenerates a complete manifest bundle from the existing setup-stub validation anchor. No proprietary binary is stored in this directory; the binary and SCAN image are produced from project source during CI.

## Generate

From the repository root after installing the package:

```sh
mkdir -p build/scan-artifact-v1

cy16-as examples/setup_stub.s \
  -o build/scan-artifact-v1/setup_stub.bin \
  --base 0x1000 \
  --lst build/scan-artifact-v1/setup_stub.lst \
  --map build/scan-artifact-v1/setup_stub.map

cy16-scanwrap \
  build/scan-artifact-v1/setup_stub.bin \
  build/scan-artifact-v1/setup_stub.scan \
  0x1000

cy16-scan-manifest create \
  build/scan-artifact-v1/setup_stub.bin \
  build/scan-artifact-v1/setup_stub.scan \
  build/scan-artifact-v1/setup_stub.manifest.json \
  --load-address 0x1000 \
  --entry-point 0x1000 \
  --execution-model bios-cooperative \
  --target-device CY7C67200 \
  --producer-repository mark-e-deyoung/CY16-bootstrap \
  --producer-commit "$(git rev-parse HEAD)" \
  --constraint "Requires BIOS LCP CALL support." \
  --provenance-note "Clean-room setup-stub validation fixture."

cy16-scan-manifest validate \
  build/scan-artifact-v1/setup_stub.manifest.json
```

## Stable byte anchors

For the current setup-stub source and SCAN wrapper behavior:

| File | Size | SHA-256 |
|---|---:|---|
| `setup_stub.bin` | 8 bytes | `fe76c3f54ae4d60c0cfa95df2e6cbf1832a3848d1051d060ba903b9f5e598322` |
| `setup_stub.scan` | 55 bytes | `125f299ca63447f56581cda452a878ba3c3189b6afb7bfd15917bedd44afc28c` |

The generated manifest itself includes the producer commit and therefore changes when intentionally generated from a different commit. Given identical files and metadata, its JSON bytes are deterministic.

## Expected record sequence

```text
0  COPY  address=0x00e0 payload=2
1  COPY  address=0x1000 payload=8   setup stub
2  CALL  address=0x1000
3  COPY  address=0x1000 payload=8   raw binary
4  CALL  address=0x1000             entry point
```

The duplicate payload is intentional in this small fixture: the raw program is the same known setup stub that `cy16-scanwrap` installs before copying the requested payload.
