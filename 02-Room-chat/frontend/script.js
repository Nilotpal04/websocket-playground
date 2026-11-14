const usernameInput = document.getElementById("username");
const connectBtn = document.getElementById("connect-btn");
const connectionStatus = document.getElementById("connection-status");

const roomSection = document.getElementById("room-section");
const createRoomBtn = document.getElementById("create-room-btn");
const roomKeyInput = document.getElementById("room-key");
const joinRoomBtn = document.getElementById("join-room-btn");
const currentRoom = document.getElementById("current-room");

const chatSection = document.getElementById("chat-section");
const messages = document.getElementById("messages");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");

let socket = null;
let username = null;
let joinedRoom = null;

connectBtn.addEventListener("click", () => {
    username = usernameInput.value.trim();

    if (!username) {
        alert("Please enter a username")
        return
    }

    if (socket && socket.readyState === WebSocket.OPEN) {
        return;
    }

    socket = new WebSocket(
        `ws://127.0.0.1:8000/ws?username=${encodeURIComponent(username)}`
    );

    socket.onopen = () => {
        connectionStatus.textContent = "Connected";
        roomSection.hidden = false;
        usernameInput.disabled = true;
        connectBtn.disabled = true;

        console.log("WebSocket connected");
    };

    socket.onmessage = (event) => {
        console.log("Server:", event.data);

        handleServerMessage(event.data);
    }

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };

    socket.onclose = () => {
        connectionStatus.textContent = "Disconnected";
        roomSection.hidden = true;
        chatSection.hidden = true;

        usernameInput.disabled = false;
        connectBtn.disabled = false;

        joinedRoom = false;
        currentRoom.textContent = "";

        console.log("WebSocket disconnected");
    };
});

createRoomBtn.addEventListener("click", () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "create_room"
        }));
    };
});

joinRoomBtn.addEventListener("click", () => {
    const roomKey = roomKeyInput.value.trim();

    if (!roomKey) {
        alert("Please enter a room key");
        return;
    }

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "join_room",
            room_key: roomKey
        }));
    }
});

function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) {
        return;
    }

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        return;
    }

    if (!joinedRoom) {
        alert("Join a room first");
        return;
    }

    socket.send(JSON.stringify({
        type: "send_message",
        message: message
    }));

    messageInput.value = "";
}

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        sendMessage();
    }
});

function handleServerMessage(rawMessage) {
    let data;

    try {
        data = JSON.parse(rawMessage);
    } catch {
        addMessage(rawMessage);
        return;
    }

    switch (data.type) {
        case "room_created":
            joinedRoom = true;
            showJoinedRoom(data.room_key);
            break;

        case "room_joined":
            joinedRoom = true;
            showJoinedRoom(data.room_key);
            break;

        case "error":
            alert(data.message);
            break;

        default:
            console.log("Unknown server message:", data);
    }
}

function showJoinedRoom(roomKey) {
    currentRoom.textContent = `Current room: ${roomKey}`;
    chatSection.hidden = false;
    roomKeyInput.value = "";
}

function addMessage(message) {
    const messageElement = document.createElement("p");
    messageElement.textContent = message;

    messages.appendChild(messageElement);
}
