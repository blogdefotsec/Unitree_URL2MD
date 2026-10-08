#!/usr/bin/env python3
"""CI helper: zip a directory recursively into an archive.

Usage:
    python zip_dir.py <src_dir> <output.zip>

The archive will contain the directory contents rooted at src_dir itself.
So `zip_dir.py foo out.zip` creates a zip that extracts to `foo/...`.
"""
import os
import sys
import zipfile


def main():
    if len(sys.argv) != 3:
        print("Usage: zip_dir.py <src_dir> <output.zip>", file=sys.stderr)
        return 2

    src = sys.argv[1]
    out = sys.argv[2]

    if not os.path.isdir(src):
        print(f"ERROR: src_dir '{src}' does not exist or is not a directory", file=sys.stderr)
        return 1

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _dirnames, filenames in os.walk(src):
            for name in filenames:
                full = os.path.join(dirpath, name)
                arcname = os.path.relpath(full, os.path.dirname(src))
                zf.write(full, arcname)

    size = os.path.getsize(out)
    print(f"Created: {out} ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
