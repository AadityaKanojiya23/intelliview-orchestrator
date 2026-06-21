"""
WebSocket Manager Module

Manages real-time WebSocket connections for live dashboard updates.

Responsibilities:
- Maintain active WebSocket connections
- Broadcast metrics updates to all connected clients
- Notify on session status changes
- Notify on worker failures
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time dashboard updates.

    Maintains:
    - Active client connections
    - Broadcast channels (metrics, alerts, events)
    - Connection lifecycle management
    """

    def __init__(self):
        """Initialize WebSocketManager"""
        self.active_connections: set[WebSocket] = set()
        self.connection_count = 0
        logger.info("WebSocketManager initialized")

    async def connect(self, websocket: WebSocket):
        """
        Register a new WebSocket connection

        Args:
            websocket: WebSocket connection object
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_count += 1

        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

        # Send welcome message
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "message": "Connected to monitoring dashboard",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def disconnect(self, websocket: WebSocket):
        """
        Unregister a WebSocket connection

        Args:
            websocket: WebSocket connection object
        """
        if websocket in self.active_connections:
            self.active_connections.discard(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_metrics(self, metrics: dict[str, Any]):
        """
        Broadcast system metrics to all connected clients

        Args:
            metrics: Dict containing system metrics
        """
        try:
            message = {
                "type": "metrics",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self._broadcast(message)

        except Exception as e:
            logger.error(f"Error broadcasting metrics: {e!s}")

    async def broadcast_session_update(self, session_id: str, status: str, details: dict | None = None):
        """
        Broadcast session status change

        Args:
            session_id: ID of session
            status: New session status
            details: Optional additional details
        """
        try:
            message = {
                "type": "session_update",
                "session_id": session_id,
                "status": status,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self._broadcast(message)

        except Exception as e:
            logger.error(f"Error broadcasting session update: {e!s}")

    async def broadcast_worker_alert(self, worker_id: str, alert_type: str, message: str):
        """
        Broadcast worker alert/failure

        Args:
            worker_id: ID of worker
            alert_type: Type of alert (failure, degraded, recovered)
            message: Alert message
        """
        try:
            payload = {
                "type": "worker_alert",
                "worker_id": worker_id,
                "alert_type": alert_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self._broadcast(payload)

        except Exception as e:
            logger.error(f"Error broadcasting worker alert: {e!s}")

    async def broadcast_failure_alert(self, failure_type: str, details: dict[str, Any]):
        """
        Broadcast system failure alert

        Args:
            failure_type: Type of failure
            details: Failure details
        """
        try:
            message = {
                "type": "failure_alert",
                "failure_type": failure_type,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self._broadcast(message)

        except Exception as e:
            logger.error(f"Error broadcasting failure alert: {e!s}")

    async def broadcast_health_status(self, health_status: str, details: dict[str, Any]):
        """
        Broadcast system health status change

        Args:
            health_status: Overall system health status
            details: Health check details
        """
        try:
            message = {
                "type": "health_update",
                "status": health_status,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self._broadcast(message)

        except Exception as e:
            logger.error(f"Error broadcasting health status: {e!s}")

    async def _broadcast(self, message: dict[str, Any]):
        """
        Send message to all connected clients

        Args:
            message: Message to broadcast
        """
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Error sending to client: {e!s}")
                disconnected.add(connection)

        # Remove disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)

    async def send_to_connection(self, websocket: WebSocket, message: dict[str, Any]):
        """
        Send message to specific connection

        Args:
            websocket: Target WebSocket connection
            message: Message to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to connection: {e!s}")
            await self.disconnect(websocket)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def get_connection_stats(self) -> dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self.connection_count,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()
