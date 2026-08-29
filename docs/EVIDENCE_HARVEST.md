# Public evidence harvesting

This workflow is a disposable, credentialless helper for the CY16 research/validator program.

It may:

- download allowlisted public sources;
- validate expected byte counts;
- compute SHA-256;
- identify basic file/container type;
- inventory ZIP contents without extraction or execution;
- retain clearly public-redistributable material as short-lived workflow artifacts;
- reduce restricted/unknown material to metadata only and delete the plaintext before artifact upload.

It MUST NOT:

- receive credentials for `CY16-research-private`;
- publish restricted/unknown historical vendor bytes;
- execute recovered binaries;
- treat successful retrieval as proof of authenticity or redistribution permission;
- replace the private evidence registry or human source chain.

The private research repository remains authoritative for provenance/classification. This public workflow is compute/network machinery only.
