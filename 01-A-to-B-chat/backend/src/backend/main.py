from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

import json

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections.setdefault(username, []).append(websocket)

    def disconnect(self, websocket: WebSocket, username: str):
        if username in self.active_connections:
            connections = self.active_connections[username]

            if websocket in connections:
                connections.remove(websocket)

            if not connections:
                del self.active_connections[username]
    async def send_personal_message(self, message: str, receiver: str):
        if receiver in self.active_connections:
            for connection in self.active_connections[receiver]:
                await connection.send_text(message)

        else:
            print(f"Message failed: {receiver} is not online")

manager = ConnectionManager()
        
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
               data = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_text("Error: Message must be valid JSON.")
                continue
            if not isinstance(data, dict):
                await websocket.send_text("Error: Expected a JSON object.")
                continue

            receiver = data.get("receiver")
            text = data.get("message")

            formatted_message = f"From {username}: {text}"

            if receiver and text:
                await manager.send_personal_message(formatted_message, receiver)
            else:
                await websocket.send_text("Error: Receiver and message are required")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, username)
        print(f"Client {username} disconnected!")