---
name: bb10-cgi-sideload
description: Safely inspect and sideload BlackBerry 10 BAR applications from Linux through the authenticated Sachesi-compatible HTTPS CGI protocol. Use for installing or upgrading a BAR on an authorized BB10 phone; not for firmware flashing, Android APK installation, publishing, or bypassing device authentication.
compatibility: Linux with Python 3, unzip, USB networking to the BB10 device, and the device password.
---

# BB10 CGI sideload

Use `scripts/bb10_sideload.py` for installation. It implements the same login challenge and `update.cgi` flow as Sachesi without requiring a GUI. Resolve script paths relative to this skill directory.

## Safety requirements

1. Establish the connected device before any write:
   - `lsusb` must show the expected BlackBerry USB device.
   - Read `uname -a` and `/etc/os.version` over the authorized SSH channel if available.
   - Never carry forward a model assumption after the user swaps phones.
2. Inspect the BAR before asking for installation approval:
   - Run `unzip -t`.
   - Read `META-INF/MANIFEST.MF`.
   - Report application name, package name/ID, version, development-mode status, size, and SHA-256.
   - Check whether the same package directory is already installed. Explain overwrite/downgrade impact.
3. Obtain explicit user confirmation for the exact BAR and target device before invoking the script.
4. Device password rules:
   - Never put a password in the command line, a maintained file, logs, or the final response.
   - Prefer the script's interactive `getpass` prompt when a human terminal is available.
   - In an agent-only session, use `--password-stdin` and pipe the password through stdin; do not echo it in the response or save it.
   - The authentication response reports retry state. On authentication failure, stop immediately; never guess or loop passwords.
5. The CGI endpoint uses obsolete TLS 1.0 by device design. Restrict this compatibility to the directly connected link-local BB10 address, normally `169.254.0.1`; do not weaken global TLS configuration.
6. Do not reboot, uninstall, clear app data, or touch unrelated PPS installation jobs unless separately authorized.

## Install workflow

1. Verify connectivity and target identity.
2. Inspect the BAR and current package state.
3. Ask once for confirmation if not already explicitly authorized.
4. Run:

```sh
python3 scripts/bb10_sideload.py /absolute/path/App.bar --host 169.254.0.1
```

or, only when secure interactive prompting is unavailable:

```sh
printf '%s\n' "$BB10_PASSWORD" | \
  python3 scripts/bb10_sideload.py /absolute/path/App.bar \
  --host 169.254.0.1 --password-stdin
```

Do not export or persist `BB10_PASSWORD`; unset it immediately if the surrounding harness created it.

5. Require this successful sequence before calling installation complete:

```text
authenticated
start UpdateStart
send UpdateSend Success
poll UpdateProgress ...
poll UpdateProgress Success 100
finish UpdateEnd Success
```

6. Verify on device using the package name and ID from the BAR manifest. Confirm the installed manifest version. Installation success does not prove the app launches; ask the user to perform the visible device test.

## Failure handling

- Authentication failure: stop; report the remaining retry context without printing credentials.
- `UpdateStart` refusal: verify free space, package state, and device connectivity; do not switch to destructive methods automatically.
- Upload/progress error: preserve the exact response and stop.
- CGI success but app missing: inspect device package registration and manifest; do not claim success.
- Root/PPS extraction errors for a valid development BAR are a reason to use this CGI workflow, not to repeatedly replay installer jobs.
