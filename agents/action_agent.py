"""
ActionAgent — execution layer of the DocuVision agentic pipeline.
Runs extraction, validates output, retries with fallback model if needed,
generates the DOCX, and produces a complete result record.
"""
from __future__ import annotations

import io
from PIL import Image

from utils.docx_generator import generate_docx


def strip_exif(image: Image.Image) -> Image.Image:
    """
    Remove EXIF metadata to protect user privacy.
    Always applied — non-overridable hard limit.
    """
    clean = Image.new(image.mode, image.size)
    clean.putdata(list(image.getdata()))
    return clean


class ActionAgent:
    """
    Executes the action plan from DecisionAgent.
    Never makes strategic decisions — that is DecisionAgent's job.
    """

    def act(
        self,
        plan: dict,
        image: Image.Image,
        extractor_registry: dict,
    ) -> dict:
        """
        Execute the extraction pipeline per the action plan.

        Returns a result dict with:
            status, text, confidence, confidence_label, model_used,
            docx (BytesIO), log, partial_text (on FAILED)
        """
        log: list[str] = list(plan.get("agent_log", []))

        if plan.get("action") == "REJECT":
            return {
                "status": "REJECTED",
                "reason": plan.get("reason", ""),
                "log": log,
            }

        # ── Hard limit: strip EXIF always ────────────────────────────────
        image = strip_exif(image)
        log.append("⚡ EXIF metadata stripped (privacy hard-limit enforced).")

        model = plan["model"]
        fallback = plan.get("fallback_model", model)
        max_retries = plan.get("max_retries", 2)
        threshold = plan.get("confidence_threshold", 0.70)

        attempt = 0
        raw_text = ""
        confidence = 0.0
        result: dict = {}

        while attempt <= max_retries:
            log.append(
                f"⚡ Attempt {attempt + 1}/{max_retries + 1}: "
                f"extracting with model '{model}'..."
            )

            try:
                extractor = extractor_registry.get(model)
                if extractor is None:
                    raise RuntimeError(
                        f"No extractor registered for model '{model}'."
                    )

                raw_text = extractor.extract_text(image)
                confidence = self._estimate_confidence(raw_text, image)

                log.append(
                    f"📊 Confidence: {confidence:.2f} "
                    f"(threshold: {threshold:.2f})"
                )

                if confidence >= threshold:
                    log.append("✅ Confidence threshold met.")
                    result = self._build_result(
                        raw_text, confidence, model, plan, log
                    )
                    break
                else:
                    if attempt < max_retries:
                        log.append(
                            f"⚠️ Confidence {confidence:.2f} below threshold "
                            f"— retrying with fallback model '{fallback}'."
                        )
                        model = fallback
                    else:
                        log.append(
                            f"⚠️ Confidence {confidence:.2f} below threshold "
                            "— max retries reached."
                        )
                    attempt += 1

            except Exception as exc:
                log.append(
                    f"❌ Extraction error on attempt {attempt + 1}: {exc}"
                )
                model = fallback
                attempt += 1

        if not result:
            log.append(
                "❌ FAILED: Could not meet confidence threshold after all retries. "
                "Returning partial result with failure notice."
            )
            result = {
                "status": "FAILED",
                "reason": (
                    f"Could not meet confidence threshold ({threshold:.2f}) "
                    "after all retries. "
                    "Try a higher-quality image or reduce the threshold in Advanced Controls."
                ),
                "partial_text": raw_text,
                "confidence": confidence,
                "confidence_label": self._label_confidence(confidence),
                "model_used": model,
                "log": log,
            }

        return result

    # ------------------------------------------------------------------ helpers
    def _estimate_confidence(self, text: str, image: Image.Image) -> float:
        """
        Heuristic confidence (no model-native score available):
        - printable character ratio (fluency proxy)
        - text length relative to image area (coverage proxy)
        """
        if not text or len(text.strip()) < 10:
            return 0.10

        printable_ratio = sum(c.isprintable() for c in text) / len(text)
        length_score = min(len(text) / 500.0, 1.0)
        score = round(printable_ratio * 0.6 + length_score * 0.4, 3)
        return score

    def _label_confidence(self, score: float) -> str:
        if score >= 0.85:
            return "High"
        if score >= 0.65:
            return "Medium"
        return "Low"

    def _build_result(
        self,
        text: str,
        confidence: float,
        model: str,
        plan: dict,
        log: list[str],
    ) -> dict:
        try:
            doc_buffer = generate_docx(text, title="Extracted Document")
            log.append("📄 Word document generated successfully.")
            docx_bytes = doc_buffer.getvalue() if hasattr(doc_buffer, "getvalue") else bytes(doc_buffer)
        except Exception as exc:
            log.append(f"⚠️ DOCX generation failed: {exc}")
            docx_bytes = None

        return {
            "status": "SUCCESS",
            "text": text,
            "confidence": confidence,
            "confidence_label": self._label_confidence(confidence),
            "model_used": model,
            "docx": docx_bytes,
            "use_case_profile": plan.get("use_case_profile", "general"),
            "log": log,
        }
