"""Command-line interface for json-differ."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from json_differ.differ import diff
from json_differ.formatter import format_diff


@click.command()
@click.argument("file_a", type=click.Path(exists=True, path_type=Path))
@click.argument("file_b", type=click.Path(exists=True, path_type=Path))
@click.option("--no-color", is_flag=True, help="Disable colored output.")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Write diff output to a file instead of stdout.",
)
def main(file_a: Path, file_b: Path, no_color: bool, output: Path | None) -> None:
    """Compare two JSON files and display structural differences.

    FILE_A is the original JSON file.
    FILE_B is the modified JSON file.
    """
    try:
        a = json.loads(file_a.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        click.echo(f"Error parsing {file_a}: {exc}", err=True)
        sys.exit(1)

    try:
        b = json.loads(file_b.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        click.echo(f"Error parsing {file_b}: {exc}", err=True)
        sys.exit(1)

    entries = diff(a, b)
    use_color = not no_color and output is None
    result = format_diff(entries, color=use_color)

    if output:
        output.write_text(result + "\n", encoding="utf-8")
        click.echo(f"Diff written to {output}")
    else:
        click.echo(result)

    # Exit with code 1 if differences were found (useful for CI)
    if entries:
        sys.exit(1)


if __name__ == "__main__":
    main()
