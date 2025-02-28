from flask import Flask, jsonify
from flask_cors import CORS
from app.routes import nlp_bp, frame_analyze_bp, emo_feedback_bp, act_feedback_bp

def create_app():
    app = Flask(__name__)
    
    CORS(app, 
         #supports_credentials=True,
         resources={
             r"/*": {
                 "origins": "*",  # 모든 출처 허용
                 "methods": ["GET", "POST", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
                 "expose_headers": ["Content-Type"],
                 "max_age": 3600
             }
         })
    
    # Health Check를 위한 루트 엔드포인트 추가
    @app.route('/')
    def health_check():
        return jsonify({
            "status": "healthy",
            "message": "SoSweet API Server is running"
        }), 200
    
    app.register_blueprint(nlp_bp)
    app.register_blueprint(frame_analyze_bp)
    app.register_blueprint(emo_feedback_bp)
    app.register_blueprint(act_feedback_bp)
    
    
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    
    return app