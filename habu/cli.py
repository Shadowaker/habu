from __future__ import annotations

import argparse
import sys
from pathlib import Path

from habu import ui
from habu.discovery import detect_project, get_project
from habu.lint import run_flake8, run_mypy, to_check_result
from habu.models import Exercise, ExerciseContext, Project, Verdict, error
from habu.registry import load_projects


def run_exercise(project_root: Path, exercise: Exercise) -> tuple[list[tuple[str, "object"]], bool]:
    missing = [f for f in exercise.files if not project_root.joinpath(f).exists()]

    if missing:
        return [], False

    ctx = ExerciseContext(root=project_root, exercise_dir=exercise.dir_path(project_root))
    results = []

    for check in exercise.checks:

        try:
            result = check.fn(ctx)
        except Exception as e:  # a bug in the check itself, not the submission
            result = error(f"check crashed: {type(e).__name__}: {e}")

        results.append((check.name, result))

    py_files = sorted({project_root.joinpath(f) for f in exercise.files if f.endswith(".py")})

    if py_files:
        results.append(("flake8", to_check_result(run_flake8(py_files, project_root))))
        results.append(("mypy", to_check_result(run_mypy(py_files, project_root))))

    return results


def main(argv: list[str] | None = None) -> int:

    parser = argparse.ArgumentParser(prog="habu", description="Modular tester for the 42 Python Piscine subjects.")
    parser.add_argument("path", nargs="?", default=".", help="submission directory (default: cwd)")
    parser.add_argument("--project", "-p", help="force a specific project id (e.g. p00), skipping auto-detection")
    parser.add_argument("--list", action="store_true", help="list known projects and exit")
    parser.add_argument("--exercise", "-e", help="only run one exercise id (e.g. ex3)")
    args = parser.parse_args(argv)

    projects = load_projects()

    if args.list:
        ui.print_project_list(projects)
        return 0

    if not projects:
        ui.print_error("no project specs are registered yet")
        return 1

    root = Path(args.path).resolve()
    if not root.is_dir():
        ui.print_error(f"not a directory: {root}")
        return 1

    detection = None
    project: Project | None
    if args.project:
        project = get_project(args.project, projects)
        if project is None:
            ui.print_error(f"unknown project id {args.project!r}. Use --list to see available ids.")
            return 1
    else:
        detection = detect_project(root, projects)
        project = detection.project
        if project is None:
            ui.print_error(
                "couldn't detect which project this submission belongs to "
                "(no known exercise files found). Use --project pXX to force one."
            )
            return 1

    ui.print_header(project, detection, str(root))

    exercises = project.exercises
    if args.exercise:
        exercises = [e for e in exercises if e.id == args.exercise]
        if not exercises:
            ui.print_error(f"no exercise {args.exercise!r} in {project.id}")
            return 1

    counts: dict[Verdict, int] = {}
    exercises_passed = 0
    exercises_total = 0

    for exercise in exercises:
        exercises_total += 1
        ui.print_exercise_header(exercise)

        missing = [f for f in exercise.files if not root.joinpath(f).exists()]
        if missing:
            ui.print_missing_files(exercise, missing)
            continue

        with ui.spinner(f"running {exercise.id}..."):
            results = run_exercise(root, exercise)

        all_pass = True
        for name, result in results:
            ui.print_check_result(name, result)
            counts[result.verdict] = counts.get(result.verdict, 0) + 1
            if result.verdict is not Verdict.PASS:
                all_pass = False

        if all_pass and results:
            exercises_passed += 1

    ui.print_summary(counts, (exercises_passed, exercises_total))

    any_fail = counts.get(Verdict.FAIL, 0) or counts.get(Verdict.ERROR, 0)

    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
