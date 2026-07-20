# Habu

A modular tester for the 42 Python Piscine subjects (`p00` – `p10`). Point it at a submission
directory and it figures out which subject it is, then runs each exercise's checks and prints a clean
pass/fail report.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

```bash
uv run habu [path]              # test a submission (defaults to the current directory)
uv run habu [path] -p p05       # skip auto-detection, force a specific project
uv run habu [path] -e ex2       # only run one exercise
uv run habu --list              # list all known projects
```

Habu detects the project by matching known exercise filenames (e.g. `ex0/ft_hello_garden.py`) inside
the target directory, so you can run it straight from a student's repo without telling it which
subject it is.

## Known projects

| id  | name             | subject                                    |
|-----|------------------|---------------------------------------------|
| p00 | Growing Code     | Python fundamentals                        |
| p01 | Code Cultivation | Object-oriented programming                |
| p02 | Garden Guardian  | Exception handling                         |
| p03 | Data Quest       | Collections (lists, sets, dicts, generators)|
| p04 | Data Archivist   | File I/O                                   |
| p05 | Code Nexus       | Abstract classes & polymorphism            |
| p06 | The Codex        | Import mechanics & packages                |
| p07 | DataDeck         | Design patterns                            |
| p08 | The Matrix       | Virtual envs, pip/Poetry, dotenv config    |
| p09 | Cosmic Data      | Pydantic v2 models & validation            |
| p10 | FuncMage         | Functional programming                     |

## How grading works

Every check runs the submission in an isolated subprocess — a crash, infinite loop, or `sys.exit()` in
a student's code can't take Habu down. Depending on the exercise, a check either:

- calls a function/class directly and checks its return value or behavior, or
- runs a script with given argv/stdin and checks its stdout/stderr, or
- inspects the source for required patterns (e.g. `with open(...)`, forbidden imports).

Where the subject gives an exact required string, checks compare it closely; where the subject allows
custom wording (e.g. self-authored demo banners, `random`-based output), checks instead verify the
underlying structure/behavior is correct.

Two exceptions worth knowing about:

- **p08** (venv/pip/Poetry/dotenv) can't be graded behaviorally without actually creating virtual
  environments and installing packages, so its checks are structural only (files exist, scripts don't
  crash, required env vars are referenced).
- **p09** (Pydantic) needs the `pydantic` package installed to run — if it's missing, those checks
  report **SKIP** instead of failing.

### flake8 / mypy

Every subject's General Instructions require flake8 and mypy compliance, so Habu runs both for every
exercise, against that exercise's own submitted `.py` file(s), and shows the results alongside its
other checks. This doesn't gate or block an exercise's other checks (they all run regardless), but a
lint failure does keep that exercise — and so the whole submission — from being marked as passing.

## Adding/editing project specs

Each subject lives in its own file under `habu/projects/pXX_*.py`, exporting a `PROJECT` object built
from `habu/models.py`. Check factories live in `habu/checks.py`; the subprocess execution primitives
(`probe()`, `run_script_file()`) live in `habu/executor.py`.
