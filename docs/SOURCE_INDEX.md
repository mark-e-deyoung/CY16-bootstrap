# CY16 and CY7C67x00 source/provenance index

This index connects each external source to the project decisions, implementation areas, and validation artifacts derived from it. It supplements `CITED_FINDINGS.md`, which records the principal technical findings.

## Source classifications

- **Normative** — vendor documentation used for the ISA, BIOS, device, or image format.
- **Behavioral reference** — source code or working examples used to cross-check behavior.
- **Artifact lead** — a filename, historical path, forum answer, or support record that points to material not yet recovered.
- **Project-owned fixture** — original code that reproduces documented behavior without copying restricted source.

## Normative and retained documents

| ID | Source | Role | Derived project artifacts |
|---|---|---|---|
| S1 | *GNUPro Toolkit User's Guide for Cypress Development* (`cy16.pdf`) | Historical tool names, staged compile/assemble/link/debug workflow, GNU syntax | `ARCHITECTURE.md`, GNUPro compatibility tests, Phase 10 |
| S2 | *CY16 Programmer's Guide v1.1* | Instruction encodings, addressing modes, flags, stack, interrupts, assembler macros | `ASM_SUBSET.md`, `ISA_CONFORMANCE_MATRIX.md`, assembler/disassembler/simulator tests |
| S3 | *CY16 Binary Utilities Reference* | SCAN records and legacy binary utilities | `SCAN_FORMAT.md`, `cy16-scanwrap`, `cy16-scan-decode` |
| S4 | *OTG-Host Boot Code Design* | Minimal startup, stack and `.bss` considerations, `-nostartfiles` model | `libcy16/startup_*.s`, runtime design |
| S5 | *OTG-Host BIOS User Manual* | Memory map, BIOS vectors, LCP, SCAN, stable software services | BIOS profiles, simulator/runtime wrappers, DE2 loader integration |
| S6 | Cypress `scanwrap.c` reference supplied with the project material | Golden setup-stub encoding and wrapping behavior | `tests/test_bootstrap.py`, `SETUP_STUB_WORDS` |
| S7 | AN048, *Building an EZ-Host / EZ-OTG Project From Start to Finish*, Rev. *B | Complete historical build recipe, linker base `0x1000`, startup alternatives, SCAN/EEPROM flow | `fixtures/an048-bal`, `AN048_BAL_COMPATIBILITY.md`, `tests/test_an048_fixture.py` |
| S8 | AN6010, *Using HPI in Co-Processor Mode with EZ-Host/EZ-OTG*, Rev. ** | HPI direct ranges, port directions, prefetch, LCP and host sequence | `DE2_115_INTEGRATION.md`; authoritative details live in `SemperSupra/DE2-115` |
| S9 | CY7C67200/CY7C67300 data sheets and errata | Register map, reset, HPI timing, silicon limitations | freestanding headers, hardware profiles, DE2 bring-up constraints |
| S10 | *USB Multi-Role Device Design By Example* | BIOS/framework architecture and application patterns | later runtime/framework compatibility work |

## External behavioral references

| ID | Reference | Pin/status | Relevant material | License/provenance treatment |
|---|---|---|---|---|
| R1 | Linux `drivers/usb/c67x00` | Snapshot used during this research: `torvalds/linux@bf4afc53b77aeaa48b5409da5c8da6bb4eff7f43` | low-level HPI, LCP, HCD, TD handling | GPL-2.0-or-later. Use as behavioral oracle or isolate copied code under a compatible license. |
| R2 | `markubiak/sv-parametric-equalizer` | `8e7a30fae34027629a318205da072e7ce01cf57c` | DE2-115 `hpi_io_intf.sv`, Nios USB keyboard example, large Cypress header, Qsys metadata | Exact license of Cypress/Terasic-derived files is uncertain. Do not silently relicense. |
| R3 | `asciilifeform/Stierlitz` | `783524ebb77b825a2ad6368bf7b3e60f23f7d738` | explicit CY7C67300 HPI state machine on ML501 | GPLv3-or-later; transaction/FSM reference only. |
| R4 | `SemperSupra/DE2-115` | companion project | HPI bridge, loader, recovered firmware, board-specific hardware validation | Project-owned code plus provenance-sensitive vendor artifacts. |

## Forum, KBA, and support-record leads

| ID | Lead | Recovery target or value |
|---|---|---|
| L1 | Infineon *CY7C67300 Interrupt Vector* answer | `Common/ISRS.S`, reportedly containing the full hardware-vector mapping |
| L2 | Infineon insert/remove interrupt KBA | Historical CY3663 Linux source path, `cy7C67200_300_hcd.c`, `hcd_irq_resumeX`, and initialization files |
| L3 | Infineon EOT-throughput KBA | `MAX_FRAME_BW`, `DEFAULT_EOT`, and `cy7c67200_300_hcd_simple.c` |
| L4 | Infineon standalone-over-coprocessor KBA | CY4640 v1.1+ SCAN parser and `COMM_WRITE_CTRL_REG` translation behavior |
| L5 | AMD/Xilinx Answer Record 31312 | `ml40x_usb.zip`, Cypress `SD1025`, and ML40x HPI reference material; current evidence is an archival lead only |
| L6 | Historical CY3663 installation tree | `Source/coprocessor/de_app`, `Source/coprocessor/linux`, `Common`, framework and utility sources |

See `CY3663_ARTIFACT_WANTED.md` for exact filenames, search results, and intake requirements.

## Project-owned clean-room fixtures

| Fixture | Source behavior represented | Validation |
|---|---|---|
| `examples/setup_stub.s` | `scanwrap.c` setup stub | exact words, round-trip disassembly, simulator, SCAN decode |
| `fixtures/an048-bal` | AN048 compile/link/base/SCAN workflow and volatile-MMIO characteristics | `tests/test_an048_fixture.py` |
| compiler feature tests | Programmer's Guide ISA and project ABI behavior | assembly, disassembly, simulator state |

## Provenance requirements

For every external artifact added later, record:

1. source URL or physical origin;
2. acquisition date;
3. original filename and archive hierarchy;
4. SHA-256;
5. license and redistribution disposition;
6. exact files/functions/pages used;
7. the original project code or test derived from it;
8. unresolved inconsistencies or assumptions.

Do not promote an artifact lead into a design requirement until the referenced material has been recovered and inspected.
