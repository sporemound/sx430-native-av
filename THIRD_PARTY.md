# Third-party material

CHDK excerpts in `reference/chdk/` retain upstream comments and provenance at
commit ad402e1b2049662594ccc7d15a9a507138b59079, from the public petabyt/chdk mirror.
CHDK is GPL; see the copied upstream COPYING and individual files for terms.

chdkptp excerpts in `reference/chdkptp/` come from the historical simonswine mirror,
commit e41ce78fb1060ce57c58b834a91290680a07d932 (2013). They are used to inspect
the dump format and Lua API, not as a modern runnable distribution. Their GPL notices
remain intact. The current upstream project is maintained by reyalp on Assembla.

Canon pairing helpers in `reference/ptpip-canon-helpers/` are from reyalpchdk,
commit 7be8abc6d907aa23942e25f2d88976b887916761, under the included MIT LICENSE.
Their external `ssdpy` dependency is not vendored or installed. Resolve and record
its environment locally before use; private machine configuration is excluded.

Canon documentation is linked, not redistributed. Canon firmware dumps and original
camera clips are not included. Test byte arrays are structural fixtures only; they
are not claimed to be captured images, audio or firmware.
