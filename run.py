from flask import Flask
from flask_socketio import SocketIO
from app.routes import socketio

app = Flask(__name__)
socketio.init_app(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print("클라이언트가 연결되었습니다.")

@socketio.on('disconnect')
def handle_disconnect():
    print("클라이언트가 연결 해제되었습니다.")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
