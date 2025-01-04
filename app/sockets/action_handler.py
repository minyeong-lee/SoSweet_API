from flask_socketio import emit
from app.utils.action_analysis import analyze_behavior, analyze_folded_arm, analyze_side_movement

def register_action_events(socketio):
    @socketio.on('action-chunk')
    def handle_video_chunk(data):
        user_id = data.get("user_id")
        frame = data.get("frame")  # 비디오 프레임 데이터

        # 동작 분석
        behavior_result = analyze_behavior(frame, user_id)
        folded_arm_result = analyze_folded_arm(frame)
        side_movement_result = analyze_side_movement(frame)

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
