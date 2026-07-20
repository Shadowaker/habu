"""
Subprocess-isolated execution primitives.

Everything a Check does to a student's submission runs in a fresh `python3` subprocess: a crashing,
hanging, or `sys.exit()`- an happy code must never take the tester down with it,
and stdin/stdout/stderr need to be exactly the channels a real grader would look at.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_TIMEOUT = 6.0
_MARKER = "###HABU_JSON###"


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False


@dataclass
class ProbeResult:
    ok: bool
    records: list = field(default_factory=list)
    stdout: str = ""
    error: str | None = None
    message: str | None = None
    raw: ExecResult | None = None


def run_python(
    code: str,
    cwd: Path,
    argv: list[str] | None = None,
    stdin: str = "",
    timeout: float = DEFAULT_TIMEOUT,
) -> ExecResult:

    cmd = [sys.executable, "-c", code, *(argv or [])]
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecResult(proc.stdout, proc.stderr, proc.returncode)
    except subprocess.TimeoutExpired as e:
        return ExecResult(e.stdout or "", e.stderr or "", -1, timed_out=True)


def run_script_file(
    path: Path,
    cwd: Path,
    argv: list[str] | None = None,
    stdin: str = "",
    timeout: float = DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
) -> ExecResult:
    """
    Invoke with a bare filename (not the absolute path) whenever cwd is the script's own directory,
    so sys.argv[0] looks the way the subject's examples show it (e.g. "ft_command_quest.py"), not a tester-specific
    absolute path.
    """

    script_arg = path.name if cwd is not None and Path(cwd) == path.parent else str(path)
    cmd = [sys.executable, script_arg, *(argv or [])]
    full_env = None

    if env is not None:
        full_env = {**os.environ, **env}
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=full_env,
        )
        return ExecResult(proc.stdout, proc.stderr, proc.returncode)
    except subprocess.TimeoutExpired as e:
        return ExecResult(e.stdout or "", e.stderr or "", -1, timed_out=True)


_PROBE_TEMPLATE = '''
import sys, json, io, contextlib, importlib.util

def _record(_records):
    def record(value):
        _records.append(value)
    return record

_records = []
_buf = io.StringIO()
_result = {{"ok": False}}
try:
    _spec = importlib.util.spec_from_file_location("_submission_mod", {module_path!r})
    mod = importlib.util.module_from_spec(_spec)
    record = _record(_records)
    with contextlib.redirect_stdout(_buf):
        _spec.loader.exec_module(mod)
{body}
    _result = {{"ok": True}}
except SystemExit as e:
    _result = {{"ok": False, "error": "SystemExit", "message": str(e.code)}}
except Exception as e:
    _result = {{"ok": False, "error": type(e).__name__, "message": str(e)}}
_result["records"] = _records
_result["stdout"] = _buf.getvalue()
print({marker!r} + json.dumps(_result, default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else repr(o)))
'''


def probe(
    module_path: Path,
    body: str,
    cwd: Path | None = None,
    stdin: str = "",
    timeout: float = DEFAULT_TIMEOUT,
) -> ProbeResult:
    """Load ``module_path`` as ``mod`` inside a subprocess, then exec ``body``.
    ``body`` is arbitrary Python source, indented as the caller likes; it runs with ``mod``
    (the loaded submission module) and ``record(value)`` (append to a results list returned to the caller)
    in scope, with stdout captured (not polluting the JSON marker channel) for the duration of both the
    module load and the body. Anything the body needs to assert lives in ``record(...)`` calls the caller
    inspects afterwards.
    """

    indented_body = "\n".join(
        ("        " + line if line.strip() else "") for line in body.strip("\n").splitlines()
    )
    code = _PROBE_TEMPLATE.format(module_path=str(module_path), body=indented_body, marker=_MARKER)
    raw = run_python(code, cwd=cwd or module_path.parent, stdin=stdin, timeout=timeout)
    return _parse_probe(raw)


def _parse_probe(raw: ExecResult) -> ProbeResult:

    if raw.timed_out:
        return ProbeResult(ok=False, error="Timeout", message="execution timed out", raw=raw)

    line = None
    for candidate in raw.stdout.splitlines()[::-1]:
        if candidate.startswith(_MARKER):
            line = candidate[len(_MARKER):]
            break

    if line is None:
        return ProbeResult(
            ok=False,
            error="NoResult",
            message="submission crashed before producing a result",
            raw=raw,
        )

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return ProbeResult(ok=False, error="BadJSON", message="internal probe error", raw=raw)

    return ProbeResult(
        ok=data.get("ok", False),
        records=data.get("records", []),
        stdout=data.get("stdout", ""),
        error=data.get("error"),
        message=data.get("message"),
        raw=raw,
    )


# pydantic is a declared project dependency (see pyproject.toml), so `uv
# sync`/`uv run habu` always installs it — this only fires as a fallback if
# habu is invoked against a stale, unsynced .venv.
THIRD_PARTY_HINTS = {"pydantic"}


def missing_dependency(result: ProbeResult | ExecResult) -> str | None:

    text = ""
    if isinstance(result, ProbeResult):
        text = f"{result.error or ''} {result.message or ''}"
        if result.raw:
            text += " " + result.raw.stderr
    else:
        text = result.stderr

    for name in THIRD_PARTY_HINTS:
        if f"No module named '{name}" in text:
            return name

    return None
