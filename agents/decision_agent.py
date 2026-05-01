"""
DecisionAgent — reasoning core of the DocuVision agentic pipeline.
Receives perception report, applies ethics gates, legal gates, and
industry-aware thresholds; produces a structured action_plan.
"""
from __future__ import annotations

from agents.memory import AgentMemory


INDUSTRY_THRESHOLDS: dict[str, float] = {
    "general":   0.70,
    "medical":   0.90,
    "legal":     0.88,
    "education": 0.75,
    "personal":  0.65,
}

MODEL_FALLBACKS: dict[str, str] = {
    "Qwen3-VL-8B":  "GPT-4-Vision",
    "GPT-4-Vision": "Qwen3-VL-8B",
}


class DecisionAgent:
    """
    Reasoning core. Produces an action plan based on:
    - Perception report
    - Memory-informed model performance history
    - Ethical constraints (privacy gate, bias disclosure)
    - Legal constraints (copyright risk)
    - Industry-specific confidence thresholds
    """

    def __init__(self, memory: AgentMemory) -> None:
        self.memory = memory

    # ------------------------------------------------------------------ main
    def decide(
        self,
        perception: dict,
        use_case_profile: str = "general",
        override_model: str | None = None,
        override_threshold: float | None = None,
        user_consented: bool = False,
    ) -> dict:
        """
        Returns an action_plan dict.
        """
        log: list[str] = list(perception.get("perception_log", []))
        plan: dict = {}

        # ── Step 1: Quality gate ──────────────────────────────────────────
        q = perception["quality_score"]
        if q < 0.3:
            log.append(
                f"❌ REJECT: Quality score {q:.2f} below minimum threshold (0.30)."
            )
            return {
                "action": "REJECT",
                "reason": (
                    f"Image quality score ({q:.2f}) is too low for reliable extraction. "
                    "Please upload a clearer, better-lit image."
                ),
                "agent_log": log,
            }
        if q < 0.5:
            log.append(
                f"⚠️ Low quality ({q:.2f}): proceeding with caution."
            )
            plan["quality_warning"] = (
                f"Quality score is {q:.2f} — extraction may be incomplete."
            )
        else:
            log.append(f"✅ Quality check passed ({q:.2f}).")

        # ── Step 2: Ethics gate (privacy) ────────────────────────────────
        sensitive_types: list[str] = []
        if perception["has_faces"]:
            sensitive_types.append("faces")
        if perception["has_signatures"]:
            sensitive_types.append("signatures")
        if perception["has_id_card_features"]:
            sensitive_types.append("ID card features")
        if perception["has_medical_indicators"]:
            sensitive_types.append("medical data indicators")

        if sensitive_types:
            if not user_consented:
                reason = f"Detected potentially sensitive content: {', '.join(sensitive_types)}."
                plan["require_user_consent"] = True
                plan["consent_reason"] = reason
                plan["action"] = "AWAIT_CONSENT"
                log.append(f"⚠️ ETHICS GATE: {reason} Awaiting user consent.")
                self.memory.log_ethics_event(
                    "SENSITIVE_CONTENT_DETECTED", f"Types: {sensitive_types}"
                )
                plan["agent_log"] = log
                return plan
            else:
                log.append(f"✅ ETHICS GATE: Sensitive content acknowledged by user. Proceeding.")

        # ── Step 3: Legal gate (copyright) ───────────────────────────────
        if perception["copyright_risk"] == "high":
            plan["legal_warning"] = (
                "This image appears to contain printed text from a published source. "
                "Ensure you have the legal right to extract and reproduce this content."
            )
            log.append("⚠️ LEGAL WARNING: High copyright risk detected.")

        # ── Step 4: Model selection ───────────────────────────────────────
        if override_model and override_model != "auto":
            selected_model = override_model
            log.append(f"🧠 Model override: using '{selected_model}'.")
        else:
            selected_model = self._select_model(perception, use_case_profile)
            log.append(
                f"🧠 Model selected autonomously: '{selected_model}' "
                f"(content={perception['content_type']}, "
                f"script={perception['language_script']})."
            )

        plan["model"] = selected_model

        # ── Step 5: Confidence threshold ─────────────────────────────────
        threshold = (
            override_threshold
            if override_threshold is not None and override_threshold >= 0
            else self._get_threshold(use_case_profile)
        )
        plan["confidence_threshold"] = threshold
        log.append(
            f"🧠 Confidence threshold: {threshold:.2f} "
            f"(profile={use_case_profile})."
        )

        # ── Step 6: Retry strategy ────────────────────────────────────────
        plan["max_retries"] = 2
        plan["fallback_model"] = MODEL_FALLBACKS.get(selected_model, selected_model)
        log.append(
            f"🧠 Retry strategy: max {plan['max_retries']} attempts, "
            f"fallback='{plan['fallback_model']}'."
        )

        # ── Step 7: Expected format hints ────────────────────────────────
        plan["expected_format"] = self._infer_expected_format(perception)
        log.append(f"🧠 Expected format: {plan['expected_format']}.")

        # ── Step 8: Bias disclosure ───────────────────────────────────────
        if perception["language_script"] not in ("latin", "unknown"):
            plan["bias_warning"] = (
                f"Detected script: {perception['language_script']}. "
                "Current models have lower accuracy on non-Latin scripts. "
                "Confidence scores may not accurately reflect output quality."
            )
            log.append(
                f"⚠️ BIAS NOTICE: Non-Latin script detected "
                f"({perception['language_script']})."
            )

        plan["action"] = "EXTRACT"
        plan["use_case_profile"] = use_case_profile
        plan["agent_log"] = log
        return plan

    # ------------------------------------------------------------------ helpers
    def _select_model(self, perception: dict, profile: str) -> str:
        history = self.memory.get_model_performance()
        routing = self.memory.get_routing()
        script = perception.get("language_script", "latin")
        content = perception.get("content_type", "handwritten")

        # Check learned routing preference
        script_key = f"script:{script}"
        if script_key in routing:
            return routing[script_key]

        content_key = f"content:{content}"
        if content_key in routing:
            return routing[content_key]

        # Medical/legal → prefer most accurate model
        if profile in ("medical", "legal"):
            return max(history, key=lambda m: history[m]["avg_confidence"])

        # Diagram → GPT-4 handles spatial reasoning better
        if content == "diagram":
            return "GPT-4-Vision"

        # Handwritten/mixed → pick best performing from memory
        if content in ("handwritten", "mixed"):
            return max(history, key=lambda m: history[m]["avg_confidence"])

        return "Qwen3-VL-8B"

    def _get_threshold(self, profile: str) -> float:
        return INDUSTRY_THRESHOLDS.get(profile, 0.70)

    def _infer_expected_format(self, perception: dict) -> str:
        content = perception.get("content_type", "handwritten")
        mapping = {
            "handwritten": "structured_notes",
            "printed": "flowing_text",
            "mixed": "structured_notes",
            "diagram": "described_diagram",
            "form": "table",
        }
        return mapping.get(content, "structured_notes")

    def _build_consent_reason(self, perception: dict) -> str:
        flags = []
        if perception.get("has_faces"):
            flags.append("faces")
        if perception.get("has_signatures"):
            flags.append("signatures")
        if perception.get("has_id_card_features"):
            flags.append("ID card features")
        if perception.get("has_medical_indicators"):
            flags.append("medical data")
        return f"Detected potentially sensitive content: {', '.join(flags)}."
