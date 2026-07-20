from __future__ import annotations

from habu.checks import file_exists, probe_check, script_stdout_contains
from habu.models import CheckResult, Exercise, Project, fail, ok

def _check_error_types(records: list) -> CheckResult:

    expected = {0: "ValueError", 1: "ZeroDivisionError", 2: "FileNotFoundError", 3: "TypeError", 4: "no_error"}
    got = dict(records)
    mismatches = {
        n: (expected[n], got.get(n)) for n in expected if got.get(n) != expected[n]
    }

    if not mismatches:
        return ok("each operation number raises the documented exception type")

    return fail(f"mismatched operations (expected -> got): {mismatches}")


PROJECT = Project(
    id="p02",
    name="Garden Guardian",
    tagline="Data Engineering for Smart Agriculture",
    exercises=[
        Exercise(
            id="ex0",
            title="Agricultural Data Validation",
            files=["ex0/ft_first_exception.py"],
            checks=[
                file_exists("ex0/ft_first_exception.py"),
                probe_check(
                    "ex0/ft_first_exception.py",
                    body="""
record(mod.input_temperature('25'))
try:
    mod.input_temperature('abc')
    record('no_error')
except Exception as e:
    record(type(e).__name__)
""",
                    assertion=lambda records: (
                        ok("returns int and raises on bad input")
                        if len(records) == 2 and records[0] == 25 and records[1] != "no_error"
                        else fail(f"unexpected behavior: {records}")
                    ),
                    name="input_temperature() converts valid input and raises on invalid input",
                ),
                script_stdout_contains(
                    "ex0/ft_first_exception.py",
                    expected_substrings=[
                        "Garden Temperature",
                        "Input data is '25'",
                        "25°C",
                        "Input data is 'abc'",
                        "didn't crash",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex1",
            title="Agricultural Data Validation Pipeline",
            files=["ex1/ft_raise_exception.py"],
            checks=[
                file_exists("ex1/ft_raise_exception.py"),
                probe_check(
                    "ex1/ft_raise_exception.py",
                    body="""
record(mod.input_temperature('25'))
record(mod.input_temperature('0'))
record(mod.input_temperature('40'))
for bad in ('100', '-50'):
    try:
        mod.input_temperature(bad)
        record('no_error:' + bad)
    except Exception as e:
        record('error:' + bad + ':' + str(e))
""",
                    assertion=lambda records: (
                        ok("accepts 0-40 inclusive and rejects out-of-range values")
                        if records[:3] == [25, 0, 40]
                        and records[3].startswith("error:100:")
                        and "hot" in records[3]
                        and records[4].startswith("error:-50:")
                        and "cold" in records[4]
                        else fail(f"unexpected behavior: {records}")
                    ),
                    name="input_temperature() enforces the 0-40°C inclusive range",
                ),
                script_stdout_contains(
                    "ex1/ft_raise_exception.py",
                    expected_substrings=[
                        "Garden Temperature",
                        "Input data is '100'",
                        "too hot for plants (max 40",
                        "Input data is '-50'",
                        "too cold for plants (min 0",
                        "didn't crash",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex2",
            title="Different Types of Problems",
            files=["ex2/ft_different_errors.py"],
            checks=[
                file_exists("ex2/ft_different_errors.py"),
                probe_check(
                    "ex2/ft_different_errors.py",
                    body="""
expected = {0: 'ValueError', 1: 'ZeroDivisionError', 2: 'FileNotFoundError', 3: 'TypeError'}
for n, exc_name in expected.items():
    try:
        mod.garden_operations(n)
        record((n, 'no_error'))
    except Exception as e:
        record((n, type(e).__name__))
try:
    mod.garden_operations(4)
    record((4, 'no_error'))
except Exception as e:
    record((4, type(e).__name__))
""",
                    assertion=lambda records: _check_error_types(records),
                    name="garden_operations() raises the expected exception type per operation number",
                ),
                script_stdout_contains(
                    "ex2/ft_different_errors.py",
                    expected_substrings=[
                        "Garden Error Types Demo",
                        "Caught ValueError",
                        "Caught ZeroDivisionError",
                        "Caught FileNotFoundError",
                        "Caught TypeError",
                        "All error types tested successfully!",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex3",
            title="Making Your Own Error Types",
            files=["ex3/ft_custom_errors.py"],
            checks=[
                file_exists("ex3/ft_custom_errors.py"),
                probe_check(
                    "ex3/ft_custom_errors.py",
                    body="""
record(issubclass(mod.PlantError, mod.GardenError))
record(issubclass(mod.WaterError, mod.GardenError))
record(issubclass(mod.GardenError, Exception))
try:
    raise mod.PlantError("custom message")
except mod.GardenError as e:
    record(str(e))
""",
                    assertion=lambda records: (
                        ok("PlantError/WaterError inherit from GardenError, catchable as GardenError")
                        if records == [True, True, True, "custom message"]
                        else fail(f"unexpected inheritance/behavior: {records}")
                    ),
                    name="PlantError and WaterError inherit from GardenError",
                ),
                script_stdout_contains(
                    "ex3/ft_custom_errors.py",
                    expected_substrings=[
                        "Custom Garden Errors Demo",
                        "Caught PlantError",
                        "Caught WaterError",
                        "Caught GardenError",
                        "All custom error types work correctly!",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex4",
            title="Finally Block - Always Clean Up",
            files=["ex4/ft_finally_block.py"],
            checks=[
                file_exists("ex4/ft_finally_block.py"),
                probe_check(
                    "ex4/ft_finally_block.py",
                    body="""
try:
    mod.water_plant('Tomato')
    record('capitalized_ok')
except Exception as e:
    record('capitalized_error:' + type(e).__name__)
try:
    mod.water_plant('lettuce')
    record('lowercase_ok')
except Exception as e:
    record('lowercase_error:' + type(e).__name__)
""",
                    assertion=lambda records: (
                        ok("accepts capitalized plant names, raises PlantError otherwise")
                        if records[0] == "capitalized_ok" and records[1] == "lowercase_error:PlantError"
                        else fail(f"unexpected behavior: {records}")
                    ),
                    name="water_plant() succeeds for capitalized names, raises PlantError otherwise",
                ),
                script_stdout_contains(
                    "ex4/ft_finally_block.py",
                    expected_substrings=[
                        "Garden Watering System",
                        "Opening watering system",
                        "[OK]",
                        "Closing watering system",
                        "Cleanup always happens, even with errors!",
                    ],
                ),
            ],
        ),
    ],
)
