from app.utils.frame_utils import decode_frame_func
from flask_socketio import emit
from app.utils.action_analysis import analyze_behavior, analyze_folded_arm, analyze_side_movement

def register_action_events(socketio):
    @socketio.on('action-chunk')
    def handle_video_chunk(data):
        user_id = data.get("user_id")
        frame = data.get("frame")  # 비디오 프레임 데이터
        print(f'액션 분석의 user_id 와 frame이 잘 들어옵니다!!! {user_id}, {type(frame)}')
        
        if not user_id or not frame:
            emit('error', {"message": "user_id나 frame이 존재하지 않습니다!"})
            return

        try:
            # frmae 디코딩
            decoded_frame = decode_frame_func(frame)
            print(f'액션 분석의 프레임 타입이 잘 변환되었어용 {type(decoded_frame)}')
        except Exception as e:
            emit('error', { "message": f"Frame decoding 실패: {str(e)}" })
            return
        
        # 동작 분석
        behavior_result = analyze_behavior(decoded_frame, user_id)
        folded_arm_result = analyze_folded_arm(decoded_frame)
        side_movement_result = analyze_side_movement(decoded_frame)

        # 결과 전송
        results = []
        if behavior_result:
            results.append({"message": behavior_result})
        if folded_arm_result:
            results.append({"message": folded_arm_result})
        if side_movement_result:
            results.append({"message": side_movement_result})

        emit('action_result', {
            "user_id": user_id,
            "results": results
        })
