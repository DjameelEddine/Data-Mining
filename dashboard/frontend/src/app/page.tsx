"use client";

import { useEffect, useRef, useState } from "react";
import ChatWidget from "@/components/ChatWidget";
import { fetchOverview, fetchRcpOverview, predictPackage, predictReceptacle, sendChatMessage, getExportPdfUrl } from "@/lib/api";
import type { OverviewStats, RcpOverviewStats, PredictionResult, RcpPredictionResult, ChatMessage, PredictionMode } from "@/types";
import {
  Search,
  Send,
  ChevronDown,
  ChevronRight,
  Download,
  Package,
  Clock,
  Activity,
  MessageCircle,
  Info,
  Loader2,
  PanelLeftClose,
  PanelLeftOpen,
  AlertTriangle,
  Box,
} from "lucide-react";

export default function DashboardPage() {
  /* ── State ─────────────────────────────────────────────────── */
  const [mode, setMode] = useState<PredictionMode>("package");
  const [inputId, setInputId] = useState("");
  const [pkgPrediction, setPkgPrediction] = useState<PredictionResult | null>(null);
  const [rcpPrediction, setRcpPrediction] = useState<RcpPredictionResult | null>(null);
  const [predError, setPredError] = useState("");
  const [predLoading, setPredLoading] = useState(false);

  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [rcpStats, setRcpStats] = useState<RcpOverviewStats | null>(null);

  const [featuresOpen, setFeaturesOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Chat state
  const [chatQuery, setChatQuery] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  /* ── Load dataset info ─────────────────────────────────────── */
  useEffect(() => {
    fetchOverview().then(setStats).catch(console.error);
    fetchRcpOverview().then(setRcpStats).catch(console.error);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  /* ── Clear prediction when mode changes ────────────────────── */
  useEffect(() => {
    setPkgPrediction(null);
    setRcpPrediction(null);
    setPredError("");
    setInputId("");
  }, [mode]);

  /* ── Handlers ──────────────────────────────────────────────── */
  async function handlePredict() {
    const id = inputId.trim();
    if (!id) {
      setPredError(`Please enter a ${mode === "package" ? "Package" : "Receptacle"} ID.`);
      return;
    }
    setPredError("");
    setPkgPrediction(null);
    setRcpPrediction(null);
    setPredLoading(true);
    try {
      if (mode === "package") {
        const res = await predictPackage(id);
        if ("error" in res) {
          setPredError((res as unknown as { error: string }).error);
        } else {
          setPkgPrediction(res);
        }
      } else {
        const res = await predictReceptacle(id);
        if ("error" in res) {
          setPredError((res as unknown as { error: string }).error);
        } else {
          setRcpPrediction(res);
        }
      }
    } catch {
      setPredError(`Failed to get prediction. Check the ${mode === "package" ? "Package" : "Receptacle"} ID and try again.`);
    } finally {
      setPredLoading(false);
    }
  }

  async function handleChat() {
    const text = chatQuery.trim();
    if (!text || chatLoading) return;
    setChatMessages((prev) => [...prev, { role: "user", content: text }]);
    setChatQuery("");
    setChatLoading(true);
    try {
      const res = await sendChatMessage(text);
      setChatMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch {
      setChatMessages((prev) => [...prev, { role: "assistant", content: "Sorry, something went wrong." }]);
    } finally {
      setChatLoading(false);
    }
  }

  const p = pkgPrediction;
  const r = rcpPrediction;

  /* ── Render ────────────────────────────────────────────────── */
  return (
    <div className="min-h-screen bg-[#0f1225] text-white">
      {/* Title bar */}
      <header className="flex items-center justify-between bg-[#1a1f36] px-6 py-4 shadow-lg">
        <h1 className="text-xl font-bold tracking-wide">
          Algerie Post &mdash; Route Duration & AI Assistant
        </h1>
        <button
          onClick={() => setSidebarOpen((v) => !v)}
          title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          className="hidden lg:flex items-center gap-1.5 rounded-md bg-[#2a2f46] px-3 py-2 text-sm text-gray-300 hover:bg-[#353b58] hover:text-white transition"
        >
          {sidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
          {sidebarOpen ? "Hide Sidebar" : "Show Sidebar"}
        </button>
      </header>

      <div className="mx-auto flex max-w-[1400px] gap-6 p-6">
        {/* ── Sidebar ──────────────────────────────────────── */}
        <aside
          className={`hidden shrink-0 space-y-6 lg:block overflow-hidden transition-all duration-300 ease-in-out ${
            sidebarOpen ? "w-80 opacity-100" : "w-0 opacity-0"
          }`}
        >
           {/* Packages Dataset Info */}
          <div className="rounded-xl bg-[#1a1f36] p-5 shadow-lg">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-gray-300">
              <Package className="h-4 w-4" /> Packages Dataset
            </h2>
            {stats ? (
              <div className="space-y-2 text-sm text-gray-300">
                <p>
                  <span className="font-semibold text-white">Records: </span>
                  {stats.total_shipments.toLocaleString()}
                </p>
                <p>
                  <span className="font-semibold text-white">Unique packages: </span>
                  {stats.unique_packages.toLocaleString()}
                </p>
                <p>
                  <span className="font-semibold text-white">Date range: </span>
                  {stats.date_range_start} to {stats.date_range_end}
                </p>
              </div>
            ) : (
              <p className="text-sm text-gray-500">Loading...</p>
            )}
          </div>

          {/* Receptacles Dataset Info */}
          <div className="rounded-xl bg-[#1a1f36] p-5 shadow-lg">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-gray-300">
              <Box className="h-4 w-4" /> Receptacles Dataset
            </h2>
            {rcpStats ? (
              <div className="space-y-2 text-sm text-gray-300">
                <p>
                  <span className="font-semibold text-white">Records: </span>
                  {rcpStats.total_records.toLocaleString()}
                </p>
                <p>
                  <span className="font-semibold text-white">Unique receptacles: </span>
                  {rcpStats.unique_receptacles.toLocaleString()}
                </p>
                <p>
                  <span className="font-semibold text-white">Date range: </span>
                  {rcpStats.date_range_start} to {rcpStats.date_range_end}
                </p>
              </div>
            ) : (
              <p className="text-sm text-gray-500">Loading...</p>
            )}
          </div>

          {/* AI Assistant */}
          <div className="rounded-xl bg-[#1a1f36] p-5 shadow-lg">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-gray-300">
              <MessageCircle className="h-4 w-4" /> Intelligent Assistant
            </h2>
            <form
              onSubmit={(e) => { e.preventDefault(); handleChat(); }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={chatQuery}
                onChange={(e) => setChatQuery(e.target.value)}
                placeholder="Ask about packages or predictions..."
                className="flex-1 rounded-md bg-[#2a2f46] px-3 py-2 text-sm text-white placeholder-gray-400 outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                disabled={chatLoading}
                title="Send message"
                className="flex h-9 w-9 items-center justify-center rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
            {chatMessages.length > 0 && (
              <div className="mt-3 max-h-64 space-y-2 overflow-y-auto rounded-md bg-[#0f1225] p-3">
                {chatMessages.map((m, i) => (
                  <div key={i} className={`text-sm ${m.role === "user" ? "text-blue-300" : "text-gray-300"}`}>
                    <span className="font-semibold">{m.role === "user" ? "You: " : "AI: "}</span>
                    {m.content}
                  </div>
                ))}
                {chatLoading && (
                  <div className="text-sm text-gray-500">AI is thinking...</div>
                )}
                <div ref={chatEndRef} />
              </div>
            )}
          </div>

         
        </aside>

        {/* ── Main content ─────────────────────────────────── */}
        <main className="flex-1 space-y-6">
          {/* Mode Toggle + Lookup */}
          <div className="rounded-xl bg-[#1a1f36] p-6 shadow-lg">
            <h2 className="mb-4 flex items-center gap-2 text-lg font-bold">
              <Search className="h-5 w-5 text-blue-400" /> Lookup & Prediction
            </h2>

            {/* Package / Receptacle Toggle */}
            <div className="mb-4 flex rounded-lg bg-[#0f1225] p-1">
              <button
                onClick={() => setMode("package")}
                className={`flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold transition ${
                  mode === "package"
                    ? "bg-blue-600 text-white shadow-md"
                    : "text-gray-400 hover:text-white hover:bg-[#2a2f46]"
                }`}
              >
                <Package className="h-4 w-4" />
                Package
              </button>
              <button
                onClick={() => setMode("receptacle")}
                className={`flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold transition ${
                  mode === "receptacle"
                    ? "bg-blue-600 text-white shadow-md"
                    : "text-gray-400 hover:text-white hover:bg-[#2a2f46]"
                }`}
              >
                <Box className="h-4 w-4" />
                Receptacle
              </button>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                type="text"
                value={inputId}
                onChange={(e) => setInputId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handlePredict()}
                placeholder={mode === "package" ? "e.g., RR123456789DZ" : "e.g., DZALGDESMADBAUL50018001110033"}
                className="flex-1 rounded-md bg-[#2a2f46] px-4 py-3 text-sm text-white placeholder-gray-400 outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handlePredict}
                disabled={predLoading}
                className="flex items-center justify-center gap-2 rounded-md bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {predLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
                Predict Route Duration
              </button>
            </div>
            {predError && (
              <p className="mt-3 rounded-md bg-red-900/40 px-4 py-2 text-sm text-red-300">
                {predError}
              </p>
            )}
          </div>

          {/* ── Package Prediction results ─────────────────── */}
          {p && mode === "package" && (
            <>
              {/* Delay Alert */}
              {p.is_delayed && (
                <div className="flex items-center gap-3 rounded-xl bg-red-900/30 border border-red-700/50 p-4 shadow-lg">
                  <AlertTriangle className="h-6 w-6 text-red-400 shrink-0" />
                  <div>
                    <p className="font-bold text-red-300">Package Delayed</p>
                    <p className="text-sm text-red-400">
                      Total estimated time ({p.total_estimated_days} days) exceeds the {p.delay_threshold_days}-day threshold.
                    </p>
                  </div>
                </div>
              )}

              {/* Package Information */}
              <div className="rounded-xl bg-[#1a1f36] p-6 shadow-lg">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-bold">
                  <Package className="h-5 w-5 text-green-400" /> Package Information
                </h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <Metric label="Package ID" value={p.mailitm_fid} />
                  <Metric label="Receptacle ID" value={p.recptcl_fid || "N/A"} />
                  <Metric label="Current Location" value={p.current_location} />
                  <Metric label="Next Location" value={p.next_location ?? "N/A"} />
                  <Metric label="Event Type" value={String(p.event_type)} />
                  <Metric label="Last Scan Date" value={p.last_scan_date} />
                  <Metric label="Total Scans" value={String(p.total_scans)} />
                </div>
              </div>

              {/* Prediction Result */}
              <div className="rounded-xl bg-[#1a1f36] p-6 shadow-lg">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-bold">
                  <Clock className="h-5 w-5 text-yellow-400" /> Prediction Result
                </h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <Metric
                    label="Receptacle Time Since First Scan"
                    value={`${p.receptacle_time_since_first_scan_hours.toFixed(2)} hours`}
                  />
                  <Metric
                    label="Predicted Route Duration"
                    value={`${p.prediction_hours.toFixed(2)} hours`}
                  />
                  <Metric
                    label="Total Estimated Time"
                    value={`${p.total_estimated_hours.toFixed(2)} hours`}
                    sub={`${p.total_estimated_days} days`}
                  />
                  <Metric
                    label="Delay Status"
                    value={p.is_delayed ? "DELAYED" : "On Time"}
                    sub={`Threshold: ${p.delay_threshold_days} days`}
                  />
                </div>
              </div>

              {/* Time Breakdown */}
              <div className="rounded-xl bg-[#1a1f36] p-6 shadow-lg">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-bold">
                  <Activity className="h-5 w-5 text-purple-400" /> Time Breakdown
                </h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="rounded-lg bg-[#2a2f46] p-4">
                    {p.prediction_hours >= 24 ? (
                      <>
                        <p className="text-xs text-gray-400">Route Duration (days)</p>
                        <p className="text-2xl font-bold">{(p.prediction_hours / 24).toFixed(1)} days</p>
                      </>
                    ) : (
                      <>
                        <p className="text-xs text-gray-400">Route Duration (minutes)</p>
                        <p className="text-2xl font-bold">{(p.prediction_hours * 60).toFixed(0)} min</p>
                      </>
                    )}
                  </div>
                  <div className="flex items-center justify-center rounded-lg p-4"
                    style={{
                      backgroundColor:
                        p.is_delayed
                          ? "rgba(239,68,68,0.15)"
                          : p.route_speed === "fast"
                          ? "rgba(34,197,94,0.15)"
                          : p.route_speed === "normal"
                          ? "rgba(234,179,8,0.15)"
                          : "rgba(239,68,68,0.15)",
                    }}
                  >
                    <span
                      className="text-lg font-bold"
                      style={{
                        color:
                          p.is_delayed
                            ? "#ef4444"
                            : p.route_speed === "fast"
                            ? "#22c55e"
                            : p.route_speed === "normal"
                            ? "#eab308"
                            : "#ef4444",
                      }}
                    >
                      {p.is_delayed
                        ? "🔴 Delayed"
                        : p.route_speed === "fast"
                        ? "🟢 Fast Route"
                        : p.route_speed === "normal"
                        ? "🟡 Normal Route"
                        : "🔴 Slow Route"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Save status */}
              <div className={`rounded-md px-4 py-3 text-sm ${p.was_saved ? "bg-green-900/30 text-green-300" : "bg-blue-900/30 text-blue-300"}`}>
                {p.was_saved
                  ? "Prediction saved to package log."
                  : "This prediction already exists in the log (not saved again)."}
              </div>

              {/* PDF Export */}
              <a
                href={getExportPdfUrl(p.mailitm_fid)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-md bg-red-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-red-700 transition"
              >
                <Download className="h-4 w-4" /> Export Details as PDF
              </a>

              {/* Features expandable */}
              <Collapsible
                title="Features Used for Prediction"
                open={featuresOpen}
                onToggle={() => setFeaturesOpen(!featuresOpen)}
              >
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-gray-700 text-xs uppercase text-gray-400">
                        <th className="pb-2 pr-4">Feature</th>
                        <th className="pb-2">Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(p.features).map(([key, val]) => (
                        <tr key={key} className="border-b border-gray-800 last:border-0">
                          <td className="py-1.5 pr-4 font-mono text-xs text-gray-400">{key}</td>
                          <td className="py-1.5 text-sm">{val}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Collapsible>

              {/* Journey History expandable */}
              <Collapsible
                title="Package Journey History"
                open={historyOpen}
                onToggle={() => setHistoryOpen(!historyOpen)}
              >
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-gray-700 text-xs uppercase text-gray-400">
                        <th className="pb-2 pr-4">Date</th>
                        <th className="pb-2 pr-4">Location</th>
                        <th className="pb-2 pr-4">Next Location</th>
                        <th className="pb-2">Event</th>
                      </tr>
                    </thead>
                    <tbody>
                      {p.journey_history.map((row, i) => (
                        <tr key={i} className="border-b border-gray-800 last:border-0">
                          <td className="py-1.5 pr-4 whitespace-nowrap text-xs">{row.date}</td>
                          <td className="py-1.5 pr-4">{row.etablissement_postal}</td>
                          <td className="py-1.5 pr-4">{row.next_etablissement_postal}</td>
                          <td className="py-1.5">{row.EVENT_TYPE_CD}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Collapsible>
            </>
          )}

          {/* ── Receptacle Prediction results ──────────────── */}
          {r && mode === "receptacle" && (
            <>
              {/* Receptacle Information */}
              <div className="rounded-xl bg-[#1a1f36] p-6 shadow-lg">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-bold">
                  <Box className="h-5 w-5 text-green-400" /> Receptacle Information
                </h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <Metric label="Receptacle ID" value={r.recptcl_fid} />
                  <Metric label="Origin Country" value={r.origin_country} />
                  <Metric label="Destination Country" value={r.destination_country} />
                  <Metric label="Current Location" value={r.current_location} />
                  <Metric label="Next Location" value={r.next_location ?? "N/A"} />
                  <Metric label="Event Type" value={String(r.event_type)} />
                  <Metric label="Last Scan Date" value={r.last_scan_date} />
                  <Metric label="Total Scans" value={String(r.total_scans)} />
                </div>
              </div>

              {/* Prediction Result */}
              <div className="rounded-xl bg-[#1a1f36] p-6 shadow-lg">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-bold">
                  <Clock className="h-5 w-5 text-yellow-400" /> Prediction Result
                </h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <Metric
                    label="Time Since First Scan"
                    value={`${r.time_since_first_scan_hours.toFixed(2)} hours`}
                  />
                  <Metric
                    label="Predicted Route Duration"
                    value={`${r.prediction_hours.toFixed(2)} hours`}
                  />
                  <Metric
                    label="Total Estimated Time"
                    value={`${r.total_estimated_hours.toFixed(2)} hours`}
                    sub={`${r.total_estimated_days} days`}
                  />
                </div>
              </div>

              {/* Time Breakdown */}
              <div className="rounded-xl bg-[#1a1f36] p-6 shadow-lg">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-bold">
                  <Activity className="h-5 w-5 text-purple-400" /> Time Breakdown
                </h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="rounded-lg bg-[#2a2f46] p-4">
                    {r.prediction_hours >= 24 ? (
                      <>
                        <p className="text-xs text-gray-400">Route Duration (days)</p>
                        <p className="text-2xl font-bold">{(r.prediction_hours / 24).toFixed(1)} days</p>
                      </>
                    ) : (
                      <>
                        <p className="text-xs text-gray-400">Route Duration (minutes)</p>
                        <p className="text-2xl font-bold">{(r.prediction_hours * 60).toFixed(0)} min</p>
                      </>
                    )}
                  </div>
                  <div className="flex items-center justify-center rounded-lg p-4"
                    style={{
                      backgroundColor:
                        r.route_speed === "fast"
                          ? "rgba(34,197,94,0.15)"
                          : r.route_speed === "normal"
                          ? "rgba(234,179,8,0.15)"
                          : "rgba(239,68,68,0.15)",
                    }}
                  >
                    <span
                      className="text-lg font-bold"
                      style={{
                        color:
                          r.route_speed === "fast"
                            ? "#22c55e"
                            : r.route_speed === "normal"
                            ? "#eab308"
                            : "#ef4444",
                      }}
                    >
                      {r.route_speed === "fast"
                        ? "🟢 Fast Route"
                        : r.route_speed === "normal"
                        ? "🟡 Normal Route"
                        : "🔴 Slow Route"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Save status */}
              <div className={`rounded-md px-4 py-3 text-sm ${r.was_saved ? "bg-green-900/30 text-green-300" : "bg-blue-900/30 text-blue-300"}`}>
                {r.was_saved
                  ? "Prediction saved to receptacle log."
                  : "This prediction already exists in the log (not saved again)."}
              </div>

              {/* Features expandable */}
              <Collapsible
                title="Features Used for Prediction"
                open={featuresOpen}
                onToggle={() => setFeaturesOpen(!featuresOpen)}
              >
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-gray-700 text-xs uppercase text-gray-400">
                        <th className="pb-2 pr-4">Feature</th>
                        <th className="pb-2">Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(r.features).map(([key, val]) => (
                        <tr key={key} className="border-b border-gray-800 last:border-0">
                          <td className="py-1.5 pr-4 font-mono text-xs text-gray-400">{key}</td>
                          <td className="py-1.5 text-sm">{val}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Collapsible>

              {/* Journey History expandable */}
              <Collapsible
                title="Receptacle Journey History"
                open={historyOpen}
                onToggle={() => setHistoryOpen(!historyOpen)}
              >
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-gray-700 text-xs uppercase text-gray-400">
                        <th className="pb-2 pr-4">Date</th>
                        <th className="pb-2 pr-4">Location</th>
                        <th className="pb-2 pr-4">Next Location</th>
                        <th className="pb-2">Event</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.journey_history.map((row, i) => (
                        <tr key={i} className="border-b border-gray-800 last:border-0">
                          <td className="py-1.5 pr-4 whitespace-nowrap text-xs">{row.date}</td>
                          <td className="py-1.5 pr-4">{row.etablissement_postal}</td>
                          <td className="py-1.5 pr-4">{row.next_etablissement_postal}</td>
                          <td className="py-1.5">{row.EVENT_TYPE_CD}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Collapsible>
            </>
          )}
        </main>
      </div>
      {/* Floating chat widget */}
      <ChatWidget />
    </div>
  );
}

/* ── Reusable small components ──────────────────────────────── */

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-lg bg-[#2a2f46] p-4">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="mt-1 text-lg font-bold">{value}</p>
      {sub && <p className="text-xs text-gray-500">{sub}</p>}
    </div>
  );
}

function Collapsible({
  title,
  open,
  onToggle,
  children,
}: {
  title: string;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl bg-[#1a1f36] shadow-lg">
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-2 px-6 py-4 text-left text-sm font-bold hover:bg-[#222844] transition rounded-xl"
      >
        {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        {title}
      </button>
      {open && <div className="px-6 pb-5">{children}</div>}
    </div>
  );
}
