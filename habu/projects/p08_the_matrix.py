from __future__ import annotations

from habu.checks import file_exists
from habu.executor import run_script_file
from habu.inspect_utils import contains as source_contains
from habu.models import Check, Exercise, ExerciseContext, Project, fail, ok

REQUIRED_ENV_VARS = ["MATRIX_MODE", "DATABASE_URL", "API_KEY", "LOG_LEVEL", "ZION_ENDPOINT"]


def _ex0_runs_and_reports_status(ctx: ExerciseContext):

    script = ctx.path("ex0/construct.py")
    if not script.exists():
        return fail("ex0/construct.py not found")

    r = run_script_file(script, cwd=script.parent)
    if r.timed_out:
        return fail("timed out")

    if r.returncode != 0:
        return fail("crashed when run directly", detail=r.stderr)

    if "MATRIX STATUS" not in r.stdout:
        return fail("expected a 'MATRIX STATUS' line reporting venv detection", detail=r.stdout)

    return ok(
        "runs cleanly and reports a MATRIX STATUS line (structural check only)"
    )


def _ex1_reports_dependencies(ctx: ExerciseContext):

    script = ctx.path("ex1/loading.py")
    if not script.exists():
        return fail("ex1/loading.py not found")

    r = run_script_file(script, cwd=script.parent, timeout=15)
    if r.timed_out:
        return fail("timed out")

    if r.returncode != 0:
        return fail(
            "crashed instead of handling missing dependencies gracefully",
            detail=r.stderr,
        )

    mentioned = [pkg for pkg in ("pandas", "numpy", "matplotlib") if pkg in r.stdout]
    if len(mentioned) < 3:
        return fail(
            f"expected the dependency report to mention pandas/numpy/matplotlib, "
            f"only saw: {mentioned}", detail=r.stdout
        )

    return ok("runs without crashing and reports status for pandas/numpy/matplotlib")


def _ex1_uses_numpy_for_data(ctx: ExerciseContext):

    script = ctx.path("ex1/loading.py")
    if not script.exists():
        return fail("ex1/loading.py not found")

    src = script.read_text(errors="replace")
    if "numpy" not in src and "np." not in src:
        return fail("expected loading.py to use numpy to generate its dataset")

    return ok("references numpy")


def _ex1_dependency_files(ctx: ExerciseContext):

    reqs = ctx.path("ex1/requirements.txt")
    pyproject = ctx.path("ex1/pyproject.toml")
    if not reqs.exists() or not pyproject.exists():
        return fail("both ex1/requirements.txt and ex1/pyproject.toml are required")

    reqs_src = reqs.read_text(errors="replace").lower()
    pyproject_src = pyproject.read_text(errors="replace").lower()

    missing = [
        pkg
        for pkg in ("pandas", "numpy", "matplotlib")
        if pkg not in reqs_src or pkg not in pyproject_src
    ]

    if missing:
        return fail(f"requirements.txt/pyproject.toml should both reference: {missing}")

    return ok("requirements.txt and pyproject.toml both declare pandas/numpy/matplotlib")


def _ex2_reads_env_vars(ctx: ExerciseContext):

    script = ctx.path("ex2/oracle.py")
    if not script.exists():
        return fail("ex2/oracle.py not found")

    src = script.read_text(errors="replace")

    missing = [v for v in REQUIRED_ENV_VARS if v not in src]

    if missing:
        return fail(f"oracle.py doesn't reference these required config variables: {missing}")

    return ok("references all 5 required configuration variables")


def _ex2_runs_without_config(ctx: ExerciseContext):

    script = ctx.path("ex2/oracle.py")
    if not script.exists():
        return fail("ex2/oracle.py not found")

    r = run_script_file(script, cwd=script.parent, env={k: "" for k in REQUIRED_ENV_VARS})
    if r.timed_out:
        return fail("timed out")

    if r.returncode != 0:
        return fail("crashed instead of handling missing configuration gracefully", detail=r.stderr)

    return ok("runs without crashing when no configuration is present")


def _ex2_env_override_changes_output(ctx: ExerciseContext):

    script = ctx.path("ex2/oracle.py")
    if not script.exists():
        return fail("ex2/oracle.py not found")

    r_dev = run_script_file(script, cwd=script.parent, env={"MATRIX_MODE": "development"})
    r_prod = run_script_file(script, cwd=script.parent, env={"MATRIX_MODE": "production"})

    if r_dev.timed_out or r_prod.timed_out:
        return fail("timed out")

    if r_dev.returncode != 0 or r_prod.returncode != 0:
        return fail(
            "crashed while testing MATRIX_MODE=development vs production", detail=r_dev.stderr + r_prod.stderr
        )

    if r_dev.stdout == r_prod.stdout:
        return fail(
            "output is identical for MATRIX_MODE=development and MATRIX_MODE=production, "
            "the subject requires a visible difference"
        )
    return ok("output visibly differs between development and production MATRIX_MODE")


def _ex2_files_and_gitignore(ctx: ExerciseContext):

    env_example = ctx.path("ex2/.env.example")

    gitignore = ctx.path("ex2/.gitignore")
    if not env_example.exists():
        return fail(".env.example not found")

    if not gitignore.exists():
        return fail(".gitignore not found")

    if not source_contains(gitignore, ".env"):
        return fail(".gitignore should list .env so real secrets never get committed")

    return ok(".env.example and .gitignore are present, and .gitignore excludes .env")


PROJECT = Project(
    id="p08",
    name="The Matrix",
    tagline="Welcome to the Real World of Data Engineering",
    exercises=[
        Exercise(
            id="ex0",
            title="Entering the Matrix",
            files=["ex0/construct.py"],
            checks=[
                file_exists("ex0/construct.py"),
                Check("runs and reports a MATRIX STATUS line", _ex0_runs_and_reports_status),
            ],
        ),
        Exercise(
            id="ex1",
            title="Loading Programs",
            files=["ex1/loading.py", "ex1/requirements.txt", "ex1/pyproject.toml"],
            checks=[
                file_exists("ex1/loading.py"),
                Check("requirements.txt and pyproject.toml declare the required packages", _ex1_dependency_files),
                Check("handles missing dependencies gracefully and reports their status", _ex1_reports_dependencies),
                Check("uses numpy to generate its dataset", _ex1_uses_numpy_for_data),
            ],
        ),
        Exercise(
            id="ex2",
            title="Accessing the Mainframe",
            files=["ex2/oracle.py", "ex2/requirements.txt", "ex2/.env.example", "ex2/.gitignore"],
            checks=[
                file_exists("ex2/oracle.py"),
                Check(".env.example and .gitignore are present and correct", _ex2_files_and_gitignore),
                Check("reads all 5 required configuration variables", _ex2_reads_env_vars),
                Check("runs without crashing when configuration is missing", _ex2_runs_without_config),
                Check("visibly differs between development and production MATRIX_MODE", _ex2_env_override_changes_output),
            ],
        ),
    ],
)
