from flask_socketio import emit
from app.utils.emotion_analysis import analyze_and_send
from app.utils.db import get_db
from run import socketio
import os
import json

@socketio.on('analyze')
def handle_emotion(data):
    user_id = data.get("user_id")
    frame = data.get("frame")

    if not user_id or not frame:
        emit('error', {"message": "Missing user_id or frame"})
        return

    # 감정 분석 수행
    dominant_emotion, percentage = analyze_and_send(frame, user_id)

    # 클라이언트에게 결과 전송
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