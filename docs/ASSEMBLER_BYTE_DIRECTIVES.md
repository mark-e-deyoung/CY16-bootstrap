# Bootstrap assembler byte-directive layout

The CY16 bootstrap assembler supports a flat byte stream for:

```text
.byte
.ascii
.asciz
.space
.skip
```

These directives pack contiguously. An odd-length directive does not force alignment before another byte directive. The final flat binary remains padded with one zero byte when needed because the current listing/output model stores 16-bit `Word` records.

## Word statements must start at even addresses

Instructions and word directives cannot safely begin at an odd address in the current assembler. The assembler now rejects them explicitly:

```text
word statement starts at odd address
```

Add an explicit pad byte before the word statement:

```asm
.ascii "ABC"
.byte 0
next:
    ret
```

Here `next` is at the even address four bytes after the start of the string.

Two single-byte directives can also restore alignment naturally:

```asm
.byte 0x11
.byte 0x22
next:
    ret
```

The bytes `11 22` are contiguous and `next` is two bytes after the first directive.

## Why this check exists

Previously, first-pass `.byte` sizing rounded to a whole word while second-pass byte emission advanced by the raw byte count. Other byte directives advanced by raw count in both passes. A word statement after an odd byte count could therefore be encoded at an odd address or overlap a temporary zero pad in the `Word` representation while the symbol table described another address.

The corrected policy is:

- all byte directives advance by their raw byte count in both passes;
- byte directives may begin and end at odd addresses;
- word-emitting statements require an even current address;
- the final image may contain one trailing zero storage pad.

This preserves the existing GNUPro-oriented flat byte behavior while failing closed before an invalid or overlapping instruction layout is emitted.

## Compatibility boundary

This remains a bootstrap assembler, not a complete section/relocation implementation. It does not yet provide `.align` or automatic instruction alignment. Alignment must be explicit in source.

Short/long branch relaxation uses first-pass addresses. PR integration must preserve raw byte-directive sizing and the odd-word-start check so branch targets equal the actual emitted label.
