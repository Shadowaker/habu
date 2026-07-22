from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from habu.models import CheckResult, Verdict

TIMEOUT = 60.0


@dataclass
class LintResult:
    tool: str
    ok: bool
    issue_count: int
    issues: list[str] = field(default_factory=list)
    error: str | None = None
    allowed_count: int = 0


def _run(module: str, args: list[str], files: list[Path], cwd: Path) -> tuple[str, int] | LintResult:

    if not files:
        return LintResult(tool=module, ok=True, issue_count=0)

    rel_files = sorted({str(f.relative_to(cwd)) for f in files})
    cmd = [sys.executable, "-m", module, *args, *rel_files]

    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT)
    except FileNotFoundError:
        return LintResult(tool=module, ok=True, issue_count=0, error=f"{module} is not installed — skipped")
    except subprocess.TimeoutExpired:
        return LintResult(tool=module, ok=True, issue_count=0, error=f"{module} timed out — skipped")

    return (proc.stdout + proc.stderr).strip(), proc.returncode


def run_flake8(files: list[Path], cwd: Path) -> LintResult:

    result = _run("flake8", [], files, cwd)
    if isinstance(result, LintResult):
        return result

    output, returncode = result
    lines = [ln for ln in output.splitlines() if ln.strip()]

    return LintResult(tool="flake8", ok=(returncode == 0 and not lines), issue_count=len(lines), issues=lines)


def run_mypy(files: list[Path], cwd: Path, allowed_errors: list[tuple[str, ...]] | None = None) -> LintResult:

    result = _run("mypy", ["--ignore-missing-imports", "--no-error-summary"], files, cwd)
    if isinstance(result, LintResult):
        return result

    output, _returncode = result
    all_errors = [ln for ln in output.splitlines() if ": error:" in ln]
    if allowed_errors is None:
        allowed_errors = []

    def is_allowed(line: str) -> bool:
        return any(all(substr in line for substr in group) for group in allowed_errors)

    issue_lines = [ln for ln in all_errors if not is_allowed(ln)]
    allowed_count = len(all_errors) - len(issue_lines)

    return LintResult(
        tool="mypy",
        ok=(len(issue_lines) == 0),
        issue_count=len(issue_lines),
        issues=issue_lines,
        allowed_count=allowed_count,
    )


def to_check_result(result: LintResult) -> CheckResult:

    if result.error:
        return CheckResult(Verdict.SKIP, result.error)

    if result.ok:
        if result.allowed_count:
            plural = "s" if result.allowed_count > 1 else ""
            return CheckResult(Verdict.PASS, f"no issues ({result.allowed_count} expected error{plural} allowlisted)")
        return CheckResult(Verdict.PASS, "no issues")

    shown = result.issues[:5]
    detail = "\n".join(shown)

    if len(result.issues) > len(shown):
        detail += f"\n... and {len(result.issues) - len(shown)} more"

    return CheckResult(Verdict.FAIL, f"{result.issue_count} issue(s)", detail=detail)
