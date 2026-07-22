from __future__ import annotations

from habu.checks import probe_check
from habu.models import Exercise, Project, fail, ok


def _check_ex0(got: dict):

    if got.get("sorted_powers") != [92, 85, 60]:
        return fail(f"artifact_sorter should sort by power descending, got {got.get('sorted_powers')}")

    if got.get("filtered_names") != ["Alice", "Carol"]:
        return fail(f"power_filter(mages, 50) should keep Alice(50) and Carol(70), got {got.get('filtered_names')}")

    if got.get("transformed") != ["* fireball *", "* heal *", "* shield *"]:
        return fail(f"spell_transformer should add '* ' / ' *' around each spell, got {got.get('transformed')}")

    stats = got.get("stats") or {}
    if stats.get("max_power") != 70 or stats.get("min_power") != 30 or stats.get("avg_power") != 50.0:
        return fail(f"mage_stats should return max_power=70, min_power=30, avg_power=50.0, got {stats}")

    return ok("all four lambda-based functions return the exact required data")


def _check_ex1(got: dict):

    if not isinstance(got.get("combined"), (list, tuple)) or len(got["combined"]) != 2:
        return fail(f"spell_combiner should return a tuple of both spells' results, got {got.get('combined')}")

    if "30" not in str(got.get("amplified")) or "Dragon" not in str(got.get("amplified")):
        return fail(
            f"power_amplifier(fireball, 3) called with power=10 should cast at power 30, got {got.get('amplified')}"
        )

    if "Dragon" not in str(got.get("cond_true")):
        return fail(
            f"conditional_caster with a True condition should cast normally, got {got.get('cond_true')}"
        )

    if got.get("cond_false") != "Spell fizzled":
        return fail(
            f"conditional_caster with a False condition should return 'Spell fizzled', got {got.get('cond_false')}"
        )

    if not isinstance(got.get("seq"), list) or len(got["seq"]) != 2:
        return fail(f"spell_sequence should return a list of both spells' results, got {got.get('seq')}")

    return ok("combiner/amplifier/conditional-caster/sequence all behave as specified")


def _check_ex2(got: dict):

    if got.get("c1_calls") != [1, 2]:
        return fail(f"mage_counter() should count 1, 2, ... on repeated calls, got {got.get('c1_calls')}")

    if got.get("c2_calls") != [1]:
        return fail(f"a second mage_counter() should start fresh at 1 (independent state), got {got.get('c2_calls')}")

    if got.get("acc_calls") != [120, 150]:
        return fail(f"spell_accumulator(100) then +20, +30 should give [120, 150], got {got.get('acc_calls')}")

    if got.get("flaming_sword") != "Flaming Sword":
        return fail(
            f"enchantment_factory('Flaming')('Sword') should return 'Flaming Sword', got {got.get('flaming_sword')!r}"
        )

    if got.get("recall_secret") != 42:
        return fail(f"memory_vault() store/recall roundtrip should return 42, got {got.get('recall_secret')!r}")

    if got.get("recall_unknown") != "Memory not found":
        return fail(f"recall() of an unknown key should return 'Memory not found', got {got.get('recall_unknown')!r}")

    return ok("all four closures maintain correct, independent, persistent state")


def _check_ex3(got: dict):

    if (got.get("sum"), got.get("mul"), got.get("max"), got.get("min")) != (10, 24, 4, 1):
        return fail(f"spell_reducer add/multiply/max/min mismatch: {got}")

    if got.get("empty") != 0:
        return fail(f"spell_reducer([], 'add') should return 0, got {got.get('empty')}")

    if (got.get("fib0"), got.get("fib1"), got.get("fib10"), got.get("fib15")) != (0, 1, 55, 610):
        return fail(f"memoized_fibonacci values are wrong: {got}")

    if not got.get("has_cache_info"):
        return fail("memoized_fibonacci should be decorated with functools.lru_cache (missing .cache_info())")

    if got.get("partial_count") != 3:
        return fail(f"partial_enchanter should return 3 partial-applied callables, got {got.get('partial_count')}")

    if "50" not in str(got.get("partial_result")):
        return fail(f"each partial_enchanter callable should pre-bind power=50, got {got.get('partial_result')!r}")

    for key in ("dispatch_int", "dispatch_str", "dispatch_list"):
        if not got.get(key):
            return fail(f"spell_dispatcher() should return type-appropriate content for {key}, got {got.get(key)!r}")

    return ok("reduce/partial/lru_cache/singledispatch all behave as specified")


