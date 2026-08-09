# Bootstrap assembler byte-directive layout

The CY16 bootstrap assembler currently emits 16-bit `Word` records rather than general byte segments. These byte-oriented directives therefore occupy a whole number of words:

```text
.byte
.ascii
.asciz
.space
.skip
```

Occupied size is:

```text
(raw byte count + 1) & ~1
```

An odd raw byte count receives one zero pad byte. The next label or statement begins after that pad at an even address.

Example:

```asm
.byte 0xaa
next:
    ret
```

emits `aa 00` followed by the RET word, and `next` is two bytes after the directive.

Previously, the two passes disagreed: some first-pass calculations used padded size, while the second pass emitted padding but advanced by raw size. A following instruction could overlap the pad byte and disagree with the symbol map. Both passes now use the same padded size and advance by the bytes actually emitted.

This is a project-specific bootstrap limitation, not complete GNU assembler compatibility. Adjacent odd directives do not pack together. A future byte-segment implementation would change symbols and binary layout and must be handled as a versioned compatibility change.

Short/long jump relaxation depends on the same first-pass addresses. Control-flow integration must preserve the shared padded-size helper so encoded targets match emitted labels.
