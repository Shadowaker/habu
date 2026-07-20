from __future__ import annotations

import ast
import re
import statistics

from habu.checks import file_exists, script_result, script_stdout_contains
from habu.models import CheckResult, Exercise, ExerciseContext, Project, fail, ok


def _parse_collection(text: str):

    if text.strip() == "set()":
        return set()

    return ast.literal_eval(text)


def _custom(rel_path: str, name: str, *, argv=None, stdin="", timeout=10.0):
    """Decorator-less helper: wraps a `(ctx, stdout) -> CheckResult` function
    into a Check, handling the file-missing/timeout/crash boilerplate."""

    def decorate(fn):
        getter = script_result(rel_path, argv=argv, stdin=stdin, timeout=timeout)

        def check_fn(ctx: ExerciseContext) -> CheckResult:
            r = getter(ctx)

            if r is None:
                return fail(f"{rel_path} not found")

            if r.timed_out:
                return fail("timed out")

            try:
                return fn(r.stdout)
            except Exception as e:
                return fail(f"couldn't verify output ({type(e).__name__}: {e})", detail=r.stdout)

        from habu.models import Check

        return Check(name, check_fn)

    return decorate


@_custom(
    "ex3/ft_achievement_tracker.py",
    "achievement sets are internally consistent (union/intersection/difference)"
)
def _ex3_check(stdout: str) -> CheckResult:

    players = dict(re.findall(r"^Player (\w+): (\{.*\}|set\(\))$", stdout, re.MULTILINE))
    if len(players) < 4:
        return fail(f"expected at least 4 'Player X: {{...}}' lines, found {len(players)}")

    players = {name: _parse_collection(s) for name, s in players.items()}

    union_m = re.search(r"^All distinct achievements: (\{.*\}|set\(\))$", stdout, re.MULTILINE)
    common_m = re.search(r"^Common achievements: (\{.*\}|set\(\))$", stdout, re.MULTILINE)
    if not union_m or not common_m:
        return fail("missing 'All distinct achievements:' or 'Common achievements:' line")

    union_set = _parse_collection(union_m.group(1))
    common_set = _parse_collection(common_m.group(1))

    expected_union = set().union(*players.values())
    if union_set != expected_union:
        return fail("'All distinct achievements' is not the union of every player's set")

    expected_common = set.intersection(*players.values())
    if common_set != expected_common:
        return fail("'Common achievements' is not the intersection of every player's set")

    only_lines = dict(re.findall(r"^Only (\w+) has: (\{.*\}|set\(\))$", stdout, re.MULTILINE))
    for name, s in only_lines.items():
        if name not in players:
            continue

        others = set().union(*(v for n, v in players.items() if n != name))
        if _parse_collection(s) != players[name] - others:
            return fail(f"'Only {name} has' does not equal {name}'s achievements minus everyone else's")

    missing_lines = dict(re.findall(r"^(\w+) is missing: (\{.*\}|set\(\))$", stdout, re.MULTILINE))
    masters = {}

    for name, s in missing_lines.items():
        if name not in players:
            continue

        missing = _parse_collection(s)
        if missing & players[name]:
            return fail(f"'{name} is missing' overlaps with achievements {name} already has")
        masters[name] = players[name] | missing

    if len(set(map(frozenset, masters.values()))) > 1:
        return fail("the master achievement list implied by different players' 'is missing' sets is inconsistent")

    return ok("union/intersection/difference all check out against the printed sets")


@_custom(
    "ex5/ft_data_stream.py",
    "gen_event/consume_event produce the required counts and draining behavior"
)
def _ex5_check(stdout: str) -> CheckResult:

    events = re.findall(r"^Event (\d+): Player \w+ did action \w+$", stdout, re.MULTILINE)

    if len(events) != 1000:
        return fail(f"expected exactly 1000 'Event N: ...' lines, found {len(events)}")

    if [int(n) for n in events] != list(range(1000)):
        return fail("event numbers are not 0..999 in order")

    built_m = re.search(r"^Built list of 10 events: (\[.*\])$", stdout, re.MULTILINE)
    if not built_m:
        return fail("missing 'Built list of 10 events:' line")

    built = ast.literal_eval(built_m.group(1))
    if len(built) != 10:
        return fail(f"expected the built list to have 10 events, found {len(built)}")

    pairs = re.findall(r"^Got event from list: (\(.*?\))\nRemains in list: (\[.*\])$", stdout, re.MULTILINE)
    if len(pairs) != 10:
        return fail(f"expected 10 'Got event from list' / 'Remains in list' pairs, found {len(pairs)}")

    remaining_lengths = [len(ast.literal_eval(remains)) for _, remains in pairs]
    if remaining_lengths != list(range(9, -1, -1)):
        return fail(f"remaining-list length should count down 9..0, got {remaining_lengths}")

    return ok("1000 events, a 10-event list, and a full drain down to []")


