# CY16 SCAN artifact manifest v1

The CY16 SCAN artifact manifest is the machine-readable handoff contract between this producer toolchain and host/FPGA consumers such as `SemperSupra/DE2-115`.

The manifest does not replace SCAN parsing, authorize execution, or prove authenticity. It binds a raw binary, a SCAN image, their parsed record inventory, build metadata, and deployment constraints so a consumer can fail closed when files or metadata disagree.

## Canonical files

- JSON Schema: `spec/cy16-scan-artifact-v1.schema.json`
- Generator/validator: `cy16-scan-manifest`
- Python implementation: `src/cy16boot/artifact_manifest.py`
- Canonical generation recipe: `examples/scan_artifact_v1/README.md`

The schema identifier is:

```text
cy16-scan-artifact/v1
```

Schema version `1` is intentionally strict. A consumer must reject an unknown version rather than silently interpreting it as v1.

## Manifest model

A v1 manifest records:

- target family and exact device;
- BIOS-cooperative, standalone, or unknown execution model;
- producer repository, commit, tool, and tool version;
- little-endian byte order;
- raw binary and SCAN relative paths, sizes, and SHA-256 values;
- load address and entry point;
- the ordered SCAN record inventory;
- required loader features derived from actual opcodes;
- constraints, warnings, and provenance notes.

Each record includes its file offset, opcode and canonical name, encoded length, total record size, effective address, payload size, and payload SHA-256. `WRITE_CONFIG` records also expose their original one-byte configuration offset and 16-bit value.

## Generation

The raw binary and SCAN image must be inside the output manifest's directory tree. This keeps every stored path relative and prevents a manifest from reaching outside its artifact bundle.

```sh
cy16-scan-manifest create \
  build/setup_stub.bin \
  build/setup_stub.scan \
  build/setup_stub.manifest.json \
  --load-address 0x1000 \
  --entry-point 0x1000 \
  --execution-model bios-cooperative \
  --target-device CY7C67200 \
  --producer-repository mark-e-deyoung/CY16-bootstrap \
  --producer-commit "$(git rev-parse HEAD)" \
  --constraint "Requires BIOS LCP CALL support."
```

Generation parses the SCAN bytes and verifies that:

1. the SCAN stream is structurally valid and has no non-zero trailing data;
2. a `COPY` record contains the exact raw binary at the declared load address;
3. a `CALL` or `JUMP` record transfers control to the declared entry point;
4. file and payload hashes are calculated from the actual bytes;
5. required loader features are derived from the parsed record set.

JSON output uses sorted keys, fixed indentation, ASCII escaping, and a trailing newline so identical inputs and metadata produce identical manifest bytes.

## Validation

```sh
cy16-scan-manifest validate build/setup_stub.manifest.json
```

Validation is independent of generation metadata. It:

- rejects unknown schema versions, artifact kinds, targets, execution models, and byte order;
- rejects absolute paths, parent traversal, and Windows-style separators;
- requires every referenced file to exist under the manifest directory;
- recomputes file sizes and SHA-256 values;
- parses the actual SCAN stream again;
- reconstructs and compares every record entry;
- recomputes required loader features;
- confirms raw-binary COPY and entry-point transfer relationships.

The implementation uses only the Python standard library. The JSON Schema is provided for ecosystem interoperability, while the project validator enforces the cross-file checks JSON Schema cannot express.

## Consumer policy

A consumer must still maintain its own capability and safety policy.

In particular:

- a valid manifest is not a digital signature;
- a valid `WRITE_CONFIG` record does not authorize a control-register write;
- unknown required loader features must be rejected;
- the consumer must parse the SCAN file rather than trusting the record list;
- runtime range, alignment, readback, and control-record gates remain mandatory;
- target-device compatibility must be checked before embedding or loading.

For the DE2-115 project, the C SCAN loader remains authoritative for executable operations. The manifest validator is an earlier supply-chain and integration gate.

## Execution models

### `bios-cooperative`

The image expects the mask-ROM BIOS and its LCP/SCAN services to remain available. CALL/JUMP behavior and any BIOS software interrupt use must be documented in constraints.

### `standalone`

The image may replace or bypass normal BIOS-cooperative behavior. Consumers should expect configuration writes or a different runtime ownership model and require explicit review.

### `unknown`

Use only for recovered artifacts whose execution model has not been established. Consumers should normally reject deployment while still allowing archival validation and inventory.

## `WRITE_CONFIG`

For SCAN opcode `0x09`, the manifest records both:

- `config_offset`: the original one-byte offset;
- `address`: the derived `0xC000 | config_offset` full address;
- `value`: the little-endian 16-bit value.

Generation automatically adds this warning:

```text
WRITE_CONFIG requires a policy-gated COMM_WRITE_CTRL_REG consumer; this manifest does not authorize execution.
```

## Release and provenance discipline

For release artifacts:

1. generate from a clean, identified commit;
2. provide the real 40-character producer commit;
3. keep the raw binary, SCAN image, and manifest together;
4. retain build logs and source-license information separately;
5. sign the release or artifact bundle when authenticity matters;
6. never use a manifest to conceal unknown or proprietary provenance.

The manifest itself contains metadata and hashes only; it does not embed source or firmware bytes.
