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

  if (loading) return <div className="text-muted">Loading...</div>;

  const versions = versionHistory.map((v) => v.version);
  const latestVersion = versions[0];
  const previousVersion = versions[1];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{name}</h1>
        {latestVersion && previousVersion && (
          <Link
            to={`/compare/${name}?v1=${previousVersion}&v2=${latestVersion}`}
            className="text-sm text-accent hover:underline"
          >
            Compare {previousVersion} vs {latestVersion}
          </Link>
        )}
      </div>

      <Card title="Version History">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-muted border-b border-border">
              <th className="pb-2 pr-4">Version</th>
              <th className="pb-2 pr-4">Total</th>
              <th className="pb-2 pr-4">Passed</th>
              <th className="pb-2">Pass Rate</th>
            </tr>
          </thead>
          <tbody>
            {versionHistory.map((v) => (
              <tr key={v.version} className="border-b border-border/50">
                <td className="py-2 pr-4 font-medium">{v.version}</td>
                <td className="py-2 pr-4 text-muted">{v.total}</td>
                <td className="py-2 pr-4 text-muted">{v.passed}</td>
                <td className="py-2">
                  <span
                    className={`font-medium ${
                      v.pass_rate >= 0.9
                        ? "text-success"
                        : v.pass_rate >= 0.6
                        ? "text-warning"
                        : "text-danger"
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
          <p className="text-muted text-sm">No test cases registered for this suite.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted border-b border-border">
                <th className="pb-2 pr-4">ID</th>
                <th className="pb-2 pr-4">Eval Type</th>
                <th className="pb-2">Expected Output</th>
              </tr>
            </thead>
            <tbody>
              {testCases.map((tc) => (
                <tr key={tc.id} className="border-b border-border/50">
                  <td className="py-2 pr-4 font-mono text-xs">{tc.test_case_id}</td>
                  <td className="py-2 pr-4 text-muted">{tc.eval_type}</td>
                  <td className="py-2 text-muted truncate max-w-xs">{tc.expected_output ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
