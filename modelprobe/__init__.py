"""ModelProbe — AI system evaluation and regression testing.

Trace any Python callable in three lines::

    from modelprobe import trace

    @trace(suite="my-agent", version="v1")
    def call_llm(prompt):
        return my_model(prompt)

Switch to a remote team server by adding one line::

    import modelprobe
    modelprobe.configure(server="http://localhost:8000")

Run a full evaluation suite::

    from modelprobe import run_suite

    result = run_suite(
        suite_name="invoice-agent",
        version="v2",
        test_cases=[
            {
                "test_case_id": "tc_001",
                "input": "Extract the total from: Invoice total $500",
                "expected_output": "$500",
                "eval_type": "contains",
                "eval_config": {"values": ["$500"]},
            }
        ],
        runner=lambda tc: my_model(tc["input"]),
    )
    print(f"Pass rate: {result.pass_rate:.1%}")

Evaluate a single output inline::

    from modelprobe import assert_eval
    assert_eval("hello world", "contains", {"values": ["hello"]})
"""

from modelprobe.config import configure
from modelprobe.trace import trace
from modelprobe.suite import run_suite, assert_eval, SuiteResult

__version__ = "0.1.1"

__all__ = [
    "configure",
    "trace",
    "run_suite",
    "assert_eval",
    "SuiteResult",
    "__version__",
]
