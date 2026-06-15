import { useState } from "react";
import Card from "../components/Card";
import StatusBadge from "../components/StatusBadge";

interface EvalResult {
  passed: boolean;
  score: number;
  reason: string;
  status: string;
  evaluator: string;
  detail?: Record<string, unknown>;
}

interface HistoryEntry {
  id: number;
  eval_type: string;
  output: string;
  result: EvalResult;
  timestamp: string;
}

const EVALUATORS = [
  { value: "exact", label: "Exact Match" },
  { value: "contains", label: "Contains" },
  { value: "regex", label: "Regex" },
  { value: "json_schema", label: "JSON Schema" },
  { value: "hallucination", label: "Hallucination" },
];

const CONFIG_HINTS: Record<string, string> = {
  exact: '{"case_sensitive": true}',
  contains: '{"values": ["hello", "world"]}',
  regex: '{"pattern": "\\\\d{4}-\\\\d{2}-\\\\d{2}"}',
  json_schema: '{"schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}',
  hallucination:
    '{"strategy": "consistency", "prompt": "What is 2+2?", "model": "llama3", "endpoint": "http://localhost:11434/api/generate", "samples": 3}',
};

export default function Playground() {
  const [output, setOutput] = useState("");
  const [expected, setExpected] = useState("");
  const [evalType, setEvalType] = useState("contains");
  const [config, setConfig] = useState(CONFIG_HINTS["contains"]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EvalResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const handleEvalTypeChange = (type: string) => {
    setEvalType(type);
    setConfig(CONFIG_HINTS[type] || "{}");
    setResult(null);
    setError(null);
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    let parsedConfig: Record<string, unknown> = {};
    try {
      parsedConfig = JSON.parse(config);
    } catch {
      setError("Invalid JSON in config");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${window.location.origin}/api/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          output,
          eval_type: evalType,
          expected: expected || null,
          config: parsedConfig,
        }),
      });

      const envelope = await res.json();
      const data = envelope.data as EvalResult;
      setResult(data);

      setHistory((prev) => [
        {
          id: Date.now(),
          eval_type: evalType,
          output: output.slice(0, 80),
          result: data,
          timestamp: new Date().toLocaleTimeString(),
        },
        ...prev.slice(0, 19),
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 flex flex-col gap-4">
        <h1 className="text-xl font-bold">Playground</h1>

        <Card>
          <div className="flex flex-col gap-4">
            <div>
              <label className="block text-sm text-muted mb-1">Evaluator</label>
              <div className="flex gap-2 flex-wrap">
                {EVALUATORS.map((ev) => (
                  <button
                    key={ev.value}
                    onClick={() => handleEvalTypeChange(ev.value)}
                    className={`px-3 py-1.5 rounded text-sm transition-colors ${
                      evalType === ev.value
                        ? "bg-accent text-white"
                        : "bg-card text-muted hover:text-white border border-border"
                    }`}
                  >
                    {ev.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-muted mb-1">Model Output</label>
              <textarea
                value={output}
                onChange={(e) => setOutput(e.target.value)}
                placeholder="Paste or type the model output to evaluate..."
                rows={4}
                className="w-full bg-surface border border-border rounded px-3 py-2 text-sm text-white placeholder-muted focus:outline-none focus:border-accent"
              />
            </div>

            {(evalType === "exact" || evalType === "contains") && (
              <div>
                <label className="block text-sm text-muted mb-1">
                  Expected Output <span className="text-muted">(optional for some evaluators)</span>
                </label>
                <input
                  value={expected}
                  onChange={(e) => setExpected(e.target.value)}
                  placeholder="Expected output..."
                  className="w-full bg-surface border border-border rounded px-3 py-2 text-sm text-white placeholder-muted focus:outline-none focus:border-accent"
                />
              </div>
            )}

            <div>
              <label className="block text-sm text-muted mb-1">Config (JSON)</label>
              <textarea
                value={config}
                onChange={(e) => setConfig(e.target.value)}
                rows={3}
                className="w-full bg-surface border border-border rounded px-3 py-2 text-sm text-white font-mono placeholder-muted focus:outline-none focus:border-accent"
              />
            </div>

            <button
              onClick={handleRun}
              disabled={loading || !output.trim()}
              className="self-start px-6 py-2 bg-accent text-white rounded font-medium text-sm hover:opacity-90 disabled:opacity-40 transition-opacity"
            >
              {loading ? "Evaluating..." : "Run"}
            </button>
          </div>
        </Card>

        {error && (
          <Card>
            <p className="text-red-400 text-sm">{error}</p>
          </Card>
        )}

        {result && (
          <Card>
            <div className="flex items-center gap-4 mb-4">
              <StatusBadge status={result.status as "pass" | "fail" | "error" | "skipped"} />
              <span className="text-2xl font-bold">
                {(result.score * 100).toFixed(0)}%
              </span>
              <span className="text-muted text-sm">via {result.evaluator}</span>
            </div>
            <p className="text-sm text-muted">{result.reason}</p>
            {result.detail && (
              <pre className="mt-3 text-xs text-muted bg-surface rounded p-3 overflow-x-auto">
                {JSON.stringify(result.detail, null, 2)}
              </pre>
            )}
          </Card>
        )}
      </div>

      <div className="flex flex-col gap-4">
        <h2 className="text-sm font-bold text-muted uppercase tracking-wider">History</h2>
        {history.length === 0 && (
          <p className="text-sm text-muted">Run an evaluation to see results here.</p>
        )}
        {history.map((entry) => (
          <Card key={entry.id}>
            <div className="flex items-center justify-between mb-1">
              <StatusBadge status={entry.result.status as "pass" | "fail" | "error" | "skipped"} />
              <span className="text-xs text-muted">{entry.timestamp}</span>
            </div>
            <p className="text-xs text-muted truncate">{entry.output}</p>
            <div className="flex items-center justify-between mt-1">
              <span className="text-xs text-muted">{entry.eval_type}</span>
              <span className="text-xs font-mono">
                {(entry.result.score * 100).toFixed(0)}%
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
