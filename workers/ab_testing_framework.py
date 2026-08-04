"""
A/B Testing Framework for Risk Scoring

Executes multiple risk scoring models on the same interview data
and exposes their results for comparison without affecting the
existing production workflow.
"""

from __future__ import annotations

import logging
from typing import Any

from workers.scoring_models import (
    BaseRiskScoringModel,
    ExperimentalRiskModel,
    WeightedRiskModel,
)

logger = logging.getLogger(__name__)


class ABTestingFramework:
    """
    Executes multiple risk scoring models independently
    and compares their outputs.
    """

    def __init__(
        self,
        production_model: BaseRiskScoringModel | None = None,
        experimental_model: BaseRiskScoringModel | None = None,
    ) -> None:

        self.production_model = production_model or WeightedRiskModel()
        self.experimental_model = experimental_model or ExperimentalRiskModel()

    def run(
        self,
        session_id: str,
        video_result: dict[str, Any],
        audio_result: dict[str, Any],
        evaluation_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute both models independently using the same input.
        """

        logger.info("Running A/B risk scoring for session %s", session_id)

        production_report = self.production_model.generate_report(
            session_id=session_id,
            video_result=video_result,
            audio_result=audio_result,
            evaluation_result=evaluation_result,
        )

        experimental_report = self.experimental_model.generate_report(
            session_id=session_id,
            video_result=video_result,
            audio_result=audio_result,
            evaluation_result=evaluation_result,
        )

        comparison = self.compare_reports(
            production_report,
            experimental_report,
        )

        return {
            "production_model": production_report,
            "experimental_model": experimental_report,
            "comparison": comparison,
        }

    @staticmethod
    def compare_reports(
        production: dict[str, Any],
        experimental: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compare two model outputs.
        """

        score_difference = round(
            experimental["final_risk_score"]
            - production["final_risk_score"],
            3,
        )

        classification_changed = (
            production["risk_classification"]
            != experimental["risk_classification"]
        )

        return {
            "production_score": production["final_risk_score"],
            "experimental_score": experimental["final_risk_score"],
            "score_difference": score_difference,
            "production_classification": production["risk_classification"],
            "experimental_classification": experimental["risk_classification"],
            "classification_changed": classification_changed,
        }