# json-differ

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

Structural JSON diff tool with colored terminal output. Compare two JSON files and see exactly what changed â added keys, removed keys, modified values, and type changes â with clear, color-coded output.

## Features

- **Structural comparison** â recursively diffs nested objects and arrays
- **Color-coded output** â green for additions, red for removals, yellow for changes, cyan for type changes
- **JSON-pointer paths** â every difference shows the exact path (e.g. `root.users[0].name`)
- **CI-friendly** â exits with code 1 when differences are found, code 0 when identical
- **File output** â optionally write plain-text diff to a file
- **Type change detection** â distinguishes between value changes and type changes (string â int)
- **Numeric compatibility** â treats int/float as compatible types (reports value change, not type change)

## Installation

```bash
pip install -e .
```

Or install from source:

```bash
git clone https://github.com/nripankadas07/json-differ.git
cd json-differ
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Compare two JSON files
json-differ original.json modified.json

# Disable colored output
json-differ original.json modified.json --no-color

# Write diff to a file
json-differ original.json modified.json -o diff-report.txt
```

### As a Library

```python
import json
from json_differ import diff, DiffType

a = {"name": "Alice", "age": 30, "tags": ["admin"]}
b = {"name": "Bob", "age": 30, "tags": ["admin", "user"], "active": True}

entries = diff(a, b)
for entry in entries:
    print(f"{entry.diff_type.value}: {entry.path}")
    # changed: root.name
    # added: root.tags[1]
    # added: root.active
```

### Output Format

```
Found 3 difference(s): 1 changed, 2 added
~ root.name: "Alice" -> "Bob"
+ root.tags[1]: "user"
+ root.active: true
```

Symbols:
- `+` Added (green)
- `-` Removed (red)
- `~` Changed value (yellow)
- `!` Type changed (cyan)

## API Reference

### `diff(a, b, path="root") -> list[DiffEntry]`

Computes structural differences between two JSON-compatible Python values.

**Parameters:**
- `a` â The original value (dict, list, or scalar)
- `b` â The modified value
- `path` â Base path prefix (default: `"root"`)

**Returns:** List of `DiffEntry` dataclass instances.

### `DiffEntry`

| Field | Type | Description |
|-------|------|-------------|
| `path` | `str` | JSON-pointer style path to the changed value |
| `diff_type` | `DiffType` | One of: `ADDED`, `REMOVED`, `CHANGED`, `TYPE_CHANGED` |
| `old_value` | `Any` | Value in the original document (`None` for additions) |
| `new_value` | `Any` | Value in the modified document (`None` for removals) |

### `format_diff(entries, *, color=True) -> str`

Formats a list of diff entries into a human-readable string with optional ANSI color codes.

## Architecture

```
src/json_differ/
  __init__.py       # Package exports
  differ.py         # Core recursive diff engine
  formatter.py      # ANSI-colored terminal formatter
  cli.py            # Click-based CLI entry point
```

The diff engine uses recursive structural comparison: dicts are compared key-by-key, lists are compared index-by-index, and scalars are compared by value and type. The formatter translates `DiffEntry` objects into colored terminal output with summary statistics.

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT License â Copyright 2024 Nripanka Das
