from deepface import DeepFace
from datetime import datetime

def analyze_emotion(frame, user_id, room_id):
    try:
        # 감정 분석
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        print(f'감정 분석이 잘 되고 있나요? {analysis}')
        emotion_scores = analysis[0]['emotion']

        # Dominant 감정 계산
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        percentage = emotion_scores[dominant_emotion]

        # 타임스탬프 추가하여 JSON 저장
        return {
            "dominant_emotion": dominant_emotion,
            "percentage": percentage,
            "emotion_scores": emotion_scores
        }

    except Exception as e:
        print(f"Error during emotion analysis: {e}")
        return {
            "dominant_emotion": "error",
            "percentage": 0,
            "emotion_scores": {}
        }