@_custom(
    "ex6/ft_data_alchemist.py",
    "comprehension outputs are consistent (capitalization, average, filter)"
)
def _ex6_check(stdout: str) -> CheckResult:

    def grab(label: str, pattern: str = r"\[.*\]"):
        m = re.search(rf"^{re.escape(label)}: ({pattern})$", stdout, re.MULTILINE)
        return ast.literal_eval(m.group(1)) if m else None

    initial = grab("Initial list of players")
    all_cap = grab("New list with all names capitalized")
    cap_only = grab("New list of capitalized names only")
    score_dict = grab("Score dict", r"\{.*\}")
    avg_m = re.search(r"^Score average is ([\d.]+)$", stdout, re.MULTILINE)
    high_scores = grab("High scores", r"\{.*\}")

    if initial is None or all_cap is None or cap_only is None:
        return fail("missing one of the required list lines")

    if score_dict is None or avg_m is None or high_scores is None:
        return fail("missing score dict / average / high scores lines")

    if all_cap != [n.capitalize() for n in initial]:
        return fail("capitalized-names list doesn't match capitalize() applied to the initial list")

    if cap_only != [n for n in initial if n[:1].isupper()]:
        return fail("capitalized-only list doesn't match the already-capitalized names from the initial list")

    real_avg = statistics.mean(score_dict.values())
    printed_avg = float(avg_m.group(1))
    if abs(real_avg - printed_avg) > 0.02:
        return fail(f"printed average {printed_avg} doesn't match the score dict's actual average {real_avg:.2f}")

    expected_high = {k: v for k, v in score_dict.items() if v > real_avg}
    if high_scores != expected_high:
        return fail("'High scores' doesn't match entries strictly greater than the average")

    return ok("capitalization, average, and high-score filtering are all consistent")


PROJECT = Project(
    id="p03",
    name="Data Quest",
    tagline="Mastering Python Collections",
    exercises=[
        Exercise(
            id="ex0",
            title="Command Quest",
            files=["ex0/ft_command_quest.py"],
            checks=[
                file_exists("ex0/ft_command_quest.py"),
                script_stdout_contains(
                    "ex0/ft_command_quest.py",
                    argv=[],
                    expected_substrings=[
                        "Command Quest",
                        "Program name: ft_command_quest.py",
                        "No arguments provided!",
                        "Total arguments: 1",
                    ],
                    name="no arguments",
                ),
                script_stdout_contains(
                    "ex0/ft_command_quest.py",
                    argv=["hello", "world", "42"],
                    expected_substrings=[
                        "Arguments received: 3",
                        "Argument 1: hello",
                        "Argument 2: world",
                        "Argument 3: 42",
                        "Total arguments: 4",
                    ],
                    name="three arguments",
                ),
            ],
        ),
        Exercise(
            id="ex1",
            title="Score Cruncher",
            files=["ex1/ft_score_analytics.py"],
            checks=[
                file_exists("ex1/ft_score_analytics.py"),
                script_stdout_contains(
                    "ex1/ft_score_analytics.py",
                    argv=["1500", "2300", "1800", "2100", "1950"],
                    expected_substrings=[
                        "Player Score Analytics",
                        "Total players: 5",
                        "Total score: 9650",
                        "Average score: 1930.0",
                        "High score: 2300",
                        "Low score: 1500",
                        "Score range: 800",
                    ],
                    name="five valid scores",
                ),
                script_stdout_contains(
                    "ex1/ft_score_analytics.py",
                    argv=[],
                    expected_substrings=["No scores provided. Usage:"],
                    name="no arguments",
                ),
                script_stdout_contains(
                    "ex1/ft_score_analytics.py",
                    argv=["ab", "ac"],
                    expected_substrings=["Invalid parameter: 'ab'", "Invalid parameter: 'ac'", "No scores provided. Usage:"],
                    name="only invalid scores",
                ),
            ],
        ),
        Exercise(
            id="ex2",
            title="Position Tracker",
            files=["ex2/ft_coordinate_system.py"],
            checks=[
                file_exists("ex2/ft_coordinate_system.py"),
                script_stdout_contains(
                    "ex2/ft_coordinate_system.py",
                    stdin="hello world\n1.0,2.5,3.0\n4,abc,5\n4,5,6\n",
                    expected_substrings=[
                        "Enter new coordinates as floats in format 'x,y,z': ",
                        "Invalid syntax",
                        "Got a first tuple: (1.0, 2.5, 3.0)",
                        "X=1.0, Y=2.5, Z=3.0",
                        "Distance to center: 4.0311",
                        "Error on parameter 'abc'",
                        "Distance between the 2 sets of coordinates: 4.9244",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex3",
            title="Achievement Hunter",
            files=["ex3/ft_achievement_tracker.py"],
            checks=[file_exists("ex3/ft_achievement_tracker.py"), _ex3_check],
        ),
        Exercise(
            id="ex4",
            title="Inventory Master",
            files=["ex4/ft_inventory_system.py"],
            checks=[
                file_exists("ex4/ft_inventory_system.py"),
                script_stdout_contains(
                    "ex4/ft_inventory_system.py",
                    argv=["sword:1", "potion:5", "shield:2", "armor:3", "helmet:1", "sword:2", "hello", "key:value"],
                    expected_substrings=[
                        "Inventory System Analysis",
                        "Redundant item 'sword' - discarding",
                        "Error - invalid parameter 'hello'",
                        "Quantity error for 'key'",
                        "Got inventory: {'sword': 1, 'potion': 5, 'shield': 2, 'armor': 3, 'helmet': 1}",
                        "Item list: ['sword', 'potion', 'shield', 'armor', 'helmet']",
                        "Total quantity of the 5 items: 12",
                        "Item sword represents 8.3%",
                        "Item potion represents 41.7%",
                        "Item shield represents 16.7%",
                        "Item armor represents 25.0%",
                        "Item helmet represents 8.3%",
                        "Item most abundant: potion with quantity 5",
                        "Item least abundant: sword with quantity 1",
                        "Updated inventory: {",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex5",
            title="Stream Wizard",
            files=["ex5/ft_data_stream.py"],
            checks=[file_exists("ex5/ft_data_stream.py"), _ex5_check],
        ),
        Exercise(
            id="ex6",
            title="Data Alchemist",
            files=["ex6/ft_data_alchemist.py"],
            checks=[file_exists("ex6/ft_data_alchemist.py"), _ex6_check],
        ),
    ],
)
