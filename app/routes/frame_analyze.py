import time
from flask import Blueprint, request, jsonify
from app.utils.emotion_analysis import analyze_emotion
from app.utils.frame_utils import decode_frame_func
from app.utils.action_analysis import analyze_hand_movement_with_queue, analyze_folded_arm_with_queue, analyze_side_movement_with_queue
from app.utils.json_utils import save_action_data, save_emotion_data
from app.utils.feedback_utils import convert_to_korean

frame_analyze_bp = Blueprint('frame_analyze', __name__)

# 사용자별 행동 카운트 전역 딕셔너리
user_counters = {}

# 구조 예: counters = {
#   "user1": {
#       "hand_count": 3,
#       "folded_arm_count": 2,
#       "side_move_count": 1
#   },
#   "user2": {...}
# }

@frame_analyze_bp.route('/api/human/frameInfo', methods=['POST'])
def frame_analyze():
    # 요청 데이터 가져오기
    data = request.get_json()
    frame_url = data.get('frame')
    user_id = data.get('user_id')
    room_id = data.get('room_id')
    timestamp = data.get('timestamp')
    
    if not frame_url or not user_id or not room_id or not timestamp:
        return jsonify({"message": "필수 데이터가 누락되었습니다."}), 400

    # 전역 counters에 사용자 키가 없으면 초기화
    if user_id not in user_counters:
        user_counters[user_id] = {
            "hand_count": 0,
            "folded_arm_count": 0,
            "side_move_count": 0
        }

    try:
        # 이미지 url 을 디코딩
        decoded_frame = decode_frame_func(frame_url)
        
        # 감정 분석 수행
        emotion_result = analyze_emotion(decoded_frame)
        dominant_emotion = emotion_result['dominant_emotion']
        percentage = emotion_result['percentage']
        emotion_scores = emotion_result.get("emotion_scores", {})
        
        # 실시간으로 보내줄 감정 한글로 변환
        converted_dominant_emotion = convert_to_korean({dominant_emotion: percentage})  # dominant_emotion 변환

        # 동작 분석 수행 (연속성 추적)
        hand_movement_result = analyze_hand_movement_with_queue(decoded_frame, timestamp)
        folded_arm_result = analyze_folded_arm_with_queue(decoded_frame, timestamp)
        side_movement_result =analyze_side_movement_with_queue(decoded_frame, timestamp)

        # 각 동작에 대해 카운트 증가 | 메시지 생성
        action_messages = []

        if hand_movement_result:
            user_counters[user_id]["hand_count"] += 1
            if user_counters[user_id]["hand_count"] >= 5:
                action_messages.append("손이 5회 이상 산만합니다!! 손을 차분하게 해주세요~")
            else:
                action_messages.append(hand_movement_result)
                
        if folded_arm_result:
            user_counters[user_id]["folded_arm_count"] += 1
            if user_counters[user_id]["folded_arm_count"] >= 3:
                action_messages.append("3번 이상 팔짱을 꼈습니다! 팔을 풀고 몸짓을 편안히 해보세요!")
            else:
                action_messages.append(folded_arm_result)
        
        if side_movement_result:
            user_counters[user_id]["side_move_count"] += 1
            if user_counters[user_id]["side_move_count"] >= 4:
                action_messages.append("4회 이상 몸을 흔들고 있어요. 조금 고정해서 자세를 가다듬어 보세요!")
            else:
                action_messages.append(side_movement_result)        
            
        # JSON 저장
        save_action_data(user_id, {
            "timestamp": timestamp,
            "actions": action_messages
        })

        save_emotion_data(room_id, user_id, {
            "timestamp": timestamp,
            "dominant_emotion": dominant_emotion,
            "percentage": percentage,
            "emotion_scores": emotion_scores
        })
        
        return jsonify({
            "user_id": user_id,
            "room_id": room_id,
            "timestamp": timestamp,
            "emo_analysis_result": {
                "dominant_emotion": converted_dominant_emotion,
                "percentage": percentage
            },
            "act_analysis": action_messages
        })
        
    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500
