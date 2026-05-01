"""
LearningAgent — feedback integration and adaptive routing.
Receives post-extraction feedback and updates memory-stored routing tables.
"""
from __future__ import annotations

from agents.memory import AgentMemory


class LearningAgent:
    """
    Receives user feedback after extraction and updates memory to
    improve future routing decisions.
    """

    def __init__(self, memory: AgentMemory) -> None:
        self.memory = memory

    # ------------------------------------------------------------------ public API
    def integrate_feedback(self, feedback: dict) -> dict:
        """
        feedback schema:
            {
                "job_id":          str,
                "model_used":      str,
                "confidence":      float,
                "user_rating":     int,      # 1-5
                "content_type":    str,
                "language_script": str,
                "use_case_profile":str,
                "corrections":     str | None,   # free-text correction
            }
        Returns updated routing summary.
        """
        log: list[str] = []

        model = feedback.get("model_used", "")
        confidence = float(feedback.get("confidence", 0.0))
        rating = int(feedback.get("user_rating", 3))
        content = feedback.get("content_type", "")
        script = feedback.get("language_script", "")
        profile = feedback.get("use_case_profile", "general")
        corrections = feedback.get("corrections", "")

        log.append(
            f"📚 Feedback received: model={model}, rating={rating}/5, "
            f"content={content}, script={script}"
        )

        # ── Update model performance memory ─────────────────────────────
        failed = rating <= 2
        adjusted_confidence = self._adjust_confidence(confidence, rating)
        self.memory.update_model_stats(model, adjusted_confidence, failed=failed)
        log.append(
            f"📚 Updated model stats: model={model}, "
            f"adjusted_conf={adjusted_confidence:.3f}, failed={failed}"
        )

        # ── Update routing based on rating ───────────────────────────────
        if rating >= 4:
            self._reinforce_routing(content, script, model, log)
        elif rating <= 2:
            self._reroute(content, script, model, log)

        # ── Record corrections ───────────────────────────────────────────
        if corrections and len(corrections.strip()) > 5:
            self.memory.session["corrections"].append(
                {
                    "model": model,
                    "content_type": content,
                    "script": script,
                    "profile": profile,
                    "correction_length": len(corrections),
                }
            )
            log.append(
                f"📚 Correction noted (length={len(corrections)} chars)."
            )

        # ── Script performance record ─────────────────────────────────────
        score = rating / 5.0
        self.memory.record_script_score(script, model, score)
        log.append(f"📚 Script score recorded: script={script}, model={model}, score={score:.2f}")

        return {
            "status": "LEARNING_APPLIED",
            "log": log,
            "current_routing": self.memory.get_routing(),
        }

    # ------------------------------------------------------------------ internals
    def _adjust_confidence(self, model_conf: float, rating: int) -> float:
        """
        Blend model's self-reported confidence with user rating.
        user_rating 5 → full trust; 1 → heavily discount.
        """
        rating_conf = (rating - 1) / 4.0  # normalise 1-5 → 0-1
        blended = round(model_conf * 0.5 + rating_conf * 0.5, 4)
        return max(0.0, min(blended, 1.0))

    def _reinforce_routing(
        self, content: str, script: str, model: str, log: list[str]
    ) -> None:
        if content:
            key = f"content:{content}"
            existing = self.memory.get_routing().get(key)
            if existing != model:
                self.memory.set_routing(key, model)
                log.append(
                    f"📚 Routing updated: {key} → '{model}' (reinforced by positive feedback)."
                )
        if script and script != "unknown":
            key = f"script:{script}"
            existing = self.memory.get_routing().get(key)
            if existing != model:
                self.memory.set_routing(key, model)
                log.append(
                    f"📚 Routing updated: {key} → '{model}'."
                )

    def _reroute(
        self, content: str, script: str, model: str, log: list[str]
    ) -> None:
        """Point future jobs for this content/script to the fallback model."""
        from agents.decision_agent import MODEL_FALLBACKS

        fallback = MODEL_FALLBACKS.get(model, model)
        if content:
            key = f"content:{content}"
            self.memory.set_routing(key, fallback)
            log.append(
                f"📚 Routing updated: {key} → '{fallback}' (negative feedback — rerouting)."
            )
        if script and script != "unknown":
            key = f"script:{script}"
            self.memory.set_routing(key, fallback)
            log.append(f"📚 Routing updated: {key} → '{fallback}'.")
