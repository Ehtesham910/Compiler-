from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import compile_and_run, compile_only


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="MiniC (basic C subset) compiler")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", type=str, help="Path to .cmini file")
    src.add_argument("--source", type=str, help="MiniC source as a string")

    parser.add_argument("--no-run", action="store_true", help="Compile only, do not execute")
    parser.add_argument("--print-tac", action="store_true", help="Print generated TAC")

    args = parser.parse_args(argv)

    if args.file:
        path = Path(args.file)
        source = path.read_text(encoding="utf-8")
    else:
        source = args.source

    if args.no_run:
        res = compile_only(source)
    else:
        res = compile_and_run(source, run=True)

    if args.print_tac:
        print(res.tac_text)

    if not res.ok:
        print("ERROR:", res.error_text)
        return 1

    if not args.no_run:
        if res.output_text:
            print(res.output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

