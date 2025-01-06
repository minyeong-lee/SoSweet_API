from flask import Blueprint, request, jsonify
from ..utils.emotion_analysis import analyze_emotion

emo_analyze_bp = Blueprint('analyze', __name__)

@emo_analyze_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    frame = data.get('frame')
    user_id = data.get('user_id')
    room_id = data.get('room_id')

    # 감정 분석 처리
    result = analyze_emotion(frame)
    
    return jsonify({
        "user_id": user_id,
        "room_id": room_id,
        "analysis_result": result
    })