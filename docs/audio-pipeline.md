# Internal microphone investigation

The upstream symbol list names `task_AudioTsk` at **0xff075bbc**, `task_AACTask` at
**0xff18e4fc**, and `task_AACDrvTask` at **0xff3174b0**. These are exact SX430 source
anchors. Inputs, output queue, sample rate, ADC/DMA descriptors and ownership are unknown.

Trace all three tasks, queue creation and callers, then intersect with MovieWriter's
audio input. A task name alone does not establish which stage performs encoding.
Record initialization, clock, DMA completion, PCM format, AAC configuration, output
length, error path and producer acknowledgement before adding an observer.

Use a normal camera movie to establish AAC profile/channel/sample-rate metadata and
decode it for a visible/audible clap reference. Run:

```powershell
python tools/sx430.py inspect-media private/camera-reference.mp4
ffmpeg -v error -i private/camera-reference.mp4 -map 0:v:0 -map 0:a:0 -f null -
```

The first command checks metadata; the second tests decoding without creating frames
or changing the source file. Neither proves live native capture. Preserve hashes and
camera-origin evidence separately. An existing file is a reference, never the transport.

Prefer AAC output interception. If impractical, establish PCM ownership and bandwidth
before considering host AAC encoding. Never activate a host audio device as a substitute.
Audio and video must share an established timebase. Measure sync with events at the
beginning and end of a 30-minute run; timestamp spacing alone cannot establish lip sync.
