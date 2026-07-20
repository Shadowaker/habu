"""Lightweight source-level checks (import style, forbidden constructs, etc).

These never execute the submission — they just read the text, so they're
safe to run on code that Check functions won't otherwise import.
"""

from __future__ import annotations

import re
from pathlib import Path


def read_source(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def contains(path: Path, pattern: str, *, regex: bool = False) -> bool:

    src = read_source(path)
    if src is None:
        return False

    if regex:
        return re.search(pattern, src, re.MULTILINE) is not None

    return pattern in src


def uses_import_style(path: Path, module: str, style: str) -> bool:
    """style: 'import' for `import module`, 'from' for `from module import ...`."""

    src = read_source(path)
    if src is None:
        return False

    mod = re.escape(module)
    if style == "import":
        return re.search(rf"^\s*import\s+{mod}(\s|$|\.|,)", src, re.MULTILINE) is not None

    if style == "from":
        return re.search(rf"^\s*from\s+{mod}\s+import\s", src, re.MULTILINE) is not None

    raise ValueError(f"unknown style {style!r}")

