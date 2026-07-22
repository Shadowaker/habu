from __future__ import annotations

from habu.checks import probe_check, source_contains_check, source_forbids
from habu.models import Exercise, Project, fail, ok


def _check_ex0(got: dict):

    if got.get("abstract_instantiable") is not False:
        return fail("DataProcessor should be abstract (not directly instantiable)")

    if got.get("validate_numeric_ok") is not True or got.get("validate_numeric_bad") is not False:
        return fail("NumericProcessor.validate() should accept numbers and reject non-numeric data")

    if got.get("numeric_outputs") != ["1", "2", "3"]:
        return fail(
            f"NumericProcessor.output() should drain FIFO as strings '1','2','3', got {got.get('numeric_outputs')}"
        )

    if not got.get("bad_ingest_raises"):
        return fail("ingest() with invalid data (no prior validate()) should raise an exception")

    if got.get("validate_text_ok") is not True or got.get("validate_text_bad") is not False:
        return fail("TextProcessor.validate() should accept str and reject non-str data")

    if got.get("text_output") != "a":
        return fail(f"TextProcessor.output() should return 'a' first (FIFO), got {got.get('text_output')!r}")

    if not got.get("validate_log_ok"):
        return fail("LogProcessor.validate() should accept a well-formed log dict")

    if got.get("log_output") != "INFO: hi":
        return fail(f"LogProcessor.output() should format as 'LEVEL: message', got {got.get('log_output')!r}")

    return ok("abstract base + all three processors validate/ingest/output correctly")


def _check_ex1(stdout: str):

    if "unhandled string" not in stdout:
        return fail("process_stream() should report the unhandled string element somewhere in its output")

    if not any(k in stdout for k in ("Can't process", "cannot process", "no processor", "No processor")):
        return fail("expected an error message indicating no processor could handle the unregistered-type element")

    return ok("reports unhandled stream elements when no matching processor is registered")


def _check_ex2(got: dict):

    received = got.get("received", "")
    if not received or len(received) != 1:
        return fail(f"expected exactly one process_output() call, got {received}")

    batch = received[0]
    if len(batch) != 2:
        return fail(f"output_pipeline(2, plugin) should send exactly 2 items, got {len(batch)}")

    values = [item[1] if isinstance(item, (list, tuple)) else item for item in batch]
    if values != ["1", "2"]:
        return fail(f"expected the first 2 FIFO items ('1', '2'), got {values}")

    return ok("output_pipeline() drains nb items per processor into the duck-typed plugin")


PROJECT = Project(
    id="p05",
    name="Code Nexus",
    tagline="Polymorphic Data Streams in the Digital Matrix",
    exercises=[
        Exercise(
            id="ex0",
            title="Data Processor",
            files=["ex0/data_processor.py"],
            checks=[
                source_forbids("ex0/data_processor.py", "eval(", message="never call eval()"),
                probe_check(
                    "ex0/data_processor.py",
                    body="""
try:
    mod.DataProcessor()
    record(('abstract_instantiable', True))
except TypeError:
    record(('abstract_instantiable', False))

np = mod.NumericProcessor()
record(('validate_numeric_ok', np.validate(42)))
record(('validate_numeric_bad', np.validate('hello')))
np.ingest([1, 2, 3])
record(('numeric_outputs', [np.output()[1] for _ in range(3)]))

try:
    mod.NumericProcessor().ingest('not a number')
    record(('bad_ingest_raises', False))
except Exception as e:
    record(('bad_ingest_raises', type(e).__name__))

tp = mod.TextProcessor()
record(('validate_text_ok', tp.validate('hello')))
record(('validate_text_bad', tp.validate(42)))
tp.ingest(['a', 'b'])
record(('text_output', tp.output()[1]))

lp = mod.LogProcessor()
log_entry = {'log_level': 'INFO', 'log_message': 'hi'}
record(('validate_log_ok', lp.validate(log_entry)))
lp.ingest(log_entry)
record(('log_output', lp.output()[1]))
""",
                    assertion=lambda records: _check_ex0(dict(records)),
                    name="DataProcessor is abstract; subclasses validate/ingest/output correctly",
                ),
            ],
        ),
        Exercise(
            id="ex1",
            title="Polymorphic Processing of a Data Stream",
            files=["ex1/data_stream.py"],
            checks=[
                probe_check(
                    "ex1/data_stream.py",
                    body="""
ds = mod.DataStream()
ds.register_processor(mod.NumericProcessor())
ds.process_stream([1, 2.5, 'unhandled string'])
record(('after_numeric_only', None))
ds.register_processor(mod.TextProcessor())
ds.process_stream(['hello', 'world'])
record(('after_text_registered', None))
""",
                    assertion=lambda records, stdout: _check_ex1(stdout),
                    name="DataStream routes elements polymorphically and reports unhandled ones",
                ),
            ],
        ),
        Exercise(
            id="ex2",
            title="Data Pipeline",
            files=["ex2/data_pipeline.py"],
            checks=[
                source_contains_check(
                    "ex2/data_pipeline.py",
                    "Protocol",
                    message="defines ExportPlugin via typing.Protocol",
                ),
                probe_check(
                    "ex2/data_pipeline.py",
                    body="""
ds = mod.DataStream()
proc = mod.NumericProcessor()
ds.register_processor(proc)
ds.process_stream([1, 2, 3])

class ProbePlugin:
    def __init__(self):
        self.received = []

    def process_output(self, data):
        self.received.append(list(data))

plugin = ProbePlugin()
ds.output_pipeline(2, plugin)
record(('received', plugin.received))
""",
                    assertion=lambda records: _check_ex2(dict(records)),
                    name="output_pipeline() feeds nb items per processor to a duck-typed plugin",
                ),
            ],
        ),
    ],
)