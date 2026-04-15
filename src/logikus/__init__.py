"""Logikus package entry points and metadata."""

import argparse
import sys
from typing import Optional, Sequence

__version__ = "0.1.0"
__author__ = "Heiko Sippel"

font = "LiberationSans-Regular.ttf"
grid_size = 15  # 15
window_size = (1155, 930)


def run(skin: str = "classic"):
    """Start Logikus with the selected skin."""
    from logikus.main import main as _main

    return _main(skin)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point for `python -m logikus`."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="logikus", description="Start Logikus - Toy Computer Emulation")
    parser.add_argument("--skin", "-s", default="classic", help="Skin name: classic, hulk, metal, (default: classic)")
    args = parser.parse_args(list(argv))

    try:
        run(args.skin)
        return 0
    except Exception as exc:
        print(f"Error starting logikus: {exc}", file=sys.stderr)
        return 1


__all__ = ["__version__", "__author__", "run", "main"]
