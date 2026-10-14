# Wyse 5070 CY16 hardware lab controller

**Recommended baseline:** Ubuntu Server 22.04 LTS x86-64 minimal;
systemd host services and rootless Podman/Quadlet for analysis jobs.
Target known inventory: Wyse 5070 Pentium Silver, 8 GiB RAM,
512 GB SSD. Re-inventory before deployment. Status: **proposed,
not installed**.

## Why Linux, not Windows

The target is an always-on remote physical-instrument controller:
USB-Blaster/JTAG, UART, Beagle USB 12, AgentWebCam, AgentKVM2USB,
network/serial capture and safe board power/reset. Linux offers
udev, stable /dev/serial/by-id links, systemd restart controls,
device cgroups, SSH, and container orchestration. Keep Quartus
Prime Lite 25.1 + Cyclone IV support on a pinned, validated
Linux runtime; do not assume that Quartus Pro supports this FPGA.
A Windows VM is only an escape hatch for a demonstrated
Windows-only instrument driver, not the primary control plane.

Altera OS compatibility table lists Ubuntu 22.04 for Lite:
https://www.altera.com/design/guidance/software/os-support
Quartus Lite 25.1 Linux distribution:
https://www.altera.com/downloads/fpga-development-tools/quartus-prime-lite-edition-design-software-version-25-1-linux

## Host layout

- `/etc/cy16-lab/`: declarative, reviewed config and allowlists.
- `/opt/cy16-lab/`: pinned lab-worker release and read-only tools.
- `/var/lib/cy16-lab/`: durable device census, board identities,
  leases, manifests and receipts.
- `/var/spool/cy16-lab/`: bounded experiment queue and raw traces.
- `/srv/cy16-lab/cache/`: verified Quartus/FPGA artifact cache;
  prune by quotas, never delete active run artifacts.
- systemd `cy16-lab-discover.service`,
  `cy16-lab-worker.service`, optional timer for read-only
  health probes; hardware execution only under explicit gate.
- rootless Podman Quadlet for offline simulator/compiler and
  evidence processing; no `--privileged` or blanket `/dev/bus/usb`.
- dedicated non-root `cy16lab` identity; udev ACL/group for
  exact observed vendor/product/serial; no MODE=0666 wildcard.
- remote Agent Dispatch submits signed/hash-pinned work orders;
  worker returns immutable results and monotonic sequence IDs.

## Instrumentation

USB-Blaster: identify actual USB VID/PID and serial, use
`jtagconfig` read-only first; programming separately gated.
Beagle USB 12: validate actual host capture SDK and permissions;
USB traffic capture does not reveal CY16 internal CPU state.
AgentWebCam: time-stamped board LEDs/display and power-state
visuals; privacy-aware local retention.
AgentKVM2USB: display/keyboard/mouse if connected to a
meaningful target, not a substitute for HPI register capture.
Serial: stable `/dev/serial/by-id` and exclusive leases.
HPI: FPGA sequencer with read-only gate first, timeouts,
bounded address allowlists and raw bus transaction receipts.
Optional managed power relay only after device identity and
safe power sequencing are verified.

## Setup automation: Discover -> Plan -> Apply -> Verify

**D0 discovery (safe):** collect `/etc/os-release`, `uname`,
CPU/RAM/storage, `lsusb`, `udevadm`, `/dev/serial/by-id`,
`jtagconfig` availability, `quartus_sh --version`, connected
instrument IDs, current networking and SSH route. Do not
read secrets or run destructive commands.

**P0 plan:** produce a machine-readable desired-state diff,
estimated storage and reboot impacts, exact package versions,
checksum-verified Quartus archive location, device mapping and
rollback procedure. Refuse unknown board identity or unsafe
udev grants.

**A0 apply:** package manager dependencies, dedicated service
account, bounded device permissions, verified Quartus install
from locally supplied licensed vendor artifacts, immutable
workcell image, Quadlet units and Agent Dispatch registration.
Idempotent, rerunnable, no arbitrary remote shell. Pin
packages and record prior state for rollback.

**V0 verify:** reboot survivability, SSH/remote reachability,
board/instrument census, Quartus Cyclone IV device support,
JTAG read-only enumeration, Beagle capture self-test,
webcam/KVM capture where connected, simulator smoke,
dry-run experiment receipt and recovery rehearsal.

**A1 (separate approval):** FPGA programming and read-only HPI.
**A2 (separate S04 approval):** bounded HPI RAM write/restore.
**A3:** independently encoded probe execution.
**A4:** compiler/emulator/hardware recovery flywheel.

## Constraints and failure handling

No automatic OS reimage without a known recovery path.
No secrets committed to repositories; file-backed scoped
credentials and SSH host-key verification. Never permit
untrusted compiler output to directly program FPGA or
access raw USB. One active board lease per board. Lab worker
must survive host reboot but default to read-only discovery.
No private GitHub-hosted Actions minutes; Agent Dispatch
runtimes must be checked including dispatcher control plane.
Use independent storage for durable experiment artifacts.
No claim of full automation until physical host is reachable,
vendor Quartus media is present, and each instrument's Linux
driver/SDK is qualified.

## What remains for zero-touch installation

A verified route to this Wyse over SSH or an existing
provisioning mechanism, initial Ubuntu installation/reimage
authority, Quartus 25.1 vendor distribution and Cyclone IV
device files (official download may require authenticated
acceptance), and a physical cable/USB inventory. The rest
can be delivered as a versioned IaC workset and applied
remotely after discovery. Do not assume an available host
or credentials from prior conversation alone.
