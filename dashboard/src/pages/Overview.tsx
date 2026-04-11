import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Suite, Regression } from "../api/client";
import Card from "../components/Card";
import PassRateBar from "../components/PassRateBar";

export default function Overview() {
  const [suites, setSuites] = useState<Suite[]>([]);
  const [regressions, setRegressions] = useState<Record<string, Regression[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const data = await api.suites.list();
      setSuites(data);

      const regMap: Record<string, Regression[]> = {};
      await Promise.all(
        data.map(async (s) => {
          try {
            const regs = await api.suites.regressions(s.name);
            if (regs.length > 0) regMap[s.name] = regs;
          } catch (_) {}
        })
      );
      setRegressions(regMap);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <div className="text-muted">Loading...</div>;

  const suitesWithRegressions = Object.entries(regressions);
  const totalRuns = suites.reduce((acc, s) => acc + s.version_count, 0);
  const avgPassRate =
    suites.length > 0
      ? suites.reduce((acc, s) => acc + (s.pass_rate ?? 0), 0) / suites.length
      : 0;

  return (
    <div className="space-y-6">
      {suitesWithRegressions.length > 0 && (
        <Card title="Regressions Detected" className="border-danger/40">
          <div className="space-y-3">
            {suitesWithRegressions.map(([name, regs]) => (
              <div key={name} className="flex items-start justify-between">
                <div>
                  <Link to={`/suites/${name}`} className="text-danger font-medium hover:underline">
                    {name}
                  </Link>
                  <p className="text-xs text-muted mt-0.5">{regs.length} test case(s) regressed</p>
                </div>
                <Link
                  to={`/suites/${name}`}
                  className="text-xs text-accent hover:underline"
                >
                  View
                </Link>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <div className="text-2xl font-bold">{suites.length}</div>
          <div className="text-xs text-muted mt-1">Active Suites</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold">{totalRuns}</div>
          <div className="text-xs text-muted mt-1">Total Versions</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold">{Math.round(avgPassRate * 100)}%</div>
          <div className="text-xs text-muted mt-1">Avg Pass Rate</div>
        </Card>
      </div>

      <Card title="Suite Pass Rates">
        <div className="space-y-3">
          {suites.map((s) => (
            <div key={s.name} className="flex items-center justify-between">
              <Link to={`/suites/${s.name}`} className="text-sm hover:text-accent">
                {s.name}
                {regressions[s.name] && (
                  <span className="ml-2 text-xs text-danger">[regression]</span>
                )}
              </Link>
              <PassRateBar rate={s.pass_rate ?? 0} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
