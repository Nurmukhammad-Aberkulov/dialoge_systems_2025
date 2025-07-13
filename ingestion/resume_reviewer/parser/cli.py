from __future__ import annotations

import argparse
from pathlib import Path

from . import parse_resume


def main() -> None:
    # ------------------------------------------------------------------ #
    # 1)  Parse arguments
    # ------------------------------------------------------------------ #
    ap = argparse.ArgumentParser(prog="parse-resume")
    ap.add_argument("file", type=Path, help="Résumé file (PDF, DOCX, JPG, PNG, TIFF)")
    ap.add_argument(
        "--plain",
        action="store_true",
        help="Return raw text (skip Markdown conversion)",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit full JSON instead of plain output",
    )
    args = ap.parse_args()

    # ------------------------------------------------------------------ #
    # 2)  Run the parser
    # ------------------------------------------------------------------ #
    result = parse_resume(args.file, convert_to_md=not args.plain)

    # ------------------------------------------------------------------ #
    # 3)  Output
    # ------------------------------------------------------------------ #
    if args.json:
        # --json takes precedence over other flags
        print(result.to_json())
        return

    # Otherwise: human-readable full text
    print(f"[META] {result.metadata}")
    print("[TEXT]")
    print(result.text)


if __name__ == "__main__":
    main()
