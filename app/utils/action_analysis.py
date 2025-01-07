from collections import deque
import mediapipe as mp
import cv2
import time

# Queue 생성
frame_queue = deque(maxlen=10) # 최대 10개의 프레임만 저장

# MediaPipe Pose 모델 초기화
# mp.options['input_stream_handler'] = 'ImmediateInputStreamHandler'
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=True, # 프레임이 연속된 데이터 흐름으로 처리됨
    model_complexity=1, 
    enable_segmentation=False, 
    min_detection_confidence=0.5
)

def analyze_hand_movement(frame):
    # 손이 중간선 위로 올라가 산만한 행동을 감지
    landmarks = get_landmarks(frame)
    if not landmarks:
        return None

    # 입 중심과 어깨 중심의 중간값 계산
    midpoint_y = get_midpoint_y(landmarks)

    # 손목의 y 좌표
    left_hand_y = landmarks[15].y  # 왼쪽 손목
    right_hand_y = landmarks[16].y  # 오른쪽 손목

    # 손목이 중간값보다 위에 있는지 확인
    if left_hand_y < midpoint_y or right_hand_y < midpoint_y:
        return "손이 너무 산만합니다!"
    return None


def analyze_folded_arm(frame):
    # 팔짱을 끼고 있는지 감지
    landmarks = get_landmarks(frame)
    if not landmarks:
        return None

    # 손목과 어깨의 x 좌표 가져오기
    left_wrist_x, right_wrist_x = landmarks[15].x, landmarks[16].x
    left_shoulder_x, right_shoulder_x = landmarks[11].x, landmarks[12].x

    # 팔짱 감지
    if left_wrist_x > right_shoulder_x or right_wrist_x < left_shoulder_x:
        return "팔짱은 노노~ 자유롭게 풀어주세요~"
    return None


def analyze_side_movement(frame):
    # 몸을 좌우로 흔드는 동작을 감지
    landmarks = get_landmarks(frame)
    if not landmarks:
        return None

    left_shoulder_x, right_shoulder_x = landmarks[11].x, landmarks[12].x
    midpoint_x = (left_shoulder_x + right_shoulder_x) / 2  # 중앙 좌표 계산

    # baseline 설정 및 기준 이동
    if not hasattr(analyze_side_movement, 'baseline_x'):
        analyze_side_movement.baseline_x = midpoint_x

    # 움직임 확인
    if midpoint_x > analyze_side_movement.baseline_x + 0.05:
        return "몸을 좌우로 너무 움직이시네요! 편안하게 고정!!"
    elif midpoint_x < analyze_side_movement.baseline_x - 0.05:
        return "몸을 좌우로 너무 움직이시네요! 편안하게 고정!!"
    return None


def get_landmarks(frame):
    # 프레임에서 랜드마크 추출
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)
    if results.pose_landmarks:
        return results.pose_landmarks.landmark
    return None


def get_midpoint_y(landmarks):
    # 입과 어깨 중간값 y 좌표 계산
    mouth_y = (landmarks[9].y + landmarks[10].y) / 2  # 입술
    shoulder_y = (landmarks[11].y + landmarks[12].y) / 2  # 어깨
    return (mouth_y + shoulder_y) / 2


def analyze_hand_movement_with_queue(frame, timestamp):
    # Queue를 사용하여 순서 보장
    frame_queue.append((frame, timestamp))
    
    # 현재 큐 내용 출력
    print(f"현재 손 동작 측정 큐 크기: {len(frame_queue)}")
    print(f"큐 내용 (최근 5개): {[ts for _, ts in list(frame_queue)[-5:]]}")
    
    # 큐에서 가장 최근 두 개의 프레임 비교
    if len(frame_queue) >= 2:
        prev_frame, prev_timestamp = frame_queue[-2]
        current_frame, current_timestamp = frame_queue[-1]

        if current_timestamp < prev_timestamp:
            # 시간 순서가 이상하면 무시
            print("타임스탬프 순서 불일치: 프레임 스킵")
            return None

        # 기존 함수 호출
        return analyze_hand_movement(frame)

    return None  # 대기 중


def analyze_folded_arm_with_queue(frame, timestamp):
    # Queue를 사용하여 팔짱 감지
    frame_queue.append((frame, timestamp))
    
    # 현재 큐 내용 출력
    print(f"현재 팔짱 측정 큐 크기: {len(frame_queue)}")
    print(f"큐 내용 (최근 5개): {[ts for _, ts in list(frame_queue)[-5:]]}")

    if len(frame_queue) >= 2:
        prev_frame, prev_timestamp = frame_queue[-2]
        current_frame, current_timestamp = frame_queue[-1]

        if current_timestamp < prev_timestamp:
            return None

        # 기존 함수 호출
        return analyze_folded_arm(frame)

    return None


def analyze_side_movement_with_queue(frame, timestamp):
    # Queue를 사용하여 몸 움직임 감지
    frame_queue.append((frame, timestamp))

    print(f"현재 양쪽으로 움직이기 측정 큐 크기: {len(frame_queue)}")
    print(f"큐 내용 (최근 5개): {[ts for _, ts in list(frame_queue)[-5:]]}")

    if len(frame_queue) >= 2:
        prev_frame, prev_timestamp = frame_queue[-2]
        current_frame, current_timestamp = frame_queue[-1]

        if current_timestamp < prev_timestamp:
            return None

        return analyze_side_movement(frame)

    return None