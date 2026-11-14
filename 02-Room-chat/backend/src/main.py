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

    def create_room(self, websocket: WebSocket) -> str | None:

        if websocket in self.client_rooms:
            return None
        
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                data = json.loads(raw_message)
                if not isinstance(data, dict):
                    await websocket.send_text("Error: Expected a JSON object")
                    continue
            except json.JSONDecodeError:
                await websocket.send_text("Error: Invalid JSON format")
                continue

            action = data.get("type")

            if action == "create_room":
                room_key = manager.create_room(websocket)

                if room_key is None:
                    await websocket.send_json({
                        "type": "error",
                        "message": "You are already in a room"
                    })
                    continue

                await websocket.send_json({
                    "type": "room_created",
                    "room_key": room_key
                })

            elif action == "join_room":
                room_key = data.get("room_key")

                if not isinstance(room_key, str) or not room_key.strip():
                    await websocket.send_json({
                        "type": "error",
                        "message": "A valid room key is required"
                    })
                    continue

                room_key = room_key.strip().upper()

                if websocket in manager.client_rooms:
                    await websocket.send_json({
                        "type": "error",
                        "message": "You are already in a room"
                    })
                    continue

                success = manager.join_room(websocket, room_key)

                if success:
                    await websocket.send_text(json.dumps({
                        "type": "room_joined",
                        "room_key": room_key
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid room key"
                    }))

            elif action == "send_message":
                text = data.get("message")

                if not isinstance(text, str) or not text.strip():
                    await websocket.send_json({
                        "type": "error",
                        "message": "message cannot be empty"
                    })
                    continue

                current_room = manager.client_rooms.get(websocket)

                if current_room is None:
                    await websocket.send_text("Error: You are not in a room!")
                    continue

                formatted_message = f"{username}: {text}"
                await manager.broadcast(formatted_message, current_room)

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "Unknown action"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, username)
        print(f"{username} disonnected")