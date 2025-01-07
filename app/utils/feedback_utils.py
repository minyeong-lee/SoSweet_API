from collections import Counter

def calculate_emo_result(emotion_data):
    # 감정 빈도 계산하기 위한 Counter 생성
    emotion_counter = Counter()
    
    for entry in emotion_data:
        emotion_scores = entry.get("emotion_scores", {})
        
        # 감정 스코어 모두 합산
        for emotion, score in emotion_scores.items():
            emotion_counter[emotion] += score
    
    # 감정 점수 내림차순으로 정렬
    sorted_emotion_scores = dict(sorted(emotion_counter.items(), key=lambda x: x[1], reverse=True))
    
    # Top 3 감정 추출
    top_3_emotions = dict(list(sorted_emotion_scores.items())[:3])
    
    return sorted_emotion_scores, top_3_emotions


# 반환 시점에 변환
def convert_to_korean(dominant_emotion):
    print(dominant_emotion)
    emotion_kor = {
                "angry": "긴장",
                "disgust": "불편함",
                "fear": "두려움",
                "happy": "기쁨",
                "sad": "슬픔",
                "surprise": "놀람",
                "neutral": "평온함"
            }
    # 입력된 감정을 한글로 변환하여 리턴
    return emotion_kor.get(dominant_emotion, "알 수 없음")  # 기본값을 알 수 없음 으로 설정함