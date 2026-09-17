# Project to-dos

## REMOTE-ACCESS-01 — Private remote access to Mac Studio apps

- [ ] Enable browser access to the laboratory from a notebook or iPad, using Cloudflare Tunnel and Cloudflare Access.

**Status:** Parked at the researcher's request.
**Recorded:** 2026-09-17T10:29:38.861882-03:00 (America/Argentina/Cordoba).
**Prerequisite:** The researcher completes installation of the new router and the associated hardware setup.
**Resume trigger:** The researcher explicitly says the hardware is ready and asks to resume remote access.
**Resume phrase:** “Resume the Mac Studio remote-access task.”

### Intended outcome

Use a normal HTTPS website address and private login to reach the existing laboratory on the Mac Studio. Every device reads and annotates the same transcripts through the same running app and live notebook database. Keep one authoritative lab working copy on the Mac. Git and the private GitHub repository retain versioned exports of research data and notebook histories; saving a comment updates the live database immediately, while publishing it to GitHub requires a snapshot and push.

Build the setup so other locally hosted web apps, including Open WebUI, can later use separate subdomains and access policies through the same tunnel infrastructure. The Mac must remain awake, connected and running the required services.

### Plan to resume

1. Confirm that the router/hardware work is finished and inspect the resulting network setup. Choose the domain/subdomain, Cloudflare account and allowed login identity; none has been selected or configured for this task.
2. Prepare the Explorer for authenticated HTTPS access: exact permitted host/origin, validated Access authentication, retained write protections, and an appropriate serving arrangement. Preserve local use and the existing evidence/notebook.
3. Configure Cloudflare Access before publishing the tunnel route. Install and configure the Mac's tunnel service to reach the Explorer on localhost. Verify denied access as well as successful access.
4. Configure managed background services and consistent notebook backups, with clear save/backup status. Keep a restart/recovery procedure and preserve all annotation histories.
5. Test from another network and on the iPad: reading, filtering, touch selection, saving comments, reconnecting, and conflicting edits from two devices. Confirm that saved annotations reach the same Mac database and that a backup restores correctly.
6. Document adding another web app through its own subdomain and access policy. Activate additional apps only as requested.

### State at parking

Discussion and planning only. No remote-access software was installed, no domain or tunnel was configured, no router or power settings were changed, and no remote service was published. The local lab and its private GitHub research snapshot already exist. Tailscale and direct router forwarding were considered; Cloudflare Tunnel with Access is the preferred plan for browser-only access.

This task stays parked during ordinary lab continuation. No reminder or automatic execution has been scheduled. Recheck provider requirements when resuming.

Related context: [continuation plan](docs/CONTINUATION.md), [repository and data ownership](docs/REPOSITORY.md), [research snapshot and restoration](docs/RESEARCH-DATA.md).
