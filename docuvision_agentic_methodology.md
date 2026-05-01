# DocuVision — Phase 2: Agentic System Transformation Methodology

> **Purpose of this document:** This file serves as a complete reference and implementation guide for transforming DocuVision from a Phase 1 reactive tool into a Phase 2 agentic system. It is intended as context for an AI coding agent tasked with extending the existing codebase. All design decisions, architectural patterns, ethical constraints, and assessment criteria are documented here for grounded implementation.

---

## Table of Contents

1. [Project Overview & Phase Comparison](#1-project-overview--phase-comparison)
2. [Assessment Criteria Mapping](#2-assessment-criteria-mapping)
3. [Agentic System Theory (Slides 20–32 Reference)](#3-agentic-system-theory-slides-2032-reference)
4. [Target Architecture](#4-target-architecture)
5. [Layer-by-Layer Implementation Guide](#5-layer-by-layer-implementation-guide)
   - 5.1 Perception Agent
   - 5.2 Decision / Reasoning Agent
   - 5.3 Action Agent
   - 5.4 Memory System
   - 5.5 Learning / Feedback Agent
6. [Ethical Design Requirements](#6-ethical-design-requirements)
7. [Legal & IPR Awareness](#7-legal--ipr-awareness)
8. [Safety Mechanisms](#8-safety-mechanisms)
9. [File Structure & Integration Map](#9-file-structure--integration-map)
10. [Implementation Checklist](#10-implementation-checklist)
11. [Critical Thinking & Known Limitations](#11-critical-thinking--known-limitations)

---

## 1. Project Overview & Phase Comparison

### What DocuVision Phase 1 Does
DocuVision Phase 1 is a Streamlit application that:
- Accepts an image upload (JPG/PNG) from a user
- Lets the user manually select a vision model
- Passes the image to the selected model for OCR/text extraction
- Displays extracted text and generates a downloadable `.docx` file

### The Fundamental Problem with Phase 1
Phase 1 treats the system as a **passive tool**. Every decision — what model to use, whether the image is suitable, whether the output is good enough — is delegated entirely to the user. The system has no judgment.

### Phase 2 Transformation Summary

| Dimension | Phase 1 (Tool) | Phase 2 (Agent) |
|---|---|---|
| **Control** | User-driven | System-driven |
| **Intelligence** | Static | Adaptive |
| **Behavior** | Reactive | Proactive |
| **Model Selection** | Manual by user | Agent decides based on content analysis |
| **Quality Assurance** | None | Agent self-validates, retries, escalates |
| **Ethics** | Not considered | Baked into decision pipeline |
| **Memory** | None (stateless) | Short-term (session) + Long-term (persistent) |
| **Learning** | Never changes | Adapts routing rules from historical outcomes |
| **Transparency** | Opaque | Full agent action log shown to user |

---

## 2. Assessment Criteria Mapping

The following table maps each assessment criterion to specific system components that must be implemented. The AI agent extending this codebase must ensure ALL criteria are addressed through concrete code, not just documentation.

### 2.1 Ethical Understanding
**What assessors want to see:** Ethical risks of autonomy are identified and mitigated in the system design — not just mentioned in a report.

**Implementation requirements:**
- A `PrivacyGate` that detects sensitive content (faces, signatures, ID cards, medical data) BEFORE any model processes the image
- Explicit user consent prompt when sensitive content is detected — the agent must halt and wait
- Bias acknowledgment logged when the agent detects a non-Latin script (known model weakness)
- No server-side image storage beyond the active session

### 2.2 Legal & IPR Awareness
**What assessors want to see:** The system acknowledges legal realities of processing user-uploaded content.

**Implementation requirements:**
- A `LegalAwarenessModule` that flags when uploaded images may contain copyrighted content (e.g., scanned book pages, printed forms)
- Display of model licensing info: Qwen2.5-VL / Qwen3-VL is Apache 2.0 licensed; GPT-4V is proprietary (OpenAI ToS applies)
- A user-facing disclaimer shown before first use: "By uploading an image you confirm you have the right to process its contents"
- Metadata stripping from uploaded images before processing (EXIF data may contain GPS, device info — privacy risk)

### 2.3 Agentic System Design Quality
**What assessors want to see:** A real PIDAL loop (Perceive → Interpret → Decide → Act → Learn) with memory and external tools.

**Implementation requirements:**
- All 5 agent layers implemented as distinct Python classes (see Section 5)
- A working memory system with both session-scoped and file-persisted storage
- At least one external tool integration beyond the vision model (e.g., language detection API, image quality estimator)
- The agent must demonstrate autonomy: model selection, retry logic, and output formatting must all happen without user input

### 2.4 Industry & Career Awareness
**What assessors want to see:** The system is grounded in real-world professional use cases.

**Implementation requirements:**
- The agent's decision logic must reference real industries: medical records digitization, legal document archival, educational content extraction
- Industry-specific confidence thresholds: medical/legal content should require higher confidence before generating a document
- A "use case profile" selector that adjusts agent behavior (e.g., selecting "Medical" raises confidence threshold to 0.90 and enables stricter privacy checks)

### 2.5 Critical Thinking & Honesty
**What assessors want to see:** The system acknowledges its own limitations and does not overclaim.

**Implementation requirements:**
- Confidence scores shown to the user for every extraction, with explicit labels: "High / Medium / Low confidence"
- If confidence is below threshold and retries are exhausted, the agent must honestly report failure rather than returning low-quality output silently
- A `LimitationsPanel` in the UI listing known agent weaknesses (see Section 11)

---

## 3. Agentic System Theory (Slides 20–32 Reference)

This section maps course slide content to implementation decisions. The AI agent must understand why each design choice was made.

### Slide 20 — Agentic System Concept
**Theory:** Perception → Decision-making → Action → Learning

**Applied to DocuVision:**
- **Perception:** Analyzing the uploaded image for quality, content type, language, and privacy risks
- **Decision-making:** Selecting a model, planning retry strategy, applying ethical gates
- **Action:** Running extraction, self-validating output, generating the document
- **Learning:** Updating model performance stats in persistent memory after each job

### Slide 22 — Agentic Vision: Tool → Agent, Reactive → Proactive
**Theory:** An agent does not wait to be told what to do — it assesses and acts.

**Applied to DocuVision:** The agent must remove the manual model selector from the main UI. The system selects the model. If the user wants visibility, they see the agent's reasoning in the log, not a dropdown.

### Slide 23 — Agent Architecture: Memory + External Tools
**Theory:** Input → Processing → Decision → Action → Feedback loop, augmented with memory and tools.

**Applied to DocuVision:**
- **Memory:** `AgentMemory` class with JSON-backed persistence for model performance history
- **External tools:** `langdetect` library for script/language detection; `Pillow` image stats for quality scoring

### Slide 24 — Agent Type: Goal-Based / Learning Agent
**Theory:** Goal-based agents evaluate actions against a goal state. Learning agents improve from experience.

**Applied to DocuVision:**
- **Goal:** Produce a high-confidence, correctly formatted document from any legible image
- **Learning:** If model A consistently underperforms on handwritten Arabic, the agent updates its routing rules to prefer model B for that content type

### Slide 25 — Operational Workflow: Observe → Interpret → Decide → Act → Learn
This maps directly to the 5 agent layers described in Section 5.

### Slide 26 — Intelligence Layer: ML / Rules / LLMs
**Applied to DocuVision:**
- **Rules:** Quality thresholds, content-type routing, retry limits — implemented as explicit Python logic
- **ML:** The vision models themselves (Qwen, GPT-4V)
- **LLMs as reasoning layer (extension):** An optional LLM call can be added to interpret ambiguous extraction results or generate structured summaries

### Slide 30 — Ethical Agent Design: Privacy, Bias, Transparency, User Control
See Section 6 for full implementation details.

### Slide 32 — Safety Mechanisms: Logging, Override, Explainability
See Section 8 for full implementation details.

---

## 4. Target Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        DocuVision Agent v2                       │
│                                                                  │
│   ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│   │  PERCEPTION │───▶│   DECISION   │───▶│     ACTION       │   │
│   │   AGENT     │    │    AGENT     │    │     AGENT        │   │
│   │             │    │              │    │                  │   │
│   │ - Quality   │    │ - Model pick │    │ - Run extraction │   │
│   │ - Lang det. │    │ - Ethics gate│    │ - Self-validate  │   │
│   │ - Privacy   │    │ - Retry plan │    │ - Format & docx  │   │
│   │ - Content   │    │ - Industry   │    │ - Log actions    │   │
│   │   classify  │    │   thresholds │    │ - Retry logic    │   │
│   └─────────────┘    └──────────────┘    └──────────────────┘   │
│          │                  │                     │              │
│          └──────────────────┴─────────────────────┘             │
│                             │                                    │
│                    ┌────────▼────────┐                           │
│                    │  AGENT MEMORY   │                           │
│                    │                 │                           │
│                    │ Session (RAM)   │                           │
│                    │ Long-term (JSON)│                           │
│                    └────────┬────────┘                           │
│                             │                                    │
│                    ┌────────▼────────┐                           │
│                    │    LEARNING     │                           │
│                    │     AGENT       │                           │
│                    │                 │                           │
│                    │ Update stats    │                           │
│                    │ Adapt routing   │                           │
│                    │ Log outcomes    │                           │
│                    └─────────────────┘                           │
└──────────────────────────────────────────────────────────────────┘
```

**Data flow:**
```
User uploads image
      │
      ▼
PerceptionAgent.perceive(image)  →  perception_report: dict
      │
      ▼
DecisionAgent.decide(perception_report)  →  action_plan: dict
      │
      ▼  [ETHICS GATE — may halt here for user consent]
      │
      ▼
ActionAgent.act(action_plan, image)  →  result: dict
      │
      ▼
UI renders: extracted text + agent log + confidence score + docx download
      │
      ▼
User provides feedback (thumbs up/down or text correction)
      │
      ▼
LearningAgent.learn(result, feedback)  →  updates AgentMemory
```

---

## 5. Layer-by-Layer Implementation Guide

### 5.1 Perception Agent

**File:** `agents/perception_agent.py`

**Responsibility:** Observe and characterize the input image. Produce a structured `perception_report` that downstream agents use for all decisions.

**Must implement:**

```python
class PerceptionAgent:
    """
    Observes the input image and produces a structured perception report.
    This is the agent's sensory layer — it must not make decisions,
    only describe what it observes.
    """

    def perceive(self, image: PIL.Image, file_metadata: dict) -> dict:
        return {
            "quality_score": float,          # 0.0–1.0, based on blur/contrast/resolution
            "resolution": tuple,             # (width, height) in pixels
            "content_type": str,             # "handwritten" | "printed" | "mixed" | "diagram" | "form"
            "language_script": str,          # "latin" | "arabic" | "devanagari" | "chinese" | "unknown"
            "text_density": float,           # estimated proportion of image covered by text
            "has_faces": bool,               # privacy flag
            "has_signatures": bool,          # privacy flag
            "has_id_card_features": bool,    # privacy flag
            "has_medical_indicators": bool,  # privacy + industry flag
            "exif_data": dict,               # raw EXIF, used for metadata stripping warning
            "copyright_risk": str,           # "low" | "medium" | "high" (based on printed text patterns)
            "timestamp": str                 # ISO format, for logging
        }

    def assess_quality(self, image: PIL.Image) -> float:
        # Use Pillow ImageStat to compute variance (blur proxy)
        # Low variance = likely blurry = low quality
        # Return normalized score 0.0–1.0
        pass

    def classify_content(self, image: PIL.Image) -> str:
        # Heuristic: if image has ruled lines → "handwritten"
        # If text is very uniform in size/spacing → "printed"
        # Can use a lightweight classifier or rule-based edge detection
        pass

    def detect_privacy_risks(self, image: PIL.Image) -> dict:
        # Use basic OpenCV face detection (Haar cascade) for faces
        # Look for signature-like thin horizontal strokes in lower portion
        # Return dict of boolean flags
        pass

    def detect_language_script(self, image: PIL.Image) -> str:
        # After lightweight OCR pre-pass (e.g., pytesseract with OSD mode)
        # or use langdetect on a sample extraction
        # Needed to route to the best model and log potential bias
        pass
```

**Quality thresholds (configurable):**
- `quality_score < 0.3` → REJECT immediately, inform user
- `0.3 <= quality_score < 0.5` → WARN, proceed with caveat logged
- `quality_score >= 0.5` → proceed normally

---

### 5.2 Decision / Reasoning Agent

**File:** `agents/decision_agent.py`

**Responsibility:** Receive the perception report and produce a structured `action_plan`. This is where intelligence, ethics, and industry awareness converge.

**Must implement:**

```python
class DecisionAgent:
    """
    The reasoning core of the agent. Produces an action plan based on
    perception output, memory-informed model performance history,
    ethical constraints, and industry-specific requirements.
    """

    def __init__(self, memory: AgentMemory):
        self.memory = memory

    def decide(self, perception: dict, use_case_profile: str = "general") -> dict:
        plan = {}

        # --- Step 1: Quality gate ---
        if perception["quality_score"] < 0.3:
            return {
                "action": "REJECT",
                "reason": "Image quality score below minimum threshold (0.3). "
                          "Please upload a clearer image.",
                "agent_log": ["❌ REJECT: Quality score too low for reliable extraction."]
            }

        # --- Step 2: Ethics gate ---
        ethics_flags = []
        if any([
            perception["has_faces"],
            perception["has_signatures"],
            perception["has_id_card_features"],
            perception["has_medical_indicators"]
        ]):
            ethics_flags.append("SENSITIVE_CONTENT_DETECTED")
            plan["require_user_consent"] = True
            plan["consent_reason"] = self._build_consent_reason(perception)

        # --- Step 3: Legal gate ---
        if perception["copyright_risk"] == "high":
            plan["legal_warning"] = (
                "This image appears to contain printed text from a published source. "
                "Ensure you have the right to extract and reproduce this content."
            )

        # --- Step 4: Model selection (memory-informed) ---
        plan["model"] = self._select_model(perception, use_case_profile)

        # --- Step 5: Confidence threshold (industry-aware) ---
        plan["confidence_threshold"] = self._get_threshold(use_case_profile)

        # --- Step 6: Retry strategy ---
        plan["max_retries"] = 2
        plan["fallback_model"] = self._get_fallback(plan["model"])

        # --- Step 7: Format hints ---
        plan["expected_format"] = self._infer_expected_format(perception)

        # --- Step 8: Bias acknowledgment ---
        if perception["language_script"] not in ["latin"]:
            plan["bias_warning"] = (
                f"Detected script: {perception['language_script']}. "
                "Current models have lower accuracy on non-Latin scripts. "
                "Confidence scores may be inflated."
            )

        plan["action"] = "EXTRACT"
        plan["agent_log"] = self._build_log(plan, perception)
        return plan

    def _select_model(self, perception: dict, profile: str) -> str:
        """
        Select the best model based on:
        1. Content type (diagram → GPT-4V; handwritten → Qwen)
        2. Historical performance from memory
        3. Industry profile requirements
        """
        history = self.memory.get_model_performance()

        if perception["content_type"] == "diagram":
            # GPT-4V handles spatial reasoning better
            return "GPT-4V"
        elif perception["content_type"] in ["handwritten", "mixed"]:
            # Pick best-performing model from memory
            return max(history, key=lambda m: history[m]["avg_confidence"])
        else:
            return "Qwen3-VL-8B"  # default

    def _get_threshold(self, profile: str) -> float:
        thresholds = {
            "general":   0.70,
            "medical":   0.90,  # high stakes — must be accurate
            "legal":     0.88,
            "education": 0.75,
            "personal":  0.65
        }
        return thresholds.get(profile, 0.70)

    def _build_consent_reason(self, perception: dict) -> str:
        flags = []
        if perception["has_faces"]:       flags.append("faces")
        if perception["has_signatures"]:  flags.append("signatures")
        if perception["has_id_card_features"]: flags.append("ID card features")
        if perception["has_medical_indicators"]: flags.append("medical data")
        return f"Detected potentially sensitive content: {', '.join(flags)}."
```

---

### 5.3 Action Agent

**File:** `agents/action_agent.py`

**Responsibility:** Execute the plan. Run extraction, validate output, retry if needed, generate the document, and produce a full result record.

**Must implement:**

```python
class ActionAgent:
    """
    Executes the action plan produced by DecisionAgent.
    Handles extraction, self-validation, retry logic, and document generation.
    Never makes strategic decisions — that is DecisionAgent's job.
    """

    def act(self, plan: dict, image: PIL.Image, extractor_registry: dict) -> dict:
        if plan["action"] == "REJECT":
            return {"status": "REJECTED", "reason": plan["reason"], "log": plan["agent_log"]}

        log = list(plan.get("agent_log", []))
        attempt = 0
        model = plan["model"]
        result = {}

        while attempt <= plan["max_retries"]:
            log.append(f"⚡ Attempt {attempt + 1}: Extracting with model '{model}'...")

            try:
                extractor = extractor_registry[model]
                raw_text = extractor.extract_text(image)
                confidence = self._estimate_confidence(raw_text, image)

                log.append(f"📊 Confidence score: {confidence:.2f} "
                           f"(threshold: {plan['confidence_threshold']:.2f})")

                if confidence >= plan["confidence_threshold"]:
                    log.append("✅ Confidence threshold met.")
                    result = self._build_result(raw_text, confidence, model, plan, log)
                    break
                else:
                    log.append(f"⚠️ Confidence below threshold. "
                               f"{'Retrying with fallback model.' if attempt < plan['max_retries'] else 'Max retries reached.'}")
                    model = plan.get("fallback_model", model)
                    attempt += 1

            except Exception as e:
                log.append(f"❌ Extraction error on attempt {attempt + 1}: {str(e)}")
                attempt += 1

        if not result:
            result = {
                "status": "FAILED",
                "reason": "Could not meet confidence threshold after all retries.",
                "log": log,
                "partial_text": raw_text if 'raw_text' in locals() else "",
                "confidence": confidence if 'confidence' in locals() else 0.0
            }
            log.append("❌ FAILED: Returning partial result with failure notice.")

        return result

    def _estimate_confidence(self, text: str, image: PIL.Image) -> float:
        """
        Heuristic confidence estimation. In absence of model-native
        confidence scores, use proxy signals:
        - Text length relative to image size (too short = likely missed content)
        - Character entropy (garbled output has unusual entropy)
        - Ratio of printable to non-printable characters
        - Presence of coherent word patterns (basic dictionary check)
        """
        if not text or len(text.strip()) < 10:
            return 0.1
        printable_ratio = sum(c.isprintable() for c in text) / len(text)
        length_score = min(len(text) / 500, 1.0)  # normalize, cap at 1
        return round((printable_ratio * 0.6 + length_score * 0.4), 2)

    def _build_result(self, text, confidence, model, plan, log) -> dict:
        from utils.docx_generator import generate_docx
        doc_buffer = generate_docx(text, title="Extracted Document")
        log.append("📄 Word document generated successfully.")
        return {
            "status": "SUCCESS",
            "text": text,
            "confidence": confidence,
            "confidence_label": self._label_confidence(confidence),
            "model_used": model,
            "docx": doc_buffer,
            "log": log
        }

    def _label_confidence(self, score: float) -> str:
        if score >= 0.85: return "High"
        if score >= 0.65: return "Medium"
        return "Low"
```

---

### 5.4 Memory System

**File:** `agents/memory.py`

**Responsibility:** Provide short-term (session) and long-term (persistent) storage. Long-term memory is stored as `agent_memory.json` in the project root.

```python
class AgentMemory:
    """
    Two-tier memory system.
    - Session memory: dict in RAM, cleared on app restart
    - Long-term memory: JSON file, persisted across sessions
    """

    MEMORY_FILE = "agent_memory.json"

    DEFAULT_LONG_TERM = {
        "model_performance": {
            "Qwen3-VL-8B": {"jobs": 0, "total_confidence": 0.0, "failures": 0, "avg_confidence": 0.75},
            "GPT-4V":       {"jobs": 0, "total_confidence": 0.0, "failures": 0, "avg_confidence": 0.80}
        },
        "content_type_routing": {},     # e.g. {"diagram": "GPT-4V", "handwritten": "Qwen3-VL-8B"}
        "script_performance": {},       # e.g. {"arabic": {"Qwen3-VL-8B": 0.55}}
        "ethics_log": [],               # anonymized log of flagged events
        "job_count": 0
    }

    def __init__(self):
        self.session = {"current_job": {}, "retry_count": 0, "corrections": []}
        self.long_term = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.MEMORY_FILE):
            with open(self.MEMORY_FILE, "r") as f:
                return json.load(f)
        return copy.deepcopy(self.DEFAULT_LONG_TERM)

    def save(self):
        with open(self.MEMORY_FILE, "w") as f:
            json.dump(self.long_term, f, indent=2)

    def update_model_stats(self, model: str, confidence: float, failed: bool = False):
        stats = self.long_term["model_performance"].setdefault(model, {
            "jobs": 0, "total_confidence": 0.0, "failures": 0, "avg_confidence": 0.0
        })
        stats["jobs"] += 1
        stats["total_confidence"] += confidence
        if failed: stats["failures"] += 1
        stats["avg_confidence"] = round(stats["total_confidence"] / stats["jobs"], 4)
        self.long_term["job_count"] += 1
        self.save()

    def get_model_performance(self) -> dict:
        return self.long_term["model_performance"]

    def log_ethics_event(self, event_type: str, details: str):
        # Anonymized — no image data, no user data
        self.long_term["ethics_log"].append({
            "type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.save()
```

---

### 5.5 Learning / Feedback Agent

**File:** `agents/learning_agent.py`

**Responsibility:** After each job, update memory and adapt routing rules based on outcomes and user feedback.

```python
class LearningAgent:
    """
    Closes the PIDAL loop. Observes job outcomes and user feedback,
    updates long-term memory, and adapts the agent's decision rules.
    """

    def __init__(self, memory: AgentMemory):
        self.memory = memory

    def learn(self, result: dict, perception: dict, user_feedback: str = None):
        """
        Called after every completed job.
        user_feedback: "good" | "poor" | None
        """
        model = result.get("model_used")
        confidence = result.get("confidence", 0.0)
        failed = result.get("status") == "FAILED"

        # Update model performance
        self.memory.update_model_stats(model, confidence, failed)

        # Update content-type routing based on performance
        content_type = perception.get("content_type")
        script = perception.get("language_script")

        if user_feedback == "poor" or failed:
            # Record that this model underperformed on this content/script
            self._record_underperformance(model, content_type, script)
        elif user_feedback == "good" and confidence >= 0.80:
            # Reinforce: this model works well for this content/script
            self._record_success(model, content_type, script)

        # Adapt routing rules
        self._adapt_routing()

    def _adapt_routing(self):
        """
        Examine historical performance and update routing preferences.
        E.g.: if Qwen3-VL-8B avg_confidence on 'arabic' < 0.60,
        prefer GPT-4V for arabic next time.
        """
        script_perf = self.memory.long_term.get("script_performance", {})
        routing = self.memory.long_term.setdefault("content_type_routing", {})

        for script, model_scores in script_perf.items():
            if model_scores:
                best = max(model_scores, key=model_scores.get)
                routing[f"script:{script}"] = best

        self.memory.save()
```

---

## 6. Ethical Design Requirements

Ethics in an agentic system must be **implemented**, not just described. The following are mandatory implementations.

### 6.1 Privacy Gate (Pre-processing)

Location: Called inside `DecisionAgent.decide()` — before any model sees the image.

```python
# In decision_agent.py
if plan.get("require_user_consent"):
    # This flag causes the Streamlit UI to halt and display a consent prompt.
    # The agent does NOT proceed until user explicitly confirms.
    plan["action"] = "AWAIT_CONSENT"
    return plan
```

In the Streamlit UI (`app.py`):
```python
if action_plan.get("action") == "AWAIT_CONSENT":
    st.warning(f"⚠️ {action_plan['consent_reason']}")
    st.info("The agent has paused. Your explicit consent is required to proceed.")
    if st.button("✅ I understand and consent to processing this image"):
        action_plan["action"] = "EXTRACT"
        # Continue pipeline
    else:
        st.stop()
```

### 6.2 Metadata Stripping

Before any image is passed to a model, strip EXIF data:
```python
from PIL import Image
import io

def strip_exif(image: PIL.Image) -> PIL.Image:
    """Remove EXIF metadata to protect user privacy."""
    data = list(image.getdata())
    clean = Image.new(image.mode, image.size)
    clean.putdata(data)
    return clean
```
Call this at the start of `ActionAgent.act()`.

### 6.3 Bias Disclosure

When `perception["language_script"]` is not `"latin"`, the agent must include a visible bias disclosure in the UI:
```
⚠️ Bias Notice: The selected vision model was primarily trained on Latin-script
documents. Extraction accuracy may be reduced for this content.
Confidence scores may not accurately reflect output quality.
```

### 6.4 No Silent Failure

The agent must never silently return low-quality output. If confidence is below threshold after all retries, it must:
1. Clearly state it could not meet quality standards
2. Offer the partial output with explicit warning
3. Suggest the user try with a better quality image

### 6.5 User Override / Control

The user must always be able to:
- Cancel any in-progress operation
- Override the agent's model selection (advanced settings panel)
- Download the raw extracted text without the agent-generated formatting

---

## 7. Legal & IPR Awareness

### 7.1 Model Licenses

| Model | License | Implications |
|---|---|---|
| Qwen2.5-VL / Qwen3-VL | Apache 2.0 | Free for commercial use; attribution required |
| GPT-4V (OpenAI) | Proprietary / OpenAI ToS | Cannot use outputs to train competing models; usage logged by OpenAI |

The agent must display model license info in the UI footer or info panel.

### 7.2 User Content Disclaimer

Display once at session start (use `st.session_state` to track if shown):
```
📋 Legal Notice: By uploading an image, you confirm that you have the legal
right to process and extract text from its contents. DocuVision does not
store your images. Extracted text is your responsibility to use in accordance
with applicable copyright and data protection laws.
```

### 7.3 Copyright Risk Detection

In `PerceptionAgent.perceive()`, assess `copyright_risk`:
- **High:** Image contains printed text in uniform columns (likely scanned book/article)
- **Medium:** Mixed printed and handwritten content
- **Low:** Clearly handwritten notes, personal diagrams

When `copyright_risk == "high"`, `DecisionAgent` adds a legal warning to the action plan, shown in the UI before extraction proceeds.

### 7.4 Data Protection
- No images are written to disk at any point
- All processing is in-memory during the session
- `agent_memory.json` stores only aggregated statistics — no image content, no user-identifiable data

---

## 8. Safety Mechanisms

### 8.1 Agent Action Log (Explainability)

Every action taken by every agent layer must produce a human-readable log entry. These are accumulated in `plan["agent_log"]` and `result["log"]` and displayed in the UI:

```python
# In app.py — show after extraction
with st.expander("🔍 Agent Decision Log", expanded=False):
    for entry in result.get("log", []):
        st.markdown(f"`{entry}`")
```

Log format convention:
- `🔍` = Perception observation
- `🧠` = Decision reasoning
- `⚡` = Action being taken
- `📊` = Metric/score
- `✅` = Success
- `⚠️` = Warning
- `❌` = Error or rejection
- `📚` = Learning/memory update

### 8.2 Human Override Controls

In the UI sidebar or advanced panel:
```python
with st.expander("⚙️ Advanced Controls"):
    override_model = st.selectbox("Override model selection", ["Auto (Agent Decides)"] + model_options)
    override_threshold = st.slider("Override confidence threshold", 0.0, 1.0, -1.0)
    st.caption("These override the agent's autonomous decisions. Use only if you know what you're doing.")
```

### 8.3 Hard Limits (Non-overridable)

The following cannot be overridden by the user:
1. EXIF stripping — always applied
2. Privacy gate — always applied; consent always required for sensitive content
3. Agent action logging — always on
4. No image persistence to disk — always enforced

### 8.4 Error Recovery

The agent must never crash silently. All exceptions in agent layers must be caught, logged, and surfaced to the user with a clear message. Use a top-level try/except in `app.py` wrapping the full pipeline:

```python
try:
    perception = perception_agent.perceive(image, file_metadata)
    plan = decision_agent.decide(perception, use_case_profile)
    result = action_agent.act(plan, image, extractor_registry)
    learning_agent.learn(result, perception, feedback)
except Exception as e:
    st.error(f"Agent pipeline error: {str(e)}")
    st.info("The agent encountered an unexpected error. Please try again or report this issue.")
```

---

## 9. File Structure & Integration Map

```
docuvision/
│
├── app.py                          # Main Streamlit app (MODIFY — integrate agent pipeline)
│
├── agents/                         # NEW directory — all agent classes
│   ├── __init__.py
│   ├── perception_agent.py         # NEW — PerceptionAgent class
│   ├── decision_agent.py           # NEW — DecisionAgent class
│   ├── action_agent.py             # NEW — ActionAgent class
│   ├── memory.py                   # NEW — AgentMemory class
│   └── learning_agent.py           # NEW — LearningAgent class
│
├── agent_memory.json               # NEW — auto-created by AgentMemory on first run
│
├── utils/                          # EXISTING — mostly unchanged
│   ├── image_utils.py              # MODIFY — add strip_exif(), enhance quality scoring
│   ├── vision_extractor.py         # EXISTING — no changes needed
│   └── docx_generator.py          # EXISTING — no changes needed
│
├── styles/
│   └── custom.css                  # EXISTING — add styles for agent log panel
│
└── requirements.txt                # MODIFY — add: langdetect, opencv-python-headless
```

### Integration Points in `app.py`

The existing `process_image()` function must be replaced with the full agent pipeline call. The manual model selector dropdown should be moved to an "Advanced / Override" expander, not the main UI. The main UI should display:

1. Image preview (existing)
2. Agent perception summary ("What the agent observed")
3. Agent decision summary ("What the agent decided and why")
4. Extracted text with confidence label
5. Agent action log (in expander)
6. Download button
7. Feedback buttons (👍 / 👎) that feed the learning agent

---

## 10. Implementation Checklist

The AI agent implementing this system must verify each item:

### Core Agentic Structure
- [ ] `PerceptionAgent` class created with all perception methods
- [ ] `DecisionAgent` class with model selection, ethics gate, industry thresholds
- [ ] `ActionAgent` class with extraction, retry logic, confidence estimation
- [ ] `AgentMemory` class with JSON persistence and session memory
- [ ] `LearningAgent` class with routing adaptation
- [ ] Full PIDAL loop wired together in `app.py`

### Ethical Requirements
- [ ] Privacy gate implemented — detects faces, signatures, ID features
- [ ] Consent prompt shown and pipeline halted awaiting user response
- [ ] EXIF stripping applied before model inference
- [ ] Bias disclosure shown for non-Latin scripts
- [ ] No silent failure — all low-confidence outputs labeled and disclosed

### Legal Requirements
- [ ] Model license info displayed in UI
- [ ] User content disclaimer shown at session start (once)
- [ ] Copyright risk detection in PerceptionAgent
- [ ] Legal warning shown in UI when copyright risk is high
- [ ] No image data stored in agent_memory.json

### Safety & Explainability
- [ ] Agent action log accumulated and displayed in UI expander
- [ ] Human override controls in advanced settings panel
- [ ] Hard limits enforced (EXIF strip, consent, logging always on)
- [ ] Top-level exception handler in app.py

### Learning
- [ ] `LearningAgent.learn()` called after every job
- [ ] Model performance stats updated in long-term memory
- [ ] Routing rules adapted based on historical performance
- [ ] User feedback (👍/👎) wired to `LearningAgent`

---

## 11. Critical Thinking & Known Limitations

The agent must honestly communicate these limitations to users and in the project report.

### Technical Limitations
1. **Confidence estimation is a proxy.** Without model-native confidence scores, the heuristic used (printable character ratio + length score) is imprecise. It will miss cases where the model produces fluent but incorrect text.
2. **Privacy detection is heuristic-based.** The face/signature detector using basic OpenCV may produce false positives and false negatives. It is a best-effort safety net, not a guarantee.
3. **Learning requires sufficient data.** The routing adaptation in `LearningAgent` requires many jobs to be meaningful. In early sessions, decisions will still be largely rule-based.
4. **No ground truth for accuracy.** The agent cannot verify that extracted text is correct — it can only estimate confidence. Human review remains necessary for high-stakes documents.

### Ethical Limitations
5. **Consent mechanism is not legally binding.** The in-app consent prompt is a UX safeguard, not a legal contract. The system cannot verify the user's claims about their rights to the image content.
6. **Bias mitigation is disclosure-only.** Informing the user of potential bias does not fix the bias. A true fix would require model fine-tuning on diverse scripts, which is beyond this project's scope.

### System Limitations
7. **Memory is local.** `agent_memory.json` is per-deployment. In a multi-user hosted scenario, memory would need a proper database to avoid cross-user data mixing.
8. **No audit trail for legal compliance.** The ethics log records event types but not enough detail for formal GDPR compliance. A production system would need a proper audit trail with a legal basis for each processing activity.

---

*End of DocuVision Phase 2 Methodology Document*

*This document was authored as a context reference for an AI coding agent. All code snippets are illustrative of required behavior — the implementing agent should treat them as specifications, not copy-paste solutions, and adapt them to fit the existing codebase structure.*
