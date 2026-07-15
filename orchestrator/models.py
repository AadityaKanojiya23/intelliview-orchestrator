"""
models.py — Pydantic schemas for Risk Weight Configuration
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime


class RiskWeights(BaseModel):
    """
    Individual risk weight values for each signal.
    All weights must be >= 0. They are normalized at scoring time
    so they do not need to sum to 1.
    """
    tab_switching:         float = Field(default=1.0, ge=0.0, description="Weight for tab switching events")
    browser_activity:      float = Field(default=1.0, ge=0.0, description="Weight for suspicious browser activity")
    audio_interruptions:   float = Field(default=1.0, ge=0.0, description="Weight for audio quality issues")
    multiple_persons:      float = Field(default=1.0, ge=0.0, description="Weight for multiple persons detected")
    candidate_absence:     float = Field(default=1.0, ge=0.0, description="Weight for candidate not present")
    gaze_deviation:        float = Field(default=1.0, ge=0.0, description="Weight for gaze direction anomalies")
    background_noise:      float = Field(default=1.0, ge=0.0, description="Weight for background noise level")

    @model_validator(mode='after')
    def at_least_one_nonzero(self):
        values = [
            self.tab_switching, self.browser_activity, self.audio_interruptions,
            self.multiple_persons, self.candidate_absence, self.gaze_deviation,
            self.background_noise
        ]
        if all(v == 0.0 for v in values):
            raise ValueError("At least one risk weight must be greater than 0")
        return self


class RiskConfigCreate(BaseModel):
    """Request body for creating a new risk weight config."""
    job_position: str = Field(..., min_length=1, max_length=100, description="Job position name e.g. 'Software Engineer'")
    weights:      RiskWeights
    description:  Optional[str] = Field(default=None, max_length=500)


class RiskConfigUpdate(BaseModel):
    """Request body for updating an existing config (all fields optional)."""
    weights:     Optional[RiskWeights] = None
    description: Optional[str]         = Field(default=None, max_length=500)


class RiskConfigResponse(BaseModel):
    """Response schema returned by all endpoints."""
    id:           str
    job_position: str
    weights:      RiskWeights
    description:  Optional[str]
    created_at:   datetime
    updated_at:   datetime
