import cv2
import mediapipe as mp

# MediaPipe Pose 모델 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False, min_detection_confidence=0.5)

# Pose 랜드마크 그리기 위한 Drawing 유틸
mp_drawing = mp.solutions.drawing_utils 

# 웹캠 연결
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Unable to access the webcam")
    exit()

# 프레임 해상도 설정 (1280x720)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("Error: Unable to open video file.")
    exit()
else:
    print("Video file opened successfully.")

# 결과 저장용 VideoWriter 초기화
output_video_path = 'output_pose_video.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # mp4 코덱
fps = int(cap.get(cv2.CAP_PROP_FPS))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

frame_count = 0
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Video processing complete.")
        break

    if frame_count % 10 == 0:
        print(f"Processing frame {frame_count}...")
    frame_count += 1

    # 프레임 전처리
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)

    # Pose 랜드마크 확인 및 그리기
    if results.pose_landmarks:
        # OpenCV로 랜드마크 그리기
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # 특정 랜드마크 좌표 확인 (예: 왼쪽 손목과 오른쪽 손목)
        left_wrist = results.pose_landmarks.landmark[15]
        right_wrist = results.pose_landmarks.landmark[16]
        
        # 좌표를 OpenCV로 표시
        left_wrist_coord = (int(left_wrist.x * frame.shape[1]), int(left_wrist.y * frame.shape[0]))
        right_wrist_coord = (int(right_wrist.x * frame.shape[1]), int(right_wrist.y * frame.shape[0]))
        
        # OpenCV로 점 찍기
        cv2.circle(frame, left_wrist_coord, 10, (0, 255, 0), -1)
        cv2.circle(frame, right_wrist_coord, 10, (0, 0, 255), -1)
        
        # 좌표 출력
        print(f"왼쪽 손목 좌표: {left_wrist_coord}, 오른쪽 손목 좌표: {right_wrist_coord}")
        
        # 화면에 표시 (실시간 확인용)
        cv2.imshow('Pose Detection', frame)
        # 'q' 키를 눌러 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    
    # frame을 파일로 저장
    out.write(frame)

cap.release()
out.release()
print("Resources released. Output saved as:", output_video_path)


# 입을 가리는 동작 감지
def detect_covering_mouth(landmarks):
    mouth = landmarks[mp_pose.PoseLandmark.MOUTH_LEFT.value].y
    left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y
    right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y
    
    if left_wrist < mouth or right_wrist < mouth:
        return True
    return False
