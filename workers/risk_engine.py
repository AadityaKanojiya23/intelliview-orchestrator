"""
Risk Scoring Engine
Combines signals from all pipelines to calculate final interview risk score

Responsibilities:
- Normalize signals from different pipelines
- Apply weighted scoring
- Generate final risk score (0-1 scale)
- Provide risk classification
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RiskScoringEngine:
    """
    Calculates comprehensive risk scores from interview analysis results
    """

    # Weights for each pipeline component
    VIDEO_WEIGHT = 0.4
    AUDIO_WEIGHT = 0.3
    EVALUATION_WEIGHT = 0.3

    # Risk thresholds for classification
    LOW_RISK_THRESHOLD = 0.3
    MEDIUM_RISK_THRESHOLD = 0.6
    HIGH_RISK_THRESHOLD = 0.8

    # Individual risk factor weights
    VIDEO_FACTORS = {
        "multiple_persons": 0.35,  # High risk: multiple people visible
        "phone_detected": 0.25,  # High risk: phone usage
        "suspicious_head_movement": 0.20,  # Medium risk: unusual behavior
        "no_face_detected": 0.45,  # Critical: candidate not visible
    }

    AUDIO_FACTORS = {
        "background_voices": 0.35,  # High risk: external help
        "suspicious_pattern": 0.25,  # Medium risk: memorized/scripted
        "no_transcription": 0.40,  # High risk: no speech
    }

    EVALUATION_FACTORS = {
        "low_quality_answers": 0.30,  # Medium risk: poor quality
        "low_accuracy": 0.40,  # High risk: wrong answers
        "poor_communication": 0.20,  # Low-medium risk: communication issues
    }

    @staticmethod
    def calculate_video_risk(video_result: Dict[str, Any]) -> float:
        """
        Calculate risk score from video analysis

        Args:
            video_result: Video analysis results

        Returns:
            float: Risk score between 0 and 1
        """
        risk_score = 0.0

        # Check for multiple persons (highest risk)
        if video_result.get("multiple_persons", {}).get("multiple_persons_detected"):
            risk_score += RiskScoringEngine.VIDEO_FACTORS["multiple_persons"]

        # Check for phone detection (high risk)
        if video_result.get("phone_detected", {}).get("phone_detected"):
            risk_score += RiskScoringEngine.VIDEO_FACTORS["phone_detected"]

        # Check for suspicious head movement (medium risk)
        if video_result.get("head_movement_suspicious", {}).get(
            "suspicious_movement_detected"
        ):
            risk_score += RiskScoringEngine.VIDEO_FACTORS["suspicious_head_movement"]

        # Check for face detection (critical - no candidate visible)
        if not video_result.get("face_detected", {}).get("faces_found"):
            risk_score += RiskScoringEngine.VIDEO_FACTORS["no_face_detected"]

        # Normalize to 0-1 scale
        return min(risk_score, 1.0)

    @staticmethod
    def calculate_audio_risk(audio_result: Dict[str, Any]) -> float:
        """
        Calculate risk score from audio analysis

        Args:
            audio_result: Audio analysis results

        Returns:
            float: Risk score between 0 and 1
        """
        risk_score = 0.0

        # Check for background voices (highest risk - external help)
        if audio_result.get("background_voices", {}).get("background_voices_detected"):
            risk_score += RiskScoringEngine.AUDIO_FACTORS["background_voices"]

        # Check for suspicious conversation patterns (medium risk)
        if audio_result.get("suspicious_conversation", {}).get(
            "suspicious_pattern_detected"
        ):
            risk_score += RiskScoringEngine.AUDIO_FACTORS["suspicious_pattern"]

        # Check for transcription quality (high risk if no speech)
        if not audio_result.get("transcription", {}).get("text"):
            risk_score += RiskScoringEngine.AUDIO_FACTORS["no_transcription"]

        # Normalize to 0-1 scale
        return min(risk_score, 1.0)

    @staticmethod
    def calculate_evaluation_risk(evaluation_result: Dict[str, Any]) -> float:
        """
        Calculate risk score from answer evaluation

        Args:
            evaluation_result: Answer evaluation results

        Returns:
            float: Risk score between 0 and 1
        """
        risk_score = 0.0

        # Extract quality scores (0-100 scale, convert to risk which is inverse)
        quality_score = evaluation_result.get("answer_quality_score", {}).get(
            "overall_quality_score", 50
        )
        accuracy_score = evaluation_result.get("technical_accuracy", {}).get(
            "accuracy_score", 50
        )
        clarity_score = evaluation_result.get("communication_clarity", {}).get(
            "clarity_score", 50
        )

        # Convert performance scores to risk scores (inverse relationship)
        # Low quality = high risk
        if quality_score < 40:
            risk_score += RiskScoringEngine.EVALUATION_FACTORS["low_quality_answers"]

        # Low accuracy = high risk
        if accuracy_score < 40:
            risk_score += RiskScoringEngine.EVALUATION_FACTORS["low_accuracy"]

        # Poor communication = medium risk
        if clarity_score < 40:
            risk_score += RiskScoringEngine.EVALUATION_FACTORS["poor_communication"]

        # Normalize to 0-1 scale
        return min(risk_score, 1.0)

    @staticmethod
    def calculate_final_risk(
        video_risk: float, audio_risk: float, evaluation_risk: float
    ) -> float:
        """
        Calculate final combined risk score using weighted average

        Formula:
        final_risk = (0.4 * video_risk) + (0.3 * audio_risk) + (0.3 * evaluation_risk)

        Args:
            video_risk: Video analysis risk score (0-1)
            audio_risk: Audio analysis risk score (0-1)
            evaluation_risk: Answer evaluation risk score (0-1)

        Returns:
            float: Final risk score between 0 and 1
        """
        final_risk = (
            RiskScoringEngine.VIDEO_WEIGHT * video_risk
            + RiskScoringEngine.AUDIO_WEIGHT * audio_risk
            + RiskScoringEngine.EVALUATION_WEIGHT * evaluation_risk
        )

        # Ensure the score is within 0-1 range
        return round(min(max(final_risk, 0.0), 1.0), 3)

    @staticmethod
    def classify_risk(risk_score: float) -> str:
        """
        Classify risk level based on score

        Args:
            risk_score: Risk score between 0 and 1

        Returns:
            str: Risk classification (LOW, MEDIUM, HIGH, CRITICAL)
        """
        if risk_score < RiskScoringEngine.LOW_RISK_THRESHOLD:
            return "LOW"
        elif risk_score < RiskScoringEngine.MEDIUM_RISK_THRESHOLD:
            return "MEDIUM"
        elif risk_score < RiskScoringEngine.HIGH_RISK_THRESHOLD:
            return "HIGH"
        else:
            return "CRITICAL"

    @staticmethod
    def generate_risk_report(
        session_id: str,
        video_result: Dict[str, Any],
        audio_result: Dict[str, Any],
        evaluation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive risk report from all analysis results

        Args:
            session_id: Interview session identifier
            video_result: Video analysis results
            audio_result: Audio analysis results
            evaluation_result: Answer evaluation results

        Returns:
            dict: Comprehensive risk report
        """
        logger.info(f"Generating risk report for session {session_id}")

        # Calculate individual component risks
        video_risk = RiskScoringEngine.calculate_video_risk(video_result)
        audio_risk = RiskScoringEngine.calculate_audio_risk(audio_result)
        evaluation_risk = RiskScoringEngine.calculate_evaluation_risk(evaluation_result)

        # Calculate final risk score
        final_risk = RiskScoringEngine.calculate_final_risk(
            video_risk, audio_risk, evaluation_risk
        )

        # Classify risk level
        risk_classification = RiskScoringEngine.classify_risk(final_risk)

        # Generate risk factors list
        risk_factors = RiskScoringEngine._identify_risk_factors(
            video_result, audio_result, evaluation_result
        )

        report = {
            "session_id": session_id,
            "final_risk_score": final_risk,
            "risk_classification": risk_classification,
            "component_risks": {
                "video_risk": video_risk,
                "audio_risk": audio_risk,
                "evaluation_risk": evaluation_risk,
            },
            "risk_factors": risk_factors,
            "recommendation": RiskScoringEngine._generate_recommendation(
                risk_classification
            ),
        }

        logger.info(
            f"Risk report generated: {risk_classification} (score: {final_risk})"
        )
        return report

    @staticmethod
    def _identify_risk_factors(
        video_result: Dict[str, Any],
        audio_result: Dict[str, Any],
        evaluation_result: Dict[str, Any],
    ) -> list:
        """
        Identify specific risk factors from analysis results

        Args:
            video_result: Video analysis results
            audio_result: Audio analysis results
            evaluation_result: Answer evaluation results

        Returns:
            list: List of identified risk factors
        """
        risk_factors = []

        # Video risk factors
        if not video_result.get("face_detected", {}).get("faces_found"):
            risk_factors.append("Candidate face not detected")

        if video_result.get("multiple_persons", {}).get("multiple_persons_detected"):
            risk_factors.append("Multiple persons detected in frame")

        if video_result.get("phone_detected", {}).get("phone_detected"):
            risk_factors.append("Mobile phone detected")

        if video_result.get("head_movement_suspicious", {}).get(
            "suspicious_movement_detected"
        ):
            risk_factors.append("Suspicious head movement detected")

        # Audio risk factors
        if audio_result.get("background_voices", {}).get("background_voices_detected"):
            risk_factors.append("Background voices detected - possible external help")

        if audio_result.get("suspicious_conversation", {}).get(
            "suspicious_pattern_detected"
        ):
            risk_factors.append("Suspicious conversation pattern detected")

        if not audio_result.get("transcription", {}).get("text"):
            risk_factors.append("No speech detected during interview")

        # Evaluation risk factors
        quality_score = evaluation_result.get("answer_quality_score", {}).get(
            "overall_quality_score", 50
        )
        accuracy_score = evaluation_result.get("technical_accuracy", {}).get(
            "accuracy_score", 50
        )

        if quality_score < 40:
            risk_factors.append("Low answer quality detected")

        if accuracy_score < 40:
            risk_factors.append("Low technical accuracy detected")

        return risk_factors

    @staticmethod
    def _generate_recommendation(risk_classification: str) -> str:
        """
        Generate recommendation based on risk classification

        Args:
            risk_classification: Risk level classification

        Returns:
            str: Recommendation text
        """
        recommendations = {
            "LOW": "Candidate appears genuine. Proceed with hiring consideration.",
            "MEDIUM": "Monitor candidate responses. Further verification may be needed.",
            "HIGH": "Multiple concerning factors detected. Recommend interview review.",
            "CRITICAL": "Significant fraud indicators detected. Recommend rejection or investigation.",
        }

        return recommendations.get(risk_classification, "Review interview manually.")
