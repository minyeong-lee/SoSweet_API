from collections import deque
import mediapipe as mp
import cv2
import numpy as np
import time

# 동작별 Queue 생성 (최대 10개씩 저장)
hand_movement_queue = deque(maxlen=10)
folded_arm_queue = deque(maxlen=10)
side_movement_queue = deque(maxlen=10)

# MediaPipe Pose 모델 초기화
# mp.options['input_stream_handler'] = 'ImmediateInputStreamHandler'
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=True, # 프레임이 연속된 데이터 흐름으로 처리됨
    model_complexity=1,   # 모델 복잡도 (0, 1, 2)
    enable_segmentation=False,   # 세분화 비활성화
    min_detection_confidence=0.5,  # 감지 신뢰도
)

# 좌우 흔들림(baseline) 기준값을 전역으로 저장할 변수
side_movement_baseline_3d = None
rebaseline_interval = 30  # 예) 30초마다 baseline 갱신 (필요시)

# 마지막으로 baseline 잡은 시각(초)
last_baseline_time = 0

# 현재 시간
current_time = time.time()

# 공통 유틸
def get_landmarks(frame):
    # 프레임에서 랜드마크 추출
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # 현재의 BGR 영상(프레임)을 RGB로 변환하여
    results = pose.process(frame_rgb) # 관절(랜드마크) 정보 얻기
    if results.pose_landmarks:
        return results.pose_landmarks.landmark
    return None


def get_midpoint_y(landmarks):
    # 입과 어깨 중간값 y 좌표 계산
    mouth_y = (landmarks[9].y + landmarks[10].y) / 2  # 입술
    shoulder_y = (landmarks[11].y + landmarks[12].y) / 2  # 어깨
    return (mouth_y + shoulder_y) / 2 


def reset_all_queues():
    # 전역 큐 초기화
    global hand_movement_queue, folded_arm_queue, side_movement_queue
    hand_movement_queue.clear()
    folded_arm_queue.clear()
    side_movement_queue.clear()


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


def analyze_hand_movement_with_queue(frame, timestamp):
    # Queue를 사용하여 순서 보장
    hand_movement_queue.append((frame, timestamp))
    
    # 현재 큐 내용 출력
    # print(f"현재 손 동작 측정 큐 크기: {len(hand_movement_queue)}")
    print(f"손 동작 큐 내용 (최근 5개): {[ts for _, ts in list(hand_movement_queue)[-5:]]}")
    
    # 큐에서 가장 최근 두 개의 프레임 비교
    if len(hand_movement_queue) >= 2:
        prev_frame, prev_timestamp = hand_movement_queue[-2]
        current_frame, current_timestamp = hand_movement_queue[-1]

        if current_timestamp < prev_timestamp:
            # 시간 순서가 이상하면 무시
            print("손 동작: 타임스탬프 순서 불일치 - 프레임 스킵")
            return None, None  # unpack 문제 수정 (None을 tuple 형태로 반환)

        message = analyze_hand_movement(frame)
        # 기존 함수 호출 (실제 분석)
        return (message, timestamp) if message else (None, None)

    return None, None  # 대기 중


def analyze_folded_arm(frame):
    # 팔짱 및 팔 산만한 동작 감지
    # 예) 왼쪽 손목이 오른쪽 팔꿈치 근처 & 오른쪽 손목이 왼쪽 팔꿈치 근처 등에 접근하면!
    landmarks = get_landmarks(frame)

    if not landmarks:
        return None

    img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # 필요 랜드마크 인덱스
    # 왼쪽 팔꿈치: 13, 왼쪽 손목: 15
    # 오른쪽 팔꿈치: 14, 오른쪽 손목: 16
    left_elbow = landmarks[13]
    left_wrist = landmarks[15]
    right_elbow = landmarks[14]
    right_wrist = landmarks[16]
    
    # 좌표 변환 (실제 해상도에서의)
    img_h, img_w, _ = frame.shape
    l_elb_x, l_elb_y = left_elbow.x * img_w, left_elbow.y * img_h
    l_wri_x, l_wri_y = left_wrist.x * img_w, left_wrist.y * img_h
    r_elb_x, r_elb_y = right_elbow.x * img_w, right_elbow.y * img_h
    r_wri_x, r_wri_y = right_wrist.x * img_w, right_wrist.y * img_h
    

    # 손목과 어깨의 x 좌표 가져오기
    # left_wrist_x, right_wrist_x = landmarks[15].x, landmarks[16].x
    # left_shoulder_x, right_shoulder_x = landmarks[11].x, landmarks[12].x

    # "팔짱"이라고 판단하는 기준 예시
    # - 왼손목과 오른팔꿈치 사이의 유클리드 거리
    # - 오른손목과 왼팔꿈치 사이의 유클리드 거리
    # - 둘 다 일정 거리 이하이면 팔짱 낀 것으로 봄
    dist_threshold = 80  # 임계값 (상황에 따라 조절)

    dist_lw_re = np.sqrt((l_wri_x - r_elb_x)**2 + (l_wri_y - r_elb_y)**2)
    dist_rw_le = np.sqrt((r_wri_x - l_elb_x)**2 + (r_wri_y - l_elb_y)**2)

    if dist_lw_re < dist_threshold and dist_rw_le < dist_threshold:
        # 연속 프레임에서 여러 번 True가 감지되면 하나의 동작으로 처리해도 됨
        return "팔이 너무 산만합니다!!!!!!!!!!!!!!!"
    else:
        return None
    

