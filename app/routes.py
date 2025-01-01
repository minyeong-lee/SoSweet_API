from flask import Blueprint, request, jsonify
from threading import Thread
from app.models import save_emotion
from app.utils.emotion_analysis import analyze_and_send

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def home():
    return jsonify({"message": "SoSweet API is running!"}), 200

@main_bp.route('/analyze', methods=['POST'])
def start_analysis():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # 비동기로 분석 시작
    analysis_thread = Thread(target=analyze_and_send, args=(user_id,))
    analysis_thread.start()

    return jsonify({"message": f"Analysis started for user {user_id}"}), 200
