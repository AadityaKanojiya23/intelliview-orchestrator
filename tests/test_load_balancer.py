from unittest.mock import patch

import pytest

from orchestrator.load_balancer import BalancingStrategy, LoadBalancer


@pytest.fixture
def mock_registry():
    """Fixture to safely mock out WorkerRegistry calls."""
    with patch("orchestrator.load_balancer.WorkerRegistry") as mock_class:
        instance = mock_class.return_value
        yield instance


# ==============================================================================
# 1. ROUND ROBIN STRATEGY TESTS
# ==============================================================================


def test_round_robin_cycles_evenly(mock_registry):
    """Verifies that Round Robin cycles through workers in sequential order."""
    workers = [{"worker_id": "w1"}, {"worker_id": "w2"}, {"worker_id": "w3"}]
    mock_registry.get_available_workers.return_value = workers

    lb = LoadBalancer(strategy=BalancingStrategy.ROUND_ROBIN)

    # First cycle
    assert lb.select_worker()["worker_id"] == "w1"
    assert lb.select_worker()["worker_id"] == "w2"
    assert lb.select_worker()["worker_id"] == "w3"
    # Second cycle (wraps around)
    assert lb.select_worker()["worker_id"] == "w1"


# ==============================================================================
# 2. LEAST LOADED STRATEGY TESTS
# ==============================================================================


def test_least_loaded_selects_lowest_active_tasks(mock_registry):
    """Verifies that Least Loaded strategy picks the worker with minimal tasks."""
    least_loaded_worker = {"worker_id": "w2", "active_tasks": 1, "capacity": 10}
    mock_registry.get_least_loaded_worker.return_value = least_loaded_worker

    lb = LoadBalancer(strategy=BalancingStrategy.LEAST_LOADED)
    selected = lb.select_worker()

    assert selected["worker_id"] == "w2"
    mock_registry.get_least_loaded_worker.assert_called_once()


# ==============================================================================
# 3. QUEUE-BASED STRATEGY TESTS
# ==============================================================================


def test_queue_based_returns_none_when_no_workers(mock_registry):
    """Verifies queue-based strategy returns None if all workers are offline."""
    mock_registry.get_least_loaded_worker.return_value = None

    lb = LoadBalancer(strategy=BalancingStrategy.QUEUE_BASED)
    assert lb.select_worker() is None


# ==============================================================================
# 4. EDGE CASES & PRIORITY/OVERLOAD TESTS
# ==============================================================================


def test_edge_cases_no_workers_available(mock_registry):
    """Ensures all strategies handle an empty worker pool gracefully."""
    mock_registry.get_available_workers.return_value = []
    mock_registry.get_least_loaded_worker.return_value = None

    for strategy in BalancingStrategy:
        lb = LoadBalancer(strategy=strategy)
        assert lb.select_worker() is None


def test_priority_worker_selection(mock_registry):
    """Tests that high, medium, and low priority jobs route to appropriate loads."""
    # Arranged specifically so most-loaded worker is at index [-1]
    workers = [
        {"worker_id": "w2", "active_tasks": 2, "capacity": 10},
        {"worker_id": "w1", "active_tasks": 5, "capacity": 10},
    ]
    mock_registry.get_available_workers.return_value = workers
    lb = LoadBalancer()

    # High priority -> targets least loaded tasks directly (w2)
    assert lb.get_best_worker_for_priority("high")["worker_id"] == "w2"

    # Low priority -> targets the last available element in the array (w1)
    assert lb.get_best_worker_for_priority("low")["worker_id"] == "w1"


def test_system_overload_detection(mock_registry):
    """Verifies system overload calculations trigger at the designated threshold."""
    lb = LoadBalancer()

    # Mock 95% utilization (Overloaded)
    mock_registry.get_worker_statistics.return_value = {"capacity_utilization": 95.0}
    assert lb.is_system_overloaded(threshold=0.9) is True

    # Mock 50% utilization (Not Overloaded)
    mock_registry.get_worker_statistics.return_value = {"capacity_utilization": 50.0}
    assert lb.is_system_overloaded(threshold=0.9) is False


def test_switch_strategy(mock_registry):
    """Verifies that runtime strategy transitions function as expected."""
    lb = LoadBalancer(strategy=BalancingStrategy.ROUND_ROBIN)
    lb.switch_strategy(BalancingStrategy.LEAST_LOADED)
    assert lb.strategy == BalancingStrategy.LEAST_LOADED
