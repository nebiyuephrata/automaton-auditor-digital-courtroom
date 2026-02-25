export function App() {
  return (
    <main className="shell">
      <header>
        <p className="kicker">Automaton Auditor</p>
        <h1>Digital Courtroom Console</h1>
      </header>

      <section className="panel">
        <h2>Audit Input</h2>
        <form className="grid">
          <label>
            Repository URL
            <input placeholder="https://github.com/org/repo.git" />
          </label>
          <label>
            PDF Path
            <input placeholder="reports/final_report.pdf" />
          </label>
          <label>
            Rubric Path
            <input placeholder="rubric.json" defaultValue="rubric.json" />
          </label>
          <button type="button">Run Audit</button>
        </form>
      </section>

      <section className="panel">
        <h2>Output</h2>
        <p>Frontend scaffold created. API wiring to CLI/graph runner is next.</p>
      </section>
    </main>
  );
}
