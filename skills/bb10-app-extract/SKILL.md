---
name: bb10-app-extract
description: Locate and back up installed BlackBerry 10 applications from an authorized rooted device, excluding private app data by default, and reconstruct BAR-shaped archives for local preservation or controlled sideload testing. Use for extracting an installed BB10 app or migrating it between the user's devices; not for extracting credentials, account data, DRM material, system firmware, or publishing third-party apps.
compatibility: Linux with SSH/SCP access to an authorized rooted BB10 device and Python 3.
---

# BB10 app extraction

Use this workflow to preserve an installed application's `/apps` package tree and optionally reconstruct a BAR-shaped ZIP. Resolve bundled scripts relative to this skill directory.

## Safety and scope

1. Re-detect the connected phone every time the user swaps devices. Check USB, link-local address, `uname -a`, and `/etc/os.version`. Never infer Q20 versus Passport from previous turns.
2. Extract only application files under `/apps/<dname>/` by default.
3. Do **not** read or copy `/accounts/1000/appdata/<dname>/` unless the user separately and explicitly requests private data backup after being warned that it may contain credentials, cookies, tokens, messages, and personal content.
4. Do not modify, stop, uninstall, or launch the source application during extraction.
5. Keep backups local. Do not publish or upload reconstructed third-party applications.
6. A reconstructed archive is not the original vendor BAR. Installed trees commonly retain only `META-INF/MANIFEST.MF`, not original signing material. Always label output as reconstructed and unverified until a controlled sideload succeeds.

## Locate the package

Search package directory names and manifests using likely app names. For each candidate, report:

- device model and OS;
- dname under `/apps`;
- `Package-Name`, `Package-Id`, `Package-Version`;
- `Application-Name`, `Application-Version`;
- author and development-mode flag;
- installed tree size.

Do not scan appdata while locating packages.

## Extract the installed tree

Create a destination such as:

```text
~/bb10-tools/<device>-app-backups/extracted/<app>/
```

Use recursive SCP from the exact `/apps/<dname>` directory. Preserve the three package roots:

```text
META-INF/
native/
public/
```

After transfer:

- count files;
- compare installed and local manifest metadata;
- record local directory size;
- preserve the original dname in a small local note if needed.

If device-side BerryCore tools are not executable because of mount or owner restrictions, do not alter permissions merely for extraction; use SCP directly.

## Reconstruct a BAR-shaped archive

Run:

```sh
python3 scripts/reconstruct_bar.py \
  /path/to/extracted/app \
  /path/to/App-version-reconstructed.bar
```

Then independently inspect:

```sh
unzip -t /path/to/App-version-reconstructed.bar
unzip -p /path/to/App-version-reconstructed.bar META-INF/MANIFEST.MF
sha256sum /path/to/App-version-reconstructed.bar
```

Report output path, size, SHA-256, manifest identity, and the warning that it is reconstructed.

## Controlled migration

Before installing on another device:

1. Load the `bb10-cgi-sideload` skill.
2. Verify the target device model and that the same Package ID is absent, or explain overwrite implications.
3. Obtain explicit installation approval.
4. Install the smaller/lower-risk app first when testing a reconstruction method.
5. Treat CGI `UpdateEnd Success` as installation success, then require a user-visible launch test before calling the migration fully successful.

## Failure handling

- Permission error copying `/apps`: stop and inspect the authorized root channel; do not broaden permissions globally.
- Missing manifest/native tree: do not reconstruct.
- ZIP passes but sideload fails: preserve exact installer response; do not repeatedly replay jobs.
- Existing target package: do not overwrite without explicit approval and version comparison.
