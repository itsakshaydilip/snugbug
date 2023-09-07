from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import secrets

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(32)  # Replace with a strong secret key
socketio = SocketIO(app, cors_allowed_origins="*")

# Dictionary to store active connections and their tokens
active_connections = {}
active_rooms = {}
room_passwords = {}
banned_words = []

# Function to generate a secure token
def generate_token():
    return secrets.token_hex(32)

# Function to authenticate the connection using a token
def authenticate_connection(token):
    return token in active_connections.values()

def contains_banned_word(message):
    return any(banned_word in message.lower() for banned_word in banned_words)

def send_leave_message(room, username):
    leave_message = f"{username} has left the chat"
    emit("message", {"message": leave_message, "username": "System"}, room=room)

def leave_and_cleanup(room, username):
    if room in active_rooms and username in active_rooms[room]["users"]:
        leave_room(room)
        active_rooms[room]["users"].remove(username)

        if username == active_rooms[room]["admin"]:
            emit("chat_ended", room=room)

        send_leave_message(room, username)

        if not active_rooms[room]["users"]:
            del active_rooms[room]

@socketio.on("join")
def on_join(data):
    room, username, password = data["room"], data["username"], data.get("password", "")

    if room in room_passwords and room_passwords[room] != password:
        emit("invalid_password", room=room)
        return

    if username in active_rooms.get(room, {}).get("users", set()):
        emit("username_exists")
        return

    join_room(room)
    active_rooms.setdefault(room, {"admin": username, "users": set()})["users"].add(
        username
    )

    emit(
        "message",
        {"message": f"{username} has joined the room", "username": "System"},
        room=room,
    )
    emit("room_users", {"users": list(active_rooms[room]["users"])}, room=room)

@socketio.on("leave")
def on_leave(data):
    room, username = data["room"], data["username"]
    leave_and_cleanup(room, username)
    emit("room_users", {"users": list(active_rooms[room]["users"])}, room=room)

@socketio.on("message")
def handle_message(data):
    room, message, username = data["room"], data["message"], data["username"]

    if contains_banned_word(message):
        leave_and_cleanup(room, username)
        os._exit(0)

    emit("message", {"message": message, "username": username}, room=room)

@socketio.on("connect")
def on_connect():
    connection_token = generate_token()
    connection_id = request.sid
    active_connections[connection_id] = connection_token
    emit("authenticate", {"token": connection_token})
    print(f"Connected to the server (Connection ID: {connection_id})")

@socketio.on("disconnect")
def on_disconnect():
    connection_id = request.sid
    if connection_id in active_connections:
        del active_connections[connection_id]
        print(f"Disconnected from the server (Connection ID: {connection_id})")

@socketio.on("list_rooms")
def handle_list_rooms():
    chatroom_list = list(active_rooms.keys())
    emit("room_list", {"rooms": chatroom_list})
    
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=3389, debug=True)
