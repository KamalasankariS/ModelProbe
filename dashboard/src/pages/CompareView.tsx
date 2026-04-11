import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { api, CompareOut, VersionCompareResult } from "../api/client";
import StatusBadge from "../components/StatusBadge";

function Section({
  title,
  rows,
  defaultOpen = false,
  colorClass,
}: {
  title: string;
  rows: VersionCompareResult[];
  defaultOpen?: boolean;
  colorClass: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  if (rows.length === 0) return null;
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        className={`w-full flex justify-between items-center px-4 py-3 font-medium text-sm ${colorClass} hover:brightness-110`}
        onClick={() => setOpen((o) => !o)}
      >
        <span>
          {title} ({rows.length})
        </span>
        <span>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-muted border-b border-border bg-panel">
              <th className="px-4 py-2">Test Case</th>
              <th className="px-4 py-2">Expected</th>
              <th className="px-4 py-2">v1</th>
              <th className="px-4 py-2">v2</th>
              <th className="px-4 py-2">Reason</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.test_case_id} className="border-b border-border/50">
                <td className="px-4 py-2 font-mono">{r.test_case_id}</td>
                <td className="px-4 py-2 text-muted truncate max-w-xs">{r.expected_output ?? "—"}</td>
                <td className="px-4 py-2">
                  {r.v1_status && (
                    <StatusBadge status={r.v1_status as "pass" | "fail" | "error" | "skipped"} />
                  )}
                </td>
                <td className="px-4 py-2">
                  {r.v2_status && (
                    <StatusBadge status={r.v2_status as "pass" | "fail" | "error" | "skipped"} />
                  )}
                </td>
                <td className="px-4 py-2 text-muted">{r.v2_reason ?? r.v1_reason ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function CompareView() {
  const { name } = useParams<{ name: string }>();
  const [params] = useSearchParams();
  const v1 = params.get("v1") ?? "";
  const v2 = params.get("v2") ?? "";
  const [data, setData] = useState<CompareOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!name || !v1 || !v2) return;
    api.suites
      .compare(name, v1, v2)
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, [name, v1, v2]);

  if (loading) return <div className="text-muted">Loading...</div>;
  if (error) return <div className="text-danger">{error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">
        {name}: {v1} vs {v2}
      </h1>
      <Section title="Regressed" rows={data.regressed} defaultOpen={true} colorClass="bg-danger/10 text-danger" />
      <Section title="Improved" rows={data.improved} colorClass="bg-success/10 text-success" />
      <Section title="New" rows={data.new} colorClass="bg-accent/10 text-accent" />
      <Section title="Removed" rows={data.removed} colorClass="bg-warning/10 text-warning" />
      <Section title="Unchanged" rows={data.unchanged} colorClass="bg-panel text-muted" />
    </div>
  );
}
