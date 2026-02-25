import { FormEvent, useMemo, useState } from "react";

type AuditResponse = {
  rendered_markdown: string;
  final_report?: Record<string, unknown>;
  errors?: string[];
};

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [pdfPath, setPdfPath] = useState("reports/final_report.pdf");
  const [rubricPath, setRubricPath] = useState("rubric.json");
  const [outputPath, setOutputPath] = useState("audit/report_onself_generated/final_audit_report.md");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AuditResponse | null>(null);

  const reportJson = useMemo(() => {
    if (!result?.final_report) {
      return "";
    }
    return JSON.stringify(result.final_report, null, 2);
  }, [result]);

  async function onRunAudit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBase}/api/audits/run`, {
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

      const payload = (await response.json()) as AuditResponse;
      setResult(payload);
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
          <button type="submit" disabled={loading}>
            {loading ? "Running..." : "Run Audit"}
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Output</h2>
        {error && <p className="error">{error}</p>}
        {!error && !result && <p>No audit run yet.</p>}
        {result && (
          <>
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
