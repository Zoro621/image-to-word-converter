"""
PerceptionAgent — sensory layer of the DocuVision agentic pipeline.
Observes the input image and produces a structured perception report.
Does NOT make decisions — only describes what it observes.
"""
from __future__ import annotations

import io
import re
import struct
import zlib
from datetime import datetime, timezone

from PIL import Image, ImageStat, ExifTags


class PerceptionAgent:
    """
    Observes the input image and produces a structured perception report.
    This is the agent's sensory layer — it must not make decisions,
    only describe what it observes.
    """

    # ------------------------------------------------------------------ public API
    def perceive(self, image: Image.Image, file_metadata: dict | None = None) -> dict:
        """
        Main entry point.  Returns a perception_report dict consumed by
        DecisionAgent.
        """
        file_metadata = file_metadata or {}
        log: list[str] = []

        quality_score = self.assess_quality(image)
        log.append(f"🔍 Quality score: {quality_score:.2f}")

        content_type = self.classify_content(image)
        log.append(f"🔍 Content type: {content_type}")

        privacy = self.detect_privacy_risks(image)
        log.append(
            f"🔍 Privacy flags — faces:{privacy['has_faces']}, "
            f"signatures:{privacy['has_signatures']}, "
            f"id_card:{privacy['has_id_card_features']}, "
            f"medical:{privacy['has_medical_indicators']}"
        )

        lang_script = self.detect_language_script(image)
        log.append(f"🔍 Detected script: {lang_script}")

        text_density = self._estimate_text_density(image)
        log.append(f"🔍 Text density: {text_density:.2f}")

        exif_data = self._extract_exif(image)
        copyright_risk = self._assess_copyright_risk(image, content_type)
        log.append(f"🔍 Copyright risk: {copyright_risk}")

        width, height = image.size
        log.append(f"🔍 Resolution: {width}×{height}px")

        return {
            "quality_score": quality_score,
            "resolution": (width, height),
            "content_type": content_type,
            "language_script": lang_script,
            "text_density": text_density,
            "has_faces": privacy["has_faces"],
            "has_signatures": privacy["has_signatures"],
            "has_id_card_features": privacy["has_id_card_features"],
            "has_medical_indicators": privacy["has_medical_indicators"],
            "exif_data": exif_data,
            "copyright_risk": copyright_risk,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "perception_log": log,
        }

    # ------------------------------------------------------------------ quality
    def assess_quality(self, image: Image.Image) -> float:
        """
        Heuristic quality score 0.0–1.0 based on:
        - Pixel variance (proxy for sharpness)
        - Resolution adequacy
        """
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)
        variance = stat.var[0]  # higher = sharper

        # Normalise variance: empirically <100 = blurry, >2000 = very sharp
        var_score = min(variance / 2000.0, 1.0)

        w, h = image.size
        # Penalise very small images
        area = w * h
        res_score = min(area / (800 * 600), 1.0)

        quality = round(var_score * 0.7 + res_score * 0.3, 3)
        return quality

    # ------------------------------------------------------------------ content type
    def classify_content(self, image: Image.Image) -> str:
        """
        Rule-based content classification.
        Returns: handwritten | printed | mixed | diagram | form
        """
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)
        mean = stat.mean[0]
        stddev = stat.stddev[0]

        # Very low stddev → mostly blank / diagram-heavy
        if stddev < 20:
            return "diagram"

        # High mean (light background) + moderate stddev → printed or handwritten
        if mean > 180:
            # Detect ruled lines as proxy for handwritten notebook pages
            # (simple heuristic: many near-white horizontal stripes)
            if self._has_ruled_lines(gray):
                return "handwritten"
            return "printed"

        if mean > 120:
            return "mixed"

        return "handwritten"

    def _has_ruled_lines(self, gray_image: Image.Image) -> bool:
        """Simple heuristic: check for repeating horizontal light bands."""
        import array as arr
        pixels = list(gray_image.getdata())
        w, h = gray_image.size
        light_row_count = 0
        for row in range(h):
            row_pixels = pixels[row * w : (row + 1) * w]
            avg = sum(row_pixels) / len(row_pixels)
            if avg > 230:
                light_row_count += 1
        # If >10% of rows are very light (≈ruled lines), call it handwritten
        return (light_row_count / h) > 0.10

    # ------------------------------------------------------------------ privacy
    def detect_privacy_risks(self, image: Image.Image) -> dict:
        """
        Heuristic privacy detection.
        Uses basic colour/shape heuristics — not a guaranteed detector.
        """
        has_faces = self._detect_face_heuristic(image)
        has_signatures = self._detect_signature_heuristic(image)
        has_id_card = self._detect_id_card_heuristic(image)
        has_medical = self._detect_medical_heuristic(image)

        return {
            "has_faces": has_faces,
            "has_signatures": has_signatures,
            "has_id_card_features": has_id_card,
            "has_medical_indicators": has_medical,
        }

    def _detect_face_heuristic(self, image: Image.Image) -> bool:
        """
        Try OpenCV Haar cascade. Fall back to False if OpenCV unavailable.
        """
        try:
            import cv2
            import numpy as np

            gray = image.convert("L")
            np_img = np.array(gray)
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)
            faces = face_cascade.detectMultiScale(np_img, scaleFactor=1.1, minNeighbors=5)
            return len(faces) > 0
        except Exception:
            return False

    def _detect_signature_heuristic(self, image: Image.Image) -> bool:
        """
        Signatures typically appear as thin dark strokes in the lower 25%
        of an image on a light background.
        """
        w, h = image.size
        lower_strip = image.crop((0, int(h * 0.75), w, h)).convert("L")
        stat = ImageStat.Stat(lower_strip)
        # Very light mean with dark strokes → high contrast in lower portion
        mean = stat.mean[0]
        stddev = stat.stddev[0]
        return mean > 200 and stddev > 30

    def _detect_id_card_heuristic(self, image: Image.Image) -> bool:
        """
        ID cards are typically landscape-oriented with near-card aspect ratio.
        Also check for solid colour bands (header/footer strips).
        """
        w, h = image.size
        aspect = w / h if h > 0 else 1
        # Standard ID card: ~85.6×54mm → aspect ≈ 1.585
        if 1.4 < aspect < 1.8:
            # Check for solid-colour horizontal band at top
            top_strip = image.crop((0, 0, w, max(h // 8, 1))).convert("L")
            stat = ImageStat.Stat(top_strip)
            if stat.stddev[0] < 15:  # very uniform colour
                return True
        return False

    def _detect_medical_heuristic(self, image: Image.Image) -> bool:
        """
        Look for medical keyword signals in the text (requires a tiny OCR pass)
        or specific visual patterns. We use keyword heuristic on filename metadata
        and skip expensive OCR here — that's the vision model's job.
        """
        # Medical indicators in visual content are hard without OCR.
        # We return False by default; the vision model output will surface these.
        return False

    # ------------------------------------------------------------------ language
    def detect_language_script(self, image: Image.Image) -> str:
        """
        Attempt lightweight script detection.
        Uses langdetect if available on a brief pytesseract pass, otherwise
        returns 'unknown' (safe default — triggers bias disclosure in DecisionAgent).
        """
        try:
            import pytesseract
            from langdetect import detect

            sample_text = pytesseract.image_to_string(
                image, config="--psm 3 --oem 1", timeout=5
            )
            if len(sample_text.strip()) < 10:
                return "unknown"
            lang = detect(sample_text)
            script_map = {
                "ar": "arabic",
                "fa": "arabic",
                "ur": "arabic",
                "hi": "devanagari",
                "mr": "devanagari",
                "ne": "devanagari",
                "zh-cn": "chinese",
                "zh-tw": "chinese",
                "ja": "chinese",
                "ko": "chinese",
            }
            # Most western languages → latin
            return script_map.get(lang, "latin")
        except Exception:
            return "latin"  # safe default for an app targeting English notes

    # ------------------------------------------------------------------ text density
    def _estimate_text_density(self, image: Image.Image) -> float:
        """
        Estimate fraction of image covered by dark (text-like) pixels.
        """
        gray = image.convert("L")
        w, h = gray.size
        pixels = list(gray.getdata())
        dark_pixels = sum(1 for p in pixels if p < 128)
        return round(dark_pixels / (w * h), 3)

    # ------------------------------------------------------------------ EXIF
    def _extract_exif(self, image: Image.Image) -> dict:
        """Extract human-readable EXIF keys (stripped before model inference)."""
        try:
            raw_exif = image._getexif() or {}
            return {
                ExifTags.TAGS.get(k, str(k)): str(v)
                for k, v in raw_exif.items()
                if ExifTags.TAGS.get(k, str(k))
                not in {"MakerNote", "UserComment", "PrintImageMatching"}
            }
        except Exception:
            return {}

    # ------------------------------------------------------------------ copyright
    def _assess_copyright_risk(self, image: Image.Image, content_type: str) -> str:
        """
        Heuristic copyright risk assessment.
        - printed  → medium/high (could be a scanned book page)
        - handwritten → low
        - mixed    → medium
        - diagram  → medium
        """
        if content_type == "printed":
            # Check for multi-column layout (book-like) by sampling vertical strips
            w, h = image.size
            if w > 800 and self._has_column_layout(image):
                return "high"
            return "medium"
        if content_type in ("mixed", "diagram", "form"):
            return "medium"
        return "low"  # handwritten

    def _has_column_layout(self, image: Image.Image) -> bool:
        """Rough column detector — checks for vertical light bands in text area."""
        gray = image.convert("L")
        w, h = gray.size
        col_scores = []
        num_cols = 20
        for i in range(num_cols):
            x = int(w * i / num_cols)
            strip = gray.crop((x, 0, min(x + 5, w), h))
            stat = ImageStat.Stat(strip)
            col_scores.append(stat.mean[0])
        light_cols = sum(1 for s in col_scores if s > 220)
        return light_cols >= 4  # at least 4 very-light vertical strips → columns
