import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, TestCase } from "../api/client";
import Card from "../components/Card";

interface VersionStat {
  version: string;
  total: number;
  passed: number;
  pass_rate: number;
}

export default function SuiteDetail() {
  const { name } = useParams<{ name: string }>();
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [versionHistory, setVersionHistory] = useState<VersionStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!name) return;
    api.suites.get(name).then((data) => {
      setVersionHistory(data.version_history as VersionStat[]);
      setTestCases(data.test_cases);
      setLoading(false);
    });
  }, [name]);

  if (loading) return <div className="text-stone-400 py-12 text-center">Loading...</div>;

  const versions = versionHistory.map((v) => v.version);
  const latestVersion = versions[0];
  const previousVersion = versions[1];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-charcoal">{name}</h1>
        {latestVersion && previousVersion && (
          <Link
            to={`/dashboard/compare/${name}?v1=${previousVersion}&v2=${latestVersion}`}
            className="text-sm text-amber-700 hover:underline font-medium"
          >
            Compare {previousVersion} vs {latestVersion}
          </Link>
        )}
      </div>

      <Card title="Version History">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-stone-400 border-b border-border">
              <th className="pb-2 pr-4 text-xs uppercase tracking-wider font-medium">Version</th>
              <th className="pb-2 pr-4 text-xs uppercase tracking-wider font-medium">Total</th>
              <th className="pb-2 pr-4 text-xs uppercase tracking-wider font-medium">Passed</th>
              <th className="pb-2 text-xs uppercase tracking-wider font-medium">Pass Rate</th>
            </tr>
          </thead>
          <tbody>
            {versionHistory.map((v) => (
              <tr key={v.version} className="border-b border-border/50">
                <td className="py-3 pr-4 font-medium text-charcoal">{v.version}</td>
                <td className="py-3 pr-4 text-stone-500">{v.total}</td>
                <td className="py-3 pr-4 text-stone-500">{v.passed}</td>
                <td className="py-3">
                  <span
                    className={`font-semibold ${
                      v.pass_rate >= 0.9
                        ? "text-emerald-600"
                        : v.pass_rate >= 0.6
                        ? "text-amber-600"
                        : "text-red-600"
                    }`}
                  >
                    {Math.round(v.pass_rate * 100)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Test Cases">
        {testCases.length === 0 ? (
          <p className="text-stone-400 text-sm">No test cases registered for this suite.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-stone-400 border-b border-border">
                <th className="pb-2 pr-4 text-xs uppercase tracking-wider font-medium">ID</th>
                <th className="pb-2 pr-4 text-xs uppercase tracking-wider font-medium">Eval Type</th>
                <th className="pb-2 text-xs uppercase tracking-wider font-medium">Expected Output</th>
              </tr>
            </thead>
            <tbody>
              {testCases.map((tc) => (
                <tr key={tc.id} className="border-b border-border/50">
                  <td className="py-3 pr-4 font-mono text-xs text-charcoal">{tc.test_case_id}</td>
                  <td className="py-3 pr-4 text-stone-500">{tc.eval_type}</td>
                  <td className="py-3 text-stone-500 truncate max-w-xs">{tc.expected_output ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
