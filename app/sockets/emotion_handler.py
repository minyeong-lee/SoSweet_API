from app.utils.frame_utils import decode_frame_func
from app.utils.json_utils import save_to_json
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
        print(f'표정분석 user_id와 frame 이 잘 들어왔어요!!!{user_id}, {type(frame)}')

        if not user_id or not frame:
            emit('error', {"message": "user_id나 frame이 존재하지 않습니다!"})
            return

        try:
            # frmae 디코딩
            decoded_frame = decode_frame_func(frame) # frame을 numpy array로 변환
            print(f'type이 잘 변환되었나요? { type(decoded_frame) }')
        except Exception as e:
            emit('error', { "message": f"Frame decoding 실패: {str(e)}" })
            return
        
        # 감정 분석 수행 (주된 감정, 퍼센트, 전체 7가지 감정 비율 반환)
        analysis_result = analyze_and_send(decoded_frame, user_id)
        print(f'감정 분석이 수행되어 결과가 잘 나왔나요? {analysis_result}')

        # 피드백에 사용할 JSON 파일 저장
        save_to_json(user_id, analysis_result)

        # 클라이언트에게 감정 분석 결과 전송
        emit('emotion_result', {
            "user_id": user_id,
            "dominant_emotion": analysis_result["dominant_emotion"],
            "percentage": analysis_result["percentage"]
        })

    # @socketio.on('end_chat')
    # def handle_end_chat(data):
    #     user_id = data.get("user_id")
    #     if not user_id:
    #         emit('error', {"message": "Missing user_id"})
    #         return

    #     # JSON 파일 경로 설정
    #     file_path = f"{user_id}_data.json"

    #     if os.path.exists(file_path):
    #         # JSON 데이터 읽기
    #         with open(file_path, "r") as f:
    #             json_data = json.load(f)

    #         # SOSWEET Bacnend Server 요청 받아서 응답으로 보내주기


    #         # JSON 파일 삭제
    #         # os.remove(file_path)

    #         emit('end_chat_success', {
    #             "message": f"Chat data saved for user {user_id}",
    #             "summary": json_data  # 저장한 데이터 클라이언트로 전송
    #         })
    #     else:
    #         emit('end_chat_error', {"message": "No data found to save"})
