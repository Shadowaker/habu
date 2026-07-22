from __future__ import annotations

from habu.checks import file_exists, probe_check, script_stdout_contains
from habu.executor import run_script_file
from habu.models import Check, CheckResult, Exercise, ExerciseContext, Project, fail, ok

ALEMBIC_FILES = ["elements.py", "alchemy/__init__.py", "alchemy/elements.py"] + [
    f"ft_alembic_{i}.py" for i in range(6)
]
DISTILLATION_FILES = ["alchemy/potions.py", "ft_distillation_0.py", "ft_distillation_1.py"]
TRANSMUTATION_FILES = ["alchemy/transmutation/recipes.py"] + [f"ft_transmutation_{i}.py" for i in range(3)]
GRIMOIRE_FILES = [
    "alchemy/grimoire/__init__.py",
    "alchemy/grimoire/light_spellbook.py",
    "alchemy/grimoire/light_validator.py",
    "alchemy/grimoire/dark_spellbook.py",
    "alchemy/grimoire/dark_validator.py",
    "ft_kaboom_0.py",
    "ft_kaboom_1.py",
]


def _transmutation_agree(ctx: ExerciseContext) -> CheckResult:

    outputs = []
    for i in range(3):
        script = ctx.path(f"ft_transmutation_{i}.py")

        if not script.exists():
            return fail(f"ft_transmutation_{i}.py not found")

        r = run_script_file(script, cwd=script.parent)
        if r.timed_out:
            return fail(f"ft_transmutation_{i}.py timed out")

        outputs.append(r.stdout)

    if not all(
            "Air element created" in o and "Fire element created" in o and "Water element created"
            in o for o in outputs
    ):
        return fail("all three scripts should print the same lead_to_gold() result, built from the four elements")

    return ok("all three access paths reach the same recipes.lead_to_gold()")


def _kaboom_1_raises_circular_import(ctx: ExerciseContext) -> CheckResult:

    script = ctx.path("ft_kaboom_1.py")
    if not script.exists():
        return fail("ft_kaboom_1.py not found")

    r = run_script_file(script, cwd=script.parent)
    if r.timed_out:
        return fail("timed out")

    combined = r.stdout + r.stderr
    if r.returncode == 0 and "circular" not in combined.lower():
        return fail("expected accessing dark_spellbook.py directly to fail with a circular-import error")

    if "circular import" in combined.lower() or "partially initialized module" in combined.lower():
        return ok("dark_spellbook/dark_validator have a genuine circular import, as required")

    if r.returncode != 0:
        return ok("script exits with an error when importing dark_spellbook directly (likely the circular import)")

    return fail("couldn't confirm a circular-import failure", detail=combined)

def _alembic_4_hides_create_earth(ctx: ExerciseContext):

    script = ctx.path("ft_alembic_4.py")
    if not script.exists():
        return fail("ft_alembic_4.py not found")

    r = run_script_file(script, cwd=script.parent)
    if r.timed_out:
        return fail("timed out")

    combined = r.stdout + r.stderr
    if "Air element created" not in combined:
        return fail("expected create_air() to still work via `import alchemy`", detail=combined)

    if "AttributeError" in combined and "create_earth" in combined:
        return ok("create_air() works via the package, but create_earth() is correctly hidden")

    return fail(
        "expected an AttributeError when accessing alchemy.create_earth (it must not be package-exposed)",
        detail=combined
    )



PROJECT = Project(
    id="p06",
    name="The Codex",
    tagline="Mastering Python's Import Mysteries",
    exercises=[
        Exercise(
            id="alembic",
            title="Part I — The Alembic",
            files=ALEMBIC_FILES,
            allowed_mypy_errors=[
                # ft_alembic_4.py deliberately calls alchemy.create_earth(), which the
                # subject requires to be hidden from the package interface — the PDF
                # explicitly states this must also raise a mypy error "on purpose".
                ("ft_alembic_4.py", "create_earth"),
            ],
            checks=[
                probe_check(
                    "elements.py",
                    body="""
record(mod.create_fire())
record(mod.create_water())
""",
                    assertion=lambda records: (
                        ok("create_fire()/create_water() return the exact required strings")
                        if records == ["Fire element created", "Water element created"]
                        else fail(f"unexpected return values: {records}")
                    ),
                    name="elements.py: create_fire()/create_water() return exact strings",
                ),
                script_stdout_contains("ft_alembic_0.py", expected_substrings=["Fire element created"]),
                script_stdout_contains("ft_alembic_1.py", expected_substrings=["Water element created"]),
                script_stdout_contains("ft_alembic_2.py", expected_substrings=["Earth element created"]),
                script_stdout_contains("ft_alembic_3.py", expected_substrings=["Air element created"]),
                Check(
                    "ft_alembic_4.py: alchemy.create_earth is not exposed at package level",
                    lambda ctx: _alembic_4_hides_create_earth(ctx),
                ),
                script_stdout_contains("ft_alembic_5.py", expected_substrings=["Air element created"]),
            ],
        ),
        Exercise(
            id="distillation",
            title="Part II — Distillation",
            files=DISTILLATION_FILES,
            checks=[
                script_stdout_contains(
                    "ft_distillation_0.py",
                    expected_substrings=[
                        "Strength potion brewed with 'Fire element created' and 'Water element created'",
                        "Healing potion brewed with 'Earth element created' and 'Air element created'",
                    ],
                ),
                script_stdout_contains(
                    "ft_distillation_1.py",
                    expected_substrings=[
                        "Strength potion brewed with 'Fire element created' and 'Water element created'",
                        "Healing potion brewed with 'Earth element created' and 'Air element created'",
                    ],
                    name="ft_distillation_1.py: alchemy.heal() is a working package-level alias of healing_potion()",
                ),
            ],
        ),
        Exercise(
            id="transmutation",
            title="Part III — The Great Transmutation",
            files=TRANSMUTATION_FILES,
            checks=[Check("all three transmutation scripts agree on lead_to_gold()", _transmutation_agree)],
        ),
        Exercise(
            id="kaboom",
            title="Part IV — Avoid the Explosion",
            files=GRIMOIRE_FILES,
            checks=[
                script_stdout_contains(
                    "ft_kaboom_0.py",
                    expected_substrings=["VALID"],
                    name="ft_kaboom_0.py: records a light spell without a circular-import crash",
                ),
                Check(
                    "ft_kaboom_1.py: dark_spellbook/dark_validator raise a genuine circular import",
                    _kaboom_1_raises_circular_import
                ),
            ],
        ),
    ],
)