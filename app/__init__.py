from flask import Flask
from app.routes import nlp_bp
from app.routes import emo_analyze_bp

def create_app():
    app = Flask(__name__)
        
    # REST API 블루프린트 등록
    app.register_blueprint(nlp_bp)  # 대화 분석 API 등록
    
    # frame 전달 블루프린트 등록
    app.register_blueprint(emo_analyze_bp)
    
    return app