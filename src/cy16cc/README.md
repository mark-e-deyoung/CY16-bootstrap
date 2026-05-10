# cy16cc source placeholder

The final CY16 C compiler should be implemented here as a chibicc-derived frontend plus CY16 backend.

Recommended import strategy:

1. Run `scripts/vendor_chibicc.sh` to vendor a pinned MIT-licensed chibicc commit under `third_party/chibicc-upstream`.
2. Copy selected frontend files into this directory or wrap them as a separately built library.
3. Delete/disable the x86-64 code generator.
4. Add:
   - `cy16_target.c/.h`
   - `cy16_ir.c/.h`
   - `cy16_codegen.c/.h`
   - `cy16_regalloc.c/.h`
   - `cy16_emit.c/.h`
5. Emit CY16 assembly first. Do not emit ELF in v0.

See `docs/POAM.md` and `prompts/AGENT_BOOTSTRAP_PROMPT.md`.
