from flask_socketio import emit
from app.utils.emotion_analysis import analyze_and_send
from app.utils.db import get_db
import os
import json

def register_emotion_events(socketio):
    @socketio.on('emotion-chunk')
    def handle_emotion_chunk(data):
        user_id = data.get("user_id")
        frame = data.get("frame")

        if not user_id or not frame:
            emit('error', {"message": "Missing user_id or frame"})
            return

        # 감정 분석 수행
        dominant_emotion, percentage = analyze_and_send(frame, user_id)

        # JSON 파일 저장
        save_to_json(user_id, {
            "dominant_emotion": dominant_emotion,
            "percentage": percentage
        })

        # 클라이언트에게 감정 분석 결과 전송
        emit('emotion_result', {
            "user_id": user_id,
            "dominant_emotion": dominant_emotion,
            "percentage": percentage
        })

    @socketio.on('end_chat')
    def handle_end_chat(data):
        user_id = data.get("user_id")
        if not user_id:
            emit('error', {"message": "Missing user_id"})
            return

        # JSON 파일 경로 설정
        file_path = f"{user_id}_data.json"

        if os.path.exists(file_path):
            # JSON 데이터 읽기
            with open(file_path, "r") as f:
                json_data = json.load(f)

            # DB 저장
            db = get_db()
            emotions_collection = db['emotions']
            emotions_collection.update_one(
                {"user_id": user_id},
                {"$set": {"summary": json_data}},  # 요약 데이터 저장
                upsert=True
            )

            # JSON 파일 삭제
            os.remove(file_path)

            emit('end_chat_success', {
                "message": f"Chat data saved for user {user_id}",
                "summary": json_data  # 저장한 데이터 클라이언트로 전송
            })
        else:
            emit('end_chat_error', {"message": "No data found to save"})


def save_to_json(user_id, data):
    """감정 분석 데이터를 JSON 파일에 저장"""
    file_path = f"{user_id}_data.json"

    # 기존 데이터 불러오기
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # 새 데이터 추가
    existing_data.append(data)

    # JSON 파일 저장
    with open(file_path, "w") as f:
        json.dump(existing_data, f, indent=4)
