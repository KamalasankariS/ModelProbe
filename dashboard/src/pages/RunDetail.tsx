import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, Run, EvalResult } from "../api/client";
import Card from "../components/Card";
import StatusBadge from "../components/StatusBadge";

function StepTree({ steps, depth = 0 }: { steps: Run[]; depth?: number }) {
  if (steps.length === 0) return null;
  return (
    <div className={`pl-${depth > 0 ? 4 : 0} border-l border-border/40`}>
      {steps.map((step) => (
        <div key={step.id} className="mt-2">
          <div className="flex items-center gap-2 text-sm">
            <StatusBadge status={step.status} />
            <span className="text-muted font-mono text-xs">{step.id}</span>
            {step.latency_ms != null && (
              <span className="text-xs text-muted">{step.latency_ms.toFixed(1)}ms</span>
            )}
          </div>
          {step.output && (
            <pre className="mt-1 text-xs text-muted bg-surface rounded p-2 overflow-x-auto whitespace-pre-wrap">
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

  if (loading) return <div className="text-muted">Loading...</div>;
  if (!run) return <div className="text-danger">Run not found.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold font-mono">{run.id}</h1>
        <StatusBadge status={run.status} />
      </div>

      <div className="grid grid-cols-4 gap-4 text-sm">
        <Card>
          <div className="text-muted text-xs">Suite</div>
          <div className="font-medium mt-1">{run.suite}</div>
        </Card>
        <Card>
          <div className="text-muted text-xs">Version</div>
          <div className="font-medium mt-1">{run.version}</div>
        </Card>
        <Card>
          <div className="text-muted text-xs">Latency</div>
          <div className="font-medium mt-1">{run.latency_ms != null ? `${run.latency_ms.toFixed(1)}ms` : "—"}</div>
        </Card>
        <Card>
          <div className="text-muted text-xs">Tokens</div>
          <div className="font-medium mt-1">{run.token_count ?? "—"}</div>
        </Card>
      </div>

      {run.status === "error" && run.output && (
        <Card title="Error" className="border-danger/40">
          <pre className="text-danger text-sm whitespace-pre-wrap">{run.output}</pre>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Card title="Input">
          <pre className="text-sm whitespace-pre-wrap text-muted overflow-x-auto">{run.input ?? "—"}</pre>
        </Card>
        <Card title="Output">
          <pre className="text-sm whitespace-pre-wrap text-muted overflow-x-auto">{run.output ?? "—"}</pre>
        </Card>
      </div>

      {Object.keys(run.tags ?? {}).length > 0 && (
        <Card title="Tags">
          <div className="flex flex-wrap gap-2">
            {Object.entries(run.tags).map(([k, v]) => (
              <span key={k} className="text-xs bg-accent/20 text-accent px-2 py-0.5 rounded">
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
              <tr className="text-left text-muted border-b border-border">
                <th className="pb-2 pr-4">Test Case</th>
                <th className="pb-2 pr-4">Evaluator</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Score</th>
                <th className="pb-2">Reason</th>
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
                    <td className="py-2 pr-4 font-mono text-xs">{r.test_case_id}</td>
                    <td className="py-2 pr-4 text-muted">{r.evaluator}</td>
                    <td className="py-2 pr-4">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="py-2 pr-4 text-muted">{r.score != null ? r.score.toFixed(2) : "—"}</td>
                    <td className="py-2 text-muted text-xs">{r.reason ?? "—"}</td>
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
