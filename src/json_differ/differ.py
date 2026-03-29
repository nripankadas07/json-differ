"""Core diffing engine for structural JSON comparison."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class DiffType(enum.Enum):
    """Types of differences between two JSON values."""

    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    TYPE_CHANGED = "type_changed"


@dataclass(frozen=True)
class DiffEntry:
    """A single difference between two JSON documents.

    Attributes:
        path: JSON-pointer style path to the changed value (e.g. "root.users[0].name").
        diff_type: The kind of change detected.
        old_value: The value in the first document (None for additions).
        new_value: The value in the second document (None for removals).
    """

    path: str
    diff_type: DiffType
    old_value: Any = None
    new_value: Any = None


def _type_label(value: Any) -> str:
    """Return a human-readable type label for a JSON value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def diff(a: Any, b: Any, path: str = "root") -> list[DiffEntry]:
    """Compute structural differences between two JSON-compatible values.

    Args:
        a: The first (original) JSON value.
        b: The second (modified) JSON value.
        path: The current path prefix (used internally for recursion).

    Returns:
        A list of ``DiffEntry`` objects describing each difference found.
    """
    entries: list[DiffEntry] = []

    # Different top-level types
    if type(a) is not type(b):
        # Special case: int vs float are considered compatible numeric types
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if a != b:
                entries.append(
                    DiffEntry(
                        path=path,
                        diff_type=DiffType.CHANGED,
                        old_value=a,
                        new_value=b,
                    )
                )
            return entries

        entries.append(
            DiffEntry(
                path=path,
                diff_type=DiffType.TYPE_CHANGED,
                old_value=a,
                new_value=b,
            )
        )
        return entries

    # Both are dicts
    if isinstance(a, dict) and isinstance(b, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for key in sorted(all_keys):
            child_path = f"{path}.{key}"
            if key not in a:
                entries.append(
                    DiffEntry(
                        path=child_path,
                        diff_type=DiffType.ADDED,
                        new_value=b[key],
                    )
                )
            elif key not in b:
                entries.append(
                    DiffEntry(
                        path=child_path,
                        diff_type=DiffType.REMOVED,
                        old_value=a[key],
                    )
                )
            else:
                entries.extend(diff(a[key], b[key], child_path))
        return entries

    # Both are lists
    if isinstance(a, list) and isinstance(b, list):
        max_len = max(len(a), len(b))
        for i in range(max_len):
            child_path = f"{path}[{i}]"
            if i >= len(a):
                entries.append(
                    DiffEntry(
                        path=child_path,
                        diff_type=DiffType.ADDED,
                        new_value=b[i],
                    )
                )
            elif i >= len(b):
                entries.append(
                    DiffEntry(
                        path=child_path,
                        diff_type=DiffType.REMOVED,
                        old_value=a[i],
                    )
                )
            else:
                entries.extend(diff(a[i], b[i], child_path))
        return entries

    # Scalar comparison
    if a != b:
        entries.append(
            DiffEntry(
                path=path,
                diff_type=DiffType.CHANGED,
                old_value=a,
                new_value=b,
            )
        )

    return entries
