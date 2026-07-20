from __future__ import annotations

import re

from habu.checks import file_exists, script_result, script_stdout_regex
from habu.models import Check, CheckResult, Exercise, ExerciseContext, Project, fail, ok

SHOW_LINE = r"\w[\w '/-]*:\s*\d+(?:\.\d+)?\s*cm,\s*\d+\s*days old"


def _at_least(rel_path: str, pattern: str, minimum: int, *, name: str) -> Check:
    getter = script_result(rel_path)

    def fn(ctx: ExerciseContext) -> CheckResult:
        r = getter(ctx)

        if r is None:
            return fail(f"{rel_path} not found")

        if r.timed_out:
            return fail("timed out")

        matches = re.findall(pattern, r.stdout, re.MULTILINE)
        if len(matches) >= minimum:
            return ok(f"found {len(matches)} matching line(s)")

        return fail(
            f"expected at least {minimum} matching line(s), found {len(matches)}",
            detail=f"--- got ---\n{r.stdout}\n--- stderr ---\n{r.stderr}",
        )

    return Check(name, fn)


PROJECT = Project(
    id="p01",
    name="Code Cultivation",
    tagline="Object-Oriented Garden Systems",
    exercises=[
        Exercise(
            id="ex0",
            title="Planting Your First Seed",
            files=["ex0/ft_garden_intro.py"],
            checks=[
                file_exists("ex0/ft_garden_intro.py"),
                script_stdout_regex(
                    "ex0/ft_garden_intro.py",
                    patterns=[r"Plant:\s*\S+", r"Height:\s*\d+\s*cm", r"Age:\s*\d+\s*days"],
                ),
            ],
        ),
        Exercise(
            id="ex1",
            title="Garden Data Organizer",
            files=["ex1/ft_garden_data.py"],
            checks=[
                file_exists("ex1/ft_garden_data.py"),
                _at_least("ex1/ft_garden_data.py", SHOW_LINE, 3, name="show()s at least 3 plants in the expected format"),
            ],
        ),
        Exercise(
            id="ex2",
            title="Plant Growth Simulator",
            files=["ex2/ft_plant_growth.py"],
            checks=[
                file_exists("ex2/ft_plant_growth.py"),
                script_stdout_regex(
                    "ex2/ft_plant_growth.py",
                    patterns=[rf"Day 1\b", rf"Day 7\b", SHOW_LINE, r"Growth this week:\s*\d+(?:\.\d+)?\s*cm"],
                ),
            ],
        ),
        Exercise(
            id="ex3",
            title="Plant Factory",
            files=["ex3/ft_plant_factory.py"],
            checks=[
                file_exists("ex3/ft_plant_factory.py"),
                _at_least(
                    "ex3/ft_plant_factory.py",
                    rf"Created:\s*{SHOW_LINE}",
                    5,
                    name="creates and shows at least 5 plants with 'Created: ' prefix",
                ),
            ],
        ),
        Exercise(
            id="ex4",
            title="Garden Security System",
            files=["ex4/ft_garden_security.py"],
            checks=[
                file_exists("ex4/ft_garden_security.py"),
                script_stdout_regex(
                    "ex4/ft_garden_security.py",
                    patterns=[
                        r"Error,\s*height can't be negative",
                        r"Height update rejected",
                        r"Error,\s*age can't be negative",
                        r"Age update rejected",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex5",
            title="Specialized Plant Types",
            files=["ex5/ft_plant_types.py"],
            checks=[
                file_exists("ex5/ft_plant_types.py"),
                script_stdout_regex(
                    "ex5/ft_plant_types.py",
                    patterns=[
                        r"has not bloomed yet",
                        r"is blooming beautifully!",
                        r"now produces a shade of\s*\d+(?:\.\d+)?\s*cm long and\s*\d+(?:\.\d+)?\s*cm wide",
                        r"Color:\s*\S+",
                        r"Trunk diameter:\s*\d+(?:\.\d+)?\s*cm",
                        r"Harvest season:\s*\S+",
                        r"Nutritional value:\s*\d+",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex6",
            title="Garden Analytics",
            files=["ex6/ft_garden_analytics.py"],
            checks=[
                file_exists("ex6/ft_garden_analytics.py"),
                script_stdout_regex(
                    "ex6/ft_garden_analytics.py",
                    patterns=[
                        r"more than a year\?\s*->\s*(True|False)",
                        r"Stats:\s*\d+\s*grow,\s*\d+\s*age,\s*\d+\s*show",
                        r"Seeds:\s*\d+",
                        r"shade",
                    ],
                ),
            ],
        ),
    ],
)
