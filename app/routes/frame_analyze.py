from flask import Blueprint, request, jsonify
from app.utils.emotion_analysis import analyze_emotion
from app.utils.frame_utils import decode_frame_func
from app.utils.action_analysis import analyze_hand_movement_with_queue, analyze_side_movement_with_queue, analyze_eye_touch_with_queue
from app.utils.json_utils import save_action_data, save_emotion_data
from app.utils.feedback_utils import convert_to_korean
from app.utils.action_analysis import hand_movement_queue, side_movement_queue, eye_touch_queue
import cv2


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

# 프레임 카운터 생성
frame_counter = 0


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
        print(f"[디버그] 디코딩된 이미지 해상도: {decoded_frame.shape}")  # 해상도 출력
        # 디버깅용 이미지 저장
        # cv2.imwrite(f"debug_frame_{timestamp}.jpg", decoded_frame)
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
    global frame_counter
    
    # 요청 데이터 가져오기
    data = request.get_json()
    frame_url = data.get('frame')
    user_id = data.get('user_id')
    room_id = data.get('room_id')
    timestamp = data.get('timestamp')
    
    if not frame_url or not user_id or not room_id or not timestamp:
        return jsonify({"message": "필수 데이터가 누락되었습니다."}), 400

    frame_counter += 1  # 프레임 카운터 증가
    
    # 모든 프레임마다 동작 분석 수행
    if frame_counter % 1 != 0:
        # print('프레임 스킵 중..') # 스킵된 프레임 로그 출력
        return jsonify({"message": "프레임 스킵 중"}), 200

    # 전역 counters에 사용자 키가 없으면 초기화
    if user_id not in user_counters:
        user_counters[user_id] = {
            "hand_count": 0,
            "hand_message_count": 0,
            "side_move_count": 0,
            "side_move_message_count": 0,
            "eye_touch_count": 0, # 눈 만지기 행동 카운트 추가함
            "eye_touch_message_count": 0,
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
        side_movement_result, side_ts = analyze_side_movement_with_queue(decoded_frame, timestamp)
        eye_touch_result, eye_ts = analyze_eye_touch_with_queue(decoded_frame, timestamp)        
        
        # 지금 프레임에서 임계치를 넘겼는지 (0 또는 1) 반환할 객체
        # 예) 손 3회 이상이면 1, 아니면 0 으로 Boolean 결과 응답
        is_actions = {
            "is_hand": 0,
            "is_side": 0,
            "is_eye": 0,
        }

        # 카운터 가져오기
        counters = user_counters[user_id]
        
        # 1) 손 움직임    
        if hand_movement_result:
            counters["hand_count"] += 1
            print("[손_CHECK]손 산만함 1회 감지")

            # 조건 설정) 3회 누적 시 -> 메시지 발송 & 카운트 리셋
            if counters["hand_count"] >= 1:
                counters["hand_message_count"] += 1
                
                # 이번 프레임에서 임계치 도달했으므로, 반환값 1fh
                is_actions["is_hand"] = 1
                
                # 카운터 리셋
                counters["hand_count"] = 0
                # 큐 비우기 (안하면, 계속 프레임 쌓임)
                hand_movement_queue.clear()

        
        # 2) 몸 좌우 흔들기
        if side_movement_result:
            counters["side_move_count"] += 1
            print("[몸흔들었음_CHECK] 몸 좌우로 흔들기 1회 감지")

            # 조건 설정
            if counters["side_move_count"] >= 2:
                counters["side_move_message_count"] += 1

                is_actions["is_side"] = 1
                
                counters["side_move_count"] = 0
                side_movement_queue.clear()
        
        # 3) 눈 만지기
        if eye_touch_result:
            counters["eye_touch_count"] += 1
            print("[눈 만졌음_CHECK] 눈 손으로 만지기 1회 감지")

            if counters["eye_touch_count"] >= 2:
                counters["eye_touch_message_count"] += 1
                
                is_actions["is_eye"] = 1
                
                counters["eye_touch_count"] = 0
                eye_touch_queue.clear()

                
        # 메시지 / 카운터 저장
        # 여기서는 매 프레임마다 저장하되, 실제로는 action_messages가 비어있지 않을 때만 저장해도 됨
        save_action_data(
            room_id,
            user_id,
            {
                "timestamp": timestamp,
                "actions": is_actions,  # ex: {"hand": 1, "side": 0, "eye":0} 등의 데이터
                "counters": {
                    "hand_count": counters["hand_count"],
                    "hand_message_count": counters["hand_message_count"],
                    "side_move_count": counters["side_move_count"],
                    "side_move_message_count": counters["side_move_message_count"],
                    "eye_touch_count": counters["eye_touch_count"],
                    "eye_touch_message_count": counters["eye_touch_message_count"],
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
            "act_analysis": is_actions
        })

    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500