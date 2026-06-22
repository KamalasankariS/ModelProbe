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
    <div className="border border-border rounded-xl overflow-hidden shadow-sm">
      <button
        className={`w-full flex justify-between items-center px-5 py-3 font-medium text-sm ${colorClass} hover:brightness-95 transition-all`}
        onClick={() => setOpen((o) => !o)}
      >
        <span>
          {title} ({rows.length})
        </span>
        <span className="text-xs">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-stone-400 border-b border-border bg-cream">
              <th className="px-5 py-2 font-medium uppercase tracking-wider">Test Case</th>
              <th className="px-5 py-2 font-medium uppercase tracking-wider">Expected</th>
              <th className="px-5 py-2 font-medium uppercase tracking-wider">v1</th>
              <th className="px-5 py-2 font-medium uppercase tracking-wider">v2</th>
              <th className="px-5 py-2 font-medium uppercase tracking-wider">Reason</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.test_case_id} className="border-b border-border/50 bg-white">
                <td className="px-5 py-2 font-mono text-charcoal">{r.test_case_id}</td>
                <td className="px-5 py-2 text-stone-500 truncate max-w-xs">{r.expected_output ?? "—"}</td>
                <td className="px-5 py-2">
                  {r.v1_status && (
                    <StatusBadge status={r.v1_status as "pass" | "fail" | "error" | "skipped"} />
                  )}
                </td>
                <td className="px-5 py-2">
                  {r.v2_status && (
                    <StatusBadge status={r.v2_status as "pass" | "fail" | "error" | "skipped"} />
                  )}
                </td>
                <td className="px-5 py-2 text-stone-500">{r.v2_reason ?? r.v1_reason ?? "—"}</td>
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

  if (loading) return <div className="text-stone-400 py-12 text-center">Loading...</div>;
  if (error) return <div className="text-red-600">{error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-charcoal">
        {name}: {v1} vs {v2}
      </h1>
      <Section title="Regressed" rows={data.regressed} defaultOpen={true} colorClass="bg-red-50 text-red-700" />
      <Section title="Improved" rows={data.improved} colorClass="bg-emerald-50 text-emerald-700" />
      <Section title="New" rows={data.new} colorClass="bg-amber-50 text-amber-700" />
      <Section title="Removed" rows={data.removed} colorClass="bg-orange-50 text-orange-700" />
      <Section title="Unchanged" rows={data.unchanged} colorClass="bg-stone-50 text-stone-500" />
    </div>
  );
}
