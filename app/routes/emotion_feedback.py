from flask import Blueprint, request, jsonify
import json
import os

emo_feedback_bp = Blueprint('emotion_feedback', __name__)

DATA_PATH = "./analysis_data/emotions"

@emo_feedback_bp.route('/api/feedback/faceinfo', methods=['POST'])
def get_emo_feedback():
    # 요청 데이터 가져오기
    data = request.get_json()
    room_id = data.get('room_id')
    user_id = data.get('user_id')
    
    if not room_id or not user_id:
        return jsonify({"message": "필수 데이터가 누락되었습니다."}), 400
    
    # DATA_PATH 에서 room_id 로 된 폴더에서 내 아이디.json 파일 가져오기
    # 분석해주는 함수 별도로 만들어서 데이터만 반환하기
    # 반환할 데이터는 