"""
Interview Schedule API Router.
Handles schedule creation, calendar listings, upcoming events, and triggering email notifications.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Candidate, InterviewSchedule
from orchestrator.email_service import email_service

logger = logging.getLogger(__name__)


class CreateScheduleRequest(BaseModel):
    """Payload for creating a new interview schedule."""

    candidate_id: str = Field(..., description="ID of the candidate")
    interviewer_id: str = Field(..., description="Name or ID of the assigned interviewer")
    scheduled_at: datetime = Field(..., description="ISO datetime string for the scheduled interview")
    notes: str | None = Field(default=None, description="Optional interview notes or description")
    send_email: bool = Field(default=True, description="Whether to send confirmation email via smtplib")


class UpdateScheduleRequest(BaseModel):
    """Payload for updating schedule status or details."""

    status: str | None = Field(default=None, description="New schedule status")
    notes: str | None = Field(default=None, description="Updated notes")
    scheduled_at: datetime | None = Field(default=None, description="Rescheduled datetime")


def create_schedule_routes() -> APIRouter:
    """Create APIRouter for interview scheduling."""

    router = APIRouter(prefix="/api/schedule", tags=["Schedule"])

    @router.post("", status_code=201)
    async def create_schedule(
        payload: CreateScheduleRequest,
        db: Session = Depends(get_db),
    ):
        """
        Create a new interview schedule and trigger an email notification to the candidate.
        """
        try:
            # Check candidate existence
            candidate = db.execute(
                select(Candidate).where(Candidate.candidate_id == payload.candidate_id)
            ).scalar_one_or_none()

            if not candidate:
                raise HTTPException(
                    status_code=404,
                    detail=f"Candidate with ID '{payload.candidate_id}' not found.",
                )

            # Format UTC or timezone-aware datetime
            scheduled_at = payload.scheduled_at
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

            # Create Schedule ORM entry
            schedule = InterviewSchedule(
                candidate_id=payload.candidate_id,
                interviewer_id=payload.interviewer_id,
                scheduled_at=scheduled_at,
                status="scheduled",
                notes=payload.notes,
            )

            db.add(schedule)
            db.commit()
            db.refresh(schedule)

            # Send Email Notification
            email_sent = False
            email_msg = "Email notification disabled."

            if payload.send_email and candidate.email:
                date_str = scheduled_at.strftime("%B %d, %Y")
                time_str = scheduled_at.strftime("%I:%M %p %Z").strip()

                email_sent, email_msg = email_service.send_interview_confirmation(
                    candidate_name=candidate.name,
                    candidate_email=candidate.email,
                    interview_date=date_str,
                    interview_time=time_str,
                    interviewer_name=payload.interviewer_id,
                    schedule_id=schedule.id,
                    notes=payload.notes,
                )

            return {
                "message": "Interview scheduled successfully.",
                "schedule": {
                    "id": schedule.id,
                    "candidate_id": schedule.candidate_id,
                    "candidate_name": candidate.name,
                    "candidate_email": candidate.email,
                    "interviewer_id": schedule.interviewer_id,
                    "scheduled_at": schedule.scheduled_at.isoformat(),
                    "status": schedule.status,
                    "notes": schedule.notes,
                    "created_at": schedule.created_at.isoformat(),
                },
                "email_notification": {
                    "sent": email_sent,
                    "detail": email_msg,
                },
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error scheduling interview: {e!s}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to schedule interview: {e!s}")

    @router.get("")
    async def list_schedules(
        candidate_id: str | None = Query(default=None),
        status: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        db: Session = Depends(get_db),
    ):
        """List all interview schedules with candidate details."""
        try:
            stmt = select(InterviewSchedule, Candidate).join(
                Candidate, InterviewSchedule.candidate_id == Candidate.candidate_id
            )

            if candidate_id:
                stmt = stmt.where(InterviewSchedule.candidate_id == candidate_id)
            if status:
                stmt = stmt.where(InterviewSchedule.status == status)

            stmt = stmt.order_by(InterviewSchedule.scheduled_at.asc()).limit(limit)
            results = db.execute(stmt).all()

            schedules_data = []
            for sched, cand in results:
                schedules_data.append(
                    {
                        "id": sched.id,
                        "candidate_id": sched.candidate_id,
                        "candidate_name": cand.name,
                        "candidate_email": cand.email,
                        "interviewer_id": sched.interviewer_id,
                        "scheduled_at": sched.scheduled_at.isoformat(),
                        "status": sched.status,
                        "notes": sched.notes,
                        "created_at": sched.created_at.isoformat(),
                    }
                )

            return {"count": len(schedules_data), "schedules": schedules_data}
        except Exception as e:
            logger.error(f"Error fetching schedules: {e!s}")
            raise HTTPException(status_code=500, detail="Error fetching interview schedules")

    @router.get("/upcoming")
    async def list_upcoming_schedules(
        limit: int = Query(default=10, ge=1, le=50),
        db: Session = Depends(get_db),
    ):
        """List upcoming scheduled interviews from the current time onwards."""
        try:
            now = datetime.now(timezone.utc)
            stmt = (
                select(InterviewSchedule, Candidate)
                .join(Candidate, InterviewSchedule.candidate_id == Candidate.candidate_id)
                .where(InterviewSchedule.scheduled_at >= now)
                .where(InterviewSchedule.status == "scheduled")
                .order_by(InterviewSchedule.scheduled_at.asc())
                .limit(limit)
            )

            results = db.execute(stmt).all()
            upcoming_data = []
            for sched, cand in results:
                upcoming_data.append(
                    {
                        "id": sched.id,
                        "candidate_id": sched.candidate_id,
                        "candidate_name": cand.name,
                        "candidate_email": cand.email,
                        "interviewer_id": sched.interviewer_id,
                        "scheduled_at": sched.scheduled_at.isoformat(),
                        "status": sched.status,
                        "notes": sched.notes,
                    }
                )

            return {"count": len(upcoming_data), "upcoming": upcoming_data}
        except Exception as e:
            logger.error(f"Error fetching upcoming schedules: {e!s}")
            raise HTTPException(status_code=500, detail="Error fetching upcoming schedules")

    @router.get("/{schedule_id}")
    async def get_schedule(
        schedule_id: str,
        db: Session = Depends(get_db),
    ):
        """Get details for a specific interview schedule."""
        try:
            stmt = (
                select(InterviewSchedule, Candidate)
                .join(Candidate, InterviewSchedule.candidate_id == Candidate.candidate_id)
                .where(InterviewSchedule.id == schedule_id)
            )
            result = db.execute(stmt).first()

            if not result:
                raise HTTPException(status_code=404, detail="Schedule not found")

            sched, cand = result
            return {
                "id": sched.id,
                "candidate_id": sched.candidate_id,
                "candidate_name": cand.name,
                "candidate_email": cand.email,
                "interviewer_id": sched.interviewer_id,
                "scheduled_at": sched.scheduled_at.isoformat(),
                "status": sched.status,
                "notes": sched.notes,
                "created_at": sched.created_at.isoformat(),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting schedule: {e!s}")
            raise HTTPException(status_code=500, detail="Error getting schedule details")

    @router.patch("/{schedule_id}")
    async def update_schedule(
        schedule_id: str,
        payload: UpdateScheduleRequest,
        db: Session = Depends(get_db),
    ):
        """Update interview schedule status or datetime."""
        try:
            schedule = db.execute(
                select(InterviewSchedule).where(InterviewSchedule.id == schedule_id)
            ).scalar_one_or_none()

            if not schedule:
                raise HTTPException(status_code=404, detail="Schedule not found")

            if payload.status:
                schedule.status = payload.status
            if payload.notes is not None:
                schedule.notes = payload.notes
            if payload.scheduled_at:
                sched_at = payload.scheduled_at
                if sched_at.tzinfo is None:
                    sched_at = sched_at.replace(tzinfo=timezone.utc)
                schedule.scheduled_at = sched_at

            db.commit()
            db.refresh(schedule)

            return {
                "message": "Schedule updated successfully",
                "schedule": {
                    "id": schedule.id,
                    "status": schedule.status,
                    "scheduled_at": schedule.scheduled_at.isoformat(),
                    "notes": schedule.notes,
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating schedule: {e!s}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Error updating schedule")

    return router
