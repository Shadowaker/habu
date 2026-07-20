from __future__ import annotations

from habu.checks import (
    file_exists,
    function_prints_contains,
    function_prints_exact,
)
from habu.executor import probe
from habu.models import Check, Exercise, Project, fail, ok


def _norm(s: str) -> str:
    return s.replace("\r\n", "\n").rstrip("\n")


def _ex6_same_output(ctx):
    it_path = ctx.path("ex6/ft_count_harvest_iterative.py")
    rec_path = ctx.path("ex6/ft_count_harvest_recursive.py")

    if not it_path.exists() or not rec_path.exists():
        return fail("both ft_count_harvest_iterative.py and ft_count_harvest_recursive.py are required")

    r1 = probe(it_path, "mod.ft_count_harvest_iterative()", stdin="5\n")
    r2 = probe(rec_path, "mod.ft_count_harvest_recursive()", stdin="5\n")

    if not r1.ok:
        return fail(f"ft_count_harvest_iterative raised {r1.error}: {r1.message}")

    if not r2.ok:
        return fail(f"ft_count_harvest_recursive raised {r2.error}: {r2.message}")

    if _norm(r1.stdout) == _norm(r2.stdout):
        return ok("iterative and recursive versions produce identical output")

    return fail(
        "iterative and recursive outputs differ",
        detail=f"--- iterative ---\n{r1.stdout}\n--- recursive ---\n{r2.stdout}",
    )


PROJECT = Project(
    id="p00",
    name="Growing Code",
    tagline="Python Fundamentals Through Garden Data",
    exercises=[
        Exercise(
            id="ex0",
            title="Hello Garden",
            files=["ex0/ft_hello_garden.py"],
            checks=[
                file_exists("ex0/ft_hello_garden.py"),
                function_prints_exact(
                    "ex0/ft_hello_garden.py",
                    "ft_hello_garden",
                    expected="Hello, Garden Community!",
                ),
            ],
        ),
        Exercise(
            id="ex1",
            title="Garden Name",
            files=["ex1/ft_garden_name.py"],
            checks=[
                file_exists("ex1/ft_garden_name.py"),
                function_prints_contains(
                    "ex1/ft_garden_name.py",
                    "ft_garden_name",
                    stdin="Community Garden\n",
                    expected_substrings=[
                        "Enter garden name: ",
                        "Garden: Community Garden",
                        "Status: Growing well!",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex2",
            title="Garden Plot Area",
            files=["ex2/ft_plot_area.py"],
            checks=[
                file_exists("ex2/ft_plot_area.py"),
                function_prints_contains(
                    "ex2/ft_plot_area.py",
                    "ft_plot_area",
                    stdin="5\n3\n",
                    expected_substrings=["Enter length: ", "Enter width: ", "Plot area: 15"],
                ),
            ],
        ),
        Exercise(
            id="ex3",
            title="Harvest Total",
            files=["ex3/ft_harvest_total.py"],
            checks=[
                file_exists("ex3/ft_harvest_total.py"),
                function_prints_contains(
                    "ex3/ft_harvest_total.py",
                    "ft_harvest_total",
                    stdin="5\n8\n3\n",
                    expected_substrings=[
                        "Day 1 harvest: ",
                        "Day 2 harvest: ",
                        "Day 3 harvest: ",
                        "Total harvest: 16",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex4",
            title="Plant Age Check",
            files=["ex4/ft_plant_age.py"],
            checks=[
                file_exists("ex4/ft_plant_age.py"),
                function_prints_contains(
                    "ex4/ft_plant_age.py",
                    "ft_plant_age",
                    stdin="75\n",
                    expected_substrings=["Enter plant age in days: ", "Plant is ready to harvest!"],
                    name="ft_plant_age() ready case (75 days)",
                ),
                function_prints_contains(
                    "ex4/ft_plant_age.py",
                    "ft_plant_age",
                    stdin="45\n",
                    expected_substrings=["Enter plant age in days: ", "Plant needs more time to grow."],
                    name="ft_plant_age() not-ready case (45 days)",
                ),
            ],
        ),
        Exercise(
            id="ex5",
            title="Water Reminder",
            files=["ex5/ft_water_reminder.py"],
            checks=[
                file_exists("ex5/ft_water_reminder.py"),
                function_prints_contains(
                    "ex5/ft_water_reminder.py",
                    "ft_water_reminder",
                    stdin="4\n",
                    expected_substrings=["Days since last watering: ", "Water the plants!"],
                    name="ft_water_reminder() needs-water case (4 days)",
                ),
                function_prints_contains(
                    "ex5/ft_water_reminder.py",
                    "ft_water_reminder",
                    stdin="1\n",
                    expected_substrings=["Days since last watering: ", "Plants are fine"],
                    name="ft_water_reminder() fine case (1 day)",
                ),
            ],
        ),
        Exercise(
            id="ex6",
            title="Count to Harvest",
            files=[
                "ex6/ft_count_harvest_iterative.py",
                "ex6/ft_count_harvest_recursive.py",
            ],
            checks=[
                file_exists("ex6/ft_count_harvest_iterative.py"),
                file_exists("ex6/ft_count_harvest_recursive.py"),
                function_prints_contains(
                    "ex6/ft_count_harvest_iterative.py",
                    "ft_count_harvest_iterative",
                    stdin="5\n",
                    expected_substrings=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Harvest time!"],
                ),
                function_prints_contains(
                    "ex6/ft_count_harvest_recursive.py",
                    "ft_count_harvest_recursive",
                    stdin="5\n",
                    expected_substrings=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Harvest time!"],
                ),
                Check("iterative and recursive versions agree", _ex6_same_output),
            ],
        ),
        Exercise(
            id="ex7",
            title="Seed Inventory with Type Annotations",
            files=["ex7/ft_seed_inventory.py"],
            checks=[
                file_exists("ex7/ft_seed_inventory.py"),
                function_prints_exact(
                    "ex7/ft_seed_inventory.py",
                    "ft_seed_inventory",
                    call="mod.ft_seed_inventory('tomato', 15, 'packets')",
                    expected="Tomato seeds: 15 packets available",
                    name="ft_seed_inventory('tomato', 15, 'packets')",
                ),
                function_prints_exact(
                    "ex7/ft_seed_inventory.py",
                    "ft_seed_inventory",
                    call="mod.ft_seed_inventory('carrot', 8, 'grams')",
                    expected="Carrot seeds: 8 grams total",
                    name="ft_seed_inventory('carrot', 8, 'grams')",
                ),
                function_prints_exact(
                    "ex7/ft_seed_inventory.py",
                    "ft_seed_inventory",
                    call="mod.ft_seed_inventory('lettuce', 12, 'area')",
                    expected="Lettuce seeds: covers 12 square meters",
                    name="ft_seed_inventory('lettuce', 12, 'area')",
                ),
                function_prints_exact(
                    "ex7/ft_seed_inventory.py",
                    "ft_seed_inventory",
                    call="mod.ft_seed_inventory('bean', 3, 'cups')",
                    expected="Unknown unit type",
                    name="ft_seed_inventory('bean', 3, 'cups') — unknown unit",
                ),
            ],
        ),
    ],
)
