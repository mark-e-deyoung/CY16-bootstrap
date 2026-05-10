# DE2-115 integration path

The compiler project should eventually feed the existing `SemperSupra/DE2-115` project by producing SCAN images that the VexRiscv/LiteX firmware can host-parse and load over the CY7C67200 HPI port.

## Proposed handoff artifact

```text
build/app.scan
```

## Loader model

The DE2-115 firmware should parse SCAN records:

```text
COPY -> write payload through HPI address/data registers
CALL -> write COMM_CODE_ADDR and send COMM_CALL_CODE or equivalent
JUMP -> write COMM_CODE_ADDR and send COMM_JUMP2CODE or equivalent
```

## Required validation ladder

Before loading compiler-generated code on hardware:

1. `cy16-scan-decode app.scan` succeeds.
2. Raw payload disassembles with `cy16-dis`.
3. Raw payload runs in `cy16-sim` if it does not depend on hardware.
4. DE2-115 HPI readback is proven: CY control registers and RAM write/read must return nonzero/plausible values.

## Current caution

If CY7C67200 HPI reads still return `0x0000`, compiler-generated code should not be used to debug USB class behavior yet. Fix HPI electrical/protocol readback first.
