"""
FastAPI Orchestration Server
Main entry point for the AI Interview Orchestrator API

Integrates:
- Session Manager for lifecycle management
- Session Tracker for monitoring
- State Synchronizer for Redis/DB consistency
- Scheduler for intelligent task scheduling
- Load Balancer for worker distribution
- Worker Registry for node tracking
- Task Queue integration with Celery
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import logging
import asyncio
import re
import time as _time
from datetime import datetime
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from config import API_TOKEN, CORS_ALLOW_ORIGINS
from orchestrator.logging_config import configure_logging, log_event

# Configure logging before anything else so startup messages are structured.
configure_logging()

from workers.tasks import process_interview_session
from orchestrator.session_manager import SessionManager
from orchestrator.session_tracker import SessionTracker
from orchestrator.state_sync import StateSynchronizer
from orchestrator.scheduler import Scheduler, TaskPriority
from orchestrator.load_balancer import LoadBalancer, BalancingStrategy
from orchestrator.worker_registry import WorkerRegistry
from orchestrator.fault_manager import FaultManager, FailureType
from orchestrator.retry_manager import RetryManager, RetryStrategy
from orchestrator.health_monitor import HealthMonitor, HealthStatus
from monitoring.metrics_collector import MetricsCollector
from monitoring.dashboard_api import create_dashboard_routes
from monitoring.websocket_manager import ws_manager
from database.db import engine
from database.models import Base

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Execute on application startup/shutdown."""
    Base.metadata.create_all(bind=engine)
    logger.info("AI Interview Orchestrator server starting...")
    yield
    logger.info("AI Interview Orchestrator server shutting down...")


# Initialize FastAPI application
app = FastAPI(
    title="AI Interview Orchestrator",
    description="Orchestration API for distributed interview processing",
    version="1.0.0",
    lifespan=lifespan,
)


# ========== Request ID + duration middleware ==========

_VALID_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request ID, measures duration, and tags the response.

    Honours an incoming `X-Request-ID` header if it matches a safe format;
    otherwise generates a new UUID4. The ID is attached to the response as
    `X-Request-ID` so callers can correlate logs.
    """

    async def dispatch(self, request: StarletteRequest, call_next):
        incoming = request.headers.get("x-request-id", "").strip()
        request_id = incoming if _VALID_ID_RE.match(incoming) else uuid4().hex
        request.state.request_id = request_id
        start = _time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (_time.perf_counter() - start) * 1000
            log_event(
                logger, logging.ERROR, "unhandled_error",
                request_id=request_id, path=request.url.path,
                elapsed_ms=round(elapsed_ms, 1),
            )
            logger.debug("traceback", exc_info=True)
            raise
        elapsed_ms = (_time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.1f}"
        if request.url.path != "/health":
            log_event(
                logger, logging.INFO, "request",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                elapsed_ms=round(elapsed_ms, 1),
            )
        return response


app.add_middleware(RequestContextMiddleware)

# CORS — configurable via env. Default "*" is for local dev only.
_cors_origins = ["*"] if CORS_ALLOW_ORIGINS in ("*", "") else [
    o.strip() for o in CORS_ALLOW_ORIGINS.split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Auth ==========

def require_token(x_api_token: Optional[str] = Header(default=None)) -> None:
    """Dependency that requires a valid API token.

    Worker agents (and any privileged caller) must send `X-API-Token`.
    Set the expected token via the API_TOKEN env var.
    """
    if not API_TOKEN or API_TOKEN == "dev-token-change-me":
        # In dev with the default token, accept but log.
        logger.debug("Using default API token — set API_TOKEN in production")
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="invalid or missing API token")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize managers and orchestrators
session_manager = SessionManager()
session_tracker = SessionTracker()
state_sync = StateSynchronizer()
load_balancer = LoadBalancer(strategy=BalancingStrategy.LEAST_LOADED)
scheduler = Scheduler(load_balancer=load_balancer)
worker_registry = WorkerRegistry()
fault_manager = FaultManager()
retry_manager = RetryManager(max_retries=3, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
health_monitor = HealthMonitor()
metrics_collector = MetricsCollector()

# Register dashboard routes
dashboard_routes = create_dashboard_routes(
    metrics_collector=metrics_collector,
    session_manager=session_manager,
    worker_registry=worker_registry,
    session_tracker=session_tracker,
    fault_manager=fault_manager,
    retry_manager=retry_manager,
    health_monitor=health_monitor,
    ws_manager=ws_manager
)
app.include_router(dashboard_routes, prefix="/monitoring", tags=["monitoring"])


# ========== Request/Response Models ==========

class StartInterviewRequest(BaseModel):
    """Request model for starting an interview"""
    candidate_id: str = Field(min_length=1, max_length=128, description="Unique candidate identifier")
    candidate_name: Optional[str] = Field(default=None, max_length=200)
    position: Optional[str] = Field(default=None, max_length=120)
    priority: str = Field(default="medium", description="One of: low, medium, high")

    @field_validator("candidate_id")
    @classmethod
    def _candidate_id_format(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[A-Za-z0-9._-]+$", v):
            raise ValueError("candidate_id may only contain letters, digits, '.', '_', '-'")
        return v

    @field_validator("priority")
    @classmethod
    def _priority_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"low", "medium", "high"}:
            raise ValueError("priority must be one of: low, medium, high")
        return v

    @field_validator("candidate_name", "position")
    @classmethod
    def _strip_optional(cls, v):
        return v.strip() if isinstance(v, str) else v


class ErrorResponse(BaseModel):
    """Standardised error envelope returned by the API."""
    detail: str
    request_id: Optional[str] = None


class WorkerRegistrationRequest(BaseModel):
    """Request model for worker registration"""
    worker_id: str
    capacity: int = 4


class WorkerHeartbeatRequest(BaseModel):
    """Request model for worker heartbeat"""
    worker_id: str
    active_tasks: int


class InterviewSessionResponse(BaseModel):
    """Response model for interview session"""
    session_id: str
    status: str
    created_at: Optional[str] = None
    candidate_id: str
    risk_score: Optional[float] = None
    estimated_wait_time: Optional[int] = None


class SessionStatusResponse(BaseModel):
    """Response model for session status"""
    session_id: str
    status: str
    candidate_id: str
    risk_score: Optional[float] = None
    assigned_node: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    updated_at: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """Response model for Celery task status (used by /task-status/{task_id})."""
    session_id: str
    task_id: str
    status: str
    result: Optional[dict] = None


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns system status
    """
    return {
        "status": "system running",
        "timestamp": datetime.utcnow().isoformat()
    }


