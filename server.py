"""
DocuVision Phase 2 — FastAPI Backend
Routes:
    POST /api/extract          — run full agentic pipeline
    POST /api/feedback         — integrate user feedback
    GET  /api/memory           — inspect long-term memory & routing
    GET  /health               — liveness probe
"""
from __future__ import annotations

import io
import os
import sys
import base64
import json
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image
from pydantic import BaseModel

# ── Agent imports ──────────────────────────────────────────────────────────────
from agents.memory import AgentMemory
from agents.perception_agent import PerceptionAgent
from agents.decision_agent import DecisionAgent
from agents.action_agent import ActionAgent
from agents.learning_agent import LearningAgent

# ── Vision extractor ───────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from utils.vision_extractor import VisionExtractor

# ── Shared singletons ──────────────────────────────────────────────────────────
memory = AgentMemory()
perception_agent = PerceptionAgent()
decision_agent = DecisionAgent(memory)
action_agent = ActionAgent()
learning_agent = LearningAgent(memory)

# ── Load secrets from .streamlit/secrets.toml if it exists ─────────────────────
def _load_streamlit_secrets():
    secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        with open(secrets_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    os.environ[k] = v

_load_streamlit_secrets()

# Build extractor registry — key = model label, value = extractor instance
_openai_api_key = os.environ.get("OPENAI_API_KEY", "")
_hf_api_token   = os.environ.get("HUGGINGFACE_API_KEY", os.environ.get("HF_TOKEN", ""))

# Lazy extractor creation — missing keys won't crash startup
def _try_build_extractor(kwargs: dict):
    try:
        return VisionExtractor(**kwargs)
    except Exception:
        return None

extractor_qwen = _try_build_extractor({"hf_token": _hf_api_token, "model_key": "Qwen3-VL-8B"})
extractor_gpt  = _try_build_extractor({"openai_key": _openai_api_key, "model_key": "GPT-4-Vision"})

EXTRACTOR_REGISTRY: dict = {}
if extractor_qwen:
    EXTRACTOR_REGISTRY["Qwen3-VL-8B"] = extractor_qwen
if extractor_gpt:
    EXTRACTOR_REGISTRY["GPT-4-Vision"] = extractor_gpt

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(title="DocuVision API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schema models ──────────────────────────────────────────────────────────────
class FeedbackPayload(BaseModel):
    job_id:           str = ""
    model_used:       str = "Qwen3-VL-8B"
    confidence:       float = 0.0
    user_rating:      int = 3
    content_type:     str = ""
    language_script:  str = ""
    use_case_profile: str = "general"
    corrections:      Optional[str] = None


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "total_jobs": memory.total_jobs}


@app.post("/api/extract")
async def extract(
    file:              UploadFile = File(...),
    use_case_profile:  str = Form("general"),
    override_model:    str = Form("auto"),
    override_threshold: str = Form("-1"),
    user_consent:      str = Form("false"),
):
    """
    Full agentic extraction pipeline.
    Returns JSON with extracted text, confidence, agent log,
    and docx_base64 for download.
    """
    # ── Load image ─────────────────────────────────────────────────────────
    raw = await file.read()
    try:
        image = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Cannot open image file.")

    file_metadata = {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(raw),
    }

    # ── Perception ─────────────────────────────────────────────────────────
    perception = perception_agent.perceive(image, file_metadata)

    # ── Decision ───────────────────────────────────────────────────────────
    threshold_val = float(override_threshold) if override_threshold else -1.0
    user_consented_bool = user_consent.lower() == "true"
    
    plan = decision_agent.decide(
        perception,
        use_case_profile=use_case_profile,
        override_model=override_model,
        override_threshold=threshold_val if threshold_val >= 0 else None,
        user_consented=user_consented_bool
    )

    # ── Consent gate ───────────────────────────────────────────────────────
    if plan.get("action") == "AWAIT_CONSENT":
        return {
            "status": "AWAIT_CONSENT",
            "consent_reason": plan.get("consent_reason", ""),
            "agent_log": plan.get("agent_log", []),
        }

    if user_consented_bool:
        memory.log_ethics_event("USER_CONSENT_GIVEN", "User acknowledged sensitive content.")

    if plan.get("action") == "REJECT":
        return {
            "status": "REJECTED",
            "reason": plan.get("reason", ""),
            "agent_log": plan.get("agent_log", []),
        }

    # ── Action ─────────────────────────────────────────────────────────────
    result = action_agent.act(plan, image, EXTRACTOR_REGISTRY)

    # ── Update model memory ────────────────────────────────────────────────
    if result.get("status") == "SUCCESS":
        memory.update_model_stats(
            result["model_used"],
            result["confidence"],
            failed=False,
        )

    # ── Prepare DOCX ───────────────────────────────────────────────────────
    docx_b64 = None
    if result.get("docx"):
        docx_b64 = base64.b64encode(result["docx"]).decode()

    response_payload = {
        "status":            result.get("status", "UNKNOWN"),
        "text":              result.get("text", result.get("partial_text", "")),
        "confidence":        result.get("confidence", 0.0),
        "confidence_label":  result.get("confidence_label", ""),
        "model_used":        result.get("model_used", plan.get("model", "")),
        "docx_base64":       docx_b64,
        "agent_log":         result.get("log", []),
        "quality_warning":   plan.get("quality_warning"),
        "legal_warning":     plan.get("legal_warning"),
        "bias_warning":      plan.get("bias_warning"),
        "perception": {
            "quality_score":  perception["quality_score"],
            "content_type":   perception["content_type"],
            "language_script": perception["language_script"],
            "text_density":   perception["text_density"],
        },
    }

    return response_payload


@app.post("/api/feedback")
async def feedback(payload: FeedbackPayload):
    """Integrate user feedback to improve routing."""
    result = learning_agent.integrate_feedback(payload.dict())
    return result


@app.get("/api/memory")
async def get_memory():
    """Expose current agent memory state for inspection/analytics."""
    return {
        "model_performance": memory.get_model_performance(),
        "routing": memory.get_routing(),
        "script_performance": memory.get_script_performance(),
        "job_count": memory.total_jobs,
    }
