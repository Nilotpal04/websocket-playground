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

    def create_room(self, websocket: WebSocket) -> str:

        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

        while True:
            room_key = "".join(secrets.choice(alphabet) for _ in range(6))

            if room_key not in self.rooms:
                break

        self.rooms[room_key] = [websocket]

        self.client_rooms[websocket] = room_key

        return room_key

    def join_room(self, websocket: WebSocket, room_key: str) -> bool:
        if room_key not in self.rooms:
            return False

        if websocket in self.client_rooms:
            return False

        self.rooms[room_key].append(websocket)
        self.client_rooms[websocket] = room_key

        return True

    async def broadcast(self, message: str, room_key: str):
        if room_key not in self.rooms:
            return

        for connection in self.rooms[room_key]:
            await connection.send_text(message)

    def disconnect(self, websocket: WebSocket, username: str):
        if username in self.active_connections:
            connections = self.active_connections[username]
            if websocket in connections:
                connections.remove(websocket)
            if not connections:
                del self.active_connections[username]

        room_key = self.client_rooms.get(websocket)

        if room_key is not None:
            if room_key in self.rooms:
                if websocket in self.rooms[room_key]:
                    self.rooms[room_key].remove(websocket)

                if not self.rooms[room_key]:
                    del self.rooms[room_key]

            del self.client_rooms[websocket]

manager = ConnectionManager()