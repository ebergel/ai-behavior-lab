# Behavior Laboratory in appHub

On the researcher's Mac Studio, open [appHub](http://localhost:5100/) and find **Behavior Laboratory**. **Open** launches the lab; **Start**, **Stop**, **Restart** and **Logs** manage its server. The app remains at [127.0.0.1:8765](http://127.0.0.1:8765/).

The registration uses the existing live workspace, including `workspace/explorer/notes.sqlite`. No second notebook or transcript library is created. The hub's supervisor owns the process independently of the Codex terminal, starts it automatically when the supervisor starts, and restarts it after a crash. Automatic startup does not wake a sleeping Mac or make the app remotely reachable.

## Registration

Registered and verified on 17 September 2026:

| Setting | Value |
|---|---|
| Name | `behavior-lab` |
| Title | Behavior Laboratory |
| Working directory | `/Users/eduardobergel/Documents/Codex/AI-Chat-Experiment/laboratory` |
| Command | `/usr/bin/python3 -u -m behaviorlab explore --workspace workspace --port 8765` |
| Port | `8765` |
| URL | `http://127.0.0.1:8765/` |
| Autostart | Enabled |

The registration lives in appHub's local configuration, outside this Git repository. A fresh lab clone does not automatically register itself; reuse these settings with its actual directory. Prefer hub controls on this Mac. The existing `Open Explorer.command` launcher remains available and reuses a responding server.

The [validation record](evidence/apphub-registration-validation.json) records HTTP and browser checks, 472 default library records, six collections, unchanged notebook contents and seven unaffected hub applications. No laboratory source code or research evidence was changed.

Remote access remains [parked](../TODO.md#remote-access-01--private-remote-access-to-mac-studio-apps) pending the researcher's hardware setup and explicit resumption.
