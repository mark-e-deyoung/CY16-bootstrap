from pathlib import Path

from cy16boot.asm import assemble
from cy16boot.scan import parse_scan, wrap_payload
from cy16boot.sim import run
from cy16cc.codegen import compile_c


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "an048-bal"


def test_an048_clean_room_fixture_compile_simulate_and_scanwrap():
    c_source = (FIXTURE_DIR / "BAL.c").read_text(encoding="utf-8")
    assembly = compile_c(c_source)
    image, _, symbols = assemble(assembly, base=0x1000)

    entry = symbols["_bal_fixture"]
    initial_regs = [0] * 16
    initial_regs[15] = 0xF000

    cpu, trace = run(
        image,
        base=0x1000,
        pc=entry,
        max_steps=100,
        initial_regs=initial_regs,
    )

    assert not any(line.startswith("ERROR:") for line in trace), trace
    assert cpu.readw(0xC03A) == 0x23B3
    assert cpu.regs[0] == 0x23B3

    scan_image = wrap_payload(image, 0x1000, call_address=entry)
    records = parse_scan(scan_image)

    assert any(
        record.name == "COPY"
        and record.address == 0x1000
        and record.payload == image
        for record in records
    )
    assert records[-1].name == "CALL"
    assert records[-1].address == entry
