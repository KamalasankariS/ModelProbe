"""Run ModelProbe benchmark against local Ollama models.

Uses the model adapter layer for standardized latency and token tracking.

Usage:
    python benchmarks/run_benchmark.py
"""

import json
import sys
import time
from pathlib import Path

from modelprobe import run_suite
from modelprobe.models import get_model

MODELS = ["gemma3:4b", "llama3", "codegemma:7b"]
TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"
RESULTS_DIR = Path(__file__).parent / "results"


def run_model(model_name: str, test_cases: list) -> dict:
    print(f"\n{'=' * 60}")
    print(f"  Model: {model_name}")
    print(f"  Test cases: {len(test_cases)}")
    print(f"{'=' * 60}")

    adapter = get_model(f"ollama/{model_name}")
    per_case_metrics = []

    def runner(tc):
        prompt = tc["input"]
        resp = adapter.generate(prompt)
        tc_id = tc.get("test_case_id", "?")
        tokens = resp.token_count or 0
        tps = tokens / (resp.latency_ms / 1000) if resp.latency_ms > 0 and tokens else 0
        print(f"  [{tc_id}] {resp.latency_ms:.0f}ms  {tokens} tokens  {tps:.1f} tok/s")
        per_case_metrics.append({
            "test_case_id": tc_id,
            "latency_ms": resp.latency_ms,
            "token_count": tokens,
            "tokens_per_sec": round(tps, 1),
        })
        return resp.text

    # Inject model + endpoint into hallucination eval configs
    patched = []
    for tc in test_cases:
        if tc.get("eval_type") == "hallucination":
            tc = {**tc, "eval_config": {
                **tc.get("eval_config", {}),
                "model": model_name,
                "endpoint": "http://localhost:11434/api/generate",
            }}
        patched.append(tc)

    wall_start = time.perf_counter()
    result = run_suite(
        suite_name="ollama-benchmark",
        version=model_name,
        test_cases=patched,
        runner=runner,
        tags={"model": model_name, "benchmark": "v2"},
    )
    wall_time = time.perf_counter() - wall_start

    latencies = [m["latency_ms"] for m in per_case_metrics]
    tokens = [m["token_count"] for m in per_case_metrics if m["token_count"] > 0]
    tps_values = [m["tokens_per_sec"] for m in per_case_metrics if m["tokens_per_sec"] > 0]

    avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0
    p50_latency = sorted(latencies)[len(latencies) // 2] if latencies else 0
    p95_idx = int(len(latencies) * 0.95)
    p95_latency = sorted(latencies)[min(p95_idx, len(latencies) - 1)] if latencies else 0
    total_tokens = sum(tokens)
    avg_tps = sum(tps_values) / len(tps_values) if tps_values else 0
    throughput = len(test_cases) / wall_time if wall_time > 0 else 0

    summary = {
        "model": model_name,
        "total": result.total,
        "passed": result.passed,
        "failed": result.failed,
        "errored": result.errored,
        "skipped": result.skipped,
        "pass_rate": result.pass_rate,
        "latency": {
            "avg_ms": round(avg_latency_ms, 1),
            "p50_ms": round(p50_latency, 1),
            "p95_ms": round(p95_latency, 1),
            "min_ms": round(min(latencies), 1) if latencies else 0,
            "max_ms": round(max(latencies), 1) if latencies else 0,
        },
        "tokens": {
            "total": total_tokens,
            "avg_per_request": round(total_tokens / len(tokens), 1) if tokens else 0,
            "avg_tokens_per_sec": round(avg_tps, 1),
        },
        "throughput": {
            "evals_per_sec": round(throughput, 3),
            "wall_time_s": round(wall_time, 1),
        },
        "results": result.results,
        "per_case": per_case_metrics,
    }

    print(f"\n  Passed: {result.passed}/{result.total} ({result.pass_rate:.0%})")
    print(f"  Latency: avg={avg_latency_ms:.0f}ms  p50={p50_latency:.0f}ms  p95={p95_latency:.0f}ms")
    print(f"  Tokens:  total={total_tokens}  avg={summary['tokens']['avg_per_request']:.0f}/req  {avg_tps:.1f} tok/s")
    print(f"  Throughput: {throughput:.3f} evals/s  wall={wall_time:.1f}s")

    return summary


def print_comparison(summaries: list):
    print(f"\n{'=' * 80}")
    print("  COMPARISON")
    print(f"{'=' * 80}")
    print(f"  {'Model':<16} {'Pass Rate':>10} {'Avg Latency':>12} {'P95':>8} {'Tok/s':>8} {'Evals/s':>9}")
    print(f"  {'-' * 70}")
    for s in summaries:
        print(
            f"  {s['model']:<16} {s['pass_rate']:>9.0%} "
            f"{s['latency']['avg_ms']:>10.0f}ms "
            f"{s['latency']['p95_ms']:>6.0f}ms "
            f"{s['tokens']['avg_tokens_per_sec']:>7.1f} "
            f"{s['throughput']['evals_per_sec']:>8.3f}"
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
                "test_case_id": pc["test_case_id"],
                "latency_ms": pc["latency_ms"],
                "token_count": pc["token_count"],
                "tokens_per_sec": pc["tokens_per_sec"],
                "status": r.get("status"),
                "score": r.get("score"),
                "reason": r.get("reason", ""),
            }
            for pc, r in zip(s["per_case"], s["results"])
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
            "latency": s["latency"],
            "tokens": s["tokens"],
            "throughput": s["throughput"],
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
