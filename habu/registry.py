"""Collects every implemented project spec into one list."""

from __future__ import annotations

from habu.models import Project

_MODULE_NAMES = [
    "p00_growing_code",
    "p01_code_cultivation",
    "p02_garden_guardian",
    "p03_data_quest",
    "p04_data_archivist",
    "p05_code_nexus",
]


def load_projects() -> list[Project]:

    projects: list[Project] = []

    for name in _MODULE_NAMES:

        try:
            mod = __import__(f"habu.projects.{name}", fromlist=["PROJECT"])
        except ModuleNotFoundError:
            continue

        project = getattr(mod, "PROJECT", None)
        if project is not None:
            projects.append(project)

    return projects
