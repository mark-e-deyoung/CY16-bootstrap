# Wyse 5070 disposable RDTE

First executable slice: a **read-only** discover/plan utility.
No OS image writing, USB programming, device reset or secret access.

```sh
python3 lab/wyse5070/plan.py
python3 -m pytest -q lab/wyse5070/test_plan.py
```

For a blank controller, build/test in disposable public CI before
physical installation. Initial boot needs a prepared USB installer or
qualified PXE path; do not pretend SSH provisioning is possible without
an installed OS. Later stages should add version-pinned autoinstall,
offline install-media tests, and a rollback/recovery rehearsal.
Never put private source material in public CI.
