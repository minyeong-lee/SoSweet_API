from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from app.routes import nlp_bp, emo_analyze_bp

socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    
    # 모든 출처 허용, credentials 없이
    CORS(app, 
         resources={
             r"/*": {
                 "origins": "*",  # 모든 출처 허용
                 "methods": ["GET", "POST", "OPTIONS"],
                 "allow_headers": ["Content-Type"],
                 "expose_headers": ["Content-Type"],
                 "max_age": 3600
             }
         })
    
    app.register_blueprint(nlp_bp)
    app.register_blueprint(emo_analyze_bp)
    
    socketio.init_app(app)
    return app