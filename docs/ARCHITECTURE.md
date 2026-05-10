# CY16 compiler architecture

## Tool pipeline

```text
C source
  -> cy16-cc -S               # chibicc frontend + CY16 backend
  -> CY16 assembly
  -> cy16-as                  # project assembler
  -> raw binary + listing/map
  -> cy16-dis                 # inspection/round-trip validation
  -> cy16-sim                 # simulator execution validation
  -> cy16-scanwrap            # BIOS/HPI-loadable SCAN image
  -> hardware loader path
```

## Repository structure

```text
cy16-toolchain/
  docs/
  prompts/
  scripts/
  src/
    cy16boot/      # bootstrap Python tools
    cy16cc/        # chibicc-derived compiler port
  include/         # freestanding C headers, added later
  libcy16/         # startup/runtime/linker files
  examples/
  tests/
  third_party/
```

## Why assembly output first?

Assembly output keeps the backend inspectable and lets us avoid object-file and relocation complexity until the ISA, ABI, startup, and SCAN packaging are proven. It also mirrors the historical GNU staged model without requiring a full GCC/binutils recreation up front.

## Validation strategy

Each compiler feature must pass this ladder:

```text
C test -> CY16 assembly -> cy16-as -> cy16-dis -> cy16-sim -> expected state
```

Deployment packaging adds:

```text
raw binary -> cy16-scanwrap -> cy16-scan-decode -> HPI/BIOS loader
```

## Bootstrap limitations

The included `cy16-as` is intentionally tiny. It is anchored on the verified Cypress scanwrap setup-stub encoding and only supports a small subset. Agents should extend it incrementally with tests.
