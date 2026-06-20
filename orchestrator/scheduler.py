"""
Scheduler
Controls when and how tasks are executed

Responsibilities:
- Schedule interview tasks to workers
- Handle task prioritization
- Support delayed execution
- Manage task retries
- Coordinate with load balancer
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from workers.tasks import process_interview_session
from orchestrator.load_balancer import LoadBalancer, BalancingStrategy
from orchestrator.worker_registry import WorkerRegistry
from orchestrator.session_manager import SessionManager

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2


class Scheduler:
    """
    Manages task scheduling and distribution to workers
    """
    
    def __init__(self, load_balancer: Optional[LoadBalancer] = None):
        """
        Initialize scheduler
        
        Args:
            load_balancer: Optional custom LoadBalancer instance
        """
        self.load_balancer = load_balancer or LoadBalancer(strategy=BalancingStrategy.LEAST_LOADED)
        self.worker_registry = WorkerRegistry()
        self.session_manager = SessionManager()
        logger.info("Scheduler initialized with Least Loaded strategy")
    
    def schedule_task(self, session_id: str, priority: TaskPriority = TaskPriority.MEDIUM,
                     delay_seconds: int = 0) -> bool:
        """
        Schedule an interview task for execution
        
        Execution flow:
        1. Get session details
        2. Select worker using load balancer
        3. If worker available: assign task directly
        4. If no worker: queue task in Redis
        5. Update session status
        
        Args:
            session_id: Interview session ID
            priority: Task priority level
            delay_seconds: Seconds to delay execution (0 = immediate)
            
        Returns:
            bool: True if scheduling successful
        """
        try:
            logger.info(f"Scheduling task for session {session_id} (priority: {priority.name})")
            
            # Verify session exists
            session_data = self.session_manager.get_session(session_id)
            if not session_data:
                logger.error(f"Session {session_id} not found")
                return False
            
            # Select worker
            worker = self.load_balancer.get_best_worker_for_priority(priority.name.lower())
            
            if not worker:
                logger.warning(f"No worker available for session {session_id} - queueing task")
                # Queue task directly to Redis, it will be picked up by any available worker
                return self._queue_task(session_id, delay_seconds)
            
            logger.info(
                f"Assigned session {session_id} to worker {worker['worker_id']} "
                f"(load: {worker['active_tasks']}/{worker['capacity']})"
            )
            
            # Update worker active task count
            self.worker_registry.increment_active_tasks(worker["worker_id"])
            
            # Enqueue the task
            if delay_seconds > 0:
                task = process_interview_session.apply_async(
                    args=[session_id],
                    countdown=delay_seconds
                )
                logger.info(f"Task queued with {delay_seconds}s delay: {task.id}")
            else:
                task = process_interview_session.delay(session_id)
                logger.info(f"Task enqueued immediately: {task.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling task: {str(e)}")
            self.session_manager.mark_session_failed(
                session_id,
                f"Scheduling error: {str(e)}"
            )
            return False
    
    def _queue_task(self, session_id: str, delay_seconds: int = 0) -> bool:
        """
        Queue a task to Redis without direct worker assignment
        
        Args:
            session_id: Session ID
            delay_seconds: Delay before execution
            
        Returns:
            bool: True if queued successfully
        """
        try:
            if delay_seconds > 0:
                task = process_interview_session.apply_async(
                    args=[session_id],
                    countdown=delay_seconds
                )
            else:
                task = process_interview_session.delay(session_id)
            
            logger.info(f"Task queued in Redis: {session_id} (task_id: {task.id})")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing task: {str(e)}")
            return False
    
    def reschedule_failed_task(self, session_id: str, retry_delay: int = 60) -> bool:
        """
        Reschedule a failed task for retry
        
        Args:
            session_id: Session ID
            retry_delay: Delay before retry in seconds
            
        Returns:
            bool: True if rescheduled successfully
        """
        try:
            logger.info(f"Rescheduling failed task: {session_id} (retry in {retry_delay}s)")
            
            # Verify session exists
            session_data = self.session_manager.get_session(session_id)
            if not session_data:
                logger.error(f"Session {session_id} not found for retry")
                return False
            
            # Check retry count
            retry_count = session_data.get("retry_count", 0)
            max_retries = 3
            
            if retry_count >= max_retries:
                logger.warning(f"Max retries exceeded for session {session_id}")
                self.session_manager.mark_session_failed(
                    session_id,
                    f"Max retries exceeded ({max_retries})"
                )
                return False
            
            # Queue task with delay
            process_interview_session.apply_async(
                args=[session_id],
                countdown=retry_delay
            )
            
            logger.info(f"Task rescheduled: {session_id} (attempt {retry_count + 1}/{max_retries})")
            return True
            
        except Exception as e:
            logger.error(f"Error rescheduling task: {str(e)}")
            return False
    
    def schedule_batch_tasks(self, session_ids: list, priority: TaskPriority = TaskPriority.MEDIUM) -> Dict[str, bool]:
        """
        Schedule multiple tasks at once
        
        Args:
            session_ids: List of session IDs
            priority: Priority level for all tasks
            
        Returns:
            dict: Mapping of session_id -> scheduling success
        """
        results = {}
        
        for session_id in session_ids:
            results[session_id] = self.schedule_task(session_id, priority)
        
        successful = sum(1 for v in results.values() if v)
        logger.info(f"Batch scheduling complete: {successful}/{len(session_ids)} successful")
        
        return results
    
    def get_scheduling_status(self) -> Dict[str, Any]:
        """Get current scheduling and load information"""
        load_status = self.load_balancer.get_load_status()
        
        # Check for overloaded system
        is_overloaded = load_status["system_overloaded"]
        
        # Recommend strategy switch if needed
        recommendation = None
        if is_overloaded and self.load_balancer.strategy != BalancingStrategy.LEAST_LOADED:
            recommendation = "Switch to LEAST_LOADED strategy to optimize load distribution"
        
        return {
            "load_balancer_strategy": self.load_balancer.strategy.value,
            "worker_stats": load_status["worker_stats"],
            "available_workers": load_status["available_workers"],
            "system_overloaded": is_overloaded,
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def optimize_strategy(self) -> None:
        """
        Automatically optimize load balancing strategy based on system state
        """
        stats = self.worker_registry.get_worker_statistics()
        utilization = stats["capacity_utilization"]
        
        # If utilization > 80%, ensure we're using least loaded
        if utilization > 80:
            if self.load_balancer.strategy != BalancingStrategy.LEAST_LOADED:
                logger.info(f"High utilization ({utilization}%) - switching to LEAST_LOADED strategy")
                self.load_balancer.switch_strategy(BalancingStrategy.LEAST_LOADED)
        
        # If utilization < 30%, can use round robin for simplicity
        elif utilization < 30:
            if self.load_balancer.strategy != BalancingStrategy.ROUND_ROBIN:
                logger.info(f"Low utilization ({utilization}%) - switching to ROUND_ROBIN strategy")
                self.load_balancer.switch_strategy(BalancingStrategy.ROUND_ROBIN)
    
    def can_accept_task(self) -> bool:
        """
        Check if system can accept new tasks
        
        Returns:
            bool: True if system has capacity
        """
        available = self.worker_registry.get_available_workers()
        return len(available) > 0
    
    def get_estimated_wait_time(self, priority: TaskPriority = TaskPriority.MEDIUM) -> int:
        """
        Estimate wait time for a task with given priority
        
        Args:
            priority: Task priority
            
        Returns:
            int: Estimated wait time in seconds (rough estimate)
        """
        available = self.worker_registry.get_available_workers()
        
        if available:
            # If worker available, minimal wait
            return 0
        
        # Estimate based on system load
        stats = self.worker_registry.get_worker_statistics()
        avg_task_duration = 600  # Assume ~10 min per task
        total_queued_tasks = stats["total_active_tasks"]
        num_workers = stats["total_workers"]
        
        if num_workers == 0:
            return -1  # Cannot estimate
        
        # Rough estimate: (queued_tasks / workers) * avg_duration
        wait_time = int((total_queued_tasks / num_workers) * avg_task_duration)
        
        return wait_time
