import React, { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  Brain,
  CalendarClock,
  Database,
  GitCompare,
  RefreshCw,
  Search,
  Send,
  Server,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

const DEFAULT_PAYLOAD = {
  environment: "prod",
  event_id: "demo-web-400-bad-request",
  exception: {
    values: [
      {
        module: "Microsoft.PowerShell.Commands.Utility",
        type: "demo-agency-pd:cad - WebException",
        value: "The remote server returned an error: (400) Bad Request.",
      },
    ],
  },
  extra: {
    endpoint: "redacted",
    logging_db: "redacted",
    logging_schema: "redacted",
    logging_server: "redacted",
    main_db: "redacted",
    main_server: "redacted",
    query: "redacted",
    query_results_count: 0,
  },
  fingerprint: [
    "demo-agency-pd",
    "cad",
    "WebException",
    "The remote server returned an error: (400) Bad Request.",
  ],
  host: "redacted",
  platform: "other",
  sdk: {
    name: "CommunityConnect-DataDog",
    version: "1.0",
  },
  server_name: "redacted",
  service: "cc-integrations",
  stacktrace: {
    frames: [
      {
        abs_path: "redacted",
        colno: 3,
        context_line: "redacted",
        filename: "redacted",
        lineno: 154,
        post_context: ["redacted"],
        pre_context: ["redacted"],
      },
    ],
  },
  status: "error",
  tags: {
    APIUser: "demo-agency-pd",
    Interface: "cad",
    app: "CommunityConnect",
    businessUnit: "CommunityConnect",
    country: "usa",
    env: "prod",
    owner: "deployment-engineers",
    team: "deployment-engineers",
  },
  timestamp: "2026-06-17T15:56:05.000Z",
  logger: "powershell",
  error: {
    type: "WebException",
  },
};

function safeJson(value, fallback = null) {
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function formatDate(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

function formatNumber(value, digits = 3) {
  if (typeof value !== "number") return "—";
  return value.toFixed(digits);
}

function getAnalysisBody(analysis) {
  if (!analysis) return {};

  // Supports both shapes:
  // GET /analysis/latest -> { root_cause: { ... } }
  // POST /analyze       -> { root_cause: { ... } } or { analysis: { ... } }
  if (analysis.root_cause && typeof analysis.root_cause === "object") {
    return analysis.root_cause;
  }

  if (analysis.analysis && typeof analysis.analysis === "object") {
    return analysis.analysis;
  }

  if (typeof analysis.root_cause === "string") {
    return {
      root_cause: analysis.root_cause,
    };
  }

  return {};
}

function getSimilarInterface(analysis) {
  if (!analysis) return "—";

  if (analysis.similar_interface_id) return analysis.similar_interface_id;
  if (analysis.similar_event?.interface_id) return analysis.similar_event.interface_id;
  if (analysis.match?.interface_id) return analysis.match.interface_id;
  if (analysis.most_similar_event?.interface_id) return analysis.most_similar_event.interface_id;

  return "—";
}

function getSimilarAnomaly(analysis) {
  if (!analysis) return "—";

  if (analysis.similar_anomaly) return analysis.similar_anomaly;
  if (analysis.similar_event?.anomaly) return analysis.similar_event.anomaly;
  if (analysis.match?.anomaly) return analysis.match.anomaly;
  if (analysis.most_similar_event?.anomaly) return analysis.most_similar_event.anomaly;

  return "—";
}

function normalizeAnalysisPayload(result, fallbackAlert = null) {
  if (!result) return null;

  return {
    ...result,
    interface_id: result.interface_id || fallbackAlert?.interface_id || "—",
    vendor: result.vendor || fallbackAlert?.vendor || "unknown vendor",
    anomaly: result.anomaly || fallbackAlert?.anomaly || "—",
    created_at: result.created_at || result.timestamp || fallbackAlert?.created_at || fallbackAlert?.timestamp || null,
    similar_interface_id: result.similar_interface_id || result.similar_event?.interface_id || result.match?.interface_id || result.most_similar_event?.interface_id,
    similar_anomaly: result.similar_anomaly || result.similar_event?.anomaly || result.match?.anomaly || result.most_similar_event?.anomaly,
  };
}

function StatusPill({ children, tone = "neutral" }) {
  const classes = {
    neutral: "bg-slate-100 text-slate-700 border-slate-200",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    danger: "bg-rose-50 text-rose-700 border-rose-200",
    info: "bg-blue-50 text-blue-700 border-blue-200",
    purple: "bg-purple-50 text-purple-700 border-purple-200",
  };

  return (
    <span
      className={`inline-flex max-w-full items-center rounded-full border px-2.5 py-1 text-xs font-medium sm:px-3 ${classes[tone]}`}
    >
      <span className="truncate">{children}</span>
    </span>
  );
}

function Section({ title, children, icon: Icon }) {
  return (
    <Card className="rounded-2xl border-slate-200 shadow-sm">
      <CardContent className="p-4 sm:p-5">
        <div className="mb-3 flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4 shrink-0 text-slate-600" />}
          <h3 className="min-w-0 truncate text-xs font-semibold uppercase tracking-wide text-slate-600 sm:text-sm">
            {title}
          </h3>
        </div>
        <div className="break-words text-sm leading-6 text-slate-800">{children}</div>
      </CardContent>
    </Card>
  );
}

function MetadataTile({ label, value, icon: Icon }) {
  return (
    <div className="min-w-0 rounded-2xl bg-slate-50 p-4">
      <div className="flex items-center gap-2">
        {Icon && <Icon className="h-4 w-4 shrink-0 text-slate-500" />}
        <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      </div>
      <p className="mt-1 break-words text-sm font-semibold text-slate-900">{value || "—"}</p>
    </div>
  );
}

function AlertCard({ alert, index, isAnalyzing, onAnalyze }) {
  const timestamp = alert.timestamp || alert.created_at;
  const rowsSynced = alert.rows_synced ?? "—";
  const nullRate = typeof alert.null_rate === "number" ? alert.null_rate.toFixed(4) : "—";
  const executionTime = alert.execution_time_ms ?? "—";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 transition hover:border-blue-200 hover:bg-blue-50/30">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <StatusPill tone="neutral">Alert #{index + 1}</StatusPill>
              <StatusPill tone="warning">{alert.anomaly || "alert"}</StatusPill>
            </div>
            <p className="break-words text-sm font-bold text-slate-950">{alert.interface_id || "unknown-interface"}</p>
            <p className="mt-1 break-words text-xs text-slate-500">{alert.vendor || "unknown vendor"}</p>
          </div>

          <Button
            onClick={() => onAnalyze(alert)}
            disabled={isAnalyzing}
            className="h-8 w-full rounded-xl px-3 text-xs sm:w-auto"
          >
            <Search className="mr-2 h-3.5 w-3.5" />
            {isAnalyzing ? "Analyzing..." : "Analyze"}
          </Button>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 sm:grid-cols-4">
          <div className="rounded-xl bg-slate-50 p-2">
            <p className="font-semibold uppercase text-slate-400">Created</p>
            <p className="mt-1 break-words">{formatDate(timestamp)}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-2">
            <p className="font-semibold uppercase text-slate-400">Rows</p>
            <p className="mt-1 break-words">{rowsSynced}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-2">
            <p className="font-semibold uppercase text-slate-400">Null Rate</p>
            <p className="mt-1 break-words">{nullRate}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-2">
            <p className="font-semibold uppercase text-slate-400">Exec ms</p>
            <p className="mt-1 break-words">{executionTime}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function InterfaceHealthMonitorDashboard() {
  const [apiBaseUrl, setApiBaseUrl] = useState(DEFAULT_API_BASE_URL);
  const [analysis, setAnalysis] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [interfaces, setInterfaces] = useState([]);
  const [payloadText, setPayloadText] = useState(JSON.stringify(DEFAULT_PAYLOAD, null, 2));
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [analyzingInterfaceId, setAnalyzingInterfaceId] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const analysisBody = getAnalysisBody(analysis);
  const similarInterface = getSimilarInterface(analysis);
  const similarAnomaly = getSimilarAnomaly(analysis);

  const stats = useMemo(() => {
    const totalEvents = Array.isArray(interfaces) ? interfaces.length : 0;
    const totalAlerts = Array.isArray(alerts) ? alerts.length : 0;
    const latestInterface = analysis?.interface_id || selectedAlert?.interface_id || alerts?.[0]?.interface_id || "—";
    const score = typeof analysis?.similarity_score === "number" ? analysis.similarity_score : null;

    return { totalEvents, totalAlerts, latestInterface, score };
  }, [analysis, selectedAlert, alerts, interfaces]);

  async function fetchJson(path, options = {}) {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`${response.status} ${response.statusText}: ${text}`);
    }

    return response.json();
  }

  async function refreshDashboard() {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const [latestAnalysis, latestAlerts, latestInterfaces] = await Promise.all([
        fetchJson("/analysis/latest"),
        fetchJson("/alerts"),
        fetchJson("/interfaces"),
      ]);

      setAnalysis(latestAnalysis?.message ? null : normalizeAnalysisPayload(latestAnalysis));
      setSelectedAlert(null);
      setAlerts(Array.isArray(latestAlerts) ? latestAlerts : []);
      setInterfaces(Array.isArray(latestInterfaces) ? latestInterfaces : []);
      setMessage("Dashboard refreshed.");
    } catch (err) {
      setError(err.message || "Failed to refresh dashboard.");
    } finally {
      setLoading(false);
    }
  }

  async function ingestPayload() {
    setIngesting(true);
    setError("");
    setMessage("");

    const payload = safeJson(payloadText);
    if (!payload) {
      setError("Payload is not valid JSON.");
      setIngesting(false);
      return;
    }

    try {
      await fetchJson("/ingest/error-log", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setMessage("Payload ingested. Give the consumer a few seconds, then refresh analysis.");
    } catch (err) {
      setError(err.message || "Failed to ingest payload.");
    } finally {
      setIngesting(false);
    }
  }

  async function analyzeInterface(alert) {
    const interfaceId = alert?.interface_id;

    if (!interfaceId) {
      setError("No interface_id was provided for analysis.");
      return;
    }

    setSelectedAlert(alert);
    setAnalyzingInterfaceId(interfaceId);
    setError("");
    setMessage("");

    try {
      const result = await fetchJson(`/analyze?interface_id=${encodeURIComponent(interfaceId)}`, {
        method: "POST",
      });

      setAnalysis(normalizeAnalysisPayload(result, alert));
      setMessage(`Analysis generated for ${interfaceId}.`);
    } catch (err) {
      setError(err.message || `Failed to analyze ${interfaceId}.`);
    } finally {
      setAnalyzingInterfaceId(null);
    }
  }

  useEffect(() => {
    refreshDashboard();
  }, []);

  return (
    <div className="min-h-screen overflow-x-hidden bg-slate-50 px-3 py-4 text-slate-950 sm:px-4 md:p-8">
      <div className="mx-auto w-full max-w-7xl space-y-4 sm:space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:rounded-3xl sm:p-6 md:p-8"
        >
          <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
            <div className="min-w-0">
              <div className="mb-3 inline-flex max-w-full items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                <Sparkles className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">AI-powered incident intelligence</span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
                Interface Health Monitor
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
                Demo dashboard for real-time ingestion, similarity matching, temporal pattern detection,
                and LLM-generated root cause analysis.
              </p>
            </div>

            <div className="flex w-full flex-col gap-2 xl:max-w-md">
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">API Base URL</label>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  value={apiBaseUrl}
                  onChange={(e) => setApiBaseUrl(e.target.value)}
                  className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-100"
                />
                <Button onClick={refreshDashboard} disabled={loading || !!analyzingInterfaceId} className="w-full rounded-2xl sm:w-auto">
                  <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
              </div>
            </div>
          </div>
        </motion.div>

        {(message || error) && (
          <div
            className={`rounded-2xl border p-3 text-sm sm:p-4 ${
              error
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : "border-emerald-200 bg-emerald-50 text-emerald-700"
            }`}
          >
            {error || message}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-4">
          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm text-slate-500">Stored Events</p>
                  <p className="mt-1 text-2xl font-bold sm:text-3xl">{stats.totalEvents}</p>
                </div>
                <Database className="h-7 w-7 shrink-0 text-slate-400 sm:h-8 sm:w-8" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm text-slate-500">Alerts</p>
                  <p className="mt-1 text-2xl font-bold sm:text-3xl">{stats.totalAlerts}</p>
                </div>
                <AlertTriangle className="h-7 w-7 shrink-0 text-amber-500 sm:h-8 sm:w-8" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm text-slate-500">Latest Interface</p>
                  <p className="mt-1 truncate text-base font-semibold sm:text-lg">{stats.latestInterface}</p>
                </div>
                <Server className="h-7 w-7 shrink-0 text-blue-500 sm:h-8 sm:w-8" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm text-slate-500">Similarity Score</p>
                  <p className="mt-1 text-2xl font-bold sm:text-3xl">{formatNumber(stats.score)}</p>
                </div>
                <Activity className="h-7 w-7 shrink-0 text-emerald-500 sm:h-8 sm:w-8" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:gap-6 xl:grid-cols-5">
          <div className="min-w-0 space-y-4 sm:space-y-6 xl:col-span-3">
            <Card className="rounded-2xl border-slate-200 shadow-sm sm:rounded-3xl">
              <CardContent className="p-4 sm:p-6">
                <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <div className="mb-2 flex items-center gap-2">
                      <Brain className="h-5 w-5 shrink-0 text-purple-600" />
                      <h2 className="truncate text-lg font-bold sm:text-xl">Latest AI Analysis</h2>
                    </div>
                    <p className="text-sm text-slate-500">
                      Stored analysis returned by <code className="rounded bg-slate-100 px-1">GET /analysis/latest</code>{" "}
                      or generated on demand with <code className="rounded bg-slate-100 px-1">POST /analyze</code>
                    </p>
                  </div>
                  <div className="sm:shrink-0">
                    <StatusPill tone={analyzingInterfaceId ? "info" : analysis ? "success" : "warning"}>
                      {analyzingInterfaceId
                        ? `Analyzing ${analyzingInterfaceId}`
                        : analysis
                          ? "Analysis available"
                          : "No analysis yet"}
                    </StatusPill>
                  </div>
                </div>

                {!analysis ? (
                  <div className="rounded-2xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 sm:p-8">
                    No analysis found yet. Ingest a payload, let the consumer process it, then refresh or analyze an alert.
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                      <MetadataTile label="Analyzed Interface" value={analysis.interface_id} icon={Server} />
                      <MetadataTile label="Current Anomaly" value={analysis.anomaly} icon={AlertTriangle} />
                      <MetadataTile label="Created / Event Time" value={formatDate(analysis.created_at)} icon={CalendarClock} />
                      <MetadataTile label="Similar Interface" value={similarInterface} icon={GitCompare} />
                      <MetadataTile label="Similar Anomaly" value={similarAnomaly} icon={Activity} />
                      <MetadataTile label="Similarity Score" value={formatNumber(stats.score)} icon={Sparkles} />
                    </div>

                    {selectedAlert && (
                      <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-800">
                        <p className="font-semibold">Selected alert context</p>
                        <p className="mt-1">
                          The analysis was requested from alert <span className="font-semibold">{selectedAlert.interface_id}</span>{" "}
                          with anomaly <span className="font-semibold">{selectedAlert.anomaly || "—"}</span>{" "}
                          at <span className="font-semibold">{formatDate(selectedAlert.timestamp || selectedAlert.created_at)}</span>.
                        </p>
                      </div>
                    )}

                    <Section title="Root Cause" icon={ShieldCheck}>
                      {analysisBody.root_cause || "—"}
                    </Section>

                    <Section title="What It Means" icon={Brain}>
                      {analysisBody.what_it_means || "—"}
                    </Section>

                    <Section title="Observed Pattern" icon={Activity}>
                      {analysisBody.observed_pattern || "—"}
                    </Section>

                    <Section title="Likely System Setup" icon={Server}>
                      {analysisBody.likely_system_setup || "—"}
                    </Section>

                    <Section title="Most Likely Cause" icon={AlertTriangle}>
                      {analysisBody.most_likely_cause || "—"}
                    </Section>

                    <Section title="What To Check First" icon={RefreshCw}>
                      {Array.isArray(analysisBody.what_to_check_first) && analysisBody.what_to_check_first.length > 0 ? (
                        <ol className="list-decimal space-y-2 pl-5">
                          {analysisBody.what_to_check_first.map((item, index) => (
                            <li className="break-words" key={`${item}-${index}`}>{item}</li>
                          ))}
                        </ol>
                      ) : (
                        "—"
                      )}
                    </Section>

                    <Section title="Why This Happens" icon={Sparkles}>
                      {analysisBody.why_this_happens || "—"}
                    </Section>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="min-w-0 space-y-4 sm:space-y-6 xl:col-span-2">
            <Card className="rounded-2xl border-slate-200 shadow-sm sm:rounded-3xl">
              <CardContent className="p-4 sm:p-6">
                <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <h2 className="truncate text-lg font-bold sm:text-xl">Ingest Test Payload</h2>
                    <p className="mt-1 text-sm text-slate-500">
                      Posts to <code className="rounded bg-slate-100 px-1">/ingest/error-log</code>
                    </p>
                  </div>
                  <Button onClick={ingestPayload} disabled={ingesting} className="w-full rounded-2xl sm:w-auto">
                    <Send className="mr-2 h-4 w-4" />
                    {ingesting ? "Sending..." : "Send"}
                  </Button>
                </div>
                <textarea
                  value={payloadText}
                  onChange={(e) => setPayloadText(e.target.value)}
                  className="h-[45vh] min-h-[300px] w-full rounded-2xl border border-slate-200 bg-slate-950 p-3 font-mono text-[11px] leading-5 text-slate-100 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-100 sm:h-[420px] sm:p-4 sm:text-xs"
                  spellCheck={false}
                />
                <p className="mt-3 text-xs leading-5 text-slate-500">
                  For demos, keep payloads anonymized and avoid sending raw queries, server names, stack traces, or PII to the LLM.
                </p>
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-slate-200 shadow-sm sm:rounded-3xl">
              <CardContent className="p-4 sm:p-6">
                <h2 className="text-lg font-bold sm:text-xl">Recent Alerts</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Each card shows the exact alert context used when clicking Analyze.
                </p>
                <div className="mt-4 max-h-[520px] space-y-3 overflow-auto pr-1">
                  {alerts.length === 0 ? (
                    <p className="text-sm text-slate-500">No alerts found.</p>
                  ) : (
                    alerts.slice(0, 10).map((alert, index) => (
                      <AlertCard
                        key={`${alert.interface_id}-${alert.timestamp || alert.created_at || index}-${index}`}
                        alert={alert}
                        index={index}
                        isAnalyzing={analyzingInterfaceId === alert.interface_id}
                        onAnalyze={analyzeInterface}
                      />
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}