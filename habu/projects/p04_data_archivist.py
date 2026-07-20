from __future__ import annotations

import tempfile
from pathlib import Path

from habu.checks import file_exists, probe_check, source_contains_check, source_forbids
from habu.executor import run_script_file
from habu.models import Check, Exercise, ExerciseContext, Project, fail, ok

SOURCE_LINES = [
    "[FRAGMENT 001] Digital preservation protocols established 2087",
    "[FRAGMENT 002] Knowledge must survive the entropy wars",
    "[FRAGMENT 003] Every byte saved is a victory against oblivion",
]
SOURCE_CONTENT = "\n".join(SOURCE_LINES) + "\n"


def _with_temp_source(fn):
    """Runs `fn(ctx, tmp_path)` with a scratch source file (outside the
    submission dir) containing SOURCE_CONTENT."""

    def check_fn(ctx: ExerciseContext):

        with tempfile.TemporaryDirectory() as td:

            src = Path(td) / "ancient_fragment.txt"
            src.write_text(SOURCE_CONTENT)
            return fn(ctx, src)

    return check_fn


def _ex0_missing_file(ctx: ExerciseContext):

    script = ctx.path("ex0/ft_ancient_text.py")
    if not script.exists():
        return fail("ex0/ft_ancient_text.py not found")

    r = run_script_file(script, cwd=script.parent, argv=["/definitely/not/a/real/path.txt"])
    if r.timed_out:
        return fail("timed out")

    if "[Errno 2]" in r.stdout and "No such file or directory" in r.stdout:
        return ok("reports Python's native FileNotFoundError text for a missing file")

    return fail("missing-file case doesn't surface the `[Errno 2] No such file or directory` message", detail=r.stdout)


@_with_temp_source
def _ex0_reads_file(ctx: ExerciseContext, src: Path):

    script = ctx.path("ex0/ft_ancient_text.py")
    if not script.exists():
        return fail("ex0/ft_ancient_text.py not found")

    r = run_script_file(script, cwd=script.parent, argv=[str(src)])
    if r.timed_out:
        return fail("timed out")

    missing = [line for line in SOURCE_LINES if line not in r.stdout]
    if missing:
        return fail("file content wasn't reproduced in stdout", detail=r.stdout)

    return ok("displays the file's content (cat-like)")


@_with_temp_source
def _ex1_transform_and_save(ctx: ExerciseContext, src: Path):

    script = ctx.path("ex1/ft_archive_creation.py")
    if not script.exists():
        return fail("ex1/ft_archive_creation.py not found")

    r_empty = run_script_file(script, cwd=script.parent, argv=[str(src)], stdin="\n")
    if r_empty.timed_out:
        return fail("timed out (empty filename case)")

    transformed_present = all(f"{line}#" in r_empty.stdout for line in SOURCE_LINES)
    if not transformed_present:
        return fail(
            "transformed content ('#' appended to each line) not found in stdout", detail=r_empty.stdout
        )

    out_name = "habu_archive_output.txt"
    out_path = script.parent / out_name
    out_path.unlink(missing_ok=True)

    try:
        r_save = run_script_file(script, cwd=script.parent, argv=[str(src)], stdin=f"{out_name}\n")
        if r_save.timed_out:
            return fail("timed out (save case)")

        if not out_path.exists():
            return fail(f"expected a new file named '{out_name}' to be created when a filename is given")

        saved = out_path.read_text()
        if not all(f"{line}#" in saved for line in SOURCE_LINES):
            return fail("saved file doesn't contain the '#'-suffixed transformed content", detail=saved)

        return ok("appends '#' to each line, skips saving on empty input, saves correctly when given a filename")

    finally:
        out_path.unlink(missing_ok=True)


@_with_temp_source
def _ex2_stream_separation(ctx: ExerciseContext, src: Path):
    script = ctx.path("ex2/ft_stream_management.py")
    if not script.exists():
        return fail("ex2/ft_stream_management.py not found")

    r = run_script_file(script, cwd=script.parent, argv=["/definitely/not/a/real/path.txt"])
    if r.timed_out:
        return fail("timed out")

    error_in_stderr = "[Errno 2]" in r.stderr
    error_in_stdout = "[Errno 2]" in r.stdout

    if error_in_stderr and not error_in_stdout:
        return ok("file-open errors go to stderr, not stdout")

    if not error_in_stderr and not error_in_stdout:
        return fail("the `[Errno 2]` error text wasn't found on either stream")

    return fail(
        "the error message appears on stdout — it must go to stderr instead",
        detail=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    )


