from unittest.mock import MagicMock, patch

from workers.tasks import process_interview_session


@patch("workers.tasks._after_parallel")
@patch("workers.tasks.group")
@patch("workers.tasks.session_manager")
@patch("workers.tasks.SessionLocal")
def test_process_interview_session_pipeline(
    mock_session_local,
    mock_session_manager,
    mock_group,
    mock_after_parallel,
):
    """
    Integration test for Celery workflow.

    ML stages are mocked.
    Only verifies pipeline orchestration.
    """

    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    interview = MagicMock()
    interview.status = "QUEUED"

    mock_db.execute.return_value.scalar_one_or_none.return_value = interview

    mock_result = MagicMock()
    mock_result.get.return_value = (MagicMock(), MagicMock())
    mock_group.return_value.apply_async.return_value = mock_result

    result = process_interview_session.run("test-session-001")

    assert result["session_id"] == "test-session-001"
    assert result["status"] == "processing_parallel"

    # Verify the group was created with video + audio subtasks
    mock_group.assert_called_once()

    # Verify _after_parallel.delay was called with session and results
    mock_after_parallel.delay.assert_called_once()

    # Verify session status updates (PROCESSING and VIDEO_PROCESSING)
    assert mock_session_manager.update_session_status.call_count == 2
