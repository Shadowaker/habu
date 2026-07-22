from __future__ import annotations

from habu.checks import probe_check
from habu.models import Exercise, Project, fail, ok


def _check(got: dict, expected: dict, success_message: str):

    mismatches = {k: (v, got.get(k)) for k, v in expected.items() if got.get(k) != v}
    if mismatches:
        return fail(f"unexpected validation behavior (expected -> got): {mismatches}", detail=str(got))

    return ok(success_message)


def _check_ex1(got: dict):

    if got.get("valid_ok") is not True:
        return fail("a well-formed AlienContact should validate successfully")

    if not got.get("telepathic_rejected"):
        return fail("telepathic contact with <3 witnesses should be rejected")

    if not got.get("bad_id_rejected"):
        return fail("contact_id not starting with 'AC' should be rejected")

    if not got.get("unverified_physical_rejected"):
        return fail("unverified physical contact should be rejected")


    return ok(
        "the three mandatory validation rules (id prefix, physical+verified, telepathic witnesses) "
        "correctly reject the corresponding bad data"
    )


PROJECT = Project(
    id="p09",
    name="Cosmic Data",
    tagline="Discover Pydantic Models & Validation",
    exercises=[
        Exercise(
            id="ex0",
            title="Space Station Data",
            files=["ex0/space_station.py"],
            checks=[
                probe_check(
                    "ex0/space_station.py",
                    body="""
from datetime import datetime
valid = mod.SpaceStation(station_id='ISS001', name='International Space Station', crew_size=6,
                          power_level=85.5, oxygen_level=92.3, last_maintenance=datetime.now())
record(('valid_crew', valid.crew_size))
try:
    mod.SpaceStation(station_id='ISS002', name='Bad', crew_size=99, power_level=50.0,
                      oxygen_level=50.0, last_maintenance=datetime.now())
    record(('crew_too_high_accepted', True))
except Exception:
    record(('crew_too_high_rejected', True))
try:
    mod.SpaceStation(station_id='AB', name='X', crew_size=1, power_level=1.0,
                      oxygen_level=1.0, last_maintenance=datetime.now())
    record(('short_id_accepted', True))
except Exception:
    record(('short_id_rejected', True))
""",
                    assertion=lambda records: _check(
                        dict(records),
                        {"valid_crew": 6, "crew_too_high_rejected": True, "short_id_rejected": True},
                        "SpaceStation validates crew_size<=20 and station_id length",
                    ),
                    name="SpaceStation accepts valid data and rejects out-of-range crew_size / short station_id",
                ),
            ],
        ),
        Exercise(
            id="ex1",
            title="Alien Contact Logs",
            files=["ex1/alien_contact.py"],
            checks=[
                probe_check(
                    "ex1/alien_contact.py",
                    body="""
from datetime import datetime
valid = mod.AlienContact(contact_id='AC001', timestamp=datetime.now(), location='Area 51, Nevada',
                          contact_type=mod.ContactType.radio, signal_strength=5.0,
                          duration_minutes=10, witness_count=2)
record(('valid_ok', True))
try:
    mod.AlienContact(contact_id='AC002', timestamp=datetime.now(), location='X',
                      contact_type=mod.ContactType.telepathic, signal_strength=1.0,
                      duration_minutes=5, witness_count=1)
    record(('telepathic_accepted', True))
except Exception as e:
    record(('telepathic_rejected', str(e)))
try:
    mod.AlienContact(contact_id='BAD001', timestamp=datetime.now(), location='X',
                      contact_type=mod.ContactType.radio, signal_strength=1.0,
                      duration_minutes=5, witness_count=2)
    record(('bad_id_accepted', True))
except Exception:
    record(('bad_id_rejected', True))
try:
    mod.AlienContact(contact_id='AC003', timestamp=datetime.now(), location='X',
                      contact_type=mod.ContactType.physical, signal_strength=1.0,
                      duration_minutes=5, witness_count=2, is_verified=False)
    record(('unverified_physical_accepted', True))
except Exception:
    record(('unverified_physical_rejected', True))
try:
    mod.AlienContact(contact_id='AC004', timestamp=datetime.now(), location='X',
                      contact_type=mod.ContactType.radio, signal_strength=9.0,
                      duration_minutes=5, witness_count=2, message_received=None)
    record(('strong_signal_no_message_accepted', True))
except Exception:
    record(('strong_signal_no_message_rejected', True))
""",
                    assertion=lambda records: _check_ex1(dict(records)),
                    name="AlienContact enforces the 4 custom business rules",
                ),
            ],
        ),
        Exercise(
            id="ex2",
            title="Space Crew Management",
            files=["ex2/space_crew.py"],
            checks=[
                probe_check(
                    "ex2/space_crew.py",
                    body="""
from datetime import datetime
crew = [
    mod.CrewMember(member_id='CM001', name='Sarah Connor', rank=mod.Rank.commander, age=40,
                    specialization='Command', years_experience=10),
    mod.CrewMember(member_id='CM002', name='John Smith', rank=mod.Rank.lieutenant, age=30,
                    specialization='Navigation', years_experience=5),
]
valid = mod.SpaceMission(mission_id='M0001', mission_name='Test Mission', destination='Mars',
                          launch_date=datetime.now(), duration_days=100, crew=crew, budget_millions=10.0)
record(('valid_ok', True))

crew_no_commander = [
    mod.CrewMember(member_id='CM003', name='Alice Johnson', rank=mod.Rank.officer, age=30,
                    specialization='Engineering', years_experience=3),
]
try:
    mod.SpaceMission(mission_id='M0002', mission_name='Test 2', destination='Mars',
                      launch_date=datetime.now(), duration_days=50, crew=crew_no_commander,
                      budget_millions=5.0)
    record(('no_commander_accepted', True))
except Exception:
    record(('no_commander_rejected', True))

try:
    mod.SpaceMission(mission_id='BADID', mission_name='Test 3', destination='Mars',
                      launch_date=datetime.now(), duration_days=50, crew=crew, budget_millions=5.0)
    record(('bad_id_accepted', True))
except Exception:
    record(('bad_id_rejected', True))
""",
                    assertion=lambda records: _check(
                        dict(records),
                        {"valid_ok": True, "no_commander_rejected": True, "bad_id_rejected": True},
                        "SpaceMission requires a Commander/Captain and a mission_id starting with 'M'",
                    ),
                    name="SpaceMission enforces crew-command and mission_id business rules",
                ),
            ],
        ),
    ],
)
