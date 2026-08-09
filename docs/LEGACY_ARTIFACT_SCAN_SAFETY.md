# Legacy artifact scanner containment and budgets

`cy16-artifact-scan` treats old disks, backups, and archives as untrusted input. It never extracts or executes archive content, and it now applies explicit filesystem and archive-work boundaries.

## Filesystem containment

A root supplied on the command line must not itself be a symbolic link. The scanner resolves an ordinary root once and treats that resolved file or directory as the authority boundary.

For directory scans:

- symbolic-link files are skipped;
- symbolic-link directories are not traversed;
- skipped links become deterministic error records using only their lexical path beneath the root;
- the scanner does not resolve, read, hash, or report the external target;
- ordinary files must resolve beneath the selected root before they are opened.

There is no `--follow-symlinks` mode. Adding one would require a separately reviewed containment and disclosure policy.

This boundary prevents a backup tree from silently drawing unrelated private files into a report through a link such as:

```text
selected-root/old-project/source -> /home/user/private-source
```

## Archive limits

Archive inspection uses three independent byte/member controls:

```text
--content-max-bytes
--archive-max-members
--archive-max-read-bytes
```

Defaults:

```text
per member content/hash read:  16 MiB
members processed per archive: 100,000
cumulative bytes read/archive: 256 MiB
```

`--content-max-bytes` remains a per-file/member threshold. A larger member may still be identified by name and metadata, but content scanning and hashing are omitted.

`--archive-max-members` bounds member-name and metadata processing. Directory entries count toward this limit because they consume archive metadata work.

`--archive-max-read-bytes` bounds the cumulative uncompressed member bytes read for symbol searching or hashing within one archive.

All limits must be non-negative. A value of zero disables the corresponding work rather than creating an unlimited setting.

## Incomplete inspection

When an archive member or cumulative-read limit is reached, the scanner:

1. stops processing that archive;
2. preserves matches already recorded;
3. emits an error naming the archive and limit;
4. increments `summary.archives_incomplete`;
5. does not claim that the remaining archive contents were searched.

An invalid ZIP/TAR file also produces an explicit archive error and incomplete count rather than being silently treated as an empty archive.

The report retains schema identifier `cy16-legacy-artifact-scan/v1`. The v1 schema accepts the new scanner-budget fields and optional `archives_incomplete` count while remaining compatible with earlier v1 reports that lack them.

## Reading reports

These values have distinct meanings:

- `archives_inspected` — archives for which inspection was attempted;
- `archives_incomplete` — attempted archives that could not be fully inspected;
- `errors` — skipped symlinks, archive limits, malformed archives, member-read errors, and other access failures.

A report with matches and errors is useful evidence, but it is not a complete negative inventory. A negative result is meaningful only when `errors == 0` and `archives_incomplete == 0`, for the recorded roots, limits, content mode, and fingerprint catalog.

## Privacy boundary

Top-level `roots` remain absolute and may reveal local paths. Symlink errors intentionally contain only lexical paths beneath those roots and never the resolved external target.

Raw reports remain private evidence until reviewed and sanitized. Containment prevents unintended reads; it does not make the selected root or archive contents public-safe.
