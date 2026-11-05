"""Read and write the reading log, one book per line."""

from pathlib import Path


def add(log: Path, title: str, author: str) -> None:
    with log.open("a", encoding="utf-8") as f:
        f.write(f"{title}\t{author}\n")


def books(log: Path) -> list[tuple[str, str]]:
    if not log.exists():
        return []
    lines = log.read_text(encoding="utf-8").splitlines()
    return [tuple(line.split("\t", 1)) for line in lines if line]
