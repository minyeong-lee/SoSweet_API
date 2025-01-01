from deepface import DeepFace
import os
import json

def save_to_json(user_id, data):
    # JSON 파일 경로 설정
    file_path = f"{user_id}_data.json"
    
    # 기존 데이터 불러오기
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing_data =json.load(f)
    else:
        existing_data = []
    
    # 새 데이터 추가
    existing_data.append(data)
    
    # JSON 파일 저장
    with open(file_path, "w") as f:
        json.dump(existing_data, f, indent=4)


def analyze_and_send(frame, user_id):
    try:
        # 감정 분석
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        emotion_scores = analysis[0]['emotion']

        # Dominant 감정 계산
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        percentage = emotion_scores[dominant_emotion]

        # 타임스탬프 추가하여 JSON 저장
        save_to_json(user_id, {
            "timestamp": datetime.utcnow().isoformat(),
            "dominant_emotion": dominant_emotion,
            "percentage": percentage,
            "emotion_scores": emotion_scores
        })

        return dominant_emotion, percentage

    except Exception as e:
        print(f"Error during emotion analysis: {e}")
        return "error", 0