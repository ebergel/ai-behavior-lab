# Session record — appHub registration

Recorded: 2026-09-17T10:37:44.274101-03:00
Timezone: America/Argentina/Cordoba.
Scope: add the existing Behavior Laboratory app to the researcher's local appHub.

## Completed

Registered **Behavior Laboratory** (`behavior-lab`) through appHub's supported API with the existing laboratory directory, Python Explorer command and port 8765. Gracefully stopped the earlier Codex terminal server and handed process ownership to appHub's supervisor. Automatic startup and crash recovery are enabled. The hub provides Open, Start, Stop, Restart and Logs controls.

Documented the local registration in `docs/APP-HUB.md`, linked it from the README and continuation guide, and saved `docs/evidence/apphub-registration-validation.json`. The appHub configuration lives outside the repository; this documentation preserves the settings for future setup.

## Verified

The supervisor reported RUNNING and its PID matched the listener at 127.0.0.1:8765. The library endpoint returned 472 default records and the studies endpoint returned six research collections. Browser inspection confirmed the new card, RUNNING state, correct Open URL and management controls. The exact notebook table fingerprint was unchanged before and after handover. All seven other hub applications retained their configuration, process state and PID.

No lab runtime code changed; verification exercised the actual registration and running service rather than rerunning the source test suite. Earlier session records are preserved.

## Still deferred

Remote access remains parked under REMOTE-ACCESS-01. No tunnel, router, domain or remote-access configuration was changed. No experiments, inference, spending or research annotation edits occurred. The live workspace remains authoritative; no new research snapshot was necessary because its research contents were unchanged.
