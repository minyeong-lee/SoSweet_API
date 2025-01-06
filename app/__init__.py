from flask import Flask
from flask_cors import CORS
from app.routes import nlp_bp, frame_analyze_bp

def create_app():
    app = Flask(__name__)
    
    # 모든 출처 허용, credentials 없이
    CORS(app, 
         resources={
             r"/*": {
                 "origins": "*",  # 모든 출처 허용
                 "methods": ["GET", "POST", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization"],
                 "expose_headers": ["Content-Type"],
                 "max_age": 3600  # OPTIONS 요청 캐시 시간(1시간)
             }
         })
    
    # REST API 라우트 등록
    app.register_blueprint(nlp_bp)
    app.register_blueprint(frame_analyze_bp)
    
    # 최대 요청 크기 제한 설정 (50MB)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    
    return app