def _check_ex4(got: dict):

    if got.get("timer_result") != "Dragon hit!":
        return fail(
            f"spell_timer should return the wrapped function's own result unchanged, got {got.get('timer_result')!r}"
        )

    if got.get("retry_eventual_success") != "success":
        return fail(
            f"retry_spell should return the eventual successful result, got {got.get('retry_eventual_success')!r}"
        )

    if not got.get("retry_exhausted_return") and not got.get("retry_exhausted_raised"):
        return fail("retry_spell exhausting all attempts should either return a failure string or raise")

    if got.get("valid_name_true") is not True or got.get("valid_name_false") is not False:
        return fail("MageGuild.validate_mage_name should accept 'Alex Mage' and reject 'Al'")

    if got.get("cast_spell_ok") != "Successfully cast Lightning with 15 power":
        return fail(
            f"cast_spell(15) with min_power=10 should succeed with the exact required string, "
            f"got {got.get('cast_spell_ok')!r}"
        )

    if got.get("cast_spell_low") != "Insufficient power for this spell":
        return fail(
            f"cast_spell(5) with min_power=10 should return 'Insufficient power for this spell',"
            f" got {got.get('cast_spell_low')!r}"
        )

    return ok("spell_timer/retry_spell/MageGuild all behave exactly as specified")


