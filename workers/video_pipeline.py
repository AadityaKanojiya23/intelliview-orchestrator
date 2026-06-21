"""
Video Analysis Pipeline
Handles computer vision tasks for interview monitoring

Responsibilities:
- Face detection
- Head movement detection
- Mobile phone detection
- Multiple person detection

This module defines the **pluggable contract** the orchestrator relies on.
Replace each detection helper with a real model (MediaPipe, YOLO, OpenCV,
etc.) — the returned dict shape is what `RiskScoringEngine` consumes.

The provided defaults are deterministic per-session seeds so that:
  * end-to-end risk scores are non-trivial in tests / demos,
  * risk classification thresholds (LOW/MEDIUM/HIGH/CRITICAL) actually
    fire under load,
  * operators can sanity-check the pipeline without GPU dependencies.
"""

import hashlib
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

_VIDEO_RISK_WEIGHTS = {
    "no_face": 0.45,
    "multiple_persons": 0.35,
    "phone": 0.25,
    "head_movement": 0.20,
}


def _seeded_unit(session_id: str, salt: str) -> float:
    """Stable pseudo-random in [0, 1) derived from session_id + salt."""
    digest = hashlib.sha256(f"{session_id}:{salt}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF


def run_video_analysis(session_id: str) -> Dict[str, Any]:
    """
    Execute video analysis pipeline for an interview session.

    Args:
        session_id: Unique interview session identifier.

    Returns:
        dict: Analysis results including detection findings and risk scores.
    """
    logger.info(f"Starting video analysis for session {session_id}")

    face = detect_face(session_id)
    head = detect_suspicious_head_movement(session_id)
    phone = detect_mobile_phone(session_id)
    multi = detect_multiple_persons(session_id)

    results = {
        "session_id": session_id,
        "face_detected": face,
        "head_movement_suspicious": head,
        "phone_detected": phone,
        "multiple_persons": multi,
        "risk_score": 0.0,
    }

    results["risk_score"] = calculate_video_risk_score(results)
    logger.info(f"Video analysis completed for session {session_id}: {results}")
    return results


def detect_face(session_id: str) -> Dict[str, Any]:
    """Detect faces in video frames."""
    logger.info(f"Detecting faces for session {session_id}")
    return {
        "faces_found": _seeded_unit(session_id, "face") > 0.05,
        "face_count": 1 if _seeded_unit(session_id, "face") > 0.05 else 0,
        "confidence": round(0.85 + _seeded_unit(session_id, "face_conf") * 0.1, 3),
        "timestamp": None,
    }


def detect_suspicious_head_movement(session_id: str) -> Dict[str, Any]:
    """Detect suspicious head movement patterns."""
    logger.info(f"Detecting head movements for session {session_id}")
    suspicion = _seeded_unit(session_id, "head")
    return {
        "suspicious_movement_detected": suspicion > 0.75,
        "head_turns_count": int(suspicion * 12),
        "avg_gaze_deviation": round(suspicion, 3),
        "timestamp": None,
    }


def detect_mobile_phone(session_id: str) -> Dict[str, Any]:
    """Detect if mobile phone is visible or used during interview."""
    logger.info(f"Detecting mobile phone for session {session_id}")
    detected = _seeded_unit(session_id, "phone") > 0.85
    return {
        "phone_detected": detected,
        "phone_usage_detected": detected,
        "detection_confidence": round(_seeded_unit(session_id, "phone_conf"), 3),
        "timestamp": None,
    }


def detect_multiple_persons(session_id: str) -> Dict[str, Any]:
    """Detect if multiple persons are visible in the frame."""
    logger.info(f"Detecting multiple persons for session {session_id}")
    multi = _seeded_unit(session_id, "multi") > 0.88
    return {
        "multiple_persons_detected": multi,
        "person_count": 2 if multi else 1,
        "detection_confidence": round(_seeded_unit(session_id, "multi_conf"), 3),
        "timestamp": None,
    }


def calculate_video_risk_score(results: Dict[str, Any]) -> float:
    """Calculate a 0–1 risk score from video detection results."""
    score = 0.0
    if results.get("multiple_persons", {}).get("multiple_persons_detected"):
        score += _VIDEO_RISK_WEIGHTS["multiple_persons"]
    if results.get("phone_detected", {}).get("phone_detected"):
        score += _VIDEO_RISK_WEIGHTS["phone"]
    if results.get("head_movement_suspicious", {}).get("suspicious_movement_detected"):
        score += _VIDEO_RISK_WEIGHTS["head_movement"]
    if not results.get("face_detected", {}).get("faces_found"):
        score += _VIDEO_RISK_WEIGHTS["no_face"]
    return round(min(score, 1.0), 3)
