"use client";

import React from "react";
import { motion } from "framer-motion";
import { CheckCircle, Circle, Loader2, AlertCircle, Eye, Brain, Zap, BookOpen } from "lucide-react";

export type AgentStepStatus = "pending" | "active" | "done" | "error" | "skipped";

export interface AgentStep {
  id: string;
  label: string;
  description: string;
  status: AgentStepStatus;
  detail?: string;
}

const ICONS: Record<string, React.ReactNode> = {
  perception: <Eye size={16} />,
  decision:   <Brain size={16} />,
  action:     <Zap size={16} />,
  learning:   <BookOpen size={16} />,
};

const STATUS_COLORS: Record<AgentStepStatus, string> = {
  pending: "step-icon pending",
  active:  "step-icon active",
  done:    "step-icon done",
  error:   "step-icon error",
  skipped: "step-icon pending",
};

function StatusIcon({ status }: { status: AgentStepStatus }) {
  if (status === "active") return <Loader2 size={15} className="animate-spin" />;
  if (status === "done")   return <CheckCircle size={15} style={{ color: "var(--accent-emerald)" }} />;
  if (status === "error")  return <AlertCircle size={15} style={{ color: "var(--accent-rose)" }} />;
  return <Circle size={15} style={{ color: "var(--text-muted)" }} />;
}

export default function AgentPipeline({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="flex flex-col gap-6" role="list" aria-label="Agent pipeline steps">
      {steps.map((step, i) => (
        <motion.div
          key={step.id}
          className="agent-step"
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.07, duration: 0.4, ease: "easeOut" }}
          role="listitem"
        >
          {/* Connector line (rendered via CSS ::before on .agent-step) */}

          {/* Step icon */}
          <motion.div
            className={STATUS_COLORS[step.status]}
            animate={
              step.status === "active"
                ? { boxShadow: ["0 0 0 0 rgba(108,99,255,0.6)", "0 0 0 8px rgba(108,99,255,0)", "0 0 0 0 rgba(108,99,255,0.6)"] }
                : {}
            }
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            {ICONS[step.id] ?? <StatusIcon status={step.status} />}
          </motion.div>

          {/* Step content */}
          <div className="flex-1 min-w-0 pb-2">
            <div className="flex items-center gap-2 mb-1">
              <span
                style={{
                  fontSize: "0.88rem",
                  fontWeight: 600,
                  color:
                    step.status === "done"  ? "var(--accent-emerald)" :
                    step.status === "active" ? "var(--accent-primary)" :
                    step.status === "error"  ? "var(--accent-rose)" :
                    "var(--text-secondary)",
                }}
              >
                {step.label}
              </span>

              {/* Status chip */}
              {step.status !== "pending" && (
                <span
                  className={`chip ${
                    step.status === "done"   ? "chip-green" :
                    step.status === "active" ? "chip-violet" :
                    step.status === "error"  ? "chip-rose" :
                    "chip-amber"
                  }`}
                >
                  {step.status}
                </span>
              )}
            </div>

            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "4px" }}>
              {step.description}
            </p>

            {/* Detail (shown only when done/error/active) */}
            {step.detail && step.status !== "pending" && (
              <motion.p
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                transition={{ duration: 0.3 }}
                style={{
                  fontSize: "0.77rem",
                  color:
                    step.status === "error" ? "var(--accent-rose)" :
                    step.status === "done"  ? "var(--accent-emerald)" :
                    "var(--accent-secondary)",
                  marginTop: "2px",
                  fontStyle: "italic",
                }}
              >
                {step.detail}
              </motion.p>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
