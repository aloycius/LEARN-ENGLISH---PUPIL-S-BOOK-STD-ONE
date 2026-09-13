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
    source = PRELOADER.read_text(encoding="utf-8")
    start = source.index(START) + len(START)
    end = source.index(END, start)
    inline = json.loads(source[start:end])
    rebuilt = {}
    for key, old_value in inline.items():
        path = ROOT / key.removeprefix("./")
        if not path.exists():
            rebuilt[key] = old_value
        elif path.suffix == ".json":
            rebuilt[key] = json.loads(path.read_text(encoding="utf-8"))
        else:
            rebuilt[key] = path.read_text(encoding="utf-8")

    # Keep every page in the reading-order manifest available offline.
    pages = json.loads((ROOT / "content/pages.json").read_text(encoding="utf-8"))
    html_files = [page["href"] for page in pages]
    for relative_path in html_files:
        path = ROOT / relative_path
        rebuilt[f"./{relative_path}"] = path.read_text(encoding="utf-8")

    payload = json.dumps(rebuilt, ensure_ascii=False, separators=(",", ":"))
    PRELOADER.write_text(source[:start] + payload + source[end:], encoding="utf-8")


if __name__ == "__main__":
    main()
