"""
Unit tests for the SessionManager state machine.
"""

import itertools

from orchestrator.session_manager import SessionManager


def test_valid_transitions_cover_full_pipeline():
    sm = SessionManager()
    # CREATED -> QUEUED -> PROCESSING -> VIDEO -> AUDIO -> EVALUATING -> COMPLETED
    pipeline = [
        sm.CREATED,
        sm.QUEUED,
        sm.PROCESSING,
        sm.VIDEO_PROCESSING,
        sm.AUDIO_PROCESSING,
        sm.EVALUATING,
        sm.COMPLETED,
    ]
    for prev, nxt in itertools.pairwise(pipeline):
        assert sm._is_valid_transition(prev, nxt), f"{prev} -> {nxt} should be valid"


def test_completed_is_terminal():
    sm = SessionManager()
    for s in [
        sm.PROCESSING,
        sm.VIDEO_PROCESSING,
        sm.AUDIO_PROCESSING,
        sm.EVALUATING,
        sm.QUEUED,
        sm.CREATED,
    ]:
        assert not sm._is_valid_transition(sm.COMPLETED, s)


def test_failed_is_terminal():
    sm = SessionManager()
    for s in [sm.COMPLETED, sm.QUEUED, sm.CREATED]:
        assert not sm._is_valid_transition(sm.FAILED, s)


def test_failed_can_be_reached_from_any_active_state():
    sm = SessionManager()
    for s in [
        sm.QUEUED,
        sm.PROCESSING,
        sm.VIDEO_PROCESSING,
        sm.AUDIO_PROCESSING,
        sm.EVALUATING,
    ]:
        assert sm._is_valid_transition(s, sm.FAILED), f"{s} -> FAILED should be valid"


def test_unknown_state_is_invalid():
    sm = SessionManager()
    assert not sm._is_valid_transition("UNKNOWN", sm.QUEUED)
    assert not sm._is_valid_transition(sm.QUEUED, "UNKNOWN")
