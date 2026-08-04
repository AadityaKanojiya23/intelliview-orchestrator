"""
Load Balancer Fairness Simulation Tests.

Executes 10,000 simulated task assignments against the real
LoadBalancer implementation.
"""

import time
from collections import Counter

from orchestrator.load_balancer import (
    BalancingStrategy,
    LoadBalancer,
)


TOTAL_TASKS = 10_000
TOTAL_WORKERS = 4


class SimulationRegistry:
    """In-memory worker registry for fairness simulation."""

    def __init__(self):
        self.workers = [
            {
                "worker_id": "worker-1",
                "capacity": TOTAL_TASKS,
                "active_tasks": 0,
                "status": "healthy",
            },
            {
                "worker_id": "worker-2",
                "capacity": TOTAL_TASKS,
                "active_tasks": 0,
                "status": "healthy",
            },
            {
                "worker_id": "worker-3",
                "capacity": TOTAL_TASKS,
                "active_tasks": 0,
                "status": "healthy",
            },
            {
                "worker_id": "worker-4",
                "capacity": TOTAL_TASKS,
                "active_tasks": 0,
                "status": "healthy",
            },
        ]

    def get_available_workers(self):
        """Return healthy workers with available capacity."""

        return [
            worker
            for worker in self.workers
            if worker["status"] == "healthy"
            and worker["active_tasks"] < worker["capacity"]
        ]

    def get_least_loaded_worker(self):
        """Return worker with minimum active task count."""

        available = self.get_available_workers()

        if not available:
            return None

        return min(
            available,
            key=lambda worker: worker["active_tasks"],
        )

    def increment_active_tasks(self, worker_id):
        """Increment selected worker task count."""

        for worker in self.workers:
            if worker["worker_id"] == worker_id:
                worker["active_tasks"] += 1
                return

    def get_worker_statistics(self):
        """Return worker statistics."""

        total_capacity = sum(
            worker["capacity"]
            for worker in self.workers
        )

        total_active_tasks = sum(
            worker["active_tasks"]
            for worker in self.workers
        )

        utilization = (
            total_active_tasks / total_capacity
        ) * 100

        return {
            "total_workers": len(self.workers),
            "total_capacity": total_capacity,
            "total_active_tasks": total_active_tasks,
            "capacity_utilization": utilization,
        }


def calculate_jains_fairness(distribution):
    """Calculate Jain's Fairness Index."""

    values = list(distribution.values())

    numerator = sum(values) ** 2

    denominator = (
        len(values)
        * sum(value ** 2 for value in values)
    )

    if denominator == 0:
        return 0.0

    return numerator / denominator


def run_real_simulation(strategy):
    """Run 10,000 tasks against real LoadBalancer."""

    load_balancer = LoadBalancer(
        strategy=strategy
    )

    registry = SimulationRegistry()

    load_balancer.worker_registry = registry

    distribution = Counter()

    start_time = time.perf_counter()

    for _ in range(TOTAL_TASKS):

        worker = load_balancer.select_worker()

        assert worker is not None

        worker_id = worker["worker_id"]

        distribution[worker_id] += 1

        registry.increment_active_tasks(
            worker_id
        )

    execution_time = (
        time.perf_counter() - start_time
    )

    return (
        distribution,
        execution_time,
    )


def test_real_round_robin_10000_tasks():
    """Test real Round Robin fairness."""

    distribution, execution_time = (
        run_real_simulation(
            BalancingStrategy.ROUND_ROBIN
        )
    )

    total_assigned = sum(
        distribution.values()
    )

    fairness = calculate_jains_fairness(
        distribution
    )

    print("\nROUND ROBIN SIMULATION")
    print(f"Total Tasks: {total_assigned}")
    print(f"Distribution: {dict(distribution)}")
    print(f"Fairness: {fairness * 100:.2f}%")
    print(
        f"Execution Time: "
        f"{execution_time:.6f} seconds"
    )

    assert total_assigned == TOTAL_TASKS

    assert len(distribution) == TOTAL_WORKERS

    assert fairness >= 0.99

    assert max(distribution.values()) - min(
        distribution.values()
    ) <= 1


def test_real_least_loaded_10000_tasks():
    """Test real Least Loaded fairness."""

    distribution, execution_time = (
        run_real_simulation(
            BalancingStrategy.LEAST_LOADED
        )
    )

    total_assigned = sum(
        distribution.values()
    )

    fairness = calculate_jains_fairness(
        distribution
    )

    print("\nLEAST LOADED SIMULATION")
    print(f"Total Tasks: {total_assigned}")
    print(f"Distribution: {dict(distribution)}")
    print(f"Fairness: {fairness * 100:.2f}%")
    print(
        f"Execution Time: "
        f"{execution_time:.6f} seconds"
    )

    assert total_assigned == TOTAL_TASKS

    assert len(distribution) == TOTAL_WORKERS

    assert fairness >= 0.99

    assert max(distribution.values()) - min(
        distribution.values()
    ) <= 1


def test_real_load_balancer_no_tasks_lost():
    """Verify no task is lost by implemented strategies."""

    strategies = [
        BalancingStrategy.ROUND_ROBIN,
        BalancingStrategy.LEAST_LOADED,
    ]

    for strategy in strategies:

        distribution, _ = run_real_simulation(
            strategy
        )

        assert sum(
            distribution.values()
        ) == TOTAL_TASKS


def test_real_distribution_accuracy():
    """Verify worker distribution accuracy."""

    strategies = [
        BalancingStrategy.ROUND_ROBIN,
        BalancingStrategy.LEAST_LOADED,
    ]

    expected_tasks = (
        TOTAL_TASKS / TOTAL_WORKERS
    )

    for strategy in strategies:

        distribution, _ = run_real_simulation(
            strategy
        )

        for task_count in distribution.values():

            difference = abs(
                task_count - expected_tasks
            )

            accuracy = (
                1
                - difference / expected_tasks
            )

            assert accuracy >= 0.99