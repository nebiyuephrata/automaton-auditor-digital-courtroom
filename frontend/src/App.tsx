import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type AuditResponse = {
  run_id: string;
  rendered_markdown: string;
  final_report?: Record<string, unknown>;
  errors?: string[];
};

type AuditRecord = {
  run_id: string;
  created_at: string;
  repo_url: string;
  pdf_path: string;
  rubric_path: string;
  output_path?: string;
  status: string;
  overall_score?: number;
  errors: string[];
};

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [pdfPath, setPdfPath] = useState("reports/final_report.pdf");
  const [rubricPath, setRubricPath] = useState("rubric.json");
  const [outputPath, setOutputPath] = useState("audit/report_onself_generated/final_audit_report.md");

  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AuditResponse | null>(null);
  const [history, setHistory] = useState<AuditRecord[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  const pollTimerRef = useRef<number | null>(null);

  const reportJson = useMemo(() => {
    if (!result?.final_report) {
      return "";
    }
    return JSON.stringify(result.final_report, null, 2);
  }, [result]);

  async function loadHistory() {
    setHistoryLoading(true);
    try {
      const response = await fetch(`${apiBase}/api/audits`);
      if (!response.ok) {
        throw new Error(`Failed to load history (${response.status})`);
      }
      const payload = (await response.json()) as AuditRecord[];
      setHistory(payload);
    } catch (historyError) {
      setError(historyError instanceof Error ? historyError.message : "Failed to load history");
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    void loadHistory();
    return () => {
      if (pollTimerRef.current !== null) {
        window.clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  async function loadRunResult(runId: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/api/audits/${runId}/result`);
      if (!response.ok) {
        throw new Error(`Failed to load run result (${response.status})`);
      }
      const payload = (await response.json()) as AuditResponse;
      setResult(payload);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function trackRunUntilTerminal(runId: string) {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
    }

    pollTimerRef.current = window.setInterval(async () => {
      try {
        const response = await fetch(`${apiBase}/api/audits/${runId}`);
        if (!response.ok) {
          throw new Error(`Failed to poll run (${response.status})`);
        }
        const record = (await response.json()) as AuditRecord;
        await loadHistory();

        if (record.status === "completed" || record.status === "failed") {
          if (pollTimerRef.current !== null) {
            window.clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
          setActiveRunId(null);
          await loadRunResult(runId);
        }
      } catch (pollError) {
        if (pollTimerRef.current !== null) {
          window.clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
        }
        setActiveRunId(null);
        setError(pollError instanceof Error ? pollError.message : "Polling failed");
      }
    }, 1500);
  }

  async function onRunAudit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${apiBase}/api/audits/run-async`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_url: repoUrl,
          pdf_path: pdfPath,
          rubric_path: rubricPath,
          output_path: outputPath
        })
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(`API ${response.status}: ${body}`);
      }

      const payload = (await response.json()) as AuditRecord;
      setActiveRunId(payload.run_id);
      await loadHistory();
      await trackRunUntilTerminal(payload.run_id);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header>
        <p className="kicker">Automaton Auditor</p>
        <h1>Digital Courtroom Console</h1>
      </header>

      <section className="panel">
        <h2>Audit Input</h2>
        <form className="grid" onSubmit={onRunAudit}>
          <label>
            Repository URL
            <input
              required
              value={repoUrl}
              onChange={(event) => setRepoUrl(event.target.value)}
              placeholder="https://github.com/org/repo.git"
            />
          </label>
          <label>
            PDF Path
            <input
              required
              value={pdfPath}
              onChange={(event) => setPdfPath(event.target.value)}
              placeholder="reports/final_report.pdf"
            />
          </label>
          <label>
            Rubric Path
            <input
              required
              value={rubricPath}
              onChange={(event) => setRubricPath(event.target.value)}
              placeholder="rubric.json"
            />
          </label>
          <label>
            Output Path
            <input
              required
              value={outputPath}
              onChange={(event) => setOutputPath(event.target.value)}
              placeholder="audit/report_onself_generated/final_audit_report.md"
            />
          </label>
          <button type="submit" disabled={loading || activeRunId !== null}>
            {activeRunId ? "Audit Running..." : loading ? "Submitting..." : "Run Audit"}
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Audit History</h2>
        {historyLoading && <p>Loading history...</p>}
        {!historyLoading && history.length === 0 && <p>No runs yet.</p>}
        {history.length > 0 && (
          <div className="historyList">
            {history.map((item) => (
              <button
                type="button"
                key={item.run_id}
                className="historyItem"
                onClick={() => void loadRunResult(item.run_id)}
              >
                <strong>{item.status.toUpperCase()}</strong>
                <span>{item.repo_url}</span>
                <span>{new Date(item.created_at).toLocaleString()}</span>
                <span>Score: {item.overall_score ?? "N/A"}</span>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Output</h2>
        {error && <p className="error">{error}</p>}
        {!error && activeRunId && <p>Run {activeRunId} is in progress. Polling status...</p>}
        {!error && !activeRunId && !result && <p>No audit run selected.</p>}
        {result && (
          <>
            <p>
              <strong>Run ID:</strong> {result.run_id}
            </p>
            {result.errors && result.errors.length > 0 && (
              <div>
                <h3>Execution Errors</h3>
                <ul>
                  {result.errors.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            <h3>Markdown Report</h3>
            <pre className="output">{result.rendered_markdown}</pre>
            {reportJson && (
              <>
                <h3>Structured Report JSON</h3>
                <pre className="output">{reportJson}</pre>
              </>
            )}
          </>
        )}
      </section>
    </main>
  );
}
