"""WebSocket Connection Manager — handles all real-time client connections"""
import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("retailiq.websocket")


class ConnectionManager:
    """
    Manages all active WebSocket connections, grouped by store_id.
    Thread-safe via asyncio locks.
    """

    def __init__(self):
        # store_id → set of WebSocket connections
        self._connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, store_id: int) -> None:
        await websocket.accept()
        async with self._lock:
            if store_id not in self._connections:
                self._connections[store_id] = set()
            self._connections[store_id].add(websocket)
        logger.info(f"WS client connected to store {store_id}. "
                    f"Total: {len(self._connections.get(store_id, set()))}")

    async def disconnect(self, websocket: WebSocket, store_id: int) -> None:
        async with self._lock:
            if store_id in self._connections:
                self._connections[store_id].discard(websocket)
                if not self._connections[store_id]:
                    del self._connections[store_id]
        logger.info(f"WS client disconnected from store {store_id}")

    async def broadcast(self, store_id: int, data: dict) -> None:
        """Send message to all clients subscribed to store_id"""
        conns = self._connections.get(store_id, set()).copy()
        if not conns:
            return

        message = json.dumps(data)
        dead = set()
        for ws in conns:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)

        # Clean up dead connections
        if dead:
            async with self._lock:
                if store_id in self._connections:
                    self._connections[store_id] -= dead

    async def broadcast_all(self, data: dict) -> None:
        """Broadcast to all stores (e.g., system health updates)"""
        for store_id in list(self._connections.keys()):
            await self.broadcast(store_id, data)

    def connection_count(self, store_id: int) -> int:
        return len(self._connections.get(store_id, set()))

    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# Singleton
ws_manager = ConnectionManager()