def analyze_folded_arm_with_queue(frame, timestamp):
    # Queue를 사용하여 팔 움직임 감지
    folded_arm_queue.append((frame, timestamp))
    
    # 현재 큐 내용 출력
    # print(f"현재 팔짱 측정 큐 크기: {len(folded_arm_queue)}")
    print(f"팔 산만 움직임 큐 내용 (최근 5개): {[ts for _, ts in list(folded_arm_queue)[-5:]]}")

    if len(folded_arm_queue) >= 2:
        prev_frame, prev_timestamp = folded_arm_queue[-2]
        current_frame, current_timestamp = folded_arm_queue[-1]

        if current_timestamp < prev_timestamp:
            return None, None

        # 기존 함수 호출 (실제 분석)
        message = analyze_folded_arm(frame)
        if message:
            return (message, timestamp) 
        else:
            return None, None
        
    return None, None


def analyze_side_movement(frame):
    global side_movement_baseline_3d, last_baseline_time

    # 몸을 좌우로 흔드는 동작을 감지
    landmarks = get_landmarks(frame)
    if not landmarks:
        return None

    # 어깨 좌표
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    
    # 평균 x, y, z
    midpoint_x = (left_shoulder.x + right_shoulder.x) / 2
    midpoint_y = (left_shoulder.y + right_shoulder.y) / 2
    midpoint_z = (left_shoulder.z + right_shoulder.z) / 2  # 3D 좌표
    
    # left_shoulder_x, right_shoulder_x = landmarks[11].x, landmarks[12].x
    # midpoint_x = (left_shoulder_x + right_shoulder_x) / 2  # 중앙 좌표 계산

    # 1) baseline 없으면 세팅
    if side_movement_baseline_3d is None:
        side_movement_baseline_3d = (midpoint_x, midpoint_y, midpoint_z)
        last_baseline_time = time.time() if current_time is None else current_time
        return None
    
    # 2) 주기적으로 baseline 다시 잡기 (예: 30초마다)
    now = time.time() if current_time is None else current_time
    if (now - last_baseline_time) > rebaseline_interval:
        side_movement_baseline_3d = (midpoint_x, midpoint_y, midpoint_z)
        last_baseline_time = now
        return None
    
    base_x, base_y, base_z = side_movement_baseline_3d      

    # 3) x,z 좌표 차이로 "좌우 흔들림" 판단 (z좌표는 카메라에 대한 상대적인 값임)
    # (y축은 상하이므로, 좌우 흔들림은 x+z만 고려하는 예시이다!!)
    move_dist = np.sqrt((midpoint_x - base_x)**2 + (midpoint_z - base_z)**2)

    # threshold는 실험적으로 조정
    # mediapipe의 x,z가 -1 ~ 1 범위라면 0.05는 약 5% 이동한 것
    threshold = 0.05

    if move_dist > threshold:
        return "몸을 좌우(또는 앞뒤)로 크게 움직이시네요! 편안하게 고정!!"
    return None


def analyze_side_movement_with_queue(frame, timestamp):
    # Queue를 사용하여 몸 움직임 감지
    side_movement_queue.append((frame, timestamp))

    # print(f"현재 양쪽으로 움직이기 측정 큐 크기: {len(side_movement_queue)}")
    print(f"좌우 움직이기 큐 내용 (최근 5개): {[ts for _, ts in list(side_movement_queue)[-5:]]}")

    if len(side_movement_queue) >= 2:
        prev_frame, prev_timestamp = side_movement_queue[-2]
        current_frame, current_timestamp = side_movement_queue[-1]

        if current_timestamp < prev_timestamp:
            return None, None
        
        # 실제 분석
        message = analyze_side_movement(frame)
        return (message, timestamp) if message else (None, None)

    return None