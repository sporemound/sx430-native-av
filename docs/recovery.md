# Recovery and future hook policy

Use a spare backed-up SD card. Verify stock startup with a non-CHDK card before
experimenting. With normal power-off complete, removing/replacing the CHDK card is
the primary recovery path. If the camera hangs, attempt normal power-off, then battery
removal if necessary; an interrupted recording can be lost. Reinsert a non-CHDK card
and confirm stock boot. SD removal does not undo internal Canon settings, so avoid
changing them in experiments and preserve known working settings.

No ROM flash, service-mode modification, arbitrary memory poke or patch is supplied.
The baseline calls public getters only. It has finite capture count and a host deadline;
the deadline is not a camera watchdog and cannot recover a deadlocked firmware task.

Before deploying future passive hooks, require all of:

- Exact owner-dump match, reviewed instruction boundaries, calling contract and
  continuation, and symbol provenance tied to the same dump SHA-256.
- Default disabled boot path, explicit enable action after successful stock CHDK boot,
  and tested disable/recovery with the experimental SD removed.
- Proven producer/consumer buffer lifetime, bounds and memory allocation budget;
  no heap allocation, network call or waiting inside an encoder callback.
- Bounded copied-data queues; drop complete units with counters on overflow;
  leave Canon's original ownership and return values intact.
- Receiver heartbeat/deadline that stops observation without blocking Canon tasks;
  repeated start/stop tests; a watchdog strategy verified in this exact task context.
- Temperature telemetry checked for plausible sensor values. Derive a stop condition
  from validated device behavior; do not invent a safe internal sensor threshold from
  Canon's ambient operating-temperature rating.

These are future deployment requirements, **not implemented safeguards** for an
existing streaming hook. No recovery mechanism can be validated without the camera.
