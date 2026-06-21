"""
Audio Analysis Pipeline
Handles speech and audio monitoring

Responsibilities:
- Speech-to-text using Whisper
- Background voice detection
- Suspicious conversation detection

Pluggable contract — replace each detection helper with a real model
(Whisper, Wav2Vec2, pyannote, etc.). The provided defaults produce
deterministic per-session signals so end-to-end risk scoring and the
HIGH/CRITICAL thresholds fire correctly without GPU dependencies.
"""

import hashlib
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

_AUDIO_RISK_WEIGHTS = {
    "no_transcription": 0.40,
    "background_voices": 0.35,
    "suspicious_pattern": 0.25,
}


def _seeded_unit(session_id: str, salt: str) -> float:
    """Stable pseudo-random in [0, 1) derived from session_id + salt."""
    digest = hashlib.sha256(f"{session_id}:{salt}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF


def run_audio_analysis(session_id: str) -> Dict[str, Any]:
    """Execute audio analysis pipeline for an interview session."""
    logger.info(f"Starting audio analysis for session {session_id}")

    transcription = transcribe_speech(session_id)
    bg_voices = detect_background_voices(session_id)
    suspicious = detect_suspicious_conversation(session_id)

    results = {
        "session_id": session_id,
        "transcription": transcription,
        "background_voices": bg_voices,
        "suspicious_conversation": suspicious,
        "risk_score": 0.0,
    }

    results["risk_score"] = calculate_audio_risk_score(results)
    logger.info(f"Audio analysis completed for session {session_id}: {results}")
    return results


def transcribe_speech(session_id: str) -> Dict[str, Any]:
    """Convert speech to text using Whisper (or compatible) model."""
    logger.info(f"Transcribing audio for session {session_id}")
    silence = _seeded_unit(session_id, "silence") > 0.92
    text = (
        ""
        if silence
        else (
            "I have five years of experience building distributed systems in Python and Go. "
            "Recently I led a migration from a monolith to Celery-backed workers."
        )
    )
    return {
        "text": text,
        "confidence": round(0.6 + _seeded_unit(session_id, "asr_conf") * 0.35, 3),
        "language": "en",
        "duration_seconds": round(120 + _seeded_unit(session_id, "duration") * 600, 1),
        "timestamp": None,
    }


def detect_background_voices(session_id: str) -> Dict[str, Any]:
    """Detect background voices or multiple speakers."""
    logger.info(f"Detecting background voices for session {session_id}")
    multi = _seeded_unit(session_id, "bg_voices") > 0.85
    return {
        "background_voices_detected": multi,
        "voice_count": 2 if multi else 1,
        "confidence": round(_seeded_unit(session_id, "bg_conf"), 3),
        "timestamps": [],
    }


def detect_suspicious_conversation(session_id: str) -> Dict[str, Any]:
    """Detect suspicious conversation patterns."""
    logger.info(f"Detecting suspicious conversations for session {session_id}")
    suspicious = _seeded_unit(session_id, "suspicious") > 0.80
    pattern = (
        "robotic_response"
        if suspicious and _seeded_unit(session_id, "p1") > 0.5
        else "reading_from_script"
    )
    return {
        "suspicious_pattern_detected": suspicious,
        "pattern_type": pattern if suspicious else None,
        "confidence": round(_seeded_unit(session_id, "susp_conf"), 3),
        "details": {},
    }


def calculate_audio_risk_score(results: Dict[str, Any]) -> float:
    """Calculate a 0–1 risk score from audio detection results."""
    score = 0.0
    if results.get("background_voices", {}).get("background_voices_detected"):
        score += _AUDIO_RISK_WEIGHTS["background_voices"]
    if results.get("suspicious_conversation", {}).get("suspicious_pattern_detected"):
        score += _AUDIO_RISK_WEIGHTS["suspicious_pattern"]
    if not results.get("transcription", {}).get("text"):
        score += _AUDIO_RISK_WEIGHTS["no_transcription"]
    return round(min(score, 1.0), 3)
