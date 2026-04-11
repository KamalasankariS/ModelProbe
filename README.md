# ModelProbe

AI system evaluation and regression testing. Works locally with zero config, scales to a shared team server by changing one line.

---

## Install

```bash
pip install modelprobe             # SDK only — no server required
pip install modelprobe[server]     # SDK + dashboard + REST API
```

---

## SDK — three lines to start tracing

```python
from modelprobe import trace

@trace(suite="invoice-agent", version="v1")
def call_llm(prompt):
    return my_model(prompt)
```

Every call writes a run record to `~/.modelprobe/modelprobe.db` automatically.

---

## Nested traces

Wrapping multiple functions with `@trace` produces a parent/child tree sharing one `trace_id`.

```python
from modelprobe import trace

@trace(suite="invoice-agent", version="v2", tags={"feature": "invoice"})
def run_agent(query):
    result = call_llm(query)
    data = call_tool(result)
    return call_llm(data)

@trace(suite="invoice-agent", version="v2")
def call_llm(prompt):
    return my_model(prompt)

@trace(suite="invoice-agent", version="v2")
def call_tool(data):
    return my_tool(data)
```

All three runs share `trace_id`. `call_llm` and `call_tool` have `parent_id` pointing at `run_agent`.

---

## Run a test suite

```python
from modelprobe import run_suite

test_cases = [
    {
        "test_case_id": "tc_001",
        "input": "What is the invoice total?",
        "expected_output": "$500",
        "eval_type": "contains",
        "eval_config": {"values": ["$500"]},
    }
]

result = run_suite(
    suite_name="invoice-agent",
    version="v2",
    test_cases=test_cases,
    runner=lambda tc: my_model(tc["input"]),
)

print(f"Pass rate: {result.pass_rate:.1%}")
print(f"Passed: {result.passed} / Failed: {result.failed} / Errored: {result.errored}")
```

---

## Inline assertion

```python
from modelprobe import assert_eval

assert_eval("The total is $500", "contains", {"values": ["$500"]})
```

Raises `AssertionError` if the evaluation fails.

---

## Team mode — remote server

```python
import modelprobe
modelprobe.configure(server="http://modelprobe.internal:8000")
```

Or set the environment variable:

```bash
export MODELPROBE_SERVER=http://modelprobe.internal:8000
```

All SDK calls route to the remote server. No code changes required.

---

## Server

```bash
pip install modelprobe[server]
modelprobe start --port 8000
```

Dashboard at `http://localhost:8000`. REST API at `http://localhost:8000/api`. OpenAPI docs at `http://localhost:8000/api/docs`.

---

## CLI

```bash
modelprobe status                                         # config and connection info
modelprobe run-suite my-agent --version v2 --file cases.json
modelprobe start --port 8000
modelprobe migrate
```

---

## Evaluators

| Type | Description |
|---|---|
| `exact` | Exact string match. `config: {"case_sensitive": true}` |
| `contains` | Substring check. `config: {"values": [...], "mode": "any\|all"}` |
| `regex` | Regex match. `config: {"pattern": "..."}` |
| `json_schema` | JSON Schema validation. `config: {"schema": {...}}` |
| `llm_judge` | LLM-graded rubric. `config: {"model": "...", "rubric": "..."}` |

All evaluators return `{passed, score, reason, status}` where `status` is one of `pass`, `fail`, `error`, `skipped`.

`llm_judge` timeouts and errors produce `status="skipped"` — never `status="fail"`.

---

## Configuration

Priority order (lowest to highest):

1. Hardcoded defaults
2. `~/.modelprobe/config.toml`
3. Environment variables
4. `modelprobe.configure(**kwargs)` — highest priority

Environment variables:

| Variable | Purpose |
|---|---|
| `MODELPROBE_SERVER` | Remote server URL |
| `MODELPROBE_DB_PATH` | Local SQLite path (default: `~/.modelprobe/modelprobe.db`) |
| `MODELPROBE_API_KEY` | Auth token for remote server |
| `MODELPROBE_LLM_ENDPOINT` | LLM endpoint for `llm_judge` |
| `MODELPROBE_LLM_API_KEY` | API key for LLM endpoint |

---

## Data model

```json
{
  "id": "uuid",
  "trace_id": "uuid",
  "parent_id": "uuid | null",
  "suite": "invoice-agent",
  "version": "v2",
  "run_group": "experiment_1",
  "commit_hash": "abc123",
  "tags": {"env": "staging"},
  "input": "...",
  "output": "...",
  "status": "pass | fail | error | skipped",
  "latency_ms": 142.3,
  "token_count": 218,
  "timestamp": "2026-04-11T12:00:00Z",
  "steps": []
}
```

---

## REST API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/runs` | Submit a run |
| `GET` | `/api/runs` | List runs with filters |
| `GET` | `/api/runs/{id}` | Run detail with step tree |
| `GET` | `/api/suites` | List suites with pass rates |
| `GET` | `/api/suites/{name}` | Suite detail + version history |
| `GET` | `/api/suites/{name}/compare?v1=x&v2=y` | Per-test-case version diff |
| `GET` | `/api/suites/{name}/regressions` | Test cases that regressed |
| `GET` | `/api/health` | Server health + uptime |

All responses follow the envelope:

```json
{
  "data": {},
  "version": "0.1.0",
  "timestamp": "...",
  "request_id": "uuid"
}
```

---

## Development setup

```bash
git clone https://github.com/your-org/modelprobe
cd modelprobe
pip install -e ".[server,dev]"
pytest
```

Dashboard (requires Node.js):

```bash
cd dashboard
npm install
npm run dev      # dev server proxies /api to localhost:8000
npm run build    # outputs to modelprobe/server/static/dist/
```
