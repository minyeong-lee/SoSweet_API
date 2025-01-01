import cv2
from deepface import DeepFace
from app.models import save_emotion

def analyze_and_send(user_id):
    cap = cv2.VideoCapture(0)
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Cannot read frame from webcam.")
            break

        if frame_count % 60 == 0:
            try:
                analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                dominant_emotion = max(analysis[0]['emotion'], key=analysis[0]['emotion'].get)

                save_emotion(user_id, frame_count, analysis[0]['emotion'], dominant_emotion)
                print(f"Data saved for user {user_id}: {dominant_emotion}")

            except Exception as e:
                print(f"Error in frame {frame_count}: {str(e)}")

        frame_count += 1
        if frame_count >= 600:  # 예: 10초 동안만 분석
            break

    cap.release()
