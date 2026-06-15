"""Run ModelProbe benchmark against local Ollama models.

Usage:
    python benchmarks/run_benchmark.py
"""

import json
import sys
import time
from pathlib import Path

import httpx

from modelprobe import run_suite

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELS = ["gemma3:4b", "llama3", "codegemma:7b"]
TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"
RESULTS_DIR = Path(__file__).parent / "results"


def query_ollama(model: str, prompt: str) -> str:
    resp = httpx.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def run_model(model: str, test_cases: list) -> dict:
    print(f"\n{'=' * 60}")
    print(f"  Model: {model}")
    print(f"  Test cases: {len(test_cases)}")
    print(f"{'=' * 60}")

    latencies = []

    def runner(tc):
        start = time.time()
        output = query_ollama(model, tc["input"])
        elapsed = time.time() - start
        latencies.append(elapsed)
        tc_id = tc.get("test_case_id", "?")
        print(f"  [{tc_id}] {elapsed:.1f}s")
        return output

    # Inject model name and endpoint into hallucination eval configs
    patched = []
    for tc in test_cases:
        if tc.get("eval_type") == "hallucination":
            tc = {**tc, "eval_config": {
                **tc.get("eval_config", {}),
                "model": model,
                "endpoint": OLLAMA_URL,
            }}
        patched.append(tc)

    result = run_suite(
        suite_name="ollama-benchmark",
        version=model,
        test_cases=patched,
        runner=runner,
        tags={"model": model, "benchmark": "v1"},
    )

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    summary = {
        "model": model,
        "total": result.total,
        "passed": result.passed,
        "failed": result.failed,
        "errored": result.errored,
        "skipped": result.skipped,
        "pass_rate": result.pass_rate,
        "avg_latency_s": round(avg_latency, 2),
        "results": result.results,
    }

    print(f"\n  Passed: {result.passed}/{result.total} ({result.pass_rate:.0%})")
    print(f"  Avg latency: {avg_latency:.2f}s")

    return summary


def print_comparison(summaries: list):
    print(f"\n{'=' * 60}")
    print("  COMPARISON")
    print(f"{'=' * 60}")
    print(f"  {'Model':<20} {'Pass Rate':>10} {'Passed':>8} {'Failed':>8} {'Latency':>10}")
    print(f"  {'-' * 56}")
    for s in summaries:
        print(
            f"  {s['model']:<20} {s['pass_rate']:>9.0%} {s['passed']:>8} "
            f"{s['failed']:>8} {s['avg_latency_s']:>9.2f}s"
        )

    # Per-category breakdown
    categories = ["math", "factual", "instruction", "code", "hallucination"]
    print(f"\n  {'Category':<15}", end="")
    for s in summaries:
        print(f" {s['model']:>18}", end="")
    print()
    print(f"  {'-' * (15 + 19 * len(summaries))}")

    for cat in categories:
        print(f"  {cat:<15}", end="")
        for s in summaries:
            cat_results = [r for r in s["results"] if r.get("test_case_id", "").startswith(cat[:4])]
            cat_passed = sum(1 for r in cat_results if r.get("status") == "pass")
            cat_total = len(cat_results)
            if cat_total > 0:
                print(f" {cat_passed:>8}/{cat_total:<3} ({cat_passed/cat_total:.0%})", end="")
            else:
                print(f" {'n/a':>18}", end="")
        print()


def save_results(summaries: list):
    RESULTS_DIR.mkdir(exist_ok=True)

    for s in summaries:
        safe_name = s["model"].replace(":", "_").replace("/", "_")
        path = RESULTS_DIR / f"{safe_name}.json"
        serializable = {k: v for k, v in s.items() if k != "results"}
        serializable["per_case"] = [
            {
                "test_case_id": r.get("test_case_id"),
                "status": r.get("status"),
                "score": r.get("score"),
                "reason": r.get("reason", ""),
            }
            for r in s["results"]
        ]
        path.write_text(json.dumps(serializable, indent=2))
        print(f"  Saved: {path}")

    comparison = []
    for s in summaries:
        comparison.append({
            "model": s["model"],
            "total": s["total"],
            "passed": s["passed"],
            "failed": s["failed"],
            "pass_rate": s["pass_rate"],
            "avg_latency_s": s["avg_latency_s"],
        })
    comp_path = RESULTS_DIR / "comparison.json"
    comp_path.write_text(json.dumps(comparison, indent=2))
    print(f"  Saved: {comp_path}")


def main():
    test_cases = json.loads(TEST_CASES_PATH.read_text())
    print(f"Loaded {len(test_cases)} test cases from {TEST_CASES_PATH.name}")
    print(f"Models: {', '.join(MODELS)}")

    summaries = []
    for model in MODELS:
        try:
            summary = run_model(model, test_cases)
            summaries.append(summary)
        except Exception as exc:
            print(f"  ERROR running {model}: {exc}")
            continue

    if not summaries:
        print("No models completed successfully.")
        sys.exit(1)

    print_comparison(summaries)
    save_results(summaries)
    print("\nDone.")


if __name__ == "__main__":
    main()
