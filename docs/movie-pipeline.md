# Native movie investigation

Evidence: pinned SX430 `funcs_by_name.csv`, `stubs_entry.S`, `sub/taskhook.S`,
`platform_camera.h`, and related ports under `reference/`.

Source-derived anchors:

| Address | Upstream name | What remains unknown |
| --- | --- | --- |
| 0xff0687bc | UIFS_StartMovieRecord_FW | start rejection branches, ABI |
| 0xff1ecdbc | task_MovieRecord | message types, encoder callbacks |
| 0xff37c6dc | task_MovieWriter | muxer queue and ownership |
| 0xff35dd00 | task_FileWrite / task_FileWriteTask | whether movie writes pass here |
| 0x00007c0c | movie_status | runtime transitions and representation |
| 0x00007bbc | video_compression_rate | mode-specific semantics |

The symbol `MovieWriter` deserves independent tracing. The presence of `FileWriteTask`
and CHDK's still-image remote-capture mechanism does not prove movies use that path.
Seek-dependent MP4 output may lack initialization/index data until finalization;
blindly teeing writes into a pipe is not necessarily a decodable live stream.

## Reuse review

- SX410 100c and SX400 100b: DIGIC 4+, DryOS R55. Their movie task implementations
  dispatch messages, invoke callbacks, and modify quality/target bitrate. These are
  structural examples, not H.264 extraction implementations.
- IXUS175 100c: DIGIC 4+, DryOS R58. Similar generated movie code, but a different
  memory map and older OS than SX430.
- SX420 100a: DIGIC 4+, DryOS R58; its snapshot also lacks `movie_rec.c`.
- SX430: R59, movie hook disabled. `lib.c` selecting viewport buffer zero while
  recording concerns the display pipeline. It is not an encoded H.264 pointer.

## Exact-ROM work sequence

1. Verify dump and initialize the Ghidra memory map using the upstream CHDK scripts.
2. Decompile MovieRecord and every callback installed into its state structure.
3. Trace message queue creation, senders, consumers and completion acknowledgments.
4. Work backward from MovieWriter as well as forward from MovieRecord.
5. Identify candidate compressed-output descriptors and size/ownership constraints.
6. Only after the passive hook review, copy bounded samples during normal recording.
7. Validate H.264 structure, SPS dimensions, decoded pictures, PTS/DTS, IDR recovery,
   and correspondence to the simultaneously recorded reference movie.

Encoder output and muxer input remain first and second choices. FileWrite is third,
contingent on evidence that movie chunks actually reach it. No addresses from another
camera may enter a build for this camera.
