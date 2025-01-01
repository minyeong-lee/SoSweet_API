from flask import Flask
from app.utils.db import get_db

def create_app():
    app = Flask(__name__)

    # MongoDB 연결
    app.config['MONGO_URI'] = "mongodb://localhost:27017/sosweet"
    get_db(app)

    # 라우트 등록
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
