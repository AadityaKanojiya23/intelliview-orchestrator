"""
Unit and integration tests for Interview Scheduling and Email Notification System.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db import Base, get_db
from database.models import Candidate, InterviewSchedule
from orchestrator.email_service import EmailService
from routers.schedule import create_schedule_routes

# Create clean testing app with in-memory SQLite engine
test_engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

test_app = FastAPI()
test_app.include_router(create_schedule_routes())


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as c:
        yield c
    test_app.dependency_overrides.clear()


def test_interview_schedule_orm_model(db_session):
    """Test creating and querying InterviewSchedule model."""
    candidate = Candidate(
        candidate_id="cand_test_101",
        name="John Doe",
        email="john.doe@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
    schedule = InterviewSchedule(
        id="sched_101",
        candidate_id="cand_test_101",
        interviewer_id="interviewer_alice",
        scheduled_at=scheduled_time,
        status="scheduled",
        notes="Senior Backend Role",
    )
    db_session.add(schedule)
    db_session.commit()

    fetched = db_session.query(InterviewSchedule).filter_by(id="sched_101").first()
    assert fetched is not None
    assert fetched.candidate_id == "cand_test_101"
    assert fetched.interviewer_id == "interviewer_alice"
    assert fetched.status == "scheduled"
    assert "sched_101" in repr(fetched)


def test_email_service_send_confirmation():
    """Test EmailService constructs email and handles SMTP gracefully."""
    email_svc = EmailService()

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        success, msg = email_svc.send_interview_confirmation(
            candidate_name="Jane Doe",
            candidate_email="jane.doe@example.com",
            interview_date="August 12, 2026",
            interview_time="10:00 AM UTC",
            interviewer_name="Alice Smith",
            schedule_id="sched_202",
        )

        assert success is True
        assert "Email sent successfully" in msg
        mock_server.send_message.assert_called_once()


def test_email_service_handles_smtp_error():
    """Test EmailService catches SMTP exceptions and logs error."""
    email_svc = EmailService()

    with patch("smtplib.SMTP", side_effect=Exception("SMTP Connection Refused")):
        success, msg = email_svc.send_interview_confirmation(
            candidate_name="Jane Doe",
            candidate_email="jane.doe@example.com",
            interview_date="August 12, 2026",
            interview_time="10:00 AM UTC",
            interviewer_name="Alice Smith",
            schedule_id="sched_202",
        )

        assert success is False
        assert "Failed to send email" in msg


def test_create_schedule_api_endpoint(client, db_session):
    """Test POST /api/schedule endpoint with candidate creation and email trigger."""
    candidate = Candidate(
        candidate_id="cand_test_303",
        name="Bob Architect",
        email="bob.architect@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    payload = {
        "candidate_id": "cand_test_303",
        "interviewer_id": "Tech Lead Charlie",
        "scheduled_at": tomorrow,
        "notes": "System Architecture Technical Round",
        "send_email": True,
    }

    with patch(
        "orchestrator.email_service.email_service.send_interview_confirmation"
    ) as mock_send:
        mock_send.return_value = (True, "Email sent successfully")
        response = client.post("/api/schedule", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Interview scheduled successfully."
    assert data["schedule"]["candidate_id"] == "cand_test_303"
    assert data["schedule"]["candidate_name"] == "Bob Architect"
    assert data["schedule"]["interviewer_id"] == "Tech Lead Charlie"
    assert data["email_notification"]["sent"] is True


def test_list_and_upcoming_schedule_api(client, db_session):
    """Test GET /api/schedule and GET /api/schedule/upcoming."""
    candidate = Candidate(
        candidate_id="cand_test_404",
        name="Alice Engineer",
        email="alice.engineer@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    future_time = datetime.now(timezone.utc) + timedelta(days=2)
    schedule = InterviewSchedule(
        id="sched_future",
        candidate_id="cand_test_404",
        interviewer_id="Manager Dave",
        scheduled_at=future_time,
        status="scheduled",
    )
    db_session.add(schedule)
    db_session.commit()

    # GET /api/schedule
    res_list = client.get("/api/schedule")
    assert res_list.status_code == 200
    schedules = res_list.json()["schedules"]
    assert len(schedules) >= 1
    assert any(s["id"] == "sched_future" for s in schedules)

    # GET /api/schedule/upcoming
    res_upcoming = client.get("/api/schedule/upcoming")
    assert res_upcoming.status_code == 200
    upcoming = res_upcoming.json()["upcoming"]
    assert len(upcoming) >= 1
    assert upcoming[0]["id"] == "sched_future"


def test_update_schedule_api(client, db_session):
    """Test PATCH /api/schedule/{schedule_id} endpoint."""
    candidate = Candidate(
        candidate_id="cand_test_505",
        name="Carol QA",
        email="carol.qa@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    schedule = InterviewSchedule(
        id="sched_patch",
        candidate_id="cand_test_505",
        interviewer_id="Lead Tester",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=3),
        status="scheduled",
    )
    db_session.add(schedule)
    db_session.commit()

    patch_res = client.patch(
        "/api/schedule/sched_patch",
        json={"status": "completed", "notes": "Passed technical test"},
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()["schedule"]
    assert updated_data["status"] == "completed"
    assert updated_data["notes"] == "Passed technical test"
