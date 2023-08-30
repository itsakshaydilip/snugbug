from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "sweatysourcecode"
socketio = SocketIO(app, cors_allowed_origins="*")

active_rooms = {}
room_passwords = {}
banned_words = []

def contains_banned_word(message):
    return any(banned_word in message.lower() for banned_word in banned_words)

def leave_and_cleanup(room, username):
    if room in active_rooms and username in active_rooms[room]["users"]:
        leave_room(room)
        active_rooms[room]["users"].remove(username)

        if username == active_rooms[room]["admin"]:
            emit("chat_ended", room=room)

        emit(
            "message",
            {"message": f"{username} has left the room", "username": "System"},
            room=room,
        )

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
    active_rooms.setdefault(room, {"admin": username, "users": set()})["users"].add(username)
    
    emit("message", {"message": f"{username} has joined the room", "username": "System"}, room=room)
    emit("room_users", {"users": list(active_rooms[room]["users"])}, room=room)

@socketio.on("leave")
def on_leave(data):
    room, username = data["room"], data["username"]
    leave_and_cleanup(room, username)
    emit("message", {"message": f"{username} has left the chat", "username": "System"}, room=room)
    emit("room_users", {"users": list(active_rooms[room]["users"])}, room=room)

@socketio.on("message")
def handle_message(data):
    room, message, username = data["room"], data["message"], data["username"]

    if contains_banned_word(message):
        leave_and_cleanup(room, username)
        os._exit(0)  # Terminate the session and close terminal

    emit("message", {"message": message, "username": username}, room=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)
