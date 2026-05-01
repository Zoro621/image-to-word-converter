"use client";

import dynamic from "next/dynamic";
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText, Download, ChevronDown, ChevronUp,
  Sparkles, Shield, Brain, Cpu, Settings, AlertTriangle,
} from "lucide-react";
import UploadZone from "@/components/UploadZone";
import AgentPipeline, { AgentStep, AgentStepStatus } from "@/components/AgentPipeline";
import FeedbackPanel from "@/components/FeedbackPanel";

const ThreeBackground = dynamic(() => import("@/components/ThreeBackground"), { ssr: false });

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const USE_CASES = [
  { id: "general",   label: "General",   icon: "📄", threshold: 0.70 },
  { id: "education", label: "Education", icon: "🎓", threshold: 0.75 },
  { id: "medical",   label: "Medical",   icon: "🏥", threshold: 0.90 },
  { id: "legal",     label: "Legal",     icon: "⚖️", threshold: 0.88 },
  { id: "personal",  label: "Personal",  icon: "👤", threshold: 0.65 },
];

const MODELS = [
  { id: "auto",          label: "Auto (Agent decides)" },
  { id: "Qwen3-VL-8B",  label: "Qwen3-VL-8B" },
  { id: "GPT-4-Vision",  label: "GPT-4 Vision" },
];

