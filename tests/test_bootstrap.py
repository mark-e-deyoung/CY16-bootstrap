from cy16boot.asm import assemble
from cy16boot.common import le_to_word
from cy16boot.dis import disassemble
from cy16boot.scan import parse_scan, wrap_payload, SETUP_STUB_WORDS
from cy16boot.sim import run

SRC = ".org 0x1000\n_start:\n    mov [0xc03a], 0x23b3\n    ret\n"


def words(data):
    return [le_to_word(data, i) for i in range(0, len(data), 2)]


def test_scanwrap_stub_encoding():
    image, assembled_words, symbols = assemble(SRC, base=0x1000)
    assert words(image) == [0x07E7, 0x23B3, 0xC03A, 0xCF97]
    assert symbols["_start"] == 0x1000


def test_disassemble_stub():
    image, _, _ = assemble(SRC, base=0x1000)
    lines = disassemble(image, base=0x1000)
    assert "mov [0xc03a], 0x23b3" in lines[0]
    assert "ret" in lines[1]


def test_sim_stub_writes_memctl():
    image, _, _ = assemble(SRC, base=0x1000)
    cpu, trace = run(image, base=0x1000, pc=0x1000, max_steps=4)
    assert cpu.readw(0xC03A) == 0x23B3
    assert cpu.halted
    assert len(trace) == 2


def test_scanwrap_decode():
    image, _, _ = assemble(SRC, base=0x1000)
    scan = wrap_payload(image, 0x1000)
    records = parse_scan(scan)
    assert records[0].name == "COPY"  # alignment dummy
    assert records[1].payload == b''.join(bytes((w & 0xff, (w >> 8) & 0xff)) for w in SETUP_STUB_WORDS)
    assert records[-1].name == "CALL"
    assert records[-1].address == 0x1000
