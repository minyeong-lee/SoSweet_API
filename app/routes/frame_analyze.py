import time
from flask import Blueprint, request, jsonify
from app.utils.emotion_analysis import analyze_emotion
from app.utils.frame_utils import decode_frame_func
from app.utils.action_analysis import analyze_hand_movement, analyze_folded_arm, analyze_side_movement


frame_analyze_bp = Blueprint('emo_analyze', __name__)

@frame_analyze_bp.route('/api/human/frameInfo', methods=['POST'])
def frame_analyze():
    # 요청 데이터 가져오기
    data = request.get_json()
    frame_url = data.get('frame')
    user_id = data.get('user_id')
    room_id = data.get('room_id')
    
    # 타임스탬프 추가 (디코딩 전에 기록하기)
    timestamp = int(time.time() * 1000) # 밀리초 단위
    
    if not frame_url or not user_id or not room_id:
        return jsonify({"message": "필수 데이터가 누락되었습니다."}), 400
    
    try:
        # 이미지 url 을 디코딩
        decoded_frame = decode_frame_func(frame_url)
        print(f'디코딩된 프레임 타입이요: {type(decoded_frame)}, 타임스탬프: {timestamp}')
        
        # 감정 분석 수행
        emotion_result = analyze_emotion(decoded_frame)

        # 동작 분석 수행
        hand_movement_result = analyze_hand_movement(decoded_frame)
        folded_arm_result = analyze_folded_arm(decoded_frame)
        side_movement_result =analyze_side_movement(decoded_frame)

        # 결과 정리
        act_results = []
        if hand_movement_result:
            act_results.append({"message": hand_movement_result})
        if folded_arm_result:
            act_results.append({"message": folded_arm_result})
        if side_movement_result:
            act_results.append({"message": side_movement_result})
            
        return jsonify({
            "user_id": user_id,
            "room_id": room_id,
            "timestamp": timestamp,
            "emo_analysis_result": emotion_result,
            "act_analysis": act_results
        })
        
    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500
