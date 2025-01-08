import time
from flask import Blueprint, request, jsonify
from app.utils.emotion_analysis import analyze_emotion
from app.utils.frame_utils import decode_frame_func
from app.utils.action_analysis import analyze_hand_movement_with_queue, analyze_folded_arm_with_queue, analyze_side_movement_with_queue
from app.utils.json_utils import save_action_data, save_emotion_data
from app.utils.feedback_utils import convert_to_korean
from app.utils.action_analysis import hand_movement_queue, folded_arm_queue, side_movement_queue

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


@frame_analyze_bp.route('/api/ai/frameInfo', methods=['POST'])
def frame_analyze_ai():
    # 요청 데이터 가져오기
    data = request.get_json()
    frame_url = data.get('frame')
    user_id = data.get('user_id')
    timestamp = data.get('timestamp')
    room_id = 'ai'
    
    if not frame_url or not user_id or not timestamp:
        return jsonify({"message": "필수 데이터가 누락되었습니다."}), 400
    
    try:
        # 이미지 url 을 디코딩
        decoded_frame = decode_frame_func(frame_url)
        emotion_result = analyze_emotion(decoded_frame)
        dominant_emotion = emotion_result['dominant_emotion']
        percentage = emotion_result['percentage']
        emotion_scores = emotion_result.get("emotion_scores", {})
        
        save_emotion_data(room_id, user_id, {
            "timestamp": timestamp,
            "dominant_emotion": dominant_emotion,
            "percentage": percentage,
            "emotion_scores": emotion_scores
        })
        
        return jsonify({
            "dominant_emotion" : convert_to_korean(dominant_emotion),
            "value" : percentage
        })
        
    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500


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
            "hand_message_count": 0,
            "folded_arm_count": 0,
            "folded_arm_message_count": 0,
            "side_move_count": 0,
            "side_move_message_count": 0
        }

    try:
        # 이미지 url 을 디코딩
        decoded_frame = decode_frame_func(frame_url)
        
        # 감정 분석 수행
        emotion_result = analyze_emotion(decoded_frame)
        dominant_emotion = emotion_result['dominant_emotion']
        percentage = emotion_result['percentage']
        emotion_scores = emotion_result.get("emotion_scores", {})
        
        # 동작 분석 수행 (연속성 추적)
        hand_movement_result, hand_ts = analyze_hand_movement_with_queue(decoded_frame, timestamp)
        
        # hand_movement_result 가 실제 메시지(문자열)일 때만 카운트 증가/로그 출력
        counters = user_counters[user_id]
        
        hand_movement_result, hand_ts = analyze_hand_movement_with_queue(decoded_frame, timestamp)
        folded_arm_result, arm_ts = analyze_folded_arm_with_queue(decoded_frame, timestamp)
        side_movement_result, side_ts = analyze_side_movement_with_queue(decoded_frame, timestamp)

        action_messages = []
        
        # 1) 손 움직임    
        if hand_movement_result:
            counters["hand_count"] += 1
            print("손이 좀 산만해요!!!!!!!!!!!!!!!!")
            # 조건 설정) 5회 누적 시 -> 메시지 발송 & 카운트 리셋
            if counters["hand_count"] >= 4:
                counters["hand_message_count"] += 1
                action_messages.append("손이 4회 이상 산만합니다!! 손을 차분하게 해주세요~")
                counters["hand_count"] = 0
                # 큐 비우기 (안하면, 계속 프레임 쌓임)
                hand_movement_queue.clear()
            else:
                # 조건 임계치 도달 전까지는 원래 메시지만
                action_messages.append(hand_movement_result)
        
        # 2) 팔짱
        if folded_arm_result:
            counters["folded_arm_count"] += 1
            print("팔 산만해요!!!!!!!!!!!!!!!")
            if counters["folded_arm_count"] >= 3:
                counters["folded_arm_message_count"] += 1
                action_messages.append("3번 이상 팔이 산만합니다! 팔을 자연스럽게 두고 편안히 해보세요!")
                counters["folded_arm_count"] = 0
                folded_arm_queue.clear()
            else:
                action_messages.append(folded_arm_result)
        
         # 3) 몸 좌우 흔들기
        if side_movement_result:
            counters["side_move_count"] += 1
            print("몸 좌우로 흔들었어요!!!!!!!!!!!!")
            if counters["side_move_count"] >= 3:
                counters["side_move_message_count"] += 1
                action_messages.append("3회 이상 몸을 흔들고 있어요. 조금 고정해서 자세를 가다듬어 보세요!")
                counters["side_move_count"] = 0
                side_movement_queue.clear()
            else:
                action_messages.append(side_movement_result)      
            
        # 메시지 / 카운터 저장
        # 여기서는 매 프레임마다 저장하되, 실제로는 action_messages가 비어있지 않을 때만 저장해도 됨
        save_action_data(
            room_id,
            user_id,
            {
                "timestamp": timestamp,
                "actions": action_messages,
                "counters": {
                    "hand_count": counters["hand_count"],
                    "folded_arm_count": counters["folded_arm_count"],
                    "side_move_count": counters["side_move_count"],
                    "hand_message_count": counters["hand_message_count"],
                    "folded_arm_message_count": counters["folded_arm_message_count"],
                    "side_move_message_count": counters["side_move_message_count"]
                }
            }
        )

        # 감정 JSON 저장
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
                "dominant_emotion": convert_to_korean(dominant_emotion),
                "percentage": percentage
            },
            "act_analysis": action_messages
        })

    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500
