from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Set, Optional
import asyncio
import json
from datetime import datetime

from backend.database import get_db
from backend.schemas.ws import WSAlertPayload, WSHealthPayload

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        # station_id -> set of websockets (None for "all stations")
        self.alert_connections: Dict[Optional[str], Set[WebSocket]] = {"all": set()}
        self.health_connections: Dict[Optional[str], Set[WebSocket]] = {"all": set()}
    
    async def connect_alerts(self, websocket: WebSocket, station_id: Optional[str] = None):
        await websocket.accept()
        key = station_id or "all"
        if key not in self.alert_connections:
            self.alert_connections[key] = set()
        self.alert_connections[key].add(websocket)
    
    async def connect_health(self, websocket: WebSocket, station_id: Optional[str] = None):
        await websocket.accept()
        key = station_id or "all"
        if key not in self.health_connections:
            self.health_connections[key] = set()
        self.health_connections[key].add(websocket)
    
    def disconnect_alerts(self, websocket: WebSocket, station_id: Optional[str] = None):
        key = station_id or "all"
        if key in self.alert_connections:
            self.alert_connections[key].discard(websocket)
    
    def disconnect_health(self, websocket: WebSocket, station_id: Optional[str] = None):
        key = station_id or "all"
        if key in self.health_connections:
            self.health_connections[key].discard(websocket)
    
    async def broadcast_alert(self, payload: WSAlertPayload, station_id: str):
        """Broadcast alert to all subscribers for this station + global."""
        message = payload.model_dump_json()
        
        # Send to station-specific connections
        if station_id in self.alert_connections:
            disconnected = set()
            for ws in self.alert_connections[station_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.add(ws)
            for ws in disconnected:
                self.alert_connections[station_id].discard(ws)
        
        # Send to global connections
        if "all" in self.alert_connections:
            disconnected = set()
            for ws in self.alert_connections["all"]:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.add(ws)
            for ws in disconnected:
                self.alert_connections["all"].discard(ws)
    
    async def broadcast_health(self, payload: WSHealthPayload, station_id: str):
        """Broadcast health update to all subscribers for this station + global."""
        message = payload.model_dump_json()
        
        if station_id in self.health_connections:
            disconnected = set()
            for ws in self.health_connections[station_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.add(ws)
            for ws in disconnected:
                self.health_connections[station_id].discard(ws)
        
        if "all" in self.health_connections:
            disconnected = set()
            for ws in self.health_connections["all"]:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.add(ws)
            for ws in disconnected:
                self.health_connections["all"].discard(ws)


# Global connection managers
alert_manager = ConnectionManager()
health_manager = ConnectionManager()


@router.websocket("/alerts")
async def websocket_alerts(
    websocket: WebSocket,
    station_id: Optional[str] = Query(None, description="Filter by station_id")
):
    """WebSocket endpoint for real-time anomaly alerts."""
    await alert_manager.connect_alerts(websocket, station_id)
    try:
        while True:
            # Keep connection alive, wait for client messages (ping/pong)
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))
    except WebSocketDisconnect:
        alert_manager.disconnect_alerts(websocket, station_id)


@router.websocket("/health")
async def websocket_health(
    websocket: WebSocket,
    station_id: Optional[str] = Query(None, description="Filter by station_id")
):
    """WebSocket endpoint for real-time health status updates."""
    await health_manager.connect_health(websocket, station_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))
    except WebSocketDisconnect:
        health_manager.disconnect_health(websocket, station_id)


# Export managers for use in other modules
__all__ = ["alert_manager", "health_manager", "ConnectionManager"]