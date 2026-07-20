"""Figure out which 42 Python Piscine project a submission directory belongs to."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from habu.models import Project


@dataclass
class DetectionResult:
    project: Project | None
    score: float
    matched: list[str]
    total: int
    runner_up: tuple[Project, float] | None = None


def detect_project(root: Path, projects: list[Project]) -> DetectionResult:
    best: tuple[Project, float, list[str]] | None = None
    second: tuple[Project, float] | None = None

    for project in projects:

        fingerprint = project.fingerprint_files()
        if not fingerprint:
            continue

        matched = [f for f in fingerprint if root.joinpath(f).exists()]
        score = len(matched) / len(fingerprint)
        if best is None or score > best[1]:
            if best is not None:
                second = (best[0], best[1])
            best = (project, score, matched)
        elif second is None or score > second[1]:
            second = (project, score)

    if best is None or best[1] == 0.0:
        return DetectionResult(project=None, score=0.0, matched=[], total=0, runner_up=second)

    project, score, matched = best
    return DetectionResult(
        project=project,
        score=score,
        matched=matched,
        total=len(project.fingerprint_files()),
        runner_up=second,
    )


def get_project(project_id: str, projects: list[Project]) -> Project | None:
    for p in projects:
        if p.id == project_id:
            return p
    return None