PROJECT = Project(
    id="p10",
    name="FuncMage",
    tagline="Master the Ancient Arts of Functional Programming",
    exercises=[
        Exercise(
            id="ex0",
            title="Lambda Sanctum",
            files=["ex0/lambda_spells.py"],
            checks=[
                probe_check(
                    "ex0/lambda_spells.py",
                    body="""
artifacts = [{'name': 'Fire Staff', 'power': 92, 'type': 'weapon'},
             {'name': 'Crystal Orb', 'power': 85, 'type': 'artifact'},
             {'name': 'Ice Wand', 'power': 60, 'type': 'weapon'}]
record(('sorted_powers', [a['power'] for a in mod.artifact_sorter(artifacts)]))

mages = [{'name': 'Alice', 'power': 50, 'element': 'fire'},
         {'name': 'Bob', 'power': 30, 'element': 'water'},
         {'name': 'Carol', 'power': 70, 'element': 'earth'}]
record(('filtered_names', sorted(m['name'] for m in mod.power_filter(mages, 50))))

record(('transformed', mod.spell_transformer(['fireball', 'heal', 'shield'])))
record(('stats', mod.mage_stats(mages)))
""",
                    assertion=lambda records: _check_ex0(dict(records)),
                    name="artifact_sorter/power_filter/spell_transformer/mage_stats return the exact required data",
                ),
            ],
        ),
        Exercise(
            id="ex1",
            title="Higher Realm",
            files=["ex1/higher_magic.py"],
            checks=[
                probe_check(
                    "ex1/higher_magic.py",
                    body="""
def fireball(target, power):
    return f"Fireball hits {target} for {power} damage"

def heal(target, power):
    return f"Heal restores {target} for {power} HP"

combined = mod.spell_combiner(fireball, heal)
record(('combined', combined('Dragon', 10)))

amplified = mod.power_amplifier(fireball, 3)
record(('amplified', amplified('Dragon', 10)))

cond_true = mod.conditional_caster(lambda t, p: True, fireball)
record(('cond_true', cond_true('Dragon', 10)))
cond_false = mod.conditional_caster(lambda t, p: False, fireball)
record(('cond_false', cond_false('Dragon', 10)))

seq = mod.spell_sequence([fireball, heal])
record(('seq', seq('Dragon', 10)))
""",
                    assertion=lambda records: _check_ex1(dict(records)),
                    name="spell_combiner/power_amplifier/conditional_caster/spell_sequence behave exactly as specified",
                ),
            ],
        ),
        Exercise(
            id="ex2",
            title="Memory Depths",
            files=["ex2/scope_mysteries.py"],
            checks=[
                probe_check(
                    "ex2/scope_mysteries.py",
                    body="""
c1 = mod.mage_counter()
c2 = mod.mage_counter()
record(('c1_calls', [c1(), c1()]))
record(('c2_calls', [c2()]))

acc = mod.spell_accumulator(100)
record(('acc_calls', [acc(20), acc(30)]))

flaming = mod.enchantment_factory('Flaming')
record(('flaming_sword', flaming('Sword')))

vault = mod.memory_vault()
vault['store']('secret', 42)
record(('recall_secret', vault['recall']('secret')))
record(('recall_unknown', vault['recall']('unknown')))
""",
                    assertion=lambda records: _check_ex2(dict(records)),
                    name="closures maintain independent, persistent state as specified",
                ),
            ],
        ),
        Exercise(
            id="ex3",
            title="Ancient Library",
            files=["ex3/functools_artifacts.py"],
            checks=[
                probe_check(
                    "ex3/functools_artifacts.py",
                    body="""
record(('sum', mod.spell_reducer([1, 2, 3, 4], 'add')))
record(('mul', mod.spell_reducer([1, 2, 3, 4], 'multiply')))
record(('max', mod.spell_reducer([1, 2, 3, 4], 'max')))
record(('min', mod.spell_reducer([1, 2, 3, 4], 'min')))
record(('empty', mod.spell_reducer([], 'add')))

record(('fib0', mod.memoized_fibonacci(0)))
record(('fib1', mod.memoized_fibonacci(1)))
record(('fib10', mod.memoized_fibonacci(10)))
record(('fib15', mod.memoized_fibonacci(15)))
record(('has_cache_info', hasattr(mod.memoized_fibonacci, 'cache_info')))

def base_ench(power, element, target):
    return f"{element} enchant on {target} with {power} power"

partials = mod.partial_enchanter(base_ench)
record(('partial_count', len(partials)))
first = next(iter(partials.values()))
record(('partial_result', first(target='Sword')))

dispatcher = mod.spell_dispatcher()
record(('dispatch_int', dispatcher(42)))
record(('dispatch_str', dispatcher('fireball')))
record(('dispatch_list', dispatcher([1, 2, 3])))
""",
                    assertion=lambda records: _check_ex3(dict(records)),
                    name="reduce/partial/lru_cache/singledispatch all behave as specified",
                ),
            ],
        ),
        Exercise(
            id="ex4",
            title="Master's Tower",
            files=["ex4/decorator_mastery.py"],
            checks=[
                probe_check(
                    "ex4/decorator_mastery.py",
                    body="""
@mod.spell_timer
def fireball(target):
    return f"{target} hit!"

record(('timer_result', fireball('Dragon')))

state = {'n': 0}

@mod.retry_spell(max_attempts=3)
def flaky():
    state['n'] += 1
    if state['n'] < 3:
        raise RuntimeError('fail')
    return 'success'

record(('retry_eventual_success', flaky()))

state2 = {'n': 0}

@mod.retry_spell(max_attempts=2)
def always_fails():
    state2['n'] += 1
    raise RuntimeError('fail')

try:
    record(('retry_exhausted_return', always_fails()))
except Exception as e:
    record(('retry_exhausted_raised', str(e)))

record(('valid_name_true', mod.MageGuild.validate_mage_name('Alex Mage')))
record(('valid_name_false', mod.MageGuild.validate_mage_name('Al')))

guild = mod.MageGuild()
record(('cast_spell_ok', guild.cast_spell('Lightning', 15)))
record(('cast_spell_low', guild.cast_spell('Lightning', 5)))
""",
                    assertion=lambda records: _check_ex4(dict(records)),
                    name="spell_timer/retry_spell/MageGuild behave exactly as specified",
                ),
            ],
        ),
    ],
)
