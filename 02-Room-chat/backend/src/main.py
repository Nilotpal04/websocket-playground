from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

import json
import secrets

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.rooms: dict[str, list[WebSocket]] = {}
        self.client_rooms: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections.setdefault(username, []).append(websocket)

    async def create_room(self, websocket: WebSocket) -> str:

        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

        while True:
            room_key = "".join(secrets.choice(alphabet) for _ in range(6))

            if room_key not in self.rooms:
                break

        self.rooms[room_key] = [websocket]

        self.client_rooms[websocket] = room_key

        return room_key