from flask import Flask
from flask_socketio import SocketIO
from app.utils.db import get_db
from app.routes import nlp_bp

socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
        
    # MongoDB 연결
    app.config['MONGO_URI'] = "mongodb://localhost:27017/sosweet"
    get_db(app)

    # REST API 블루프린트 등록
    app.register_blueprint(nlp_bp)  # 대화 분석 API 등록
    
    # socketio 객체를 Flask 앱에 연결
    socketio.init_app(app) # 이 결합이 없으면 socketio.run(app) 호출 시 server 객체가 None이 되어 AttributeError 발생함
    
    # WebSocket 이벤트 등록
    register_socket_handlers(socketio)

    return app


# WebSocket 이벤트 등록 함수
def register_socket_handlers(socketio):
    from app.sockets.emotion_handler import register_emotion_events  # 감정 분석 이벤트 등록
    from app.sockets.action_handler import register_action_events  # 동작 분석 이벤트 등록

    register_emotion_events(socketio)
    register_action_events(socketio)