@_with_temp_source
def _ex2_reads_without_input(ctx: ExerciseContext, src: Path):

    script = ctx.path("ex2/ft_stream_management.py")
    if not script.exists():
        return fail("ex2/ft_stream_management.py not found")

    if "input(" in script.read_text(errors="replace"):
        return fail("ex2 must read the filename without using input() (per the subject)")

    r = run_script_file(script, cwd=script.parent, argv=[str(src)], stdin="\n")
    if r.timed_out:
        return fail("timed out")

    if all(line in r.stdout for line in SOURCE_LINES):
        return ok("reads the file and doesn't use input()")

    return fail("file content wasn't reproduced in stdout", detail=r.stdout)


def _ex3_probe_assertion(records: list):
    got = dict((r[0], r[1:]) for r in records)
    if "missing" not in got or "read" not in got:
        return fail(f"expected both a 'missing' and a 'read' result, got: {records}")

    m_ok, m_msg = got["missing"]
    if m_ok is not False or "No such file or directory" not in m_msg:
        return fail(f"missing-file case should return (False, <errno-2 message>), got {got['missing']}")

    r_ok, r_content = got["read"]
    if r_ok is not True or "hello vault" not in r_content:
        return fail(f"reading a real file should return (True, <its content>), got {got['read']}")

    return ok("returns (bool, str) correctly for both a missing file and a real file")


PROJECT = Project(
    id="p04",
    name="Data Archivist",
    tagline="Digital Preservation in the Cyber Archives",
    exercises=[
        Exercise(
            id="ex0",
            title="Ancient Text Recovery",
            files=["ex0/ft_ancient_text.py"],
            checks=[
                file_exists("ex0/ft_ancient_text.py"),
                source_forbids(
                    "ex0/ft_ancient_text.py",
                    r"\bwith\s+open\(",
                    regex=True,
                    message="use the `with` statement (introduced in ex3)",
                ),
                Check("handles a missing file with Python's native error text", _ex0_missing_file),
                Check("reads and displays the file's content", _ex0_reads_file),
            ],
        ),
        Exercise(
            id="ex1",
            title="Archive Creation",
            files=["ex1/ft_archive_creation.py"],
            checks=[
                file_exists("ex1/ft_archive_creation.py"),
                Check("transforms content with '#' and saves only when a filename is given", _ex1_transform_and_save),
            ],
        ),
        Exercise(
            id="ex2",
            title="Stream Management",
            files=["ex2/ft_stream_management.py"],
            checks=[
                file_exists("ex2/ft_stream_management.py"),
                Check("errors are printed to stderr, not stdout", _ex2_stream_separation),
                Check("reads input without using input()", _ex2_reads_without_input),
            ],
        ),
        Exercise(
            id="ex3",
            title="Vault Security",
            files=["ex3/ft_vault_security.py"],
            checks=[
                file_exists("ex3/ft_vault_security.py"),
                source_contains_check(
                    "ex3/ft_vault_security.py",
                    r"\bwith\s+open\(",
                    regex=True,
                    message="uses `with open(...)` for automatic cleanup",
                ),
                probe_check(
                    "ex3/ft_vault_security.py",
                    body="""
ok_flag, message = mod.secure_archive('/definitely/not/a/real/path.txt')
record(('missing', ok_flag, message))
import tempfile, os
fd, path = tempfile.mkstemp()
os.write(fd, b'hello vault\\n')
os.close(fd)
try:
    ok_flag, content = mod.secure_archive(path)
    record(('read', ok_flag, content))
finally:
    os.unlink(path)
""",
                    assertion=_ex3_probe_assertion,
                    name="secure_archive() reads real files and reports (False, <error>) for missing ones",
                ),
            ],
        ),
    ],
)
