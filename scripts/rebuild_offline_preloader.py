#!/usr/bin/env python3
"""Rebuild the ADT offline-preloader's inline data from source files."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRELOADER = ROOT / "assets/offline-preloader.js"
START = "  var INLINE = "
END = ";\n  var BASE_DIR"


def main() -> None:
    source = PRELOADER.read_text()
    start = source.index(START) + len(START)
    end = source.index(END, start)
    inline = json.loads(source[start:end])
    rebuilt = {}
    for key, old_value in inline.items():
        path = ROOT / key.removeprefix("./")
        if not path.exists():
            rebuilt[key] = old_value
        elif path.suffix == ".json":
            rebuilt[key] = json.loads(path.read_text())
        else:
            rebuilt[key] = path.read_text()
    payload = json.dumps(rebuilt, ensure_ascii=False, separators=(",", ":"))
    PRELOADER.write_text(source[:start] + payload + source[end:])


if __name__ == "__main__":
    main()
