# SCAN artifact manifest validation levels

`cy16-scan-artifact/v1` has multiple validation levels. They answer different questions and must not be treated as interchangeable.

## Metadata-only validation

`validate_manifest_data(..., verify_files=False)` validates the JSON object without opening artifact files.

It verifies:

- schema, artifact, target, execution-model, byte-order, producer, image, and descriptor shapes;
- safe relative path syntax;
- integer and digest formats;
- record indexes and contiguous offsets beginning at zero;
- `record_size == encoded_length + 5`;
- canonical known-opcode names;
- COPY length equals address bytes plus payload size;
- CALL and JUMP have exactly a 16-bit address and no payload;
- WRITE_CONFIG has the offset/value shape and `0xC000 | offset` address mapping;
- unknown opcodes use the explicit generic address-record shape;
- `required_loader_features` equals the sorted unique record-name set.

Metadata-only validation proves that the manifest describes one internally consistent record layout. It does not prove that any file exists or that the record inventory matches actual SCAN bytes.

## File-backed producer validation

`validate_manifest_file()` and the CLI `validate` command additionally:

- open the raw binary and SCAN files beneath the manifest directory;
- verify size and SHA-256 descriptors;
- parse the SCAN bytes;
- compare the complete parsed inventory with manifest metadata;
- derive and compare loader features;
- require the SCAN image to COPY the exact raw binary at the declared load address;
- require CALL or JUMP to the declared entry point.

This is the producer repository's complete internal-consistency check.

## Independent consumer validation

The DE2-115 repository retains a separately written parser and policy implementation. Producer validation must not replace it.

The consumer independently verifies the files and bytes, then applies DE2-115-specific static loadability policy. Runtime HPI range checks, COPY readback, LCP health, and physical-board evidence remain later authoritative gates.

## Trust boundary

None of these levels:

- authenticate the claimed repository or commit;
- act as a signature;
- prove reproducible compilation;
- authorize WRITE_CONFIG or another control operation;
- prove that the hardware can execute the image.

The schema remains v1 because this hardening does not change serialized fields or meanings. It makes existing relationships fail closed earlier.
