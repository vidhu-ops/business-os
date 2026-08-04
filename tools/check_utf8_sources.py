"""Fail the Docker build if any Python source contains null bytes (UTF-16 corruption)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOTS = [Path("backend"), Path("iidatech")]
bad: list[str] = []
for root in ROOTS:
    if not root.is_dir():
        continue
    for path in root.rglob("*.py"):
        data = path.read_bytes()
        if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff") or b"\x00" in data[:512]:
            bad.append(str(path))

if bad:
    print("ERROR: UTF-16 / null-byte Python sources detected:", file=sys.stderr)
    for item in bad:
        print(f"  - {item}", file=sys.stderr)
    print("Re-save these files as UTF-8 without BOM, then rebuild.", file=sys.stderr)
    sys.exit(1)

print("UTF-8 source check passed.")