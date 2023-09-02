import socketio
from threading import Thread
from datetime import datetime
import sys
import os

sio = socketio.Client()

def display_message(data, username):
    timestamp = datetime.now().strftime("%H:%M:%S")
    sender_username = data["username"]
    message = data["message"]
    
    if sender_username != username:
        print(f"{timestamp} - {sender_username}: {message}")
    else:
        print(f"{timestamp} - You: {message}")

@sio.on("message")
def handle_message(data):
    display_message(data, username)

@sio.on("username_exists")
def handle_username_exists():
    print("A user with the same username already exists in this room.")
    os._exit(0)

@sio.on("connect")
def on_connect():
    print("Connected to the server")
    request_secret_key()  # Request the secret key from the server

@sio.on("disconnect")
def on_disconnect():
    print("Disconnected from the server")

@sio.on("authentication_failed")
def authentication_failed():
    print("Authentication failed.")
    os._exit(0)

def request_secret_key():
    sio.emit("request_secret_key")

def send_message(message, username, room):
    timestamp = datetime.now().strftime("%H:%M:%S")
    sio.emit("message", {"message": message, "username": username, "room": room})

def leave_chat(username, room):
    sio.emit("leave", {"username": username, "room": room})
    sys.exit(0)

EMOTICON_TO_EMOJI = {
    ":)": "😊",
    ":(": "😢",
    ";)": "😉",
    ":D": "😄",
    ":P": "😛",
    "<3": "❤️",
    ":|": "😐",
    ":O": "😮",
    ":/": "😕",
    ":3": "😺",
    ":*": "😘",
    ":')": "😂",
    ":|": "😐",
    ":'(": "😥",
    ":>": "😆",
    ":<": "😔",
}

def handle_input(username, room):
    paste_mode = False
    paste_buffer = []
    stick_mode = False
    stick_file_path = ""

    while True:
        message = input(": ")

        # Convert emoticons to emojis if found
        for emoticon, emoji in EMOTICON_TO_EMOJI.items():
            message = message.replace(emoticon, emoji)

        if message.strip() == "/exit":
            leave_chat(username, room)
        elif message.startswith("/paste"):
            paste_mode = True
            paste_buffer = []
            print(
                "Paste mode activated. Enter your code. Type '/send' to send and exit paste mode."
            )
        elif paste_mode:
            if message.strip() == "/send":
                if paste_buffer:
                    code_message = "\n".join(paste_buffer)
                    send_message(code_message, username, room)
                    print("Code sent. Reverting to message mode.")
                    paste_mode = False
                    paste_buffer = []
                else:
                    print("No code to send. Reverting to message mode.")
                    paste_mode = False
            else:
                paste_buffer.append(message)
        elif message.startswith("/stick"):
            stick_mode = True
            print(
                "Stick mode activated. Enter the path of the file to send. Type '/send' to send and exit stick mode."
            )
        elif stick_mode:
            if message.strip() == "/send":
                if stick_file_path:
                    if os.path.exists(stick_file_path):
                        file_link = f'[{os.path.basename(stick_file_path)}]({stick_file_path.replace(" ", "%20")})'
                        send_message(file_link, username, room)
                        print("File link sent. Reverting to message mode.")
                    else:
                        print("File not found. Reverting to message mode.")
                    stick_mode = False
                    stick_file_path = ""
                else:
                    print("No file path provided. Reverting to message mode.")
                    stick_mode = False
            else:
                stick_file_path = message
        else:
            send_message(message, username, room)

if __name__ == "__main__":
    server_url = "http://34.125.3.30:3389"  # Replace with your server URL
    sio.connect(server_url)

    username = input("Enter your username: ")
    room = input("Enter the chatroom name: ")

    sio.emit("join", {"room": room, "username": username})

    print(f"Welcome to the '{room}' chatroom, {username}!\n")

    thread = Thread(target=sio.wait)
    thread.daemon = True
    thread.start()

    handle_input(username, room)
