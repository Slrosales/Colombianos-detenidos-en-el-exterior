#!/usr/bin/env python3
"""Download the latest public CSV from datos.gov.co."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    params = json.loads((ROOT / "config" / "params.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=params["source_url"])
    parser.add_argument("--output", default=str(ROOT / params["raw_file"]))
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"Descargando {args.url}")
    urllib.request.urlretrieve(args.url, output)
    print(f"Guardado en {output} ({output.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
