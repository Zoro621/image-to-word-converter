"""
AgentMemory — Two-tier memory (session RAM + long-term JSON).
"""
import os
import json
import copy
from datetime import datetime, timezone


class AgentMemory:
    """
    Provides short-term (session) and long-term (JSON-persisted) memory
    for the DocuVision agentic pipeline.
    """

    MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "agent_memory.json")

    DEFAULT_LONG_TERM: dict = {
        "model_performance": {
            "Qwen3-VL-8B": {
                "jobs": 0,
                "total_confidence": 0.0,
                "failures": 0,
                "avg_confidence": 0.75,
            },
            "GPT-4-Vision": {
                "jobs": 0,
                "total_confidence": 0.0,
                "failures": 0,
                "avg_confidence": 0.80,
            },
        },
        "content_type_routing": {},
        "script_performance": {},
        "ethics_log": [],
        "job_count": 0,
    }

    def __init__(self) -> None:
        self.session: dict = {
            "current_job": {},
            "retry_count": 0,
            "corrections": [],
        }
        self.long_term: dict = self._load()

    # ------------------------------------------------------------------ load / save
    def _load(self) -> dict:
        path = os.path.abspath(self.MEMORY_FILE)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Backfill any missing top-level keys
                for k, v in self.DEFAULT_LONG_TERM.items():
                    data.setdefault(k, copy.deepcopy(v))
                return data
            except (json.JSONDecodeError, OSError):
                pass
        return copy.deepcopy(self.DEFAULT_LONG_TERM)

    def save(self) -> None:
        path = os.path.abspath(self.MEMORY_FILE)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.long_term, f, indent=2)
        except OSError:
            pass  # non-fatal — memory continues in RAM

    # ------------------------------------------------------------------ model stats
    def update_model_stats(
        self, model: str, confidence: float, failed: bool = False
    ) -> None:
        stats = self.long_term["model_performance"].setdefault(
            model,
            {"jobs": 0, "total_confidence": 0.0, "failures": 0, "avg_confidence": 0.0},
        )
        stats["jobs"] += 1
        stats["total_confidence"] += confidence
        if failed:
            stats["failures"] += 1
        stats["avg_confidence"] = round(
            stats["total_confidence"] / stats["jobs"], 4
        )
        self.long_term["job_count"] += 1
        self.save()

    def get_model_performance(self) -> dict:
        return self.long_term["model_performance"]

    # ------------------------------------------------------------------ routing
    def get_routing(self) -> dict:
        return self.long_term.get("content_type_routing", {})

    def set_routing(self, key: str, model: str) -> None:
        self.long_term.setdefault("content_type_routing", {})[key] = model
        self.save()

    def get_script_performance(self) -> dict:
        return self.long_term.get("script_performance", {})

    def record_script_score(self, script: str, model: str, score: float) -> None:
        sp = self.long_term.setdefault("script_performance", {})
        sp.setdefault(script, {})[model] = round(
            (sp.get(script, {}).get(model, score) + score) / 2, 4
        )
        self.save()

    # ------------------------------------------------------------------ ethics log
    def log_ethics_event(self, event_type: str, details: str) -> None:
        """Anonymised — no image data, no user-identifiable information."""
        self.long_term["ethics_log"].append(
            {
                "type": event_type,
                "details": details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.save()

    # ------------------------------------------------------------------ job count
    @property
    def total_jobs(self) -> int:
        return self.long_term.get("job_count", 0)
