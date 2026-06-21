"""
Answer Evaluation Pipeline
Handles interview answer evaluation and scoring

Responsibilities:
- LLM-based answer evaluation
- Score generation
- Feedback generation

Pluggable contract — replace each evaluator with your own LLM client
(OpenAI, Anthropic, local Llama, etc.). The provided defaults produce
deterministic per-session signals so the risk engine's HIGH/CRITICAL
thresholds exercise without external services.
"""

import hashlib
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

_EVAL_RISK_WEIGHTS = {
    "low_quality": 0.30,
    "low_accuracy": 0.40,
    "poor_communication": 0.20,
}


def _seeded_unit(session_id: str, salt: str) -> float:
    """Stable pseudo-random in [0, 1) derived from session_id + salt."""
    digest = hashlib.sha256(f"{session_id}:{salt}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF


def evaluate_answers(session_id: str) -> Dict[str, Any]:
    """Execute answer evaluation pipeline for an interview session."""
    logger.info(f"Starting answer evaluation for session {session_id}")

    quality = evaluate_answer_quality(session_id)
    accuracy = evaluate_technical_accuracy(session_id)
    clarity = evaluate_communication(session_id)
    feedback = generate_feedback(session_id)

    results = {
        "session_id": session_id,
        "answer_quality_score": quality,
        "technical_accuracy": accuracy,
        "communication_clarity": clarity,
        "feedback": feedback,
        "risk_score": 0.0,
    }

    results["risk_score"] = calculate_evaluation_risk_score(results)
    logger.info(f"Answer evaluation completed for session {session_id}: {results}")
    return results


def evaluate_answer_quality(session_id: str) -> Dict[str, Any]:
    """Evaluate the quality and relevance of answers using LLM."""
    logger.info(f"Evaluating answer quality for session {session_id}")
    base = 0.55 + _seeded_unit(session_id, "quality") * 0.45
    return {
        "overall_quality_score": round(base * 100, 2),
        "relevance": round(base * 0.95, 2),
        "completeness": round(base * 0.9, 2),
        "clarity": round(base * 0.92, 2),
        "feedback": "Response is on-topic and reasonably complete.",
    }


def evaluate_technical_accuracy(session_id: str) -> Dict[str, Any]:
    """Evaluate technical accuracy and correctness of answers."""
    logger.info(f"Evaluating technical accuracy for session {session_id}")
    base = 0.5 + _seeded_unit(session_id, "accuracy") * 0.5
    return {
        "accuracy_score": round(base * 100, 2),
        "correct_concepts_count": int(base * 8),
        "incorrect_concepts_count": max(0, 3 - int(base * 8)),
        "knowledge_gaps": [] if base > 0.6 else ["systems design depth"],
    }


def evaluate_communication(session_id: str) -> Dict[str, Any]:
    """Evaluate communication clarity and professional presentation."""
    logger.info(f"Evaluating communication clarity for session {session_id}")
    base = 0.55 + _seeded_unit(session_id, "comms") * 0.45
    return {
        "clarity_score": round(base * 100, 2),
        "professionalism": round(base * 100, 2),
        "confidence_level": round(base * 0.9, 2),
        "pace_appropriateness": round(base * 0.95, 2),
    }


def generate_feedback(session_id: str) -> Dict[str, Any]:
    """Generate comprehensive feedback based on evaluation."""
    logger.info(f"Generating feedback for session {session_id}")
    return {
        "strengths": ["clear structure", "relevant examples"],
        "improvements": ["deepen systems-design discussion"],
        "detailed_feedback": "Solid answers overall with room to elaborate on trade-offs.",
        "recommendation": "progress",
    }


def calculate_evaluation_risk_score(results: Dict[str, Any]) -> float:
    """Calculate a 0–1 risk score (inverse of performance)."""
    quality = (
        results.get("answer_quality_score", {}).get("overall_quality_score", 50) / 100.0
    )
    accuracy = results.get("technical_accuracy", {}).get("accuracy_score", 50) / 100.0
    clarity = results.get("communication_clarity", {}).get("clarity_score", 50) / 100.0

    quality_risk = (1 - quality) * _EVAL_RISK_WEIGHTS["low_quality"]
    accuracy_risk = (1 - accuracy) * _EVAL_RISK_WEIGHTS["low_accuracy"]
    clarity_risk = (1 - clarity) * _EVAL_RISK_WEIGHTS["poor_communication"]

    score = quality_risk + accuracy_risk + clarity_risk
    return round(min(score, 1.0), 3)
