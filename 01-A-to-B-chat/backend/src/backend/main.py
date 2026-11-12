from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

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

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
        
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast(message)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected!")