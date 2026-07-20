"""Reusable Check factories built on top of executor.probe/run_script_file.

Project spec modules are meant to read as declarative lists of these calls;
drop down to a raw `Check(name, fn)` with a hand-written `fn` only when a
project's behavior genuinely needs something bespoke (most OOP-heavy
projects do, via `probe_check`).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable
import inspect

from habu.executor import ExecResult, ProbeResult, missing_dependency, probe, run_script_file
from habu.inspect_utils import contains as source_contains
from habu.inspect_utils import uses_import_style
from habu.models import Check, CheckResult, ExerciseContext, error, fail, ok, skip


def _diff_detail(expected: str, actual: str) -> str:
    return f"--- expected ---\n{expected}\n--- got ---\n{actual}"


def _norm(s: str) -> str:
    return s.replace("\r\n", "\n").rstrip("\n")


def file_exists(rel_path: str, *, name: str | None = None) -> Check:

    def fn(ctx: ExerciseContext) -> CheckResult:
        if ctx.path(rel_path).exists():
            return ok("present")
        return fail(f"{rel_path} not found")

    return Check(name or f"{rel_path} exists", fn)


def source_has_import(rel_path: str, module: str, style: str, *, name: str | None = None) -> Check:

    def fn(ctx: ExerciseContext) -> CheckResult:

        p = ctx.path(rel_path)
        if not p.exists():
            return fail(f"{rel_path} not found")

        if uses_import_style(p, module, style):
            return ok(f"uses {style}-style import of {module}")
        verb = f"import {module}" if style == "import" else f"from {module} import ..."

        return fail(f"expected `{verb}` in {rel_path}")

    return Check(name or f"{rel_path} imports {module} ({style})", fn)


def source_contains_check(
        rel_path: str,
        pattern: str,
        *,
        regex: bool = False,
        message: str,
        name: str | None = None
) -> Check:

    def fn(ctx: ExerciseContext) -> CheckResult:

        p = ctx.path(rel_path)
        if not p.exists():
            return fail(f"{rel_path} not found")

        if source_contains(p, pattern, regex=regex):
            return ok(message)

        return fail(f"expected {rel_path} to match: {message}")

    return Check(name or f"{rel_path}: {message}", fn)


def source_forbids(
        rel_path: str,
        pattern: str,
        *,
        regex: bool = False,
        message: str,
        name: str | None = None
) -> Check:

    def fn(ctx: ExerciseContext) -> CheckResult:

        p = ctx.path(rel_path)
        if not p.exists():
            return fail(f"{rel_path} not found")

        if source_contains(p, pattern, regex=regex):
            return fail(f"{rel_path} should not: {message}")

        return ok(f"does not: {message}")

    return Check(name or f"{rel_path}: not {message}", fn)


def _probe_or_signal(module_path: Path, body: str, stdin: str) -> tuple[ProbeResult | None, CheckResult | None]:

    result = probe(module_path, body, stdin=stdin)
    dep = missing_dependency(result)
    if dep:
        return None, skip(f"requires {dep}, which isn't installed — run `uv sync`")
    return result, None


def function_prints_exact(
    rel_path: str,
    func_name: str,
    *,
    expected: str,
    stdin: str = "",
    call: str | None = None,
    name: str | None = None,
) -> Check:
    """Call `func_name()` (or the `call` expression) and require exact stdout."""

    def fn(ctx: ExerciseContext) -> CheckResult:

        module_path = ctx.path(rel_path)
        if not module_path.exists():
            return fail(f"{rel_path} not found")

        body = call or f"mod.{func_name}()"
        result, signal = _probe_or_signal(module_path, body, stdin)
        if signal:
            return signal

        if not result.ok:
            return fail(
                f"raised {result.error}: {result.message}", detail=result.raw.stderr if result.raw else None
            )

        actual, expected_n = _norm(result.stdout), _norm(expected)
        if actual == expected_n:
            return ok("output matches exactly")

        return fail("output does not match expected text exactly", detail=_diff_detail(expected_n, actual))

    return Check(name or f"{func_name}() prints the expected output", fn)


def function_prints_contains(
    rel_path: str,
    func_name: str,
    *,
    expected_substrings: list[str],
    stdin: str = "",
    call: str | None = None,
    name: str | None = None,
) -> Check:
    """Call `func_name()` and require each of expected_substrings to appear in stdout."""

    def fn(ctx: ExerciseContext) -> CheckResult:

        module_path = ctx.path(rel_path)
        if not module_path.exists():
            return fail(f"{rel_path} not found")

        body = call or f"mod.{func_name}()"
        result, signal = _probe_or_signal(module_path, body, stdin)
        if signal:
            return signal

        if not result.ok:
            return fail(
                f"raised {result.error}: {result.message}", detail=result.raw.stderr if result.raw else None
            )

        missing = [s for s in expected_substrings if s not in result.stdout]
        if not missing:
            return ok("output contains the expected content")

        return fail(
            f"missing expected content: {missing[0]!r}" + (f" (+{len(missing) - 1} more)" if len(missing) > 1 else ""),
            detail=f"--- got ---\n{result.stdout}",
        )

    return Check(name or f"{func_name}() output contains expected content", fn)


def probe_check(
    rel_path: str,
    body: str,
    assertion: Callable[[list], CheckResult] | Callable[[list, str], CheckResult],
    *,
    stdin: str = "",
    name: str,
) -> Check:
    """
    General escape hatch: run `body` (which should call `record(...)` with whatever the test needs to inspect),
    then hand the collected records (and, if `assertion` takes a second parameter, the captured stdout of the
    whole probe) to `assertion` to decide pass/fail. Use this for OOP/behavioral tests that don't reduce to
    "one function call, one stdout diff".
    """

    def fn(ctx: ExerciseContext) -> CheckResult:

        module_path = ctx.path(rel_path)
        if not module_path.exists():
            return fail(f"{rel_path} not found")

        result, signal = _probe_or_signal(module_path, body, stdin)
        if signal:
            return signal

        if not result.ok:
            return fail(
                f"raised {result.error}: {result.message}", detail=result.raw.stderr if result.raw else None
            )

        try:
            if len(inspect.signature(assertion).parameters) >= 2:
                return assertion(result.records, result.stdout)

            return assertion(result.records)
        except Exception as e:
            return error(f"assertion crashed: {type(e).__name__}: {e}")

    return Check(name, fn)


def script_stdout_exact(
    rel_path: str,
    *,
    expected: str,
    argv: list[str] | None = None,
    stdin: str = "",
    name: str | None = None,
) -> Check:

    def fn(ctx: ExerciseContext) -> CheckResult:

        script = ctx.path(rel_path)
        if not script.exists():
            return fail(f"{rel_path} not found")

        r: ExecResult = run_script_file(script, cwd=script.parent, argv=argv, stdin=stdin)
        if r.timed_out:
            return fail("timed out")

        actual, expected_n = _norm(r.stdout), _norm(expected)
        if actual == expected_n:
            return ok("stdout matches exactly")

        return fail("stdout does not match expected text exactly", detail=_diff_detail(expected_n, actual))

    return Check(name or f"{rel_path} stdout matches exactly", fn)


def script_stdout_contains(
    rel_path: str,
    *,
    expected_substrings: list[str],
    argv: list[str] | None = None,
    stdin: str = "",
    name: str | None = None,
) -> Check:

    def fn(ctx: ExerciseContext) -> CheckResult:

        script = ctx.path(rel_path)
        if not script.exists():
            return fail(f"{rel_path} not found")

        r: ExecResult = run_script_file(script, cwd=script.parent, argv=argv, stdin=stdin)
        if r.timed_out:
            return fail("timed out")

        missing = [s for s in expected_substrings if s not in r.stdout]
        if not missing:
            return ok("stdout contains the expected content")

        return fail(
            f"missing expected content: {missing[0]!r}" + (f" (+{len(missing) - 1} more)" if len(missing) > 1 else ""),
            detail=f"--- got ---\n{r.stdout}\n--- stderr ---\n{r.stderr}",
        )

    return Check(name or f"{rel_path} stdout contains expected content", fn)


def script_runs_without_crash(
        rel_path: str,
        *, argv: list[str] | None = None,
        stdin: str = "",
        name: str | None = None
) -> Check:

    def fn(ctx: ExerciseContext) -> CheckResult:
        script = ctx.path(rel_path)
        if not script.exists():
            return fail(f"{rel_path} not found")

        r = run_script_file(script, cwd=script.parent, argv=argv, stdin=stdin)
        if r.timed_out:
            return fail("timed out")

        if r.returncode != 0:
            return fail(f"exited with code {r.returncode}", detail=f"--- stderr ---\n{r.stderr}")

        return ok("ran without crashing")

    return Check(name or f"{rel_path} runs without crashing", fn)


def script_stdout_regex(
    rel_path: str,
    patterns: list[str],
    *,
    argv: list[str] | None = None,
    stdin: str = "",
    name: str | None = None,
) -> Check:
    """
    Require each regex pattern to be found somewhere in stdout. For freeform/self-authored demo scripts
    (OOP projects etc.) where the exact wording is up to the student but the shape of the required output isn't.
    """

    def fn(ctx: ExerciseContext) -> CheckResult:

        script = ctx.path(rel_path)
        if not script.exists():
            return fail(f"{rel_path} not found")

        r = run_script_file(script, cwd=script.parent, argv=argv, stdin=stdin)
        if r.timed_out:
            return fail("timed out")

        missing = [p for p in patterns if not re.search(p, r.stdout, re.MULTILINE)]
        if not missing:
            return ok("stdout matches the expected structure")

        return fail(
            f"missing expected pattern: {missing[0]!r}",
            detail=f"--- got ---\n{r.stdout}\n--- stderr ---\n{r.stderr}",
        )

    return Check(name or f"{rel_path} stdout matches expected structure", fn)


def script_result(
        rel_path: str,
        *, argv: list[str] | None = None,
        stdin: str = "",
        timeout: float = 10.0
) -> Callable[[ExerciseContext], ExecResult | None]:
    """Low-level accessor for custom Check functions that need the raw ExecResult (e.g. to count regex matches)
    rather than a canned assertion."""

    def get(ctx: ExerciseContext) -> ExecResult | None:

        script = ctx.path(rel_path)
        if not script.exists():
            return None

        return run_script_file(script, cwd=script.parent, argv=argv, stdin=stdin, timeout=timeout)

    return get
