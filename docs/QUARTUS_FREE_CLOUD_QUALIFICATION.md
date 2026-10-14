# Quartus 25.1 DE2-115 cloud qualification contract

Main quest. This is a *preflight/acceptance contract*, not proof that
Quartus has been installed or executed.

## Critical acceptance

- A pinned, license-compliant Quartus Prime Lite 25.1 standard
  image including **Cyclone IV E** device support.
- A fresh free-tier disposable Linux executor can pull/use the
  image and run `quartus_sh --version`.
- The executor compiles a checked-in DE2-115 reference project
  targeting **EP4CE115F29C7**, completing map/fit/asm/sta.
- Preserve exit codes, wall time, peak memory, available disk,
  installer and image digests, version/device checks, .sof SHA256,
  and reports as an immutable run receipt.
- Repeat on a second fresh executor or a second clean run to
  demonstrate reproducibility. Do not equate identical .sof
  hashes with deterministic build unless timestamps and
  toolchain nondeterminism are controlled.

## Independent parallel tracks

1. Locate/reconcile actual OCI Dockerfile, install scripts,
   source artifact provenance and GHCR target; never reconstruct
   vendor payload from guesses.
2. Build a tiny checked-in DE2-115 HDL + QSF smoke project,
   verify pin constraints against authoritative Terasic sources.
3. Profile free-tier executor capabilities: architecture, RAM,
   disk, time, container runtime, storage limits, cache policy.
4. Qualify vendor licensing/redistribution; private registry or
   runtime installer fetch may be required. Never publish vendor
   binaries without rights.
5. Develop an executor-neutral receipt schema and artifact
   upload; Agent Dispatch remains scheduler.

## Sequential gates

Q0 source/artifact inventory -> Q1 license/device-pack checks ->
Q2 OCI build -> Q3 GHCR digest -> Q4 fresh-cloud tool invocation
-> Q5 DE2-115 reference compile -> Q6 second clean repeat ->
Q7 LiteX and Zephyr -> Q8 board HIL.

Q4-Q6 are **NOT VERIFIED** until a real cloud run receipt exists.
A passing Python unit test is not a Quartus qualification.

## Failure classifications

NO_INSTALLER, LICENSE_REVIEW, NO_CYCLONE_IV, INSUFFICIENT_DISK,
OOM, TIMEOUT, NO_CONTAINER_RUNTIME, REGISTRY_AUTH, TOOL_FAILURE,
HDL_FAILURE, DEVICE_MISMATCH, UNKNOWN. Record negative results
and test alternate free runtime shapes rather than retrying
identical failing configurations.

## Safety/cost

No private GitHub-hosted Actions; use public-repo allowance
only for genuinely public redistributable assets, and use
qualified Agent Dispatch free executors for private work.
No cloud FPGA programming; CY16 S04 HPI write gate remains closed.
