# Camera-side status

No experimental C/ARM hooks are deployed. `baseline.lua` runs inside host chdkptp
and sends only short public getter scripts to the camera. It is guarded for the
SX430 100b **CHDK build**; that is not independent Canon firmware verification.

The future camera modifications must extend the exact upstream port after buffer
ownership is established. Review docs/recovery.md before enabling any task replacement.
The experimental directory contains a separately generated, guarded native-call
candidate for the inspected mode pre-handler. It has not been validated on hardware.
No socket ABI or AAC buffer layout is assumed by that experiment.
