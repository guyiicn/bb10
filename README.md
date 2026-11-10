# BB10 Skills

Agent skills and supporting Linux utilities for authorized BlackBerry 10 application management.

## Included skills

- [`bb10-app-extract`](skills/bb10-app-extract/): back up an installed app's `/apps` package tree without private app data, then reconstruct a BAR-shaped archive for preservation and controlled testing.
- [`bb10-cgi-sideload`](skills/bb10-cgi-sideload/): inspect and sideload a BAR through the authenticated Sachesi-compatible BB10 HTTPS CGI protocol.

## Requirements

- Linux and Python 3
- An authorized BlackBerry 10 device connected over USB networking
- Root SSH access for extracting installed application files
- The device password for CGI sideloading

## Security boundaries

- App extraction excludes `/accounts/1000/appdata` by default.
- The sideload utility prompts for the device password and does not require it in command-line arguments.
- Legacy TLS compatibility is scoped to the directly connected BB10 link-local endpoint.
- Reconstructed BAR files are not guaranteed to contain original signing material and must be tested on an authorized device.

## Installing the skills for Pi

Copy or symlink each skill directory into `~/.agents/skills/`, then reload Pi:

```sh
ln -s "$PWD/skills/bb10-app-extract" ~/.agents/skills/bb10-app-extract
ln -s "$PWD/skills/bb10-cgi-sideload" ~/.agents/skills/bb10-cgi-sideload
```

If those destination paths already exist, replace them only after reviewing local changes.

## License

MIT
