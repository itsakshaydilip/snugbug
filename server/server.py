from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import os
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["SECRET_KEY"] = "sweatysourcecode"
socketio = SocketIO(app, cors_allowed_origins="*")

db_connection = sqlite3.connect("chat_history.db")
db_cursor = db_connection.cursor()
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        room TEXT,
        username TEXT,
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
db_connection.commit()

active_rooms = {}
room_passwords = {}
banned_words = ["fuck", "cunt", "bastard"]

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

    timestamp = datetime.now()
    db_cursor.execute("INSERT INTO messages (room, username, message, timestamp) VALUES (?, ?, ?, ?)",
                      (room, username, message, timestamp))
    db_connection.commit()

    cleanup_messages(room)

@socketio.on("cleanup_messages")
def cleanup_messages(data):
    room = data["room"]
    now = datetime.now()
    cutoff_time = now - timedelta(minutes=3)  # Corrected timedelta usage
    db_cursor.execute("DELETE FROM messages WHERE room=? AND timestamp < ?", (room, cutoff_time))
    db_connection.commit()

if __name__ == "__main__":
    socketio.run(app, debug=True)
