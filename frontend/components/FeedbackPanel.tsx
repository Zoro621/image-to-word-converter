"use client";

import { useState } from "react";
import { motion } from "framer-motion";


interface FeedbackPanelProps {
  modelUsed: string;
  confidence: number;
  contentType: string;
  languageScript: string;
  useCase: string;
  onFeedbackSent?: () => void;
}

export default function FeedbackPanel({
  modelUsed,
  confidence,
  contentType,
  languageScript,
  useCase,
  onFeedbackSent,
}: FeedbackPanelProps) {
  const [rating, setRating] = useState(0);
  const [hovered, setHovered] = useState(0);
  const [corrections, setCorrections] = useState("");
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);

  const send = async () => {
    if (rating === 0) return;
    setSending(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: `job-${Date.now()}`,
          model_used: modelUsed,
          confidence,
          user_rating: rating,
          content_type: contentType,
          language_script: languageScript,
          use_case_profile: useCase,
          corrections: corrections || null,
        }),
      });
      setSent(true);
      onFeedbackSent?.();
    } catch {
      // non-fatal
    } finally {
      setSending(false);
    }
  };

  if (sent) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          textAlign: "center",
          padding: "20px",
          color: "var(--accent-emerald)",
          fontWeight: 600,
        }}
      >
        ✦ Thanks! The agent learned from your feedback.
      </motion.div>
    );
  }

  return (
    <div style={{ padding: "16px 0" }}>
      <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: 12 }}>
        How accurate was the extraction? Your rating helps the agent improve.
      </p>

      {/* Star rating */}
      <div style={{ display: "flex", gap: 6, marginBottom: 14 }} role="group" aria-label="Rate extraction accuracy">
        {[1, 2, 3, 4, 5].map((s) => (
          <motion.button
            key={s}
            whileHover={{ scale: 1.25 }}
            whileTap={{ scale: 0.9 }}
            className="star"
            style={{
              background: "none",
              border: "none",
              color:
                s <= (hovered || rating)
                  ? "var(--accent-amber)"
                  : "var(--text-muted)",
              cursor: "pointer",
            }}
            onClick={() => setRating(s)}
            onMouseEnter={() => setHovered(s)}
            onMouseLeave={() => setHovered(0)}
            aria-label={`Rate ${s} star${s > 1 ? "s" : ""}`}
          >
            ★
          </motion.button>
        ))}
        {rating > 0 && (
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", alignSelf: "center", marginLeft: 6 }}>
            {["", "Poor", "Fair", "Good", "Great", "Perfect"][rating]}
          </span>
        )}
      </div>

      {/* Correction text */}
      <textarea
        className="input-field"
        placeholder="Optional: paste corrected text here…"
        value={corrections}
        onChange={(e) => setCorrections(e.target.value)}
        rows={3}
        style={{ width: "100%", padding: "10px 14px", fontSize: "0.82rem", marginBottom: 12 }}
        aria-label="Correction text"
      />

      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        className="btn-primary"
        style={{ padding: "9px 22px", fontSize: "0.85rem" }}
        onClick={send}
        disabled={rating === 0 || sending}
        aria-label="Submit feedback"
      >
        {sending ? "Sending…" : "Submit Feedback"}
      </motion.button>
    </div>
  );
}
