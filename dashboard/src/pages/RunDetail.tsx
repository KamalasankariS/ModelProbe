import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, Run, EvalResult } from "../api/client";
import Card from "../components/Card";
import StatusBadge from "../components/StatusBadge";

function StepTree({ steps, depth = 0 }: { steps: Run[]; depth?: number }) {
  if (steps.length === 0) return null;
  return (
    <div className={`${depth > 0 ? "pl-4" : ""} border-l border-border/40`}>
      {steps.map((step) => (
        <div key={step.id} className="mt-2">
          <div className="flex items-center gap-2 text-sm">
            <StatusBadge status={step.status} />
            <span className="text-stone-500 font-mono text-xs">{step.id}</span>
            {step.latency_ms != null && (
              <span className="text-xs text-stone-400">{step.latency_ms.toFixed(1)}ms</span>
            )}
          </div>
          {step.output && (
            <pre className="mt-1 text-xs text-stone-600 bg-cream rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
              {step.output}
            </pre>
          )}
          {step.steps?.length > 0 && <StepTree steps={step.steps} depth={depth + 1} />}
        </div>
      ))}
    </div>
  );
}

export default function RunDetail() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<Run | null>(null);
  const [evalResults, setEvalResults] = useState<EvalResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([api.runs.get(id), api.runs.evalResults(id)]).then(([r, ev]) => {
      setRun(r);
      setEvalResults(ev);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="text-stone-400 py-12 text-center">Loading...</div>;
  if (!run) return <div className="text-red-600">Run not found.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-charcoal font-mono">{run.id}</h1>
        <StatusBadge status={run.status} />
      </div>

      <div className="grid grid-cols-4 gap-4 text-sm">
        <Card>
          <div className="text-stone-400 text-xs uppercase tracking-wide">Suite</div>
          <div className="font-medium mt-1 text-charcoal">{run.suite}</div>
        </Card>
        <Card>
          <div className="text-stone-400 text-xs uppercase tracking-wide">Version</div>
          <div className="font-medium mt-1 text-charcoal">{run.version}</div>
        </Card>
        <Card>
          <div className="text-stone-400 text-xs uppercase tracking-wide">Latency</div>
          <div className="font-medium mt-1 text-charcoal">{run.latency_ms != null ? `${run.latency_ms.toFixed(1)}ms` : "—"}</div>
        </Card>
        <Card>
          <div className="text-stone-400 text-xs uppercase tracking-wide">Tokens</div>
          <div className="font-medium mt-1 text-charcoal">{run.token_count ?? "—"}</div>
        </Card>
      </div>

      {run.status === "error" && run.output && (
        <Card title="Error" className="border-red-200 bg-red-50/50">
          <pre className="text-red-700 text-sm whitespace-pre-wrap">{run.output}</pre>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Card title="Input">
          <pre className="text-sm whitespace-pre-wrap text-stone-600 overflow-x-auto">{run.input ?? "—"}</pre>
        </Card>
        <Card title="Output">
          <pre className="text-sm whitespace-pre-wrap text-stone-600 overflow-x-auto">{run.output ?? "—"}</pre>
        </Card>
      </div>

      {Object.keys(run.tags ?? {}).length > 0 && (
        <Card title="Tags">
          <div className="flex flex-wrap gap-2">
            {Object.entries(run.tags).map(([k, v]) => (
              <span key={k} className="text-xs bg-amber-50 text-amber-800 px-2.5 py-1 rounded-full ring-1 ring-amber-200">
                {k}: {v}
              </span>
            ))}
          </div>
        </Card>
      )}

      {evalResults.length > 0 && (
        <Card title="Eval Results">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-stone-400 border-b border-border">
                <th className="pb-2 pr-4 text-xs uppercase tracking-wider font-medium">Test Case</th>
                <th className="pb-2 pr-4 text-xs uppercase tracking-wider font-medium">Evaluator</th>
                <th className="pb-2 pr-4 text-xs uppercase tracking-wider font-medium">Status</th>
                <th className="pb-2 pr-4 text-xs uppercase tracking-wider font-medium">Score</th>
                <th className="pb-2 text-xs uppercase tracking-wider font-medium">Reason</th>
              </tr>
            </thead>
            <tbody>
              {evalResults
                .sort((a, b) => {
                  const order = { error: 0, fail: 1, skipped: 2, pass: 3 };
                  return (order[a.status] ?? 3) - (order[b.status] ?? 3);
                })
                .map((r) => (
                  <tr key={r.id} className="border-b border-border/50">
                    <td className="py-3 pr-4 font-mono text-xs text-charcoal">{r.test_case_id}</td>
                    <td className="py-3 pr-4 text-stone-500">{r.evaluator}</td>
                    <td className="py-3 pr-4">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="py-3 pr-4 text-stone-500">{r.score != null ? r.score.toFixed(2) : "—"}</td>
                    <td className="py-3 text-stone-500 text-xs">{r.reason ?? "—"}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </Card>
      )}

      {run.steps?.length > 0 && (
        <Card title="Step Tree">
          <StepTree steps={run.steps} />
        </Card>
      )}
    </div>
  );
}
