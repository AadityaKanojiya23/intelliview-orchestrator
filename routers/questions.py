"""Question bank routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.db import get_db

logger = logging.getLogger(__name__)


class AddQuestionRequest(BaseModel):
    """Request model for adding a question to the bank"""

    text: str = Field(min_length=1, max_length=1000)
    category: str
    difficulty: str = "medium"
    tags: list[str] | None = None


class UpdateQuestionRequest(BaseModel):
    """Request model for updating a question (all fields optional)"""

    text: str | None = Field(default=None, min_length=1, max_length=1000)
    category: str | None = None
    difficulty: str | None = None
    tags: list[str] | None = None


def create_question_routes(question_bank) -> APIRouter:
    """Create question bank routes.

    Args:
        question_bank: QuestionBank instance

    Returns:
        APIRouter with question routes
    """

    router = APIRouter()

    @router.get("/questions")
    async def list_questions(
        category: str | None = None,
        difficulty: str | None = None,
        limit: int = 100,
        session_db: Session = Depends(get_db),
    ):
        """List questions with optional category/difficulty filter"""
        try:
            questions = question_bank.get_questions(category=category, difficulty=difficulty, limit=limit)
            return {"count": len(questions), "questions": questions}
        except Exception as e:
            logger.error(f"Error listing questions: {e!s}")
            raise HTTPException(status_code=500, detail="Error listing questions")

    @router.post("/questions")
    async def add_question(
        request: AddQuestionRequest,
        session_db: Session = Depends(get_db),
    ):
        """Add a new question to the bank"""
        try:
            question = question_bank.add_question(
                text=request.text,
                category=request.category,
                difficulty=request.difficulty,
                tags=request.tags,
            )
            return question
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error adding question: {e!s}")
            raise HTTPException(status_code=500, detail="Error adding question")

    @router.post("/questions/by-plan")
    async def get_questions_by_plan(
        question_plan: dict[str, int],
        session_db: Session = Depends(get_db),
    ):
        """
        Retrieve questions according to a template-generated question plan.

        Example request:
        {
            "technical": 4,
            "behavioral": 3,
            "situational": 3
        }
        """
        try:
            questions = question_bank.get_questions_for_plan(question_plan=question_plan)

            return {
                "count": len(questions),
                "questions": questions,
            }

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

        except Exception as e:
            logger.error(f"Error retrieving questions by plan: {e!s}")

            raise HTTPException(
                status_code=500,
                detail="Error retrieving questions by plan",
            )

    @router.put("/questions/{question_id}")
    async def update_question(
        question_id: str,
        request: UpdateQuestionRequest,
        session_db: Session = Depends(get_db),
    ):
        """Update an existing question in the bank"""
        try:
            updated = question_bank.update_question(
                question_id=question_id,
                text=request.text,
                category=request.category,
                difficulty=request.difficulty,
                tags=request.tags,
            )
            if updated is None:
                raise HTTPException(status_code=404, detail="Question not found")
            return updated
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating question: {e!s}")
            raise HTTPException(status_code=500, detail="Error updating question")

    @router.delete("/questions/{question_id}", status_code=204)
    async def delete_question(
        question_id: str,
        session_db: Session = Depends(get_db),
    ):
        """Delete a question from the bank"""
        try:
            deleted = question_bank.delete_question(question_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Question not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting question: {e!s}")
            raise HTTPException(status_code=500, detail="Error deleting question")

    return router
