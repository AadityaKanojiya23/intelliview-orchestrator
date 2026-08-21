"""
Interview Templates Module
Manages interview structure templates, usage tracking, and success rates
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select

from database.db import SessionLocal
from database.models import InterviewTemplate
from orchestrator.interview_question_logic import (
    build_question_plan,
    normalize_domain,
    validate_category_distribution,
)
from orchestrator.time_utils import utcnow

logger = logging.getLogger(__name__)


class InterviewTemplateManager:
    """Manages interview templates and their usage statistics"""

    INTERVIEW_TYPES = ["technical", "behavioral", "mixed"]

    def __init__(self):
        pass

    def create_template(
        self,
        name: str,
        interview_type: str,
        domain: str = "general",
        description: str | None = None,
        duration_minutes: int = 60,
        question_count: int = 10,
        category_distribution: dict[str, float] | None = None,
        difficulty_distribution: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Create a new interview template."""
        interview_type = interview_type.strip().lower()
        domain = normalize_domain(domain)

        if interview_type not in self.INTERVIEW_TYPES:
            raise ValueError(
                f"Invalid interview type: {interview_type}. Must be one of: {self.INTERVIEW_TYPES}"
            )

        self._validate_distribution(
            category_distribution,
            "category_distribution",
        )
        self._validate_distribution(
            difficulty_distribution,
            "difficulty_distribution",
        )

        template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
        now = utcnow()

        db = SessionLocal()

        try:
            template = InterviewTemplate(
                template_id=template_id,
                name=name,
                description=description,
                interview_type=interview_type,
                domain=domain,
                duration_minutes=duration_minutes,
                question_count=question_count,
                category_distribution=validate_category_distribution(category_distribution),
                difficulty_distribution=difficulty_distribution or {},
                usage_count=0,
                success_rate=None,
                created_at=now,
                updated_at=now,
            )

            db.add(template)
            db.commit()

            logger.info(
                "Created interview template %s: %s (type=%s, domain=%s, questions=%s)",
                template_id,
                name,
                interview_type,
                domain,
                question_count,
            )

            return {
                "template_id": template_id,
                "name": name.strip(),
                "description": description,
                "interview_type": interview_type,
                "domain": domain,
                "duration_minutes": duration_minutes,
                "question_count": question_count,
                "category_distribution": category_distribution,
                "difficulty_distribution": difficulty_distribution or {},
                "usage_count": 0,
                "success_rate": None,
                "created_at": now.isoformat(),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating template: {e}")
            raise

        finally:
            db.close()

    def get_template(self, template_id: str) -> dict[str, Any] | None:
        """Get a template by ID."""
        db = SessionLocal()

        try:
            template = db.execute(
                select(InterviewTemplate).where(InterviewTemplate.template_id == template_id)
            ).scalar_one_or_none()

            if not template:
                return None

            return {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "interview_type": template.interview_type,
                "domain": template.domain,
                "duration_minutes": template.duration_minutes,
                "question_count": template.question_count,
                "category_distribution": (template.category_distribution or {}),
                "difficulty_distribution": (template.difficulty_distribution or {}),
                "usage_count": template.usage_count,
                "success_rate": template.success_rate,
                "created_at": (template.created_at.isoformat() if template.created_at else None),
            }

        finally:
            db.close()

    def build_template_question_plan(
        self,
        template_id: str,
    ) -> dict[str, Any] | None:
        """Build a question plan for an interview template."""
        template = self.get_template(template_id)

        if not template:
            return None

        return build_question_plan(template)

    def list_templates(
        self,
        interview_type: str | None = None,
        domain: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List templates with optional type and domain filters."""
        db = SessionLocal()

        try:
            stmt = select(InterviewTemplate)

            if interview_type:
                stmt = stmt.where(InterviewTemplate.interview_type == interview_type.strip().lower())

            if domain:
                stmt = stmt.where(InterviewTemplate.domain == normalize_domain(domain))

            stmt = stmt.order_by(InterviewTemplate.created_at.desc()).limit(limit)

            rows = db.execute(stmt).scalars().all()

            return [
                {
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "interview_type": template.interview_type,
                    "domain": template.domain,
                    "duration_minutes": template.duration_minutes,
                    "question_count": template.question_count,
                    "category_distribution": (template.category_distribution or {}),
                    "difficulty_distribution": (template.difficulty_distribution or {}),
                    "usage_count": template.usage_count,
                    "success_rate": template.success_rate,
                    "created_at": (template.created_at.isoformat() if template.created_at else None),
                }
                for template in rows
            ]

        finally:
            db.close()

    def update_template(
        self,
        template_id: str,
        name: str | None = None,
        interview_type: str | None = None,
        domain: str | None = None,
        description: str | None = None,
        duration_minutes: int | None = None,
        question_count: int | None = None,
        category_distribution: dict[str, float] | None = None,
        difficulty_distribution: dict[str, float] | None = None,
    ) -> dict[str, Any] | None:
        """Update an existing interview template."""
        db = SessionLocal()

        try:
            template = db.execute(
                select(InterviewTemplate).where(InterviewTemplate.template_id == template_id)
            ).scalar_one_or_none()

            if not template:
                return None

            if name is not None:
                template.name = name.strip()

            if interview_type is not None:
                interview_type = interview_type.strip().lower()

                if interview_type not in self.INTERVIEW_TYPES:
                    raise ValueError(
                        f"Invalid interview type: {interview_type}. Must be one of: {self.INTERVIEW_TYPES}"
                    )

                template.interview_type = interview_type

            if domain is not None:
                template.domain = normalize_domain(domain)

            if description is not None:
                template.description = description

            if duration_minutes is not None:
                template.duration_minutes = duration_minutes

            if question_count is not None:
                template.question_count = question_count

            if category_distribution is not None:
                template.category_distribution = validate_category_distribution(category_distribution)

            if difficulty_distribution is not None:
                template.difficulty_distribution = difficulty_distribution

            template.updated_at = utcnow()

            db.commit()
            db.refresh(template)

            return {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "interview_type": template.interview_type,
                "domain": template.domain,
                "duration_minutes": template.duration_minutes,
                "question_count": template.question_count,
                "category_distribution": (template.category_distribution or {}),
                "difficulty_distribution": (template.difficulty_distribution or {}),
                "usage_count": template.usage_count,
                "success_rate": template.success_rate,
                "created_at": (template.created_at.isoformat() if template.created_at else None),
                "updated_at": (template.updated_at.isoformat() if template.updated_at else None),
            }

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def record_usage(
        self,
        template_id: str,
        success: bool = True,
    ) -> bool:
        """Record a template usage and update success rate."""
        db = SessionLocal()

        try:
            template = db.execute(
                select(InterviewTemplate).where(InterviewTemplate.template_id == template_id)
            ).scalar_one_or_none()

            if not template:
                return False

            template.usage_count = (template.usage_count or 0) + 1
            count = template.usage_count

            if template.success_rate is None:
                template.success_rate = 1.0 if success else 0.0
            else:
                template.success_rate = (
                    (template.success_rate * (count - 1)) + (1.0 if success else 0.0)
                ) / count

            template.updated_at = utcnow()

            db.commit()

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error recording template usage: {e}")
            return False

        finally:
            db.close()

    def delete_template(self, template_id: str) -> bool:
        """Delete an interview template by ID."""
        db = SessionLocal()

        try:
            template = db.execute(
                select(InterviewTemplate).where(InterviewTemplate.template_id == template_id)
            ).scalar_one_or_none()

            if not template:
                return False

            db.delete(template)
            db.commit()

            logger.info(
                "Deleted interview template %s",
                template_id,
            )

            return True

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def _validate_distribution(
        self,
        distribution: dict[str, float] | None,
        field_name: str,
    ) -> None:
        """Ensure a percentage distribution sums to 100 if provided."""
        if not distribution:
            return

        total = sum(distribution.values())

        if any(pct < 0 for pct in distribution.values()):
            raise ValueError(f"{field_name} percentages cannot be negative")

        if abs(total - 100) > 0.01:
            raise ValueError(f"{field_name} must sum to 100, got {total}")

    def get_question_plan(
        self,
        template_id: str,
    ) -> dict[str, Any] | None:
        """
        Connect a template to the question system.

        Given a template's question_count and category_distribution,
        return how many questions to pull from each category.
        """
        template = self.get_template(template_id)

        if not template:
            return None

        question_count = template["question_count"]
        distribution = template["category_distribution"] or {}

        plan = {category: round(question_count * pct / 100) for category, pct in distribution.items()}

        return {
            "template_id": template_id,
            "question_plan": plan,
        }


interview_template_manager = InterviewTemplateManager()