function makeSteps(overrides: Partial<Record<string, { status?: AgentStepStatus; detail?: string }>> = {}): AgentStep[] {
  return [
    { id: "perception", label: "Perception Agent", description: "Analyzing image quality, content type, and privacy signals.", status: "pending", ...overrides["perception"] },
    { id: "decision",   label: "Decision Agent",   description: "Selecting model, applying ethics & legal gates, setting thresholds.", status: "pending", ...overrides["decision"] },
    { id: "action",     label: "Action Agent",     description: "Extracting text with retry logic and confidence validation.", status: "pending", ...overrides["action"] },
    { id: "learning",   label: "Learning Agent",   description: "Awaiting your feedback to improve future routing.", status: "pending", ...overrides["learning"] },
  ];
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [useCase, setUseCase] = useState("general");
  const [model, setModel] = useState("auto");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [customThreshold, setCustomThreshold] = useState(-1);
  const [mounted, setMounted] = useState(false);
  const [disclaimerDismissed, setDisclaimerDismissed] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (localStorage.getItem("dv_disclaimer") === "1") {
      setDisclaimerDismissed(true);
    }
  }, []);
  const [showLimitations, setShowLimitations] = useState(false);

  const [steps, setSteps] = useState<AgentStep[]>(makeSteps());
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [showLog, setShowLog] = useState(false);
  const [consentPending, setConsentPending] = useState<string | null>(null);

  const fileRef = useRef<File | null>(null);

  function dismissDisclaimer() {
    localStorage.setItem("dv_disclaimer", "1");
    setDisclaimerDismissed(true);
  }

  function setStep(id: string, status: AgentStepStatus, detail?: string) {
    setSteps((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status, detail: detail ?? s.detail } : s))
    );
  }

  async function runExtraction(userConsent = false) {
    if (!fileRef.current) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setConsentPending(null);
    setSteps(makeSteps());

    const form = new FormData();
    form.append("file", fileRef.current);
    form.append("use_case_profile", useCase);
    form.append("override_model", model);
    form.append("override_threshold", String(customThreshold));
    form.append("user_consent", String(userConsent));

    // Perception
    setStep("perception", "active");
    await delay(400);

    try {
      const res = await fetch(`${API}/api/extract`, { method: "POST", body: form });
      const data = await res.json();

      setStep("perception", "done", `Content: ${data.perception?.content_type ?? "—"} · Quality: ${((data.perception?.quality_score ?? 0) * 100).toFixed(0)}%`);

      if (data.status === "AWAIT_CONSENT") {
        setConsentPending(data.consent_reason);
        setStep("decision", "error", "Ethics gate: sensitive content detected");
        setLoading(false);
        return;
      }

      // Decision step
      setStep("decision", "active");
      await delay(300);
      setStep("decision", "done", `Model: ${data.model_used} · Threshold: ${data.perception ? ((data.perception.quality_score ?? 0) * 100).toFixed(0) + "%" : "—"}`);

      // Action step
      setStep("action", "active");
      await delay(300);

      if (data.status === "REJECTED" || data.status === "FAILED") {
        setStep("action", "error", data.reason ?? "Extraction failed");
        setError(data.reason ?? "Extraction failed.");
        setLoading(false);
        return;
      }

      setStep("action", "done", `Confidence: ${((data.confidence ?? 0) * 100).toFixed(1)}% · ${data.confidence_label}`);
      setStep("learning", "pending", "Awaiting your feedback below");

      setResult(data);
    } catch (e: any) {
      setStep("perception", "error");
      setError("Cannot reach the backend. Make sure the server is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  function handleFileSelect(f: File) {
    setFile(f);
    fileRef.current = f;
    setResult(null);
    setError(null);
    setSteps(makeSteps());
  }

  function downloadDocx() {
    if (!result?.docx_base64) return;
    const bytes = atob(result.docx_base64);
    const ab = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) ab[i] = bytes.charCodeAt(i);
    const blob = new Blob([ab], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "extracted_document.docx"; a.click();
    URL.revokeObjectURL(url);
  }

  const confPct = result ? Math.round((result.confidence ?? 0) * 100) : 0;
  const confColor = confPct >= 85 ? "var(--accent-emerald)" : confPct >= 65 ? "var(--accent-amber)" : "var(--accent-rose)";

  return (
    <main style={{ minHeight: "100vh", position: "relative" }}>
      <ThreeBackground />

      {/* ── Legal disclaimer (shown once per session) ─────────────── */}
      <AnimatePresence>
        {mounted && !disclaimerDismissed && (
          <motion.div
            initial={{ y: -60, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -60, opacity: 0 }}
            transition={{ duration: 0.4 }}
            style={{
              position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
              background: "rgba(13,21,38,0.97)",
              borderBottom: "1px solid var(--border-default)",
              backdropFilter: "blur(12px)",
              display: "flex", alignItems: "center", justifyContent: "space-between",
              gap: 16, padding: "12px 24px", flexWrap: "wrap",
            }}
            role="banner"
          >
            <div style={{ display: "flex", alignItems: "flex-start", gap: 10, flex: 1 }}>
              <span style={{ fontSize: "1rem", flexShrink: 0 }}>📋</span>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.6 }}>
                <strong style={{ color: "var(--text-primary)" }}>Legal Notice:</strong> By uploading an image,
                you confirm that you have the legal right to process and extract text from its contents.
                DocuVision does not store your images. Extracted text is your responsibility to use in
                accordance with applicable copyright and data protection laws.
              </p>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={dismissDisclaimer}
              className="btn-primary"
              style={{ padding: "7px 18px", fontSize: "0.8rem", flexShrink: 0 }}
              aria-label="Acknowledge legal notice"
            >
              I understand
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      <div style={{ position: "relative", zIndex: 10, maxWidth: 1200, margin: "0 auto", padding: "0 24px 80px" }}>
        {/* ── Hero ─────────────────────────────────────────────────── */}
        <motion.section
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          style={{ textAlign: "center", padding: "80px 0 48px" }}
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.5 }}
            style={{ display: "inline-flex", alignItems: "center", gap: 8, marginBottom: 20,
              padding: "6px 16px", borderRadius: 99, background: "rgba(108,99,255,0.12)",
              border: "1px solid var(--border-default)" }}
          >
            <Sparkles size={14} color="var(--accent-primary)" />
            <span style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--accent-secondary)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
              Phase 2 · Agentic Pipeline
            </span>
          </motion.div>

          <h1 className="gradient-text" style={{ fontSize: "clamp(2.4rem, 6vw, 4rem)", fontWeight: 800, lineHeight: 1.15, marginBottom: 20, letterSpacing: "-0.02em" }}>
            DocuVision
          </h1>
          <p style={{ fontSize: "clamp(1rem, 2.5vw, 1.2rem)", color: "var(--text-secondary)", maxWidth: 560, margin: "0 auto 12px", lineHeight: 1.7 }}>
            Multi-agent document intelligence. Upload handwritten notes, diagrams,<br />
            or forms — get a formatted Word document in seconds.
          </p>

          <div style={{ display: "flex", justifyContent: "center", gap: 16, flexWrap: "wrap", marginTop: 28 }}>
            {[{ icon: <Shield size={13}/>, label: "Ethics-gated" }, { icon: <Brain size={13}/>, label: "Memory-aware" }, { icon: <Cpu size={13}/>, label: "Adaptive routing" }].map((f) => (
              <div key={f.label} className="chip chip-violet" style={{ padding: "6px 14px", fontSize: "0.8rem", gap: 6 }}>
                {f.icon} {f.label}
              </div>
            ))}
          </div>
        </motion.section>

        {/* ── Main grid ────────────────────────────────────────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24, alignItems: "start" }}>
          {/* LEFT COLUMN */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* Upload card */}
            <motion.div className="glass reveal" style={{ padding: 24 }}>
              <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <FileText size={16} color="var(--accent-primary)" /> Upload Image
              </h2>
              <UploadZone onFileSelect={handleFileSelect} disabled={loading} selectedFile={file} />
            </motion.div>

            {/* Use case selection */}
            <motion.div className="glass reveal reveal-delay-1" style={{ padding: 24 }}>
              <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 14 }}>Use Case Profile</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
                {USE_CASES.map((uc) => (
                  <motion.button
                    key={uc.id}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => setUseCase(uc.id)}
                    style={{
                      padding: "12px 8px", borderRadius: "var(--radius-md)", cursor: "pointer",
                      border: useCase === uc.id ? "2px solid var(--accent-primary)" : "1px solid var(--border-subtle)",
                      background: useCase === uc.id ? "var(--accent-glow)" : "var(--bg-elevated)",
                      color: useCase === uc.id ? "var(--text-primary)" : "var(--text-secondary)",
                      fontWeight: 600, fontSize: "0.8rem", textAlign: "center",
                      transition: "all 0.18s",
                    }}
                    aria-pressed={useCase === uc.id}
                  >
                    <div style={{ fontSize: "1.4rem", marginBottom: 4 }}>{uc.icon}</div>
                    {uc.label}
                    <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: 2 }}>
                      ≥{Math.round(uc.threshold * 100)}%
                    </div>
                  </motion.button>
                ))}
              </div>
            </motion.div>

            {/* Advanced controls */}
            <motion.div className="glass reveal reveal-delay-2" style={{ padding: 24 }}>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                style={{ display: "flex", alignItems: "center", gap: 8, background: "none", border: "none",
                  color: "var(--text-secondary)", cursor: "pointer", fontSize: "0.88rem", fontWeight: 600, width: "100%" }}
              >
                <Settings size={15} /> Advanced Controls
                {showAdvanced ? <ChevronUp size={14} style={{ marginLeft: "auto" }} /> : <ChevronDown size={14} style={{ marginLeft: "auto" }} />}
              </button>

              <AnimatePresence>
                {showAdvanced && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    style={{ overflow: "hidden" }}
                  >
                    <div style={{ paddingTop: 18, display: "flex", flexDirection: "column", gap: 16 }}>
                      <div>
                        <label style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 6, display: "block" }}>
                          Override Model
                        </label>
                        <select
                          className="input-field"
                          value={model}
                          onChange={(e) => setModel(e.target.value)}
                          style={{ width: "100%", padding: "9px 12px", fontSize: "0.85rem" }}
                        >
                          {MODELS.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 6, display: "block" }}>
                          Custom Confidence Threshold: {customThreshold < 0 ? "Auto" : `${Math.round(customThreshold * 100)}%`}
                        </label>
                        <input type="range" min={-1} max={100} value={customThreshold < 0 ? -1 : Math.round(customThreshold * 100)}
                          onChange={(e) => { const v = Number(e.target.value); setCustomThreshold(v < 0 ? -1 : v / 100); }}
                          style={{ width: "100%" }} />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Extract button */}
            <motion.button
              className="btn-primary"
              whileHover={!loading && file ? { scale: 1.02 } : {}}
              whileTap={!loading && file ? { scale: 0.98 } : {}}
              onClick={() => runExtraction(false)}
              disabled={!file || loading}
              style={{ padding: "16px", fontSize: "1rem", fontWeight: 700, width: "100%",
                opacity: !file || loading ? 0.5 : 1 }}
              aria-label="Run extraction"
            >
              {loading ? (
                <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
                  <motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>⚙️</motion.span>
                  Processing…
                </span>
              ) : (
                <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                  <Sparkles size={18} /> Extract Document
                </span>
              )}
            </motion.button>

            {/* Consent gate */}
            <AnimatePresence>
              {consentPending && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="glass"
                  style={{ padding: 20, border: "1px solid var(--accent-amber)" }}
                >
                  <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
                    <AlertTriangle size={18} color="var(--accent-amber)" style={{ flexShrink: 0, marginTop: 2 }} />
                    <div>
                      <p style={{ fontWeight: 700, fontSize: "0.9rem", marginBottom: 4 }}>Sensitive Content Detected</p>
                      <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>{consentPending}</p>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 10 }}>
                    <button className="btn-primary" style={{ padding: "9px 18px", fontSize: "0.85rem", flex: 1 }}
                      onClick={() => runExtraction(true)}>I consent — proceed</button>
                    <button className="btn-ghost" style={{ padding: "9px 18px", fontSize: "0.85rem" }}
                      onClick={() => setConsentPending(null)}>Cancel</button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="glass" style={{ padding: 16, border: "1px solid var(--accent-rose)", display: "flex", gap: 10 }}>
                  <AlertTriangle size={16} color="var(--accent-rose)" style={{ flexShrink: 0 }} />
                  <p style={{ fontSize: "0.84rem", color: "var(--accent-rose)" }}>{error}</p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Result */}
            <AnimatePresence>
              {result && result.status === "SUCCESS" && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="glass"
                  style={{ padding: 24 }}
                >
                  {/* Confidence bar */}
                  <div style={{ marginBottom: 18 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>Extraction Confidence</span>
                      <span className={`chip ${confPct >= 85 ? "chip-green" : confPct >= 65 ? "chip-amber" : "chip-rose"}`}>
                        {confPct}% · {result.confidence_label}
                      </span>
                    </div>
                    <div className="conf-bar-track">
                      <motion.div
                        className="conf-bar-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${confPct}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        style={{ background: `linear-gradient(90deg, ${confColor}, var(--accent-cyan))` }}
                      />
                    </div>
                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
                      <span className="chip chip-violet">Model: {result.model_used}</span>
                      {result.perception?.content_type && <span className="chip chip-cyan">{result.perception.content_type}</span>}
                      {result.model_used === "Qwen3-VL-8B" && (
                        <span className="chip chip-green" title="Qwen3-VL is Apache 2.0 — free for commercial use, attribution required">⚖️ Apache 2.0</span>
                      )}
                      {result.model_used === "GPT-4-Vision" && (
                        <span className="chip chip-amber" title="GPT-4V is under OpenAI ToS — outputs may not train competing models; usage logged by OpenAI">⚖️ OpenAI ToS</span>
                      )}
                    </div>
                  </div>

                  {/* Warnings */}
                  {[result.quality_warning, result.legal_warning, result.bias_warning].filter(Boolean).map((w, i) => (
                    <div key={i} style={{ display: "flex", gap: 8, marginBottom: 10, padding: "10px 12px",
                      background: "rgba(251,191,36,0.08)", borderRadius: "var(--radius-sm)", border: "1px solid rgba(251,191,36,0.2)" }}>
                      <AlertTriangle size={14} color="var(--accent-amber)" style={{ flexShrink: 0, marginTop: 2 }} />
                      <p style={{ fontSize: "0.8rem", color: "var(--accent-amber)" }}>{w}</p>
                    </div>
                  ))}

                  {/* Extracted text */}
                  <label style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 6, display: "block", fontWeight: 600 }}>
                    Extracted Text
                  </label>
                  <textarea
                    className="text-output"
                    value={result.text ?? ""}
                    readOnly
                    rows={12}
                    style={{ width: "100%", padding: "14px 16px" }}
                    aria-label="Extracted document text"
                  />

                  {/* Download */}
                  {result.docx_base64 && (
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.97 }}
                      className="btn-primary"
                      onClick={downloadDocx}
                      style={{ marginTop: 14, width: "100%", padding: "12px", fontSize: "0.9rem", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
                      aria-label="Download Word document"
                    >
                      <Download size={16} /> Download .docx
                    </motion.button>
                  )}

                  {/* Feedback */}
                  <div className="divider" style={{ marginTop: 24 }} />
                  <p style={{ fontSize: "0.82rem", fontWeight: 700, marginBottom: 6 }}>
                    Feedback &amp; Learning
                  </p>
                  <FeedbackPanel
                    modelUsed={result.model_used}
                    confidence={result.confidence}
                    contentType={result.perception?.content_type ?? ""}
                    languageScript={result.perception?.language_script ?? ""}
                    useCase={useCase}
                    onFeedbackSent={() => setStep("learning", "done", "Routing updated from your feedback")}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* RIGHT COLUMN — Agent Pipeline */}
          <motion.div
            className="glass reveal reveal-delay-3"
            style={{ padding: 24, position: "sticky", top: 24 }}
          >
            <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
              <Brain size={16} color="var(--accent-primary)" /> Agent Pipeline
            </h2>
            <AgentPipeline steps={steps} />

            {/* Agent log */}
            {result?.agent_log && result.agent_log.length > 0 && (
              <div style={{ marginTop: 24 }}>
                <button
                  onClick={() => setShowLog(!showLog)}
                  style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%",
                    background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", fontSize: "0.82rem", fontWeight: 600 }}
                >
                  Agent Log ({result.agent_log.length} entries)
                  {showLog ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                </button>
                <AnimatePresence>
                  {showLog && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      style={{ overflow: "hidden", marginTop: 10, maxHeight: 320, overflowY: "auto" }}
                    >
                      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                        {result.agent_log.map((entry: string, i: number) => {
                          const cls = entry.startsWith("✅") ? "success" : entry.startsWith("❌") ? "error" : entry.startsWith("⚠️") ? "warning" : "info";
                          return (
                            <div key={i} className={`log-entry ${cls}`}>
                              <span style={{ color: "var(--text-muted)", flexShrink: 0, fontSize: "0.72rem", paddingTop: 1 }}>{String(i+1).padStart(2,"0")}</span>
                              {entry}
                            </div>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </motion.div>
        </div>
        {/* ── Limitations Panel ─────────────────────────────────── */}
        <motion.div
          className="glass reveal"
          style={{ padding: 24, marginTop: 24 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <button
            onClick={() => setShowLimitations(!showLimitations)}
            style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%",
              background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer",
              fontSize: "0.88rem", fontWeight: 700 }}
            aria-expanded={showLimitations}
          >
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <AlertTriangle size={15} color="var(--accent-amber)" /> Known Limitations
            </span>
            {showLimitations ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          <AnimatePresence>
            {showLimitations && (
              <motion.div
                initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}
                style={{ overflow: "hidden" }}
              >
                <div style={{ paddingTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {[
                    { label: "Confidence is a proxy", detail: "Without model-native scores, the heuristic (printable ratio + length) can miss fluent but incorrect extractions." },
                    { label: "Privacy detection is heuristic", detail: "Face/signature detection uses basic OpenCV. It may produce false positives and false negatives." },
                    { label: "Learning needs data", detail: "Routing adaptation is only meaningful after many jobs. Early sessions rely on rule-based decisions." },
                    { label: "No ground-truth verification", detail: "The agent cannot confirm extracted text is correct. Human review is necessary for high-stakes documents." },
                    { label: "Consent is not legally binding", detail: "The in-app consent prompt is a UX safeguard, not a legal contract or GDPR-compliant mechanism." },
                    { label: "Bias mitigation is disclosure-only", detail: "Non-Latin script notice informs but does not fix the underlying model bias. Fine-tuning is out of scope." },
                    { label: "Memory is local", detail: "agent_memory.json is per-deployment. Multi-user hosted scenarios would need a proper shared database." },
                    { label: "No formal audit trail", detail: "The ethics log is not GDPR-compliant. A production system would need legal basis recording per processing activity." },
                  ].map((lim, i) => (
                    <div key={i} style={{ padding: "10px 14px", borderRadius: "var(--radius-md)",
                      background: "rgba(251,191,36,0.05)", border: "1px solid rgba(251,191,36,0.12)" }}>
                      <p style={{ fontWeight: 600, fontSize: "0.82rem", color: "var(--accent-amber)", marginBottom: 4 }}>{i + 1}. {lim.label}</p>
                      <p style={{ fontSize: "0.77rem", color: "var(--text-muted)", lineHeight: 1.5 }}>{lim.detail}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </main>
  );
}

function delay(ms: number) { return new Promise((r) => setTimeout(r, ms)); }
