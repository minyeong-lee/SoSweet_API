from flask import Flask
from flask_cors import CORS
from app.routes import nlp_bp, frame_analyze_bp

def create_app():
    app = Flask(__name__)
    
    CORS(app, 
         supports_credentials=True,
         resources={
             r"/*": {
                 "origins": ["http://localhost:3000"],
                 "methods": ["GET", "POST", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization"],
                 "expose_headers": ["Content-Type"],
                 "max_age": 3600
             }
         })
    
    app.register_blueprint(nlp_bp)
    app.register_blueprint(frame_analyze_bp)
    
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    
    return app