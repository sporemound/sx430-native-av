# OBS integration status

No OBS plugin or live media source has been implemented or tested. There is currently
no camera URL to add to OBS.

After native video and camera microphone extraction succeeds, evaluate a dedicated
source against an FFmpeg-compatible localhost stream. OBS must receive both streams
with preserved camera timing. An eventual UDP URL carries a correctly muxed stream;
concatenated H.264 and raw AAC bytes do not form MPEG-TS by themselves.

OBS Window Capture, viewport upscaling, external microphones and prerecorded files
cannot satisfy acceptance.
