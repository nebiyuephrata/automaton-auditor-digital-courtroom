import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type RuntimeConfig = {
  judge_provider: string;
  judge_model: string;
  vision_provider: string;
  vision_model: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
  openrouter_api_key?: string;
  openrouter_base_url?: string;
  ollama_base_url?: string;
};

type AuditResponse = {
  run_id: string;
  rendered_markdown: string;
  final_report?: FinalReport;
  errors?: string[];
};

type JudicialOpinionView = {
  judge: string;
  score: number;
  argument: string;
  cited_evidence: string[];
};

type CriterionResultView = {
  dimension_id: string;
  dimension_name: string;
  final_score: number;
  judge_opinions: JudicialOpinionView[];
  dissent_summary?: string | null;
  remediation: string;
  recommended_changes?: string[];
  detailed_improvements?: {
    priority: "P0" | "P1" | "P2";
    action: string;
    rationale: string;
    target_files: string[];
  }[];
};

type FinalReport = {
  repo_url: string;
  executive_summary: string;
  overall_score: number;
  governance_maturity: string;
  governance_maturity_rationale: string;
  criteria: CriterionResultView[];
  remediation_plan: string;
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

type RubricPreset = {
  id: string;
  name: string;
  description: string;
  path: string;
  framework: string;
  standard: string;
};

type RuntimeOptions = {
  judge_providers: string[];
  vision_providers: string[];
  default_models: Record<string, string>;
  default_judge_provider: string;
  default_vision_provider: string;
  rubric_presets: RubricPreset[];
};

type Locale = "en" | "am";
type ThemeMode = "light" | "dark";
type ModelTarget = "judge" | "vision";
type CredentialMode = "env" | "openai" | "anthropic" | "openrouter" | "ollama";

type Translation = {
  appTitle: string;
  appKicker: string;
  mode: string;
  language: string;
  english: string;
  amharic: string;
  darkMode: string;
  lightMode: string;
  auditInput: string;
  repositoryUrl: string;
  pdfPath: string;
  useDefaultRubric: string;
  rubricPreset: string;
  rubricPath: string;
  outputPath: string;
  runtimeSettings: string;
  judgeProvider: string;
  judgeModel: string;
  visionProvider: string;
  visionModel: string;
  openaiKey: string;
  credentialSource: string;
  credentialValue: string;
  credentialFromEnv: string;
  credentialOpenAI: string;
  credentialAnthropic: string;
  credentialOpenRouter: string;
  credentialOllama: string;
  credentialKeyPlaceholder: string;
  credentialUrlPlaceholder: string;
  runAudit: string;
  submitting: string;
  running: string;
  cancelRun: string;
  auditHistory: string;
  loadingHistory: string;
  clearHistory: string;
  clearingHistory: string;
  noRunsYet: string;
  score: string;
  output: string;
  noRunSelected: string;
  runInProgress: string;
  loadingProgress: string;
  runId: string;
  executionErrors: string;
  markdownReport: string;
  reportJson: string;
  downloadPdf: string;
  downloadingPdf: string;
  dismiss: string;
  apiUnauthorized: string;
  apiForbidden: string;
  apiRateLimited: string;
  apiUnavailable: string;
  apiConflict: string;
  apiServerError: string;
  apiGenericError: string;
  networkError: string;
  loadRuntimeFailed: string;
  loadHistoryFailed: string;
  clearHistoryFailed: string;
  loadResultFailed: string;
  cancelFailed: string;
  submitFailed: string;
  pollingFailed: string;
};

const copy: Record<Locale, Translation> = {
  en: {
    appTitle: "Digital Courtroom Console",
    appKicker: "Automaton Auditor",
    mode: "Mode",
    language: "Language",
    english: "English",
    amharic: "Amharic",
    darkMode: "Dark",
    lightMode: "Light",
    auditInput: "Audit Input",
    repositoryUrl: "Repository URL",
    pdfPath: "PDF Path",
    useDefaultRubric: "Use default rubric preset",
    rubricPreset: "Rubric Preset",
    rubricPath: "Rubric Path",
    outputPath: "Output Path",
    runtimeSettings: "Runtime LLM Settings",
    judgeProvider: "Judge Provider",
    judgeModel: "Judge Model",
    visionProvider: "Vision Provider",
    visionModel: "Vision Model",
    openaiKey: "Provider Credential",
    credentialSource: "Credential Type",
    credentialValue: "Credential Value",
    credentialFromEnv: "Use Server Env",
    credentialOpenAI: "OpenAI API Key",
    credentialAnthropic: "Anthropic API Key",
    credentialOpenRouter: "OpenRouter API Key",
    credentialOllama: "Ollama Base URL",
    credentialKeyPlaceholder: "Enter API key",
    credentialUrlPlaceholder: "http://localhost:11434",
    runAudit: "Run Audit",
    submitting: "Submitting...",
    running: "Audit Running...",
    cancelRun: "Cancel Active Run",
    auditHistory: "Audit History",
    loadingHistory: "Loading history...",
    clearHistory: "Clear History",
    clearingHistory: "Clearing...",
    noRunsYet: "No runs yet.",
    score: "Score",
    output: "Output",
    noRunSelected: "No audit run selected.",
    runInProgress: "Run is in progress. Polling status...",
    loadingProgress: "Progress",
    runId: "Run ID",
    executionErrors: "Execution Errors",
    markdownReport: "Markdown Report",
    reportJson: "Structured Report JSON",
    downloadPdf: "Download PDF Report",
    downloadingPdf: "Downloading PDF...",
    dismiss: "Dismiss",
    apiUnauthorized: "Authentication failed. Check API key configuration.",
    apiForbidden: "Access denied for this request.",
    apiRateLimited: "Too many requests. Please wait and retry.",
    apiUnavailable: "Service is unavailable. Ensure API auth key is configured.",
    apiConflict: "Run is not complete yet. Please wait for terminal status.",
    apiServerError: "Server error occurred. Check backend logs and retry.",
    apiGenericError: "Request failed.",
    networkError: "Cannot reach API server. Verify backend URL and connectivity.",
    loadRuntimeFailed: "Failed to load runtime options.",
    loadHistoryFailed: "Failed to load audit history.",
    clearHistoryFailed: "Failed to clear audit history.",
    loadResultFailed: "Failed to load audit result.",
    cancelFailed: "Failed to cancel active run.",
    submitFailed: "Failed to submit audit run.",
    pollingFailed: "Failed while polling run status."
  },
  am: {
    appTitle: "ዲጂታል ፍርድ ቤት ኮንሶል",
    appKicker: "አውቶማቶን ኦዲተር",
    mode: "ሞድ",
    language: "ቋንቋ",
    english: "እንግሊዝኛ",
    amharic: "አማርኛ",
    darkMode: "ጨለማ",
    lightMode: "ብርሃን",
    auditInput: "የኦዲት ግቤት",
    repositoryUrl: "የሪፖዚቶሪ URL",
    pdfPath: "የPDF መንገድ",
    useDefaultRubric: "ነባሪ ሩብሪክ ይጠቀሙ",
    rubricPreset: "የሩብሪክ ቅድመ-ቅንብር",
    rubricPath: "የሩብሪክ መንገድ",
    outputPath: "የውጤት መንገድ",
    runtimeSettings: "የLLM አሂድ ቅንብሮች",
    judgeProvider: "የዳኛ ፕሮቫይደር",
    judgeModel: "የዳኛ ሞዴል",
    visionProvider: "የራዕይ ፕሮቫይደር",
    visionModel: "የራዕይ ሞዴል",
    openaiKey: "የፕሮቫይደር ምስጢር",
    credentialSource: "የምስጢር አይነት",
    credentialValue: "የምስጢር ዋጋ",
    credentialFromEnv: "የሰርቨር Env ተጠቀም",
    credentialOpenAI: "OpenAI API ቁልፍ",
    credentialAnthropic: "Anthropic API ቁልፍ",
    credentialOpenRouter: "OpenRouter API ቁልፍ",
    credentialOllama: "Ollama Base URL",
    credentialKeyPlaceholder: "API ቁልፍ ያስገቡ",
    credentialUrlPlaceholder: "http://localhost:11434",
    runAudit: "ኦዲት አስኪድ",
    submitting: "በመላክ ላይ...",
    running: "ኦዲት በመስራት ላይ...",
    cancelRun: "እየሄደ ያለውን አቁም",
    auditHistory: "የኦዲት ታሪክ",
    loadingHistory: "ታሪክ በመጫን ላይ...",
    clearHistory: "ታሪክ አጥፋ",
    clearingHistory: "በማጥፋት ላይ...",
    noRunsYet: "እስካሁን ሩጫ የለም።",
    score: "ውጤት",
    output: "ውጤት",
    noRunSelected: "የተመረጠ ኦዲት የለም።",
    runInProgress: "ሩጫ በሂደት ላይ ነው። ሁኔታ እየተመረመረ ነው...",
    loadingProgress: "ሂደት",
    runId: "የሩጫ መለያ",
    executionErrors: "የአስኬድ ስህተቶች",
    markdownReport: "ማርክዳውን ሪፖርት",
    reportJson: "የተዋቀረ JSON ሪፖርት",
    downloadPdf: "PDF ሪፖርት አውርድ",
    downloadingPdf: "PDF በማውረድ ላይ...",
    dismiss: "ዝጋ",
    apiUnauthorized: "ማረጋገጫ አልተሳካም። API key ያረጋግጡ።",
    apiForbidden: "ይህን ጥያቄ ለማድረግ ፍቃድ የለዎትም።",
    apiRateLimited: "ብዙ ጥያቄዎች ተልከዋል። ትንሽ ጊዜ ጠብቀው ይሞክሩ።",
    apiUnavailable: "አገልግሎቱ አልተገኘም። API_AUTH_KEY ተዘጋጅቶ እንዳለ ያረጋግጡ።",
    apiConflict: "ሩጫው ገና አልጨረሰም። የመጨረሻ ሁኔታ ይጠብቁ።",
    apiServerError: "የሰርቨር ስህተት ተከስቷል። የbackend ሎግ ይመልከቱ።",
    apiGenericError: "ጥያቄው አልተሳካም።",
    networkError: "API ሰርቨር አልተደረሰበትም። URL እና ግንኙነት ያረጋግጡ።",
    loadRuntimeFailed: "የruntime አማራጮችን መጫን አልተሳካም።",
    loadHistoryFailed: "የኦዲት ታሪክን መጫን አልተሳካም።",
    clearHistoryFailed: "የኦዲት ታሪክ ማጥፋት አልተሳካም።",
    loadResultFailed: "የኦዲት ውጤትን መጫን አልተሳካም።",
    cancelFailed: "እየሄደ ያለውን ሩጫ ማቆም አልተሳካም።",
    submitFailed: "ኦዲት ማስጀመር አልተሳካም።",
    pollingFailed: "ሁኔታ ሲመረመር ስህተት ተፈጠረ።"
  }
};

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const apiKey = import.meta.env.VITE_API_KEY ?? "change-me";

const providerModelCatalog: Record<ModelTarget, Record<string, string[]>> = {
  judge: {
    openai: ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
    anthropic: ["claude-3-5-sonnet-latest", "claude-3-7-sonnet-latest"],
    openrouter: ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-001"],
    ollama: ["llama3.1", "llama3.1:latest", "llama3.2", "mistral", "qwen2.5"]
  },
  vision: {
    openai: ["gpt-4o-mini", "gpt-4o"],
    anthropic: ["claude-3-5-sonnet-latest", "claude-3-7-sonnet-latest"],
    openrouter: ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-001"],
    ollama: ["llama3.1", "llama3.2", "llava"]
  }
};

function modelOptionsFor(
  target: ModelTarget,
  provider: string,
  defaultModel?: string,
  currentModel?: string
): string[] {
  const configured = providerModelCatalog[target][provider] ?? [];
  const merged = [defaultModel ?? "", currentModel ?? "", ...configured].filter(Boolean);
  return Array.from(new Set(merged));
}

async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers ?? {});
  headers.set("x-api-key", apiKey);
  if (!headers.has("Content-Type") && init.method && init.method !== "GET") {
    headers.set("Content-Type", "application/json");
  }
  return fetch(`${apiBase}${path}`, { ...init, headers });
}

