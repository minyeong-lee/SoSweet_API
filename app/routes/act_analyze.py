from flask import Blueprint, request, jsonify
from app.utils.frame_utils import decode_frame_func
from app.utils.action_analysis import analyze_hand_movement, analyze_folded_arm, analyze_side_movement, get_landmarks, get_midpoint_y

act_analyze_bp = Blueprint('act_analyze', __name__)

@act_analyze_bp.route('/api/human/actioninfo', methods=['POST'])
def act_analyze():
    try:
        # 요청 데이터 가져오기
        data = request.get_json()
        frame_url = data.get('frame')
        user_id = data.get('user_id')
        
        if not frame_url or not user_id:
            return jsonify({"message": "필수 데이터가 누락되었습니다."}), 400
        
        try:
            # 이미지 url 디코딩
            decoded_frame = decode_frame_func(frame_url)
            print(f'디코딩된 프레임 타입이요: {type(decoded_frame)}')
        except Exception as e:
            return jsonify({"error": f"Frame 디코딩 실패: {str(e)}"}), 500
        
        # 동작 분석 수행
        hand_movement_result = analyze_hand_movement(decoded_frame)
        folded_arm_result = analyze_folded_arm(decoded_frame)
        side_movement_result =analyze_side_movement(decoded_frame)
        
        # 결과 정리
        results = []
        if hand_movement_result:
            results.append({"message": hand_movement_result})
        if folded_arm_result:
            results.append({"message": folded_arm_result})
        if side_movement_result:
            results.append({"message": side_movement_result})
        
        #  분석 결과 반환
        return jsonify({
            "user_id": user_id,
            "results": results
        }), 200
    
    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500