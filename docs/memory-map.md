# Memory map

Imported from SX430 100b `stubs_entry.S`; end addresses below are exclusive.

| Region | Runtime range | ROM source |
| --- | --- | --- |
| ROM | 0xff010000–0x100000000 | file mapping depends on dump origin |
| Copied ARM code | 0x006b1000–0x006e01c4 | 0xff7cf0a8 |
| Initialized data | 0x00001900–0x00014f30 | 0xff7bba78 |

`MAXRAMADDR=0x0fffffff` is a port constant, not a measurement of free RAM.
`MEMISOSTART=0x002b9464` is not permission to allocate an arbitrary streaming pool.
`CAM_UNCACHED_BIT=0x40000000` is also source-derived; DMA cache coherency must be
understood for each actual producer buffer.

The verifier checks the version string at 0xff0acde9, platform ID 13013 at
0xfffe0270, and both upstream CRC blocks:

| ROM start | Length | CRC32 |
| --- | --- | --- |
| 0xff010000 | 0x5e45d8 | 09b947f3 |
| 0xff7bba78 | 0x427f4 | b1cf0156 |

CRC blocks do not cover every ROM byte. Record each input's SHA-256 privately;
whole-device dump hashes are excluded from this publication. CRC is a build fingerprint, not
cryptographic authenticity or proof that runtime RAM matches ROM initializers.

The documented Canon BASIC dumper may omit the final four ROM bytes, ending at
0xfffffffc exclusive. The verifier explicitly reports this omission and permits
the build fingerprint check because both CRC blocks and identity fields are covered.
Other incomplete extents are rejected. The omitted bytes are never fabricated or padded.

`firmware-slice` translates copied code/data addresses into ROM initial bytes. It
does not retrieve changing runtime buffers. Unmapped runtime addresses fail closed.
Firmware string results are string locations, not function identifications.