async function readErrorDetail(response: Response): Promise<string> {
  const text = await response.text();
  if (!text) {
    return "";
  }
  try {
    const payload = JSON.parse(text) as { detail?: string };
    return payload.detail ?? text;
  } catch {
    return text;
  }
}

function mapApiError(t: Translation, status: number, detail: string): string {
  if (status === 401) return t.apiUnauthorized;
  if (status === 403) return t.apiForbidden;
  if (status === 409) return t.apiConflict;
  if (status === 429) return t.apiRateLimited;
  if (status === 503) return t.apiUnavailable;
  if (status >= 500) return t.apiServerError;
  return `${t.apiGenericError} (${status})${detail ? `: ${detail}` : ""}`;
}

function mapUnknownError(t: Translation, fallback: string, error: unknown): string {
  if (error instanceof TypeError) {
    return t.networkError;
  }
  if (error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}

function runtimeCredentialPayload(
  mode: CredentialMode,
  value: string
): Pick<
  RuntimeConfig,
  "openai_api_key" | "anthropic_api_key" | "openrouter_api_key" | "openrouter_base_url" | "ollama_base_url"
> {
  const trimmed = value.trim();
  if (!trimmed || mode === "env") {
    return {};
  }
  if (mode === "openai") {
    return { openai_api_key: trimmed };
  }
  if (mode === "anthropic") {
    return { anthropic_api_key: trimmed };
  }
  if (mode === "openrouter") {
    return { openrouter_api_key: trimmed };
  }
  return { ollama_base_url: trimmed };
}

function progressFromStatus(status: string): number {
  if (status === "queued") return 25;
  if (status === "running") return 70;
  if (status === "cancel_requested") return 85;
  if (["completed", "failed", "canceled"].includes(status)) return 100;
  return 10;
}

export function App() {
  const [locale, setLocale] = useState<Locale>(() =>
    (localStorage.getItem("ui_locale") as Locale) || "en"
  );
  const [theme, setTheme] = useState<ThemeMode>(() =>
    (localStorage.getItem("ui_theme") as ThemeMode) || "light"
  );

  const [repoUrl, setRepoUrl] = useState("");
  const [pdfPath, setPdfPath] = useState("reports/final_report.pdf");
  const [rubricPath, setRubricPath] = useState("rubric.json");
  const [rubricPreset, setRubricPreset] = useState("industry_iso_soc2");
  const [useRubricPreset, setUseRubricPreset] = useState(true);
  const [outputPath, setOutputPath] = useState("audit/report_onself_generated/final_audit_report.md");

  const [judgeProvider, setJudgeProvider] = useState("ollama");
  const [judgeModel, setJudgeModel] = useState("gpt-4o-mini");
  const [visionProvider, setVisionProvider] = useState("ollama");
  const [visionModel, setVisionModel] = useState("gpt-4o-mini");
  const [credentialMode, setCredentialMode] = useState<CredentialMode>("env");
  const [credentialValue, setCredentialValue] = useState("");

  const [runtimeOptions, setRuntimeOptions] = useState<RuntimeOptions | null>(null);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [clearingHistory, setClearingHistory] = useState(false);
  const [pdfDownloading, setPdfDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AuditResponse | null>(null);
  const [history, setHistory] = useState<AuditRecord[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runProgress, setRunProgress] = useState(0);
  const [runStatusText, setRunStatusText] = useState("");

  const pollTimerRef = useRef<number | null>(null);
  const t = copy[locale];

  const reportJson = useMemo(() => {
    if (!result?.final_report) {
      return "";
    }
    return JSON.stringify(result.final_report, null, 2);
  }, [result]);

  const criterionBreakdown = useMemo(
    () => result?.final_report?.criteria ?? [],
    [result]
  );

  const judgeModelOptions = useMemo(
    () =>
      modelOptionsFor(
        "judge",
        judgeProvider,
        runtimeOptions?.default_models[judgeProvider],
        judgeModel
      ),
    [judgeProvider, judgeModel, runtimeOptions]
  );

  const visionModelOptions = useMemo(
    () =>
      modelOptionsFor(
        "vision",
        visionProvider,
        runtimeOptions?.default_models[visionProvider],
        visionModel
      ),
    [visionProvider, visionModel, runtimeOptions]
  );

  useEffect(() => {
    localStorage.setItem("ui_locale", locale);
  }, [locale]);

  useEffect(() => {
    localStorage.setItem("ui_theme", theme);
    document.body.dataset.theme = theme;
  }, [theme]);

  async function loadRuntimeOptions() {
    try {
      const response = await apiFetch("/api/runtime/options");
      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(mapApiError(t, response.status, detail));
      }
      const payload = (await response.json()) as RuntimeOptions;
      setRuntimeOptions(payload);

      const defaultJudgeProvider = payload.default_judge_provider || "ollama";
      const defaultVisionProvider = payload.default_vision_provider || "ollama";
      setJudgeProvider(defaultJudgeProvider);
      setVisionProvider(defaultVisionProvider);
      setJudgeModel(payload.default_models[defaultJudgeProvider] ?? "llama3.1");
      setVisionModel(payload.default_models[defaultVisionProvider] ?? "llama3.1");
      if (payload.rubric_presets.length > 0) {
        setRubricPreset(payload.rubric_presets[0].id);
      }
    } catch (runtimeError) {
      setError(mapUnknownError(t, t.loadRuntimeFailed, runtimeError));
    }
  }

  async function loadHistory() {
    setHistoryLoading(true);
    try {
      const response = await apiFetch(`/api/audits`);
      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(mapApiError(t, response.status, detail));
      }
      const payload = (await response.json()) as AuditRecord[];
      setHistory(payload);
    } catch (historyError) {
      setError(mapUnknownError(t, t.loadHistoryFailed, historyError));
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    void loadRuntimeOptions();
    void loadHistory();
    return () => {
      if (pollTimerRef.current !== null) {
        window.clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!runtimeOptions) {
      return;
    }
    const defaultModel = runtimeOptions.default_models[judgeProvider] ?? "gpt-4o-mini";
    setJudgeModel(defaultModel);
  }, [judgeProvider, runtimeOptions]);

  useEffect(() => {
    if (!runtimeOptions) {
      return;
    }
    const defaultModel = runtimeOptions.default_models[visionProvider] ?? "gpt-4o-mini";
    setVisionModel(defaultModel);
  }, [visionProvider, runtimeOptions]);

  async function loadRunResult(runId: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch(`/api/audits/${runId}/result`);
      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(mapApiError(t, response.status, detail));
      }
      const payload = (await response.json()) as AuditResponse;
      setResult(payload);
    } catch (runError) {
      setError(mapUnknownError(t, t.loadResultFailed, runError));
    } finally {
      setLoading(false);
    }
  }

  async function cancelActiveRun() {
    if (!activeRunId) {
      return;
    }
    try {
      const response = await apiFetch(`/api/audits/${activeRunId}/cancel`, { method: "POST" });
      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(mapApiError(t, response.status, detail));
      }
      await loadHistory();
    } catch (cancelError) {
      setError(mapUnknownError(t, t.cancelFailed, cancelError));
    }
  }

  async function trackRunUntilTerminal(runId: string) {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
    }

    pollTimerRef.current = window.setInterval(async () => {
      try {
        const response = await apiFetch(`/api/audits/${runId}`);
        if (!response.ok) {
          const detail = await readErrorDetail(response);
          throw new Error(mapApiError(t, response.status, detail));
        }
        const record = (await response.json()) as AuditRecord;
        setRunStatusText(record.status);
        setRunProgress(progressFromStatus(record.status));

        if (["completed", "failed", "canceled"].includes(record.status)) {
          if (pollTimerRef.current !== null) {
            window.clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
          setActiveRunId(null);
          await loadHistory();
          if (record.status !== "canceled") {
            await loadRunResult(runId);
          }
        }
      } catch (pollError) {
        if (pollTimerRef.current !== null) {
          window.clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
        }
        setActiveRunId(null);
        setRunStatusText("");
        setError(mapUnknownError(t, t.pollingFailed, pollError));
      }
    }, 3000);
  }

  async function clearHistory() {
    setClearingHistory(true);
    setError(null);
    try {
      const response = await apiFetch("/api/audits", { method: "DELETE" });
      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(mapApiError(t, response.status, detail));
      }
      await loadHistory();
      setResult(null);
    } catch (clearError) {
      setError(mapUnknownError(t, t.clearHistoryFailed, clearError));
    } finally {
      setClearingHistory(false);
    }
  }

  async function onRunAudit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setRunProgress(10);
    setRunStatusText("submitting");
    const runtimeConfig: RuntimeConfig = {
      judge_provider: judgeProvider,
      judge_model: judgeModel,
      vision_provider: visionProvider,
      vision_model: visionModel,
      ...runtimeCredentialPayload(credentialMode, credentialValue)
    };

    try {
      const response = await apiFetch(`/api/audits/run-async`, {
        method: "POST",
        body: JSON.stringify({
          repo_url: repoUrl,
          pdf_path: pdfPath,
          rubric_path: useRubricPreset ? "" : rubricPath,
          rubric_preset: useRubricPreset ? rubricPreset : undefined,
          runtime_config: runtimeConfig,
          output_path: outputPath
        })
      });

      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(mapApiError(t, response.status, detail));
      }

      const payload = (await response.json()) as AuditRecord;
      setActiveRunId(payload.run_id);
      setRunStatusText(payload.status);
      setRunProgress(progressFromStatus(payload.status));
      await loadHistory();
      await trackRunUntilTerminal(payload.run_id);
    } catch (runError) {
      setRunStatusText("");
      setError(mapUnknownError(t, t.submitFailed, runError));
    } finally {
      setLoading(false);
    }
  }

  async function onDownloadPdf(runId: string) {
    setPdfDownloading(true);
    setError(null);
    try {
      const response = await apiFetch(`/api/audits/${runId}/report-pdf`);
      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(mapApiError(t, response.status, detail));
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `audit-report-${runId}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
    } catch (downloadError) {
      setError(mapUnknownError(t, t.loadResultFailed, downloadError));
    } finally {
      setPdfDownloading(false);
    }
  }

  return (
    <main className={`shell theme-${theme}`}>
      <header className="headerTop">
        <div>
          <p className="kicker">{t.appKicker}</p>
          <h1>{t.appTitle}</h1>
        </div>
        <div className="controlsBar">
          <label>
            {t.language}
            <select value={locale} onChange={(event) => setLocale(event.target.value as Locale)}>
              <option value="en">{t.english}</option>
              <option value="am">{t.amharic}</option>
            </select>
          </label>
          <button
            type="button"
            className="secondary"
            onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}
          >
            {t.mode}: {theme === "light" ? t.lightMode : t.darkMode}
          </button>
        </div>
      </header>

      <section className="panel">
        <h2>{t.auditInput}</h2>
        <form className="grid" onSubmit={onRunAudit}>
          <label>
            {t.repositoryUrl}
            <input
              required
              value={repoUrl}
              onChange={(event) => setRepoUrl(event.target.value)}
              placeholder="https://github.com/org/repo.git"
            />
          </label>
          <label>
            {t.pdfPath}
            <input
              required
              value={pdfPath}
              onChange={(event) => setPdfPath(event.target.value)}
              placeholder="reports/final_report.pdf"
            />
          </label>
          <div className="inlineToggle">
            <label>
              <input
                type="checkbox"
                checked={useRubricPreset}
                onChange={(event) => setUseRubricPreset(event.target.checked)}
              />
              {t.useDefaultRubric}
            </label>
          </div>
          {useRubricPreset ? (
            <label>
              {t.rubricPreset}
              <select value={rubricPreset} onChange={(event) => setRubricPreset(event.target.value)}>
                {(runtimeOptions?.rubric_presets ?? []).map((preset) => (
                  <option key={preset.id} value={preset.id}>
                    {preset.name} ({preset.framework})
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <label>
              {t.rubricPath}
              <input
                required
                value={rubricPath}
                onChange={(event) => setRubricPath(event.target.value)}
                placeholder="rubric.json"
              />
            </label>
          )}
          <label>
            {t.outputPath}
            <input
              required
              value={outputPath}
              onChange={(event) => setOutputPath(event.target.value)}
              placeholder="audit/report_onself_generated/final_audit_report.md"
            />
          </label>

          <h3>{t.runtimeSettings}</h3>
          <label>
            {t.judgeProvider}
            <select value={judgeProvider} onChange={(event) => setJudgeProvider(event.target.value)}>
              {(runtimeOptions?.judge_providers ?? ["openai", "anthropic", "openrouter", "ollama"]).map((provider) => (
                <option key={provider} value={provider}>
                  {provider}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t.judgeModel}
            <select
              value={judgeModel}
              onChange={(event) => setJudgeModel(event.target.value)}
            >
              {judgeModelOptions.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t.visionProvider}
            <select value={visionProvider} onChange={(event) => setVisionProvider(event.target.value)}>
              {(runtimeOptions?.vision_providers ?? ["openai", "anthropic", "openrouter", "ollama"]).map((provider) => (
                <option key={provider} value={provider}>
                  {provider}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t.visionModel}
            <select
              value={visionModel}
              onChange={(event) => setVisionModel(event.target.value)}
            >
              {visionModelOptions.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t.credentialSource}
            <select
              value={credentialMode}
              onChange={(event) => setCredentialMode(event.target.value as CredentialMode)}
            >
              <option value="env">{t.credentialFromEnv}</option>
              <option value="openai">{t.credentialOpenAI}</option>
              <option value="anthropic">{t.credentialAnthropic}</option>
              <option value="openrouter">{t.credentialOpenRouter}</option>
              <option value="ollama">{t.credentialOllama}</option>
            </select>
          </label>
          <label>
            {t.credentialValue}
            <input
              type={credentialMode === "ollama" || credentialMode === "env" ? "text" : "password"}
              value={credentialValue}
              onChange={(event) => setCredentialValue(event.target.value)}
              placeholder={
                credentialMode === "ollama" ? t.credentialUrlPlaceholder : t.credentialKeyPlaceholder
              }
              disabled={credentialMode === "env"}
            />
          </label>

          <div className="actions">
            <button type="submit" disabled={loading || activeRunId !== null}>
              {activeRunId ? t.running : loading ? t.submitting : t.runAudit}
            </button>
            <button type="button" className="secondary" onClick={() => void cancelActiveRun()} disabled={!activeRunId}>
              {t.cancelRun}
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        <h2>{t.auditHistory}</h2>
        <div className="actions">
          <button
            type="button"
            className="secondary"
            onClick={() => void clearHistory()}
            disabled={historyLoading || clearingHistory}
          >
            {clearingHistory ? t.clearingHistory : t.clearHistory}
          </button>
        </div>
        {historyLoading && <p>{t.loadingHistory}</p>}
        {!historyLoading && history.length === 0 && <p>{t.noRunsYet}</p>}
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
                <span>{t.score}: {item.overall_score ?? "N/A"}</span>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <h2>{t.output}</h2>
        {error && (
          <div className="errorBanner">
            <span>{error}</span>
            <button type="button" className="secondary" onClick={() => setError(null)}>
              {t.dismiss}
            </button>
          </div>
        )}
        {!error && activeRunId && <p>{t.runInProgress}</p>}
        {!error && activeRunId && (
          <div className="runLoader">
            <div className="spinner" aria-hidden="true" />
            <div className="progressMeta">
              <div>
                {t.loadingProgress}: {runProgress}% {runStatusText ? `(${runStatusText})` : ""}
              </div>
              <div className="progressBar">
                <div className="progressFill" style={{ width: `${runProgress}%` }} />
              </div>
            </div>
          </div>
        )}
        {!error && !activeRunId && !result && <p>{t.noRunSelected}</p>}
        {result && (
          <>
            <p>
              <strong>{t.runId}:</strong> {result.run_id}
            </p>
            <button
              type="button"
              className="secondary"
              onClick={() => void onDownloadPdf(result.run_id)}
              disabled={pdfDownloading}
            >
              {pdfDownloading ? t.downloadingPdf : t.downloadPdf}
            </button>
            {criterionBreakdown.length > 0 && (
              <div>
                <h3>Rubric Scores</h3>
                {criterionBreakdown.map((criterion) => (
                  <div key={criterion.dimension_id} className="criterionCard">
                    <p>
                      <strong>
                        {criterion.dimension_name} ({criterion.dimension_id})
                      </strong>
                    </p>
                    <p>
                      <strong>{t.score}:</strong> {criterion.final_score}/5
                    </p>
                    <ul>
                      {criterion.judge_opinions.map((opinion) => (
                        <li key={`${criterion.dimension_id}-${opinion.judge}`}>
                          {opinion.judge}: {opinion.score}/5 - {opinion.argument}
                        </li>
                      ))}
                    </ul>
                    {criterion.dissent_summary && <p>{criterion.dissent_summary}</p>}
                    <p>
                      <strong>Recommendation:</strong> {criterion.remediation}
                    </p>
                    {criterion.recommended_changes && criterion.recommended_changes.length > 0 && (
                      <>
                        <p>
                          <strong>File Changes:</strong>
                        </p>
                        <ul>
                          {criterion.recommended_changes.map((item) => (
                            <li key={`${criterion.dimension_id}-${item}`}>{item}</li>
                          ))}
                        </ul>
                      </>
                    )}
                    {criterion.detailed_improvements && criterion.detailed_improvements.length > 0 && (
                      <>
                        <p>
                          <strong>Detailed Improvements:</strong>
                        </p>
                        <ul>
                          {criterion.detailed_improvements.map((item, idx) => (
                            <li key={`${criterion.dimension_id}-detail-${idx}`}>
                              [{item.priority}] {item.action} - {item.rationale}
                              {item.target_files.length > 0 ? ` (Targets: ${item.target_files.join(", ")})` : ""}
                            </li>
                          ))}
                        </ul>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
            {result.errors && result.errors.length > 0 && (
              <div>
                <h3>{t.executionErrors}</h3>
                <ul>
                  {result.errors.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            <h3>{t.markdownReport}</h3>
            <pre className="output">{result.rendered_markdown}</pre>
            {reportJson && (
              <>
                <h3>{t.reportJson}</h3>
                <pre className="output">{reportJson}</pre>
              </>
            )}
          </>
        )}
      </section>
    </main>
  );
}
