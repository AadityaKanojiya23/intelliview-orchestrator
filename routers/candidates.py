"""Candidate profile routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.db import get_db

logger = logging.getLogger(__name__)


class CreateCandidateRequest(BaseModel):
    """Request model for creating a candidate profile"""

    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=1, max_length=255)
    resume_text: str | None = None
    skills: list[str] | None = None


def create_candidate_routes(candidate_manager) -> APIRouter:
    """Create candidate profile routes.

    Args:
        candidate_manager: CandidateManager instance

    Returns:
        APIRouter with candidate routes
    """

    router = APIRouter()

    @router.get("/candidates")
    async def list_candidates(
        limit: int = 100,
        session_db: Session = Depends(get_db),
    ):
        """List all candidates"""
        try:
            candidates = candidate_manager.list_candidates(limit=limit)
            return {"count": len(candidates), "candidates": candidates}
        except Exception as e:
            logger.error(f"Error listing candidates: {e!s}")
            raise HTTPException(status_code=500, detail="Error listing candidates")

    @router.post("/candidates")
    async def create_candidate(
        request: CreateCandidateRequest,
        session_db: Session = Depends(get_db),
    ):
        """Create a new candidate profile"""
        try:
            candidate = candidate_manager.create_candidate(
                name=request.name,
                email=request.email,
                resume_text=request.resume_text,
                skills=request.skills,
            )
            return candidate
        except Exception as e:
            logger.error(f"Error creating candidate: {e!s}")
            raise HTTPException(status_code=500, detail="Error creating candidate")

    @router.get("/candidates/{candidate_id}")
    async def get_candidate(
        candidate_id: str,
        session_db: Session = Depends(get_db),
    ):
        """Get candidate details by ID"""
        try:
            candidate = candidate_manager.get_candidate(candidate_id)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
            return candidate
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching candidate: {e!s}")
            raise HTTPException(status_code=500, detail="Error fetching candidate")

    @router.get("/candidates/{candidate_id}/history")
    async def get_candidate_history(
        candidate_id: str,
        session_db: Session = Depends(get_db),
    ):
        """Get candidate interview history"""
        try:
            candidate = candidate_manager.get_candidate(candidate_id)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
            history = candidate_manager.get_interview_history(candidate_id)
            return {"candidate_id": candidate_id, "history": history}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching candidate history: {e!s}")
            raise HTTPException(
                status_code=500, detail="Error fetching candidate history"
            )

    return router