# ========== Interview Session Endpoints ==========

@app.post("/start-interview", response_model=InterviewSessionResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start a new interview session using intelligent scheduling
    
    Execution flow:
    1. Create session in database (status: CREATED)
    2. Cache session in Redis
    3. Update status to QUEUED
    4. Use Scheduler to intelligently assign to worker
    5. Task pushed to Redis queue and/or assigned to specific worker
    
    Args:
        request: Interview session request with candidate details
        
    Returns:
        InterviewSessionResponse: Created session details with estimated wait time
        
    Raises:
        HTTPException: On creation failure
    """
    try:
        logger.info(f"API: Creating interview session for candidate {request.candidate_id}")
        
        # Parse priority
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH
        }
        priority = priority_map.get(request.priority.lower(), TaskPriority.MEDIUM)
        
        # Create session
        session_id = session_manager.create_session(
            candidate_id=request.candidate_id,
            candidate_name=request.candidate_name,
            position=request.position
        )
        
        logger.info(f"Session created: {session_id}")
        
        # Update status to QUEUED
        session_manager.update_session_status(
            session_id,
            session_manager.QUEUED,
            {"priority": priority.name}
        )
        
        # Check if system can accept task
        if not scheduler.can_accept_task():
            logger.warning(f"System at capacity, queuing task: {session_id}")
        
        # Use scheduler to intelligently assign task
        scheduler.schedule_task(session_id, priority=priority)
        
        # Get estimated wait time
        wait_time = scheduler.get_estimated_wait_time(priority)
        
        # Retrieve and return session details
        session_data = session_manager.get_session(session_id)
        
        return InterviewSessionResponse(
            session_id=session_id,
            status=session_manager.QUEUED,
            created_at=session_data.get("created_at"),
            candidate_id=request.candidate_id,
            risk_score=None,
            estimated_wait_time=wait_time if wait_time >= 0 else None
        )
        
    except Exception as e:
        logger.error(f"Error starting interview session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")


@app.get("/session-status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get current status of an interview session
    
    Retrieves real-time session information including:
    - Current status (CREATED, QUEUED, PROCESSING, COMPLETED, FAILED)
    - Risk score if available
    - Processing node information
    - Timestamps
    
    Args:
        session_id: Interview session identifier
        
    Returns:
        SessionStatusResponse: Current session status and details
        
    Raises:
        HTTPException: If session not found
    """
    try:
        logger.debug(f"API: Fetching status for session {session_id}")
        
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            logger.warning(f"Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionStatusResponse(
            session_id=session_id,
            status=session_data.get("status"),
            candidate_id=session_data.get("candidate_id"),
            risk_score=session_data.get("risk_score"),
            assigned_node=session_data.get("assigned_node"),
            start_time=session_data.get("start_time"),
            end_time=session_data.get("end_time"),
            updated_at=session_data.get("updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")


@app.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a Celery task by its ID.

    Args:
        task_id: Celery task identifier (returned by the scheduler).

    Returns:
        TaskStatusResponse: Current task status and result if available.
    """
    try:
        from workers.celery_app import celery_app
        result = celery_app.AsyncResult(task_id)
        status = result.status
        payload = {
            "session_id": result.result.get("session_id") if isinstance(result.result, dict) else None,
            "task_id": task_id,
            "status": status,
            "result": result.result if status == "SUCCESS" else None,
        }
        return TaskStatusResponse(**payload)
    except Exception as e:
        logger.error(f"Error fetching task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching task status: {e}")


# ========== Session Tracking Endpoints ==========

@app.get("/active-sessions")
async def get_active_sessions():
    """
    Get all currently active sessions

    Returns sessions in states: CREATED, QUEUED, PROCESSING

    Returns:
        dict: List of active sessions with brief details
    """
    try:
        active = session_tracker.get_active_sessions()
        return {
            "count": len(active),
            "sessions": active
        }
    except Exception as e:
        logger.error(f"Error fetching active sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching active sessions")


@app.get("/completed-sessions")
async def get_completed_sessions(limit: int = 100):
    """
    Get recently completed sessions
    
    Args:
        limit: Maximum number of sessions to retrieve (default: 100)
        
    Returns:
        dict: List of completed sessions with results
    """
    try:
        completed = session_tracker.get_completed_sessions(limit=limit)
        return {
            "count": len(completed),
            "sessions": completed
        }
    except Exception as e:
        logger.error(f"Error fetching completed sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching completed sessions")


@app.get("/stuck-sessions")
async def get_stuck_sessions(timeout_minutes: int = 30):
    """
    Get sessions that appear to be stuck in PROCESSING
    
    Args:
        timeout_minutes: Timeout threshold in minutes (default: 30)
        
    Returns:
        dict: List of stuck sessions
    """
    try:
        stuck = session_tracker.get_stuck_sessions(timeout_minutes=timeout_minutes)
        return {
            "count": len(stuck),
            "timeout_minutes": timeout_minutes,
            "sessions": stuck
        }
    except Exception as e:
        logger.error(f"Error fetching stuck sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching stuck sessions")


# ========== Statistics Endpoints ==========

@app.get("/session-statistics")
async def get_session_statistics():
    """
    Get comprehensive session statistics
    
    Returns statistics including:
    - Total sessions by status
    - Average processing duration
    - Risk score distribution
    - High-risk session count
    
    Returns:
        dict: Session statistics
    """
    try:
        stats = session_tracker.get_session_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error generating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating statistics")


@app.get("/worker-distribution")
async def get_worker_distribution():
    """
    Get distribution of sessions across worker nodes
    
    Returns:
        dict: Worker node -> session count mapping
    """
    try:
        distribution = session_tracker.get_worker_distribution()
        return {
            "workers": distribution,
            "total_active": sum(distribution.values())
        }
    except Exception as e:
        logger.error(f"Error fetching worker distribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching worker distribution")


@app.get("/high-risk-sessions")
async def get_high_risk_sessions(threshold: float = 0.8, limit: int = 50):
    """
    Get high-risk completed sessions
    
    Args:
        threshold: Risk score threshold (0-1, default: 0.8)
        limit: Maximum sessions to return (default: 50)
        
    Returns:
        dict: List of high-risk sessions
    """
    try:
        high_risk = session_tracker.get_high_risk_sessions(threshold=threshold, limit=limit)
        return {
            "count": len(high_risk),
            "threshold": threshold,
            "sessions": high_risk
        }
    except Exception as e:
        logger.error(f"Error fetching high-risk sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching high-risk sessions")


# ========== Cache Management Endpoints ==========

@app.get("/cache-stats")
async def get_cache_stats():
    """
    Get Redis cache statistics
    
    Returns:
        dict: Cache health and statistics
    """
    try:
        cache_stats = state_sync.get_cache_stats()
        return cache_stats
    except Exception as e:
        logger.error(f"Error fetching cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching cache stats")


@app.post("/sync-to-database")
async def sync_cache_to_database(session_id: Optional[str] = None):
    """
    Manually sync cache to database
    
    Args:
        session_id: Specific session to sync, or None to sync all active sessions
        
    Returns:
        dict: Sync result
    """
    try:
        if session_id:
            session_data = state_sync.get_session_state(session_id)
            if session_data:
                state_sync.sync_state_to_db(session_id, session_data)
                return {"message": f"Synced session {session_id}", "status": "success"}
            else:
                raise HTTPException(status_code=404, detail="Session not found in cache")
        else:
            # Sync all active sessions
            active_sessions = state_sync.get_active_sessions()
            for sid in active_sessions:
                session_data = state_sync.get_session_state(sid)
                if session_data:
                    state_sync.sync_state_to_db(sid, session_data)
            
            return {
                "message": f"Synced {len(active_sessions)} sessions",
                "status": "success",
                "synced_count": len(active_sessions)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing to database: {str(e)}")
        raise HTTPException(status_code=500, detail="Error syncing to database")


@app.delete("/clear-cache", dependencies=[Depends(require_token)])
async def clear_session_cache():
    """
    Clear all session cache from Redis
    
    WARNING: This will clear all cached session states
    
    Returns:
        dict: Clear operation result
    """
    try:
        logger.warning("Clearing all session cache from Redis")
        result = state_sync.clear_cache()
        return {
            "message": "Cache cleared",
            "status": "success" if result else "failed"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Error clearing cache")


@app.get("/interviews")
async def list_interviews():
    """
    List all interview sessions (legacy endpoint)
    
    Returns:
        dict: List of interview sessions
    """
    logger.info("Listing all interview sessions")
    return {
        "sessions": [],
        "total_count": 0
    }


# ========== Worker Management Endpoints ==========

@app.post("/register-worker", dependencies=[Depends(require_token)])
async def register_worker(request: WorkerRegistrationRequest):
    """
    Register a new worker node
    
    Args:
        request: Worker registration details (worker_id, capacity)
        
    Returns:
        dict: Registration confirmation
    """
    try:
        logger.info(f"Registering worker: {request.worker_id} with capacity {request.capacity}")
        
        # Register worker in registry
        worker_registry.register_worker(
            worker_id=request.worker_id,
            capacity=request.capacity
        )
        
        # Log successful registration
        logger.info(f"Worker registered successfully: {request.worker_id}")
        
        return {
            "status": "success",
            "message": f"Worker {request.worker_id} registered",
            "worker_id": request.worker_id,
            "capacity": request.capacity,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error registering worker: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error registering worker: {str(e)}")


@app.post("/worker/heartbeat", dependencies=[Depends(require_token)])
async def worker_heartbeat(request: WorkerHeartbeatRequest):
    """
    Process heartbeat from worker node
    
    Workers send periodic heartbeats to indicate they are alive
    and to report current active task count
    
    Args:
        request: Heartbeat data (worker_id, active_tasks)
        
    Returns:
        dict: Heartbeat confirmation
    """
    try:
        logger.debug(f"Heartbeat from worker: {request.worker_id} (active_tasks: {request.active_tasks})")
        
        # Update worker heartbeat in registry
        worker_registry.heartbeat(
            worker_id=request.worker_id,
            active_tasks=request.active_tasks
        )
        
        # Get worker health status
        worker_status = worker_registry.get_worker(request.worker_id)
        health_status = "healthy" if worker_status and worker_status.get("health_status") == "healthy" else "unknown"
        
        return {
            "status": "success",
            "message": "Heartbeat received",
            "worker_id": request.worker_id,
            "health": health_status,
            "active_tasks": request.active_tasks,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing heartbeat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing heartbeat: {str(e)}")


@app.get("/workers")
async def list_workers():
    """
    Get list of all registered workers with status
    
    Returns:
        dict: Worker nodes with status information
    """
    try:
        logger.debug("Fetching worker list")
        
        # Get all workers from registry
        all_workers = worker_registry.get_all_workers()
        
        # Detect unhealthy workers (no heartbeat for timeout period)
        unhealthy = worker_registry.detect_unhealthy_workers()
        
        # Build worker list with status
        workers_list = []
        for worker_id, worker_data in all_workers.items():
            is_healthy = worker_id not in unhealthy
            workers_list.append({
                "worker_id": worker_id,
                "capacity": worker_data.get("capacity", 0),
                "active_tasks": worker_data.get("active_tasks", 0),
                "available_capacity": worker_data.get("capacity", 0) - worker_data.get("active_tasks", 0),
                "health_status": "healthy" if is_healthy else "unhealthy",
                "last_heartbeat": worker_data.get("last_heartbeat", None),
                "joined_at": worker_data.get("joined_at", None)
            })
        
        return {
            "total_workers": len(all_workers),
            "healthy_workers": len(all_workers) - len(unhealthy),
            "unhealthy_workers": len(unhealthy),
            "workers": workers_list,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching worker list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching worker list: {str(e)}")


@app.get("/worker-statistics")
async def get_worker_stats():
    """
    Get detailed worker statistics and utilization metrics
    
    Returns:
        dict: Worker utilization and performance metrics
    """
    try:
        logger.debug("Generating worker statistics")
        
        # Get worker statistics
        stats = worker_registry.get_worker_statistics()
        
        # Calculate aggregate metrics
        total_capacity = stats.get("total_capacity", 0)
        total_active = stats.get("total_active_tasks", 0)
        utilization = (total_active / total_capacity * 100) if total_capacity > 0 else 0
        
        return {
            "total_workers": stats.get("total_workers", 0),
            "total_capacity": total_capacity,
            "total_active_tasks": total_active,
            "system_utilization_percent": round(utilization, 2),
            "average_utilization_per_worker": stats.get("average_active_tasks", 0),
            "min_worker_load": stats.get("min_active_tasks", 0),
            "max_worker_load": stats.get("max_active_tasks", 0),
            "idle_workers": stats.get("idle_workers", 0),
            "worker_details": stats.get("workers", []),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating worker statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating worker statistics: {str(e)}")


@app.get("/load-status")
async def get_load_status():
    """
    Get current system load and capacity status
    
    Provides visualization of:
    - Overall system utilization
    - Queue depth
    - Worker availability
    - Load balancer strategy recommendations
    
    Returns:
        dict: System load information
    """
    try:
        logger.debug("Fetching system load status")
        
        # Get load status from load balancer
        load_status = load_balancer.get_load_status()
        
        return {
            "current_strategy": load_status.get("current_strategy", "unknown"),
            "system_utilization_percent": load_status.get("system_utilization", 0),
            "available_workers": load_status.get("total_workers", 0),
            "busy_workers": load_status.get("busy_workers", 0),
            "idle_workers": load_status.get("idle_workers", 0),
            "system_at_capacity": load_status.get("system_at_capacity", False),
            "system_overloaded": load_status.get("system_overloaded", False),
            "recommended_strategy": load_status.get("recommended_strategy", "LEAST_LOADED"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching load status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching load status: {str(e)}")


@app.get("/scheduling-status")
async def get_scheduling_status():
    """
    Get scheduler status and health information
    
    Returns:
        dict: Scheduler operational status and metrics
    """
    try:
        logger.debug("Fetching scheduler status")
        
        # Get scheduling status
        status_info = scheduler.get_scheduling_status()
        
        return {
            "scheduler_active": True,
            "current_strategy": load_balancer.strategy.name,
            "system_overloaded": status_info.get("system_overloaded", False),
            "available_workers": status_info.get("available_workers", 0),
            "can_accept_tasks": scheduler.can_accept_task(),
            "recommendation": status_info.get("recommendation"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching scheduling status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching scheduling status: {str(e)}")


@app.post("/switch-strategy")
async def switch_load_balancing_strategy(strategy: str):
    """
    Change the active load balancing strategy
    
    Supported strategies:
    - ROUND_ROBIN: Sequential worker assignment (even task distribution)
    - LEAST_LOADED: Assign to worker with fewest active tasks (recommended)
    - QUEUE_BASED: Use Redis queue length as selection metric
    
    Args:
        strategy: Strategy name (ROUND_ROBIN, LEAST_LOADED, QUEUE_BASED)
        
    Returns:
        dict: Strategy change confirmation
    """
    try:
        logger.info(f"Switching load balancing strategy to: {strategy}")
        
        # Validate strategy
        valid_strategies = {
            "ROUND_ROBIN": BalancingStrategy.ROUND_ROBIN,
            "LEAST_LOADED": BalancingStrategy.LEAST_LOADED,
            "QUEUE_BASED": BalancingStrategy.QUEUE_BASED
        }
        
        if strategy.upper() not in valid_strategies:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strategy. Valid options: {', '.join(valid_strategies.keys())}"
            )
        
        # Switch strategy
        new_strategy = valid_strategies[strategy.upper()]
        load_balancer.switch_strategy(new_strategy)
        
        logger.info(f"Load balancing strategy switched to: {strategy}")
        
        return {
            "status": "success",
            "message": f"Strategy switched to {strategy}",
            "previous_strategy": load_balancer.strategy.name,
            "new_strategy": strategy,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error switching strategy: {str(e)}")


@app.delete("/deregister-worker/{worker_id}", dependencies=[Depends(require_token)])
async def deregister_worker(worker_id: str):
    """
    Deregister a worker node (remove from active pool)
    
    Use this when a worker is permanently removed from the system
    
    Args:
        worker_id: ID of worker to deregister
        
    Returns:
        dict: Deregistration confirmation
    """
    try:
        logger.info(f"Deregistering worker: {worker_id}")
        
        # Deregister worker
        worker_registry.deregister_worker(worker_id)
        
        logger.info(f"Worker deregistered successfully: {worker_id}")
        
        return {
            "status": "success",
            "message": f"Worker {worker_id} deregistered",
            "worker_id": worker_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error deregistering worker: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deregistering worker: {str(e)}")


# ========== Fault Tolerance & Recovery Endpoints ==========

@app.get("/failed-sessions")
async def get_failed_sessions(limit: int = 100):
    """
    Get sessions that failed during processing
    
    Args:
        limit: Maximum number of failed sessions to return
        
    Returns:
        dict: List of failed sessions with details
    """
    try:
        logger.debug("Fetching failed sessions")
        
        # Get from session tracker
        failed = session_tracker.get_failed_sessions(limit=limit)
        
        return {
            "count": len(failed),
            "failed_sessions": failed,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching failed sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching failed sessions: {str(e)}")


@app.post("/retry-session/{session_id}")
async def retry_failed_session(session_id: str):
    """
    Retry a failed interview session
    
    Attempts to reschedule the session if it hasn't exceeded max retries.
    
    Args:
        session_id: ID of session to retry
        
    Returns:
        dict: Retry scheduling result
    """
    try:
        logger.info(f"Retry request for session: {session_id}")
        
        # Check if can retry
        if not retry_manager.can_retry(session_id):
            raise HTTPException(
                status_code=400,
                detail=f"Session {session_id} has exceeded maximum retry attempts"
            )
        
        # Get retry info
        retry_info = retry_manager.get_retry_info(session_id)
        
        # Schedule retry with exponential backoff
        retry_scheduled = retry_manager.schedule_retry(session_id)
        
        if not retry_scheduled:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to schedule retry for session {session_id}"
            )
        
        logger.info(f"Session {session_id} scheduled for retry: {retry_info}")
        
        return {
            "status": "success",
            "message": f"Session {session_id} scheduled for retry",
            "session_id": session_id,
            "retry_info": retry_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrying session: {str(e)}")


@app.get("/system-health")
async def get_system_health():
    """
    Get comprehensive system health status
    
    Performs health checks on:
    - Redis connectivity
    - Worker nodes
    - Active sessions
    - Queue backlog
    
    Returns:
        dict: System health status and metrics
    """
    try:
        logger.debug("Performing system health check")
        
        # Perform comprehensive health check
        health = health_monitor.check_system_health(
            worker_registry=worker_registry,
            session_manager=session_manager
        )
        
        return health
    except Exception as e:
        logger.error(f"Error checking system health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking system health: {str(e)}")


@app.get("/worker-health")
async def get_worker_health():
    """
    Get detailed health status of all workers
    
    Returns:
        dict: Worker health information
    """
    try:
        logger.debug("Fetching worker health status")
        
        # Check worker health
        worker_health = health_monitor.check_worker_health(worker_registry)
        
        return worker_health
    except Exception as e:
        logger.error(f"Error fetching worker health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching worker health: {str(e)}")


@app.get("/recovery-queue")
async def get_recovery_queue(limit: int = 50):
    """
    Get sessions queued for recovery/retry
    
    Args:
        limit: Maximum number to return
        
    Returns:
        dict: Recovery queue entries
    """
    try:
        logger.debug("Fetching recovery queue")
        
        recovery_queue = fault_manager.get_recovery_queue(limit=limit)
        
        return {
            "count": len(recovery_queue),
            "recovery_queue": recovery_queue,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching recovery queue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching recovery queue: {str(e)}")


@app.get("/failure-log")
async def get_failure_log(limit: int = 100):
    """
    Get system failure log entries
    
    Args:
        limit: Maximum number of entries to return
        
    Returns:
        dict: Failure log entries
    """
    try:
        logger.debug("Fetching failure log")
        
        failures = fault_manager.get_failure_log(limit=limit)
        
        return {
            "count": len(failures),
            "failures": failures,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching failure log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching failure log: {str(e)}")


@app.get("/dead-letter-queue")
async def get_dead_letter_queue(limit: int = 50):
    """
    Get permanently failed sessions in dead letter queue
    
    Args:
        limit: Maximum number to return
        
    Returns:
        dict: Dead letter queue entries
    """
    try:
        logger.debug("Fetching dead letter queue")
        
        dlq = fault_manager.get_dead_letter_queue(limit=limit)
        
        return {
            "count": len(dlq),
            "dead_letter_queue": dlq,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching dead letter queue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching dead letter queue: {str(e)}")


@app.get("/fault-statistics")
async def get_fault_statistics():
    """
    Get aggregate fault and recovery statistics
    
    Returns:
        dict: System fault metrics and trends
    """
    try:
        logger.debug("Generating fault statistics")
        
        fault_stats = fault_manager.get_system_fault_stats()
        retry_stats = retry_manager.get_retry_statistics()
        
        return {
            "fault_statistics": fault_stats,
            "retry_statistics": retry_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating fault statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating fault statistics: {str(e)}")


@app.post("/detect-failures")
async def detect_and_handle_failures():
    """
    Manually trigger failure detection and recovery
    
    Scans for:
    - Failed sessions (stuck in PROCESSING)
    - Unhealthy workers
    - Stuck sessions
    
    Triggers recovery for detected failures.
    
    Returns:
        dict: Detection and recovery results
    """
    try:
        logger.info("Manual failure detection triggered")
        
        # Detect failed sessions
        failed_sessions = fault_manager.detect_failed_sessions()
        
        # Detect unhealthy workers
        unhealthy_workers = health_monitor.detect_worker_failures(worker_registry)
        
        # Detect stuck sessions
        stuck_sessions = health_monitor.detect_stuck_sessions(session_manager)
        
        # Handle worker failures
        handled = 0
        for worker_id in unhealthy_workers:
            if fault_manager.handle_worker_failure(worker_id, "Detected as unhealthy"):
                handled += 1
        
        results = {
            "status": "success",
            "failed_sessions_detected": len(failed_sessions),
            "failed_sessions": failed_sessions,
            "unhealthy_workers_detected": len(unhealthy_workers),
            "unhealthy_workers": unhealthy_workers,
            "workers_handled": handled,
            "stuck_sessions_detected": len(stuck_sessions),
            "stuck_sessions": stuck_sessions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Failure detection complete: {len(failed_sessions)} failed, "
                   f"{len(unhealthy_workers)} unhealthy workers, {len(stuck_sessions)} stuck")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during failure detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during failure detection: {str(e)}")


# ========== Dashboard HTML Endpoint ==========

@app.get("/dashboard")
async def get_dashboard():
    """
    Serve the monitoring dashboard HTML
    
    Returns:
        HTML content of the dashboard
    """
    try:
        import os
        dashboard_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "monitoring", 
            "dashboard.html"
        )
        
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html_content)
        else:
            raise HTTPException(status_code=404, detail="Dashboard HTML not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving dashboard: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
