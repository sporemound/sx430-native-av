# Public source snapshot

This repository starts with new Git history and a neutral contributor identity. The initial commit uses a synthetic UTC timestamp to avoid retaining the private development timeline or local timezone.

The export includes source, tests, public upstream references, and sanitized technical summaries. It excludes private Git history, firmware dumps, firmware-derived instruction tables, raw disassembly, camera crash logs, capture files, media metadata, session timestamps, network addresses, Wi-Fi names, pairing identifiers, local usernames and machine paths, runtime configuration, and downloaded binaries.

The experimental firmware table is generated locally from an independently verified ROM. The code-region digest in the generator identifies the reviewed firmware routine; it is not a device identifier or a hash of a privately retained whole-device dump. Generated artifacts belong in the ignored `private/` directory.

Upstream copyright notices, public author credits, source URLs, and public source hashes remain intact to preserve provenance and licensing.

GitHub exposes the owning account and repository creation/publication activity. File sanitization and neutral Git authorship do not make account ownership anonymous. Review new logs and generated artifacts before sharing; ignore rules are only a default safeguard.
