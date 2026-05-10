# Legal and IP notes

This bootstrap package is original source code and original documentation summaries generated for the CY16 toolchain effort.

## chibicc

chibicc is MIT-licensed upstream. If vendored, preserve its `LICENSE` file and record the exact commit in `third_party/chibicc-upstream-commit.txt`.

## Cypress/Infineon materials

The Cypress/Infineon documents are used as reference material. Avoid copying proprietary tables, large excerpts, or source code into public project files unless the applicable license permits that use. Prefer short factual summaries with citations to the original document name and page/section.

## Old GNUPro materials

The old Red Hat GNUPro CY16 toolchain may contain GPL components, permissive components, and proprietary/restricted documentation. Treat binaries as historical references. If source patches are recovered, inspect license files before reuse.

## GPL Linux driver-derived material

If register headers or LCP constants are copied from GPL Linux driver source, isolate them and decide whether the resulting project or component must be GPL-compatible. A clean alternative is to regenerate register definitions from public datasheets and hand-authored notes.
