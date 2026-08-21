"""
Question Bank Module
Manages interview questions by category, difficulty, and usage statistics
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select

from database.db import SessionLocal
from database.models import Question
from orchestrator.time_utils import utcnow

logger = logging.getLogger(__name__)


class QuestionBank:
    """Manages interview question storage, retrieval, and usage tracking"""

    CATEGORIES = ["technical", "behavioral", "situational"]
    DIFFICULTIES = ["easy", "medium", "hard"]

    def __init__(self):
        pass

    def add_question(
        self,
        text: str,
        category: str,
        difficulty: str = "medium",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Add a new question to the bank"""
        category = category.strip().lower()
        difficulty = difficulty.strip().lower()

        if category not in self.CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of: {self.CATEGORIES}")
        if difficulty not in self.DIFFICULTIES:
            raise ValueError(f"Invalid difficulty: {difficulty}. Must be one of: {self.DIFFICULTIES}")

        question_id = f"q_{uuid.uuid4().hex[:12]}"
        now = utcnow()

        db = SessionLocal()
        try:
            question = Question(
                question_id=question_id,
                text=text,
                category=category,
                difficulty=difficulty,
                tags=tags or [],
                usage_count=0,
                avg_score=None,
                created_at=now,
                updated_at=now,
            )
            db.add(question)
            db.commit()

            logger.info(f"Added question {question_id} [{category}/{difficulty}]")
            return {
                "question_id": question_id,
                "text": text,
                "category": category,
                "difficulty": difficulty,
                "tags": tags or [],
                "usage_count": 0,
                "avg_score": None,
                "created_at": now.isoformat(),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding question: {e}")
            raise
        finally:
            db.close()

    def get_questions(
        self,
        category: str | None = None,
        difficulty: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List questions with optional filters"""
        db = SessionLocal()
        try:
            stmt = select(Question)
            if category:
                stmt = stmt.where(Question.category == category.strip().lower())
            if difficulty:
                stmt = stmt.where(Question.difficulty == difficulty.strip().lower())
            stmt = stmt.order_by(Question.created_at.desc()).limit(limit)
            rows = db.execute(stmt).scalars().all()

            return [
                {
                    "question_id": r.question_id,
                    "text": r.text,
                    "category": r.category,
                    "difficulty": r.difficulty,
                    "tags": r.tags or [],
                    "usage_count": r.usage_count,
                    "avg_score": r.avg_score,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        finally:
            db.close()

    def get_questions_for_plan(
        self,
        question_plan: dict[str, int],
        exclude_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve questions according to a template question plan.

        question_plan example:
        {
            "technical": 4,
            "behavioral": 3,
            "situational": 3
        }

        Questions are selected from each category independently.
        Already-used question IDs can be excluded.
        """

        exclude_ids = set(exclude_ids or [])
        selected_questions: list[dict[str, Any]] = []

        db = SessionLocal()

        try:
            for category, required_count in question_plan.items():
                if category not in self.CATEGORIES:
                    raise ValueError(
                        f"Invalid category in question plan: {category}. Must be one of: {self.CATEGORIES}"
                    )

                if required_count <= 0:
                    continue

                stmt = (
                    select(Question)
                    .where(Question.category == category)
                    .order_by(
                        Question.usage_count.asc(),
                        Question.created_at.desc(),
                    )
                )

                rows = db.execute(stmt).scalars().all()

                category_count = 0

                for question in rows:
                    if question.question_id in exclude_ids:
                        continue

                    selected_questions.append(
                        {
                            "question_id": question.question_id,
                            "text": question.text,
                            "category": question.category,
                            "difficulty": question.difficulty,
                            "tags": question.tags or [],
                            "usage_count": question.usage_count,
                        }
                    )

                    exclude_ids.add(question.question_id)
                    category_count += 1

                    if category_count >= required_count:
                        break

            return selected_questions

        finally:
            db.close()

    def get_question(self, question_id: str) -> dict[str, Any] | None:
        """Get a single question by ID"""
        db = SessionLocal()
        try:
            q = db.execute(select(Question).where(Question.question_id == question_id)).scalar_one_or_none()
            if not q:
                return None
            return {
                "question_id": q.question_id,
                "text": q.text,
                "category": q.category,
                "difficulty": q.difficulty,
                "tags": q.tags or [],
                "usage_count": q.usage_count,
                "avg_score": q.avg_score,
                "created_at": q.created_at.isoformat() if q.created_at else None,
            }
        finally:
            db.close()

    def get_next_question(
        self,
        category: str | None = None,
        exclude_ids: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Get next question, preferring less-used ones, optional category filter"""
        exclude_ids = exclude_ids or []
        db = SessionLocal()
        try:
            stmt = select(Question)
            if category:
                stmt = stmt.where(Question.category == category.strip().lower())
            stmt = stmt.order_by(Question.usage_count.asc(), Question.created_at.desc())
            rows = db.execute(stmt).scalars().all()

            for q in rows:
                if q.question_id not in exclude_ids:
                    return {
                        "question_id": q.question_id,
                        "text": q.text,
                        "category": q.category,
                        "difficulty": q.difficulty,
                        "tags": q.tags or [],
                        "usage_count": q.usage_count,
                    }
            return None
        finally:
            db.close()

    def record_usage(self, question_id: str, score: float | None = None) -> bool:
        """Increment usage count and optionally update running average score"""
        db = SessionLocal()
        try:
            q = db.execute(select(Question).where(Question.question_id == question_id)).scalar_one_or_none()
            if not q:
                return False

            q.usage_count = (q.usage_count or 0) + 1
            if score is not None:
                if q.avg_score is None:
                    q.avg_score = score
                else:
                    count = q.usage_count
                    q.avg_score = ((q.avg_score * (count - 1)) + score) / count
            q.updated_at = utcnow()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error recording usage for {question_id}: {e}")
            return False
        finally:
            db.close()

    def update_question(
        self,
        question_id: str,
        text: str | None = None,
        category: str | None = None,
        difficulty: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Update an existing question. Only non-None fields are changed."""
        if category is not None:
            category = category.strip().lower()
            if category not in self.CATEGORIES:
                raise ValueError(f"Invalid category: {category}. Must be one of: {self.CATEGORIES}")
        if difficulty is not None:
            difficulty = difficulty.strip().lower()
            if difficulty not in self.DIFFICULTIES:
                raise ValueError(f"Invalid difficulty: {difficulty}. Must be one of: {self.DIFFICULTIES}")

        db = SessionLocal()
        try:
            q = db.execute(select(Question).where(Question.question_id == question_id)).scalar_one_or_none()
            if not q:
                return None
            if text is not None:
                q.text = text
            if category is not None:
                q.category = category
            if difficulty is not None:
                q.difficulty = difficulty
            if tags is not None:
                q.tags = tags
            q.updated_at = utcnow()
            db.commit()
            logger.info(f"Updated question {question_id}")
            return {
                "question_id": q.question_id,
                "text": q.text,
                "category": q.category,
                "difficulty": q.difficulty,
                "tags": q.tags or [],
                "usage_count": q.usage_count,
                "avg_score": q.avg_score,
                "created_at": q.created_at.isoformat() if q.created_at else None,
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating question {question_id}: {e}")
            raise
        finally:
            db.close()

    def delete_question(self, question_id: str) -> bool:
        """Delete a question by ID. Returns True if deleted, False if not found."""
        db = SessionLocal()
        try:
            q = db.execute(select(Question).where(Question.question_id == question_id)).scalar_one_or_none()
            if not q:
                return False
            db.delete(q)
            db.commit()
            logger.info(f"Deleted question {question_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting question {question_id}: {e}")
            raise
        finally:
            db.close()


question_bank = QuestionBank()
