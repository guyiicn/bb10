#!/usr/bin/env python3
"""Reconstruct a BAR-shaped ZIP from an extracted BB10 /apps package tree."""
import argparse
import hashlib
import os
from pathlib import Path
import sys
import zipfile


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="extracted package root containing META-INF/native/public")
    parser.add_argument("output", help="output .bar path")
    args = parser.parse_args()
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    manifest = source / "META-INF" / "MANIFEST.MF"
    if not manifest.is_file():
        parser.error("missing META-INF/MANIFEST.MF")
    roots = [name for name in ("META-INF", "native", "public") if (source / name).exists()]
    if "native" not in roots:
        parser.error("missing native directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    if temp.exists():
        temp.unlink()
    count = 0
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for top in roots:
            for path in sorted((source / top).rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(source).as_posix())
                    count += 1
    with zipfile.ZipFile(temp, "r") as archive:
        bad = archive.testzip()
        if bad:
            temp.unlink(missing_ok=True)
            raise RuntimeError("ZIP integrity failure at " + bad)
        if "META-INF/MANIFEST.MF" not in archive.namelist():
            raise RuntimeError("manifest absent from output")
    os.replace(temp, output)
    print("output=%s" % output)
    print("files=%d" % count)
    print("bytes=%d" % output.stat().st_size)
    print("sha256=%s" % sha256(output))
    print("warning=reconstructed from installed files; installability must be device-tested")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("error: %s" % exc, file=sys.stderr)
        sys.exit(1)
