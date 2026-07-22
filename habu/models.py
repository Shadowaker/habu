"""Core data model shared by the framework and every project spec module."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


class Verdict(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class CheckResult:
    verdict: Verdict
    message: str = ""
    detail: str | None = None

    @property
    def passed(self) -> bool:
        return self.verdict is Verdict.PASS


def ok(message: str = "OK", detail: str | None = None) -> CheckResult:
    return CheckResult(Verdict.PASS, message, detail)


def fail(message: str, detail: str | None = None) -> CheckResult:
    return CheckResult(Verdict.FAIL, message, detail)


def skip(message: str, detail: str | None = None) -> CheckResult:
    return CheckResult(Verdict.SKIP, message, detail)


def error(message: str, detail: str | None = None) -> CheckResult:
    return CheckResult(Verdict.ERROR, message, detail)


@dataclass
class ExerciseContext:
    """Handed to every Check function; knows where the submission lives."""

    root: Path
    exercise_dir: Path

    def path(self, *parts: str) -> Path:
        """Path relative to the submission root."""
        return self.root.joinpath(*parts)

    def ex_path(self, *parts: str) -> Path:
        """Path relative to this exercise's directory."""
        return self.exercise_dir.joinpath(*parts)

    def exists(self, *parts: str) -> bool:
        return self.path(*parts).exists()


CheckFn = Callable[[ExerciseContext], CheckResult]


@dataclass
class Check:
    name: str
    fn: CheckFn


@dataclass
class Exercise:
    id: str
    title: str
    files: list[str]
    checks: list[Check] = field(default_factory=list)
    directory: str = ""

    # Each entry is a tuple of substrings
    # A mypy error line is allowlisted when every substring in on of these tuples appears in it
    allowed_mypy_errors: list[tuple[str, ...]] = field(default_factory=list) #

    def dir_path(self, root: Path) -> Path:
        return root.joinpath(self.directory) if self.directory else root


@dataclass
class Project:
    id: str
    name: str
    tagline: str
    exercises: list[Exercise]

    def fingerprint_files(self) -> list[str]:
        seen: list[str] = []
        for ex in self.exercises:
            for f in ex.files:
                if f not in seen:
                    seen.append(f)
        return seen
