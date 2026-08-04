"""
Scoring Models

Provides a pluggable interface for risk scoring models.

Model A:
    Existing weighted RiskScoringEngine.

Model B:
    Experimental weighted model used for A/B testing.

Future models only need to inherit BaseRiskScoringModel.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from workers.risk_engine import RiskScoringEngine


class BaseRiskScoringModel(ABC):
    """
    Abstract interface for every risk scoring model.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique model name."""

    @abstractmethod
    def generate_report(
        self,
        session_id: str,
        video_result: dict[str, Any],
        audio_result: dict[str, Any],
        evaluation_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a complete risk report.
        """


class WeightedRiskModel(BaseRiskScoringModel):
    """
    Production model.

    Uses the existing RiskScoringEngine without modification.
    """

    @property
    def name(self) -> str:
        return "weighted_model"

    def generate_report(
        self,
        session_id: str,
        video_result: dict[str, Any],
        audio_result: dict[str, Any],
        evaluation_result: dict[str, Any],
    ) -> dict[str, Any]:

        report = RiskScoringEngine.generate_risk_report(
            session_id=session_id,
            video_result=video_result,
            audio_result=audio_result,
            evaluation_result=evaluation_result,
        )

        report["model"] = self.name

        return report


class ExperimentalRiskModel(BaseRiskScoringModel):
    """
    Experimental scoring model.

    Uses different pipeline weights so researchers can compare
    against the production implementation.
    """

    VIDEO_WEIGHT = 0.30
    AUDIO_WEIGHT = 0.20
    EVALUATION_WEIGHT = 0.50

    @property
    def name(self) -> str:
        return "experimental_model"

    def generate_report(
        self,
        session_id: str,
        video_result: dict[str, Any],
        audio_result: dict[str, Any],
        evaluation_result: dict[str, Any],
    ) -> dict[str, Any]:

        video_risk = RiskScoringEngine.calculate_video_risk(video_result)

        audio_risk = RiskScoringEngine.calculate_audio_risk(audio_result)

        evaluation_risk = RiskScoringEngine.calculate_evaluation_risk(
            evaluation_result
        )

        final_risk = (
            self.VIDEO_WEIGHT * video_risk
            + self.AUDIO_WEIGHT * audio_risk
            + self.EVALUATION_WEIGHT * evaluation_risk
        )

        final_risk = round(min(max(final_risk, 0.0), 1.0), 3)

        classification = RiskScoringEngine.classify_risk(final_risk)

        report = {
            "session_id": session_id,
            "model": self.name,
            "final_risk_score": final_risk,
            "risk_classification": classification,
            "component_risks": {
                "video_risk": video_risk,
                "audio_risk": audio_risk,
                "evaluation_risk": evaluation_risk,
            },
            "risk_factors": RiskScoringEngine._identify_risk_factors(
                video_result,
                audio_result,
                evaluation_result,
            ),
            "recommendation": RiskScoringEngine._generate_recommendation(
                classification
            ),
        }

        return report