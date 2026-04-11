const BASE = `${window.location.origin}/api`;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  const envelope = await res.json();
  return envelope.data as T;
}

export interface Run {
  id: string;
  trace_id: string;
  parent_id: string | null;
  suite: string;
  version: string;
  run_group: string | null;
  commit_hash: string | null;
  tags: Record<string, string>;
  input: string | null;
  output: string | null;
  status: "pass" | "fail" | "error" | "skipped";
  latency_ms: number | null;
  token_count: number | null;
  timestamp: string | null;
  steps: Run[];
}

export interface EvalResult {
  id: string;
  run_id: string;
  test_case_id: string;
  passed: boolean;
  score: number | null;
  reason: string | null;
  status: "pass" | "fail" | "error" | "skipped";
  evaluator: string;
}

export interface Suite {
  name: string;
  latest_version: string | null;
  pass_rate: number | null;
  has_regressions: boolean;
  last_run: string | null;
  version_count: number;
}

export interface TestCase {
  id: string;
  test_case_id: string;
  input: string | null;
  expected_output: string | null;
  eval_type: string;
  eval_config: Record<string, unknown>;
}

export interface VersionCompareResult {
  test_case_id: string;
  input: string | null;
  expected_output: string | null;
  v1_status: string | null;
  v1_score: number | null;
  v1_reason: string | null;
  v2_status: string | null;
  v2_score: number | null;
  v2_reason: string | null;
}

export interface CompareOut {
  suite: string;
  v1: string;
  v2: string;
  regressed: VersionCompareResult[];
  improved: VersionCompareResult[];
  unchanged: VersionCompareResult[];
  new: VersionCompareResult[];
  removed: VersionCompareResult[];
}

export interface Regression {
  test_case_id: string;
  previous_pass_rate: number;
  current_pass_rate: number;
  severity: number;
  input: string | null;
  expected_output: string | null;
}

export const api = {
  runs: {
    list: (params?: Record<string, string>) => {
      const qs = params ? "?" + new URLSearchParams(params).toString() : "";
      return request<Run[]>(`/runs${qs}`);
    },
    get: (id: string) => request<Run>(`/runs/${id}`),
    evalResults: (id: string) => request<EvalResult[]>(`/runs/${id}/eval-results`),
  },
  suites: {
    list: () => request<Suite[]>("/suites"),
    get: (name: string) => request<{ name: string; version_history: unknown[]; test_cases: TestCase[] }>(`/suites/${name}`),
    compare: (name: string, v1: string, v2: string) =>
      request<CompareOut>(`/suites/${name}/compare?v1=${v1}&v2=${v2}`),
    regressions: (name: string) => request<Regression[]>(`/suites/${name}/regressions`),
  },
  health: () => request<{ version: string; mode: string; db_status: string; uptime_s: number }>("/health"),
};
