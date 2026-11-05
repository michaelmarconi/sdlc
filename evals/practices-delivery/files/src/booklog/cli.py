"""The booklog command."""

import argparse
from pathlib import Path

from booklog.log import add, books


def main() -> None:
    parser = argparse.ArgumentParser(prog="booklog")
    parser.add_argument("--log", type=Path, default=Path.home() / ".booklog")
    sub = parser.add_subparsers(dest="command", required=True)
    added = sub.add_parser("add")
    added.add_argument("title")
    added.add_argument("author")
    sub.add_parser("list")
    args = parser.parse_args()
    if args.command == "add":
        add(args.log, args.title, args.author)
    else:
        for title, author in books(args.log):
            print(f"{title} by {author}")
