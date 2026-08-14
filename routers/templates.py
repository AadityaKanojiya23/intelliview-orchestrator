"""Interview template API routes for template CRUD management."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.db import get_db

logger = logging.getLogger(__name__)


class CreateTemplateRequest(BaseModel):
    """Request model for creating an interview template"""

    name: str = Field(min_length=1, max_length=200)
    interview_type: str = Field(default="mixed")
    domain: str = Field(default="python")
    description: str | None = None
    duration_minutes: int = Field(default=60, ge=5, le=300)
    question_count: int = Field(default=10, ge=1, le=50)
    category_distribution: dict[str, float] | None = None
    difficulty_distribution: dict[str, float] | None = None


class UpdateTemplateRequest(BaseModel):
    """Request model for updating an interview template"""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    interview_type: str | None = None
    domain: str | None = None
    description: str | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=300)
    question_count: int | None = Field(default=None, ge=1, le=50)
    category_distribution: dict[str, float] | None = None
    difficulty_distribution: dict[str, float] | None = None


def create_template_routes(interview_template_manager) -> APIRouter:
    """Create interview template routes."""

    router = APIRouter()

    @router.get("/templates")
    async def list_templates(
        interview_type: str | None = Query(default=None),
        domain: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ):
        """List interview templates with optional type/domain filter."""
        try:
            templates = interview_template_manager.list_templates(
                interview_type=interview_type,
                domain=domain,
                limit=limit,
            )
            return {"count": len(templates), "templates": templates}
        except Exception as e:
            logger.error(f"Error listing templates: {e!s}")
            raise HTTPException(
                status_code=500,
                detail="Error listing templates",
            )

    @router.get("/templates/{template_id}")
    async def get_template(
        template_id: str = Path(..., description="Unique template identifier"),
    ):
        """Get a single interview template by ID."""
        try:
            template = interview_template_manager.get_template(template_id)

            if not template:
                raise HTTPException(
                    status_code=404,
                    detail="Template not found",
                )

            return template

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error getting template {template_id}: {e!s}"
            )
            raise HTTPException(
                status_code=500,
                detail="Error retrieving template",
            )

    @router.post("/templates", status_code=201)
    async def create_template(
        request: CreateTemplateRequest,
        session_db: Session = Depends(get_db),
    ):
        """Create a new interview template."""
        try:
            template = interview_template_manager.create_template(
                name=request.name,
                interview_type=request.interview_type,
                domain=request.domain,
                description=request.description,
                duration_minutes=request.duration_minutes,
                question_count=request.question_count,
                category_distribution=request.category_distribution,
                difficulty_distribution=request.difficulty_distribution,
            )
            return template

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

        except Exception as e:
            logger.error(
                f"Error creating template: {e!s}"
            )
            raise HTTPException(
                status_code=500,
                detail="Error creating template",
            )

    @router.put("/templates/{template_id}")
    async def update_template(
        request: UpdateTemplateRequest,
        template_id: str = Path(..., description="Unique template identifier"),
        session_db: Session = Depends(get_db),
    ):
        """Update an existing interview template."""
        try:
            template = interview_template_manager.update_template(
                template_id=template_id,
                name=request.name,
                interview_type=request.interview_type,
                domain=request.domain,
                description=request.description,
                duration_minutes=request.duration_minutes,
                question_count=request.question_count,
                category_distribution=request.category_distribution,
                difficulty_distribution=request.difficulty_distribution,
            )

            if not template:
                raise HTTPException(
                    status_code=404,
                    detail="Template not found",
                )

            return template

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.error(
                f"Error updating template {template_id}: {e!s}"
            )
            raise HTTPException(
                status_code=500,
                detail="Error updating template",
            )

    @router.delete("/templates/{template_id}")
    async def delete_template(
        template_id: str = Path(..., description="Unique template identifier"),
        session_db: Session = Depends(get_db),
    ):
        """Delete an interview template."""
        try:
            success = interview_template_manager.delete_template(
                template_id
            )

            if not success:
                raise HTTPException(
                    status_code=404,
                    detail="Template not found",
                )

            return {
                "deleted": True,
                "success": True,
                "message": f"Template {template_id} deleted successfully",
            }

        except HTTPException:
            raise

        except Exception as e:
            logger.error(
                f"Error deleting template {template_id}: {e!s}"
            )
            raise HTTPException(
                status_code=500,
                detail="Error deleting template",
            )

    @router.get("/templates/{template_id}/question-plan")
    async def get_template_question_plan(
        template_id: str = Path(
            ...,
            description="Unique template identifier",
        ),
    ):
        """Generate the question plan for a selected interview template."""
        try:
            plan = interview_template_manager.build_template_question_plan(
                template_id
            )

            if not plan:
                raise HTTPException(
                    status_code=404,
                    detail="Template not found",
                )

            return {"question_plan": plan}

        except HTTPException:
            raise

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

        except Exception as e:
            logger.error(
                f"Error generating question plan for "
                f"{template_id}: {e!s}"
            )
            raise HTTPException(
                status_code=500,
                detail="Error generating question plan",
            )

    return router