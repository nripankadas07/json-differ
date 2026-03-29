"""Tests for the json-differ core engine and formatter."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from json_differ.differ import diff, DiffEntry, DiffType
from json_differ.formatter import format_diff


# ââ Core diff engine tests ââââââââââââââââââââââââââââââââââââââââââ


class TestIdenticalDocuments:
    """No differences should be reported for equal inputs."""

    def test_empty_objects(self) -> None:
        assert diff({}, {}) == []

    def test_identical_flat_objects(self) -> None:
        obj = {"name": "Alice", "age": 30}
        assert diff(obj, obj.copy()) == []

    def test_identical_nested_objects(self) -> None:
        obj = {"a": {"b": {"c": 1}}, "d": [1, 2, 3]}
        assert diff(obj, json.loads(json.dumps(obj))) == []


class TestScalarChanges:
    """Detect value changes in leaf nodes."""

    def test_string_change(self) -> None:
        entries = diff({"name": "Alice"}, {"name": "Bob"})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.CHANGED
        assert entries[0].path == "root.name"
        assert entries[0].old_value == "Alice"
        assert entries[0].new_value == "Bob"

    def test_number_change(self) -> None:
        entries = diff({"count": 10}, {"count": 20})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.CHANGED

    def test_boolean_change(self) -> None:
        entries = diff({"active": True}, {"active": False})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.CHANGED

    def test_null_to_value(self) -> None:
        entries = diff({"val": None}, {"val": "hello"})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.TYPE_CHANGED


class TestKeyAdditionsAndRemovals:
    """Detect added and removed keys."""

    def test_key_added(self) -> None:
        entries = diff({"a": 1}, {"a": 1, "b": 2})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.ADDED
        assert entries[0].path == "root.b"
        assert entries[0].new_value == 2

    def test_key_removed(self) -> None:
        entries = diff({"a": 1, "b": 2}, {"a": 1})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.REMOVED
        assert entries[0].path == "root.b"
        assert entries[0].old_value == 2

    def test_multiple_additions_and_removals(self) -> None:
        a = {"keep": 1, "remove1": 2, "remove2": 3}
        b = {"keep": 1, "add1": 4, "add2": 5}
        entries = diff(a, b)
        added = [e for e in entries if e.diff_type == DiffType.ADDED]
        removed = [e for e in entries if e.diff_type == DiffType.REMOVED]
        assert len(added) == 2
        assert len(removed) == 2


class TestNestedChanges:
    """Detect changes in deeply nested structures."""

    def test_nested_value_change(self) -> None:
        a = {"user": {"profile": {"name": "Alice"}}}
        b = {"user": {"profile": {"name": "Bob"}}}
        entries = diff(a, b)
        assert len(entries) == 1
        assert entries[0].path == "root.user.profile.name"

    def test_nested_key_added(self) -> None:
        a = {"config": {"debug": False}}
        b = {"config": {"debug": False, "verbose": True}}
        entries = diff(a, b)
        assert len(entries) == 1
        assert entries[0].path == "root.config.verbose"
        assert entries[0].diff_type == DiffType.ADDED


class TestArrayChanges:
    """Detect changes in arrays (index-based comparison)."""

    def test_array_element_changed(self) -> None:
        entries = diff({"items": [1, 2, 3]}, {"items": [1, 99, 3]})
        assert len(entries) == 1
        assert entries[0].path == "root.items[1]"
        assert entries[0].diff_type == DiffType.CHANGED

    def test_array_element_added(self) -> None:
        entries = diff({"items": [1, 2]}, {"items": [1, 2, 3]})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.ADDED
        assert entries[0].path == "root.items[2]"

    def test_array_element_removed(self) -> None:
        entries = diff({"items": [1, 2, 3]}, {"items": [1, 2]})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.REMOVED
        assert entries[0].path == "root.items[2]"

    def test_array_of_objects(self) -> None:
        a = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        b = {"users": [{"name": "Alice"}, {"name": "Charlie"}]}
        entries = diff(a, b)
        assert len(entries) == 1
        assert entries[0].path == "root.users[1].name"


class TestTypeChanges:
    """Detect when the type of a value changes entirely."""

    def test_string_to_int(self) -> None:
        entries = diff({"val": "hello"}, {"val": 42})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.TYPE_CHANGED

    def test_object_to_array(self) -> None:
        entries = diff({"val": {"a": 1}}, {"val": [1, 2]})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.TYPE_CHANGED

    def test_int_float_compatible(self) -> None:
        """int and float are treated as compatible numeric types."""
        entries = diff({"val": 1}, {"val": 1.5})
        assert len(entries) == 1
        assert entries[0].diff_type == DiffType.CHANGED  # not TYPE_CHANGED


# ââ Formatter tests âââââââââââââââââââââââââââââââââââââââââââââââââ


class TestFormatter:
    """Tests for human-readable output formatting."""

    def test_no_differences(self) -> None:
        assert format_diff([]) == "No differences found."

    def test_plain_output(self) -> None:
        entries = diff({"a": 1}, {"a": 2})
        result = format_diff(entries, color=False)
        assert "1 difference(s)" in result
        assert "root.a" in result
        assert "->" in result

    def test_added_symbol(self) -> None:
        entries = diff({}, {"new_key": "val"})
        result = format_diff(entries, color=False)
        assert "+ root.new_key" in result

    def test_removed_symbol(self) -> None:
        entries = diff({"old_key": "val"}, {})
        result = format_diff(entries, color=False)
        assert "- root.old_key" in result

    def test_summary_line(self) -> None:
        a = {"keep": 1, "remove": 2}
        b = {"keep": 1, "add": 3}
        entries = diff(a, b)
        result = format_diff(entries, color=False)
        assert "1 added" in result
        assert "1 removed" in result
