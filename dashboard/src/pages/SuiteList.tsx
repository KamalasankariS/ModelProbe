import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Suite } from "../api/client";
import PassRateBar from "../components/PassRateBar";

export default function SuiteList() {
  const [suites, setSuites] = useState<Suite[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.suites.list().then((data) => {
      setSuites(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="text-muted">Loading...</div>;

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Suites</h1>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted border-b border-border">
            <th className="pb-2 pr-4">Name</th>
            <th className="pb-2 pr-4">Latest Version</th>
            <th className="pb-2 pr-4">Pass Rate</th>
            <th className="pb-2 pr-4">Versions</th>
            <th className="pb-2">Last Run</th>
          </tr>
        </thead>
        <tbody>
          {suites.map((s) => (
            <tr key={s.name} className="border-b border-border/50 hover:bg-panel/50">
              <td className="py-3 pr-4">
                <Link to={`/suites/${s.name}`} className="hover:text-accent font-medium">
                  {s.name}
                </Link>
                {s.has_regressions && (
                  <span className="ml-2 text-xs bg-danger/20 text-danger px-1.5 py-0.5 rounded">
                    regression
                  </span>
                )}
              </td>
              <td className="py-3 pr-4 text-muted">{s.latest_version ?? "—"}</td>
              <td className="py-3 pr-4">
                <PassRateBar rate={s.pass_rate ?? 0} />
              </td>
              <td className="py-3 pr-4 text-muted">{s.version_count}</td>
              <td className="py-3 text-muted">
                {s.last_run ? new Date(s.last_run).toLocaleString() : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
