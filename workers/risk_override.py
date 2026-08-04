"""
Rule-based Risk Override Engine.

This module contains override rules that can supersede the weighted
risk classification when critical conditions are detected.

The design is intentionally extensible:
- Add a new rule by subclassing OverrideRule.
- Register it in RiskOverrideEngine.RULES.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OverrideRule(ABC):
    """Base class for all override rules."""

    @abstractmethod
    def evaluate(
        self,
        video_result: dict[str, Any],
        audio_result: dict[str, Any],
        evaluation_result: dict[str, Any],
    ) -> str | None:
        """
        Return a risk classification override if the rule matches.

        Returns:
            "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
            or None if the rule does not apply.
        """


class MultiplePersonsRule(OverrideRule):
    """Override to CRITICAL if multiple people are detected."""

    def evaluate(
        self,
        video_result: dict[str, Any],
        audio_result: dict[str, Any],
        evaluation_result: dict[str, Any],
    ) -> str | None:

        if video_result.get("multiple_persons", {}).get(
            "multiple_persons_detected", False
        ):
            return "CRITICAL"

        return None


class FaceAbsentRule(OverrideRule):
    """
    Temporary implementation.

    Currently uses faces_found boolean.

    Later this can be replaced with:
        face_absent_duration > threshold
    """

    def evaluate(
        self,
        video_result: dict[str, Any],
        audio_result: dict[str, Any],
        evaluation_result: dict[str, Any],
    ) -> str | None:

        if not (video_result.get("face_detected", {}).get("faces_found", True)):
            return "HIGH"

        return None


class RiskOverrideEngine:
    """
    Evaluates registered override rules.

    Rule order defines priority.
    """

    RULES: list[OverrideRule] = [
        MultiplePersonsRule(),
        FaceAbsentRule(),
    ]

    @classmethod
    def evaluate(
        cls,
        video_result: dict[str, Any],
        audio_result: dict[str, Any],
        evaluation_result: dict[str, Any],
    ) -> str | None:

        for rule in cls.RULES:
            result = rule.evaluate(
                video_result,
                audio_result,
                evaluation_result,
            )

            if result is not None:
                return result

        return None
