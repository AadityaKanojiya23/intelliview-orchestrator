"""
Monitoring Module

Provides real-time dashboards and observability for the AI Interview Orchestration system.
"""

from monitoring.metrics_collector import MetricsCollector
from monitoring.websocket_manager import WebSocketManager, ws_manager
from monitoring.dashboard_api import create_dashboard_routes

__all__ = [
    "MetricsCollector",
    "WebSocketManager",
    "ws_manager",
    "create_dashboard_routes",
]
