from __future__ import annotations

from habu.checks import script_stdout_contains, script_stdout_regex
from habu.models import Exercise, Project

PROJECT = Project(
    id="p07",
    name="DataDeck",
    tagline="Abstract Card Architecture",
    exercises=[
        Exercise(
            id="ex0",
            title="Creature Factory",
            files=["ex0/__init__.py", "battle.py"],
            checks=[
                script_stdout_contains(
                    "battle.py",
                    expected_substrings=[
                        "Flameling is a Fire type Creature",
                        "Flameling uses Ember!",
                        "Pyrodon is a Fire/Flying type Creature",
                        "Pyrodon uses Flamethrower!",
                        "Aquabub is a Water type Creature",
                        "Aquabub uses Water Gun!",
                        "Torragon is a Water type Creature",
                        "Torragon uses Hydro Pump!",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex1",
            title="Capabilities",
            files=["ex1/__init__.py", "capacitor.py"],
            checks=[
                script_stdout_contains(
                    "capacitor.py",
                    expected_substrings=[
                        "Sproutling is a Grass type Creature",
                        "Sproutling uses Vine Whip!",
                        "Sproutling heals itself for a small amount",
                        "Bloomelle is a Grass/Fairy type Creature",
                        "Bloomelle uses Petal Dance!",
                        "Bloomelle heals itself and others for a large amount",
                        "Shiftling is a Normal type Creature",
                        "Shiftling attacks normally.",
                        "Shiftling shifts into a sharper form!",
                        "Shiftling performs a boosted strike!",
                        "Shiftling returns to normal.",
                        "Morphagon is a Normal/Dragon type Creature",
                        "Morphagon attacks normally.",
                        "Morphagon morphs into a dragonic battle form!",
                        "Morphagon unleashes a devastating morph strike!",
                        "Morphagon stabilizes its form.",
                    ],
                ),
            ],
        ),
        Exercise(
            id="ex2",
            title="Abstract Strategy",
            files=["ex2/__init__.py", "tournament.py"],
            checks=[
                script_stdout_regex(
                    "tournament.py",
                    patterns=[
                        r"\*\*\* Tournament \*\*\*",
                        r"\d+ opponents involved",
                        r"\* Battle \*",
                        r" vs\.",
                        r" now fight!",
                    ],
                ),
                script_stdout_contains(
                    "tournament.py",
                    expected_substrings=["Battle error, aborting tournament:"],
                    name="invalid Creature/strategy combinations are caught and reported, not crashed",
                ),
            ],
        ),
    ],
)
