from flask import Blueprint, request, jsonify
import json
import os
from app.utils.feedback_utils import calculate_emo_result, convert_to_korean

emo_feedback_bp = Blueprint('emotion_feedback', __name__)

DATA_PATH = "./analysis_data/emotions"

@emo_feedback_bp.route('/api/feedback/faceinfo', methods=['POST', 'OPTIONS'])
def get_emo_feedback():
    # OPTIONS 요청 처리 추가
    if request.method == 'OPTIONS':
        return '', 204  # 204 No Content로 응답
        
    # 요청 데이터 가져오기
    data = request.get_json()
    room_id = data.get('room_id')
    user_id = data.get('user_id')
    
    if not room_id or not user_id:
        return jsonify({"message": "필수 데이터가 누락되었습니다."}), 400
    
    # 파일 경로 설정하기
    file_path = os.path.join(DATA_PATH, room_id, f"{user_id}.json")
    
    # JSON 파일 없을 경우
    if not os.path.exists(file_path):
        return jsonify({"error": "해당 데이터가 존재하지 않습니다"}), 404
    
    # JSON 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as file:
        emotion_data = json.load(file)
    
    # 필요 데이터만 추출해오기
    emo_sorted_scores, emo_top_3 = calculate_emo_result(emotion_data)
    print(f"필요 데이터가 잘 추출되어왔나요? {emo_sorted_scores} 과 Top 3 감정은 {emo_top_3}")
    
    # 각각 한글로 변환
    converted_sorted_scores = {convert_to_korean(k): v for k, v in emo_sorted_scores.items()}
    
    # 하나의 딕셔너리로 합치기
    # combined_emo_result = {
    #     "sorted_emotion_scores": converted_sorted_scores,
    #     "top_3_emotions": converted_top_3
    # }
    
    print(f"정렬된 전체 감정 점수: {converted_sorted_scores}")
    # print(f"Top 3 감정: {combined_emo_result['top_3_emotions']}")
    
    json_scores = json.dumps(converted_sorted_scores)
    
    return jsonify({
        "emo_feedback_result": json_scores,
    })