"""Colored terminal output for JSON diffs."""

from __future__ import annotations

import json
from typing import Sequence

from json_differ.differ import DiffEntry, DiffType

# ANSI color codes
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _truncate(value: object, max_len: int = 80) -> str:
    """Return a compact JSON representation, truncated if needed."""
    text = json.dumps(value, default=str)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def format_diff(entries: Sequence[DiffEntry], *, color: bool = True) -> str:
    """Format a list of diff entries into a human-readable string.

    Args:
        entries: Sequence of ``DiffEntry`` objects from :func:`json_differ.diff`.
        color: Whether to include ANSI color codes (disable for file output).

    Returns:
        A multi-line string summarizing all differences.
    """
    if not entries:
        return "No differences found."

    lines: list[str] = []

    for entry in entries:
        path = entry.path
        if entry.diff_type == DiffType.ADDED:
            symbol = "+"
            col = GREEN if color else ""
            detail = _truncate(entry.new_value)
            line = f"{col}{symbol} {path}: {detail}{RESET if color else ''}"

        elif entry.diff_type == DiffType.REMOVED:
            symbol = "-"
            col = RED if color else ""
            detail = _truncate(entry.old_value)
            line = f"{col}{symbol} {path}: {detail}{RESET if color else ''}"

        elif entry.diff_type == DiffType.CHANGED:
            symbol = "~"
            col = YELLOW if color else ""
            old = _truncate(entry.old_value)
            new = _truncate(entry.new_value)
            line = f"{col}{symbol} {path}: {old} -> {new}{RESET if color else ''}"

        elif entry.diff_type == DiffType.TYPE_CHANGED:
            symbol = "!"
            col = CYAN if color else ""
            old = _truncate(entry.old_value)
            new = _truncate(entry.new_value)
            line = f"{col}{symbol} {path}: {old} -> {new} (type change){RESET if color else ''}"

        else:
            line = f"  {path}: unknown diff type"

        lines.append(line)

    summary_parts: list[str] = []
    added = sum(1 for e in entries if e.diff_type == DiffType.ADDED)
    removed = sum(1 for e in entries if e.diff_type == DiffType.REMOVED)
    changed = sum(1 for e in entries if e.diff_type == DiffType.CHANGED)
    type_changed = sum(1 for e in entries if e.diff_type == DiffType.TYPE_CHANGED)

    if added:
        summary_parts.append(f"{added} added")
    if removed:
        summary_parts.append(f"{removed} removed")
    if changed:
        summary_parts.append(f"{changed} changed")
    if type_changed:
        summary_parts.append(f"{type_changed} type changes")

    header = f"Found {len(entries)} difference(s): {', '.join(summary_parts)}"
    if color:
        header = f"{BOLD}{header}{RESET}"

    return header + "\n" + "\n".join(lines)
