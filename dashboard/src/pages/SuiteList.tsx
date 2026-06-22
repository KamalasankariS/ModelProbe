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

  if (loading) return <div className="text-stone-400 py-12 text-center">Loading...</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-charcoal mb-6">Suites</h1>
      <div className="bg-white border border-border rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-stone-400 border-b border-border bg-cream">
              <th className="px-5 py-3 font-medium text-xs uppercase tracking-wider">Name</th>
              <th className="px-5 py-3 font-medium text-xs uppercase tracking-wider">Latest Version</th>
              <th className="px-5 py-3 font-medium text-xs uppercase tracking-wider">Pass Rate</th>
              <th className="px-5 py-3 font-medium text-xs uppercase tracking-wider">Versions</th>
              <th className="px-5 py-3 font-medium text-xs uppercase tracking-wider">Last Run</th>
            </tr>
          </thead>
          <tbody>
            {suites.map((s) => (
              <tr key={s.name} className="border-b border-border/50 hover:bg-cream/50 transition-colors">
                <td className="px-5 py-4">
                  <Link to={`/dashboard/suites/${s.name}`} className="text-charcoal hover:text-amber-700 font-medium">
                    {s.name}
                  </Link>
                  {s.has_regressions && (
                    <span className="ml-2 text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded-full ring-1 ring-red-200">
                      regression
                    </span>
                  )}
                </td>
                <td className="px-5 py-4 text-stone-500">{s.latest_version ?? "—"}</td>
                <td className="px-5 py-4">
                  <PassRateBar rate={s.pass_rate ?? 0} />
                </td>
                <td className="px-5 py-4 text-stone-500">{s.version_count}</td>
                <td className="px-5 py-4 text-stone-500">
                  {s.last_run ? new Date(s.last_run).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
