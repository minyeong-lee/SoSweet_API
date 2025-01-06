from flask import Blueprint, request, jsonify
from app.utils.emotion_analysis import analyze_emotion
from app.utils.frame_utils import decode_frame_func

emo_analyze_bp = Blueprint('emo_analyze', __name__)

@emo_analyze_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    frame_url = data.get('frame')
    user_id = data.get('user_id')
    room_id = data.get('room_id')
    
    if not frame_url or not user_id or not room_id:
        return jsonify({"message": "필수 데이터가 누락되었습니다."}), 400
    
    try:
        # 이미지 url 을 디코딩
        decoded_frame = decode_frame_func(frame_url)
        result = analyze_emotion(decoded_frame)
    except Exception as e:
        return jsonify({"message": "분석 중 오류가 발생하였습니다", "error": str(e)}), 500
    
    return jsonify({
        "user_id": user_id,
        "room_id": room_id,
        "analysis_result": result
    })