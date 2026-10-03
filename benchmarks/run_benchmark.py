"""Run ModelProbe benchmark against local Ollama models.

Uses the model adapter layer for standardized latency and token tracking.
Supports multiple trials for statistical confidence.

Usage:
    python benchmarks/run_benchmark.py                # single trial (default)
    python benchmarks/run_benchmark.py --trials 3     # 3 trials with mean ± std
"""

import argparse
import json
import math
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


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def _ci95(values: list[float]) -> float:
    """95% confidence interval half-width (t-based for small N)."""
    n = len(values)
    if n < 2:
        return 0.0
    # t-values for 95% CI, df=1..9
    t_table = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
               6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}
    t_val = t_table.get(n - 1, 1.96)
    return t_val * _std(values) / math.sqrt(n)


def aggregate_trials(trial_summaries: list[list[dict]]) -> list[dict]:
    """Aggregate multiple trial runs into mean ± CI for each model."""
    n_trials = len(trial_summaries)
    models = [s["model"] for s in trial_summaries[0]]

    aggregated = []
    for model in models:
        runs = []
        for trial in trial_summaries:
            match = [s for s in trial if s["model"] == model]
            if match:
                runs.append(match[0])

        if not runs:
            continue

        pass_rates = [r["pass_rate"] for r in runs]
        avg_latencies = [r["latency"]["avg_ms"] for r in runs]
        p95_latencies = [r["latency"]["p95_ms"] for r in runs]
        wall_times = [r["throughput"]["wall_time_s"] for r in runs]

        # Per-category pass rates across trials
        categories = ["math", "factual", "instruction", "code", "hallucination"]
        cat_stats = {}
        for cat in categories:
            cat_rates = []
            for r in runs:
                cat_results = [c for c in r["results"] if c.get("test_case_id", "").startswith(cat[:4])]
                cat_total = len(cat_results)
                if cat_total > 0:
                    cat_passed = sum(1 for c in cat_results if c.get("status") == "pass")
                    cat_rates.append(cat_passed / cat_total)
            cat_stats[cat] = {
                "mean": round(_mean(cat_rates), 4),
                "std": round(_std(cat_rates), 4),
                "ci95": round(_ci95(cat_rates), 4),
                "values": [round(v, 4) for v in cat_rates],
            }

        aggregated.append({
            "model": model,
            "trials": n_trials,
            "pass_rate": {
                "mean": round(_mean(pass_rates), 4),
                "std": round(_std(pass_rates), 4),
                "ci95": round(_ci95(pass_rates), 4),
                "values": [round(v, 4) for v in pass_rates],
            },
            "latency_avg_ms": {
                "mean": round(_mean(avg_latencies), 1),
                "std": round(_std(avg_latencies), 1),
                "ci95": round(_ci95(avg_latencies), 1),
            },
            "latency_p95_ms": {
                "mean": round(_mean(p95_latencies), 1),
                "std": round(_std(p95_latencies), 1),
                "ci95": round(_ci95(p95_latencies), 1),
            },
            "wall_time_s": {
                "mean": round(_mean(wall_times), 1),
                "std": round(_std(wall_times), 1),
                "ci95": round(_ci95(wall_times), 1),
            },
            "categories": cat_stats,
        })

    return aggregated


def print_comparison(summaries: list, multi_trial: list[dict] | None = None):
    print(f"\n{'=' * 80}")
    print("  COMPARISON")
    print(f"{'=' * 80}")

    if multi_trial:
        n = multi_trial[0]["trials"]
        print(f"  Aggregated over {n} trials (mean ± 95% CI)\n")
        print(f"  {'Model':<16} {'Pass Rate':>18} {'Avg Latency':>20} {'Wall Time':>18}")
        print(f"  {'-' * 75}")
        for m in multi_trial:
            pr = m["pass_rate"]
            lat = m["latency_avg_ms"]
            wt = m["wall_time_s"]
            print(
                f"  {m['model']:<16} "
                f"{pr['mean']:>6.0%} ± {pr['ci95']:.1%}    "
                f"{lat['mean']:>7.0f} ± {lat['ci95']:.0f}ms    "
                f"{wt['mean']:>6.1f} ± {wt['ci95']:.1f}s"
            )

        categories = ["math", "factual", "instruction", "code", "hallucination"]
        print(f"\n  Per-category (mean ± 95% CI):")
        print(f"  {'Category':<15}", end="")
        for m in multi_trial:
            print(f" {m['model']:>24}", end="")
        print()
        print(f"  {'-' * (15 + 25 * len(multi_trial))}")
        for cat in categories:
            print(f"  {cat:<15}", end="")
            for m in multi_trial:
                cs = m["categories"][cat]
                print(f" {cs['mean']:>10.0%} ± {cs['ci95']:.1%}       ", end="")
            print()
        return

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


def save_results(summaries: list, multi_trial: list[dict] | None = None):
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

    if multi_trial:
        mt_path = RESULTS_DIR / "multi_trial.json"
        mt_path.write_text(json.dumps(multi_trial, indent=2))
        print(f"  Saved: {mt_path}")


def main():
    parser = argparse.ArgumentParser(description="Run ModelProbe benchmarks")
    parser.add_argument("--trials", type=int, default=1,
                        help="Number of trials to run per model (default: 1). "
                             "Multiple trials compute mean ± 95%% CI.")
    args = parser.parse_args()

    test_cases = json.loads(TEST_CASES_PATH.read_text())
    print(f"Loaded {len(test_cases)} test cases from {TEST_CASES_PATH.name}")
    print(f"Models: {', '.join(MODELS)}")
    if args.trials > 1:
        print(f"Trials: {args.trials}")

    all_trial_summaries = []

    for trial_num in range(args.trials):
        if args.trials > 1:
            print(f"\n{'#' * 80}")
            print(f"  TRIAL {trial_num + 1} of {args.trials}")
            print(f"{'#' * 80}")

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

        all_trial_summaries.append(summaries)

    multi_trial = None
    if args.trials > 1:
        multi_trial = aggregate_trials(all_trial_summaries)

    # Print and save using the last trial's summaries as the per-model detail
    print_comparison(summaries, multi_trial=multi_trial)
    save_results(summaries, multi_trial=multi_trial)
    print("\nDone.")


if __name__ == "__main__":
    main()
