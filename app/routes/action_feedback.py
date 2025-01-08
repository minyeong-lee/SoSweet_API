from flask import Blueprint, request, jsonify
import os
import json

act_feedback_bp = Blueprint('action_feedback', __name__)

@act_feedback_bp.route('/api/feedback/actioninfo', methods=['POST'])
def get_action_feedback():
    """
    analysis_data/actions/{room_id}_{user_id}.json 파일에서
    마지막(가장 최근) 데이터의 counters 부분을 꺼내서 반환
    """
    data = request.get_json()
    room_id = data.get('room_id')
    user_id = data.get('user_id')

    if not room_id or not user_id:
        return jsonify({"message": "필수 데이터(room_id, user_id)가 누락되었습니다."}), 400

    # 파일 경로: analysis_data/actions/room123_userABC.json
    actions_dir = "analysis_data/actions"
    filename = f"{room_id}_{user_id}.json"
    file_path = os.path.join(actions_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "해당 액션 데이터가 존재하지 않습니다."}), 404

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            action_data = json.load(f)  # list of dict
    except json.JSONDecodeError:
        return jsonify({"error": "액션 데이터 파일이 손상되었습니다."}), 500

    if not action_data:
        return jsonify({"error": "액션 데이터가 비어있습니다."}), 404

    # 마지막(가장 최근) entry
    latest_entry = action_data[-1]
    counters = latest_entry.get("counters", {})
    
    print(f"counters 를 확인하세용!!!!!!!!!!!!!!! {counters}")

    # 원하는 counter만 뽑아서 보내도 되고, 전체 counters 그대로 보내도 됨
    # 여기서는 전체를 반환 예시
    return jsonify({
        "user_id": user_id,
        "room_id": room_id,
        "counters": counters
    }), 200
