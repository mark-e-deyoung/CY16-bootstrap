$ErrorActionPreference = 'Stop'
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -e . pytest
pytest -q
New-Item -ItemType Directory -Force build | Out-Null
cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000 --lst build/setup_stub.lst --map build/setup_stub.map
cy16-dis build/setup_stub.bin --base 0x1000
cy16-sim build/setup_stub.bin --base 0x1000 --pc 0x1000 --dump 0xc03a
cy16-scanwrap build/setup_stub.bin build/setup_stub.scan 0x1000
cy16-scan-decode build/setup_stub.scan
