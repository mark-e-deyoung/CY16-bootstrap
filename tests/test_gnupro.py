from cy16boot.asm import assemble
from cy16boot.dis import disassemble


def test_percent_register_syntax_matches_native_register_syntax():
    native, _, _ = assemble(
        """
        mov r0, 0x1234
        mov [r8], r0
        mov [--r15], r0
        mov r1, [r15++]
        """
    )
    gnupro, _, _ = assemble(
        """
        mov %r0, 0x1234
        mov [%r8], %r0
        mov [--%r15], %r0
        mov %r1, [%r15++]
        """
    )
    assert gnupro == native


def test_string_and_space_directives_emit_flat_binary_bytes():
    image, assembled_words, symbols = assemble(
        """
        .org 0x1000
        label:
        .ascii "A,\\n"
        .asciz "B"
        .space 3, 0x55
        .skip 1
        .bss
        """
    )
    assert symbols["label"] == 0x1000
    assert image == b"A,\nB\x00UUU\x00\x00"
    assert [w.addr for w in assembled_words] == [0x1000, 0x1002, 0x1003, 0x1005, 0x1007, 0x1008]


def test_disassemble_gnupro_register_output():
    image, _, _ = assemble(
        """
        mov %r0, 0x1234
        mov [%r8], %r0
        mov [--%r15], %r0
        mov %r1, [%r15++]
        """
    )
    text = "\n".join(disassemble(image, gnupro=True))
    assert "mov %r0, 0x1234" in text
    assert "mov [%r8], %r0" in text
    assert "mov [--%r15], %r0" in text
    assert "mov %r1, [%r15++]" in text
