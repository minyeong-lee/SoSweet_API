from collections import deque
import mediapipe as mp
import cv2
import numpy as np
import time

# 동작별 Queue 생성 (최대 10개씩 저장)
hand_movement_queue = deque(maxlen=20)
folded_arm_queue = deque(maxlen=20)
side_movement_queue = deque(maxlen=20)
eye_touch_queue = deque(maxlen=20)

# MediaPipe Pose 모델, Face Mesh 모델, Hands 모델 초기화
# mp.options['input_stream_handler'] = 'ImmediateInputStreamHandler'
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False, # 프레임이 연속된 데이터 흐름으로 처리됨
    model_complexity=1,   # 모델 복잡도 (0, 1, 2)
    enable_segmentation=False,   # 세분화 비활성화
    min_detection_confidence=0.8,  # 감지 신뢰도
)
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, min_detection_confidence=0.5)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5)



# 좌우 흔들림(baseline) 기준값을 전역으로 저장할 변수
side_movement_baseline_3d = None
rebaseline_interval = 10   # 10초마다 baseline 갱신

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
        return results.pose_landmarks.landmark  # landmark 객체 그대로 반환
    return None


def get_midpoint_y(landmarks):
    if not landmarks[9] or not landmarks[10] or not landmarks[11] or not landmarks[12]:
        return None
    
    # 입과 어깨 중간값 y 좌표 계산
    mouth_y = (landmarks[9].y + landmarks[10].y) / 2  # 입술
    shoulder_y = (landmarks[11].y + landmarks[12].y) / 2  # 어깨
    return (mouth_y + shoulder_y) / 2 


def calculate_threshold(landmarks):
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    shoulder_width = np.sqrt((left_shoulder.x - right_shoulder.x) ** 2 +
                             (left_shoulder.y - right_shoulder.y ** 2))
    return 0.1 * shoulder_width  # 어깨 너비의 10%를 임계값으로 설정 (거리 멀거나 가까운 사용자에 대해 임계값 동적으로 조정)



def reset_all_queues():
    # 전역 큐 초기화
    global hand_movement_queue, folded_arm_queue, side_movement_queue
    hand_movement_queue.clear()
    folded_arm_queue.clear()
    side_movement_queue.clear()


# 얼굴 - 손 감지 공통 함수
def euclidean_distance(point1, point2):
    return np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2 + (point1.z - point2.z) ** 2)


#########################################################################################################

def analyze_hand_movement(frame):
    # 손이 중간선 위로 올라가 산만한 행동을 감지
    landmarks = get_landmarks(frame)
    if not landmarks:
        return None

    # 입 중심과 어깨 중심의 중간값 계산
    midpoint_y = get_midpoint_y(landmarks)
    if midpoint_y is None:
        return None # 랜드마크 제대로 추출 안되면 종료하기
    
    # 손목의 y 좌표
    left_hand_y = landmarks[15].y  # 왼쪽 손목
    right_hand_y = landmarks[16].y  # 오른쪽 손목

    # 손목이 중간값보다 위에 있는지 확인
    if left_hand_y < midpoint_y or right_hand_y < midpoint_y:
        return "[손_CHECK] 손이 너무 산만합니다!"
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

        if current_timestamp <= prev_timestamp:
            # 시간 순서가 이상하면 무시
            print(f"경고: 시간 순서가 잘못되었습니다. {prev_timestamp} >= {current_timestamp}")
            return None, None  # unpack 문제 수정 (None을 tuple 형태로 반환)

        message = analyze_hand_movement(frame)
        # 기존 함수 호출 (실제 분석)
        return (message, timestamp) if message else (None, None)

    return None, None  # 대기 중




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
    if (time.time() - last_baseline_time) > rebaseline_interval:  # time.time() 직접 호출로 매번 시간 갱신함
        side_movement_baseline_3d = (midpoint_x, midpoint_y, midpoint_z)
        last_baseline_time = time.time()
        return None
    
    base_x, base_y, base_z = side_movement_baseline_3d      

    # 3) x,z 좌표 차이로 "좌우 흔들림" 판단 (z좌표는 카메라에 대한 상대적인 값임)
    # (y축은 상하이므로, 좌우 흔들림은 x+z만 고려하는 예시이다!!)
    # move_dist = np.sqrt((midpoint_x - base_x)**2 + (midpoint_z - base_z)**2)

    # x축 움직임에 더 큰 가중치를 부여했음!!! 개선사항
    x_weight = 1.5
    z_weight = 0.5
    move_dist = np.sqrt(
        x_weight * (midpoint_x - base_x)**2 + 
        z_weight * (midpoint_z - base_z)**2
    )


    # threshold는 실험적으로 조정
    # mediapipe의 x,z가 -1 ~ 1 범위라면 0.05는 약 5% 이동한 것
    threshold = 0.1  # 10%로 증가

    if move_dist > threshold:
        return "[흔드는몸_CHECK] 몸을 좌우(또는 앞뒤)로 크게 움직이시네요! 편안하게 고정!!"
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
            print(f"경고: 시간 순서가 잘못되었습니다. {prev_timestamp} >= {current_timestamp}")
            return None, None
        
        # 실제 분석 
        message = analyze_side_movement(frame)
        return (message, timestamp) if message else (None, None)

    return None, None


# 눈과 손의 거리 확인 함수
def is_hand_near_eye(face_landmarks, hand_landmarks):
    left_eye_points = [33, 133, 159, 145]  # 왼쪽 눈 주요 랜드마크
    right_eye_points = [362, 263, 386, 374]  # 오른쪽 눈 주요 랜드마크
    index_finger_tips = [hand_landmarks[8], hand_landmarks[12], hand_landmarks[16]]  # 검지, 중지, 약지
    
    # 평균 좌표 계산하여 눈 영역 생성
    def get_eye_center(eye_points):
        avg_x = np.mean([face_landmarks[i].x for i in eye_points])
        avg_y = np.mean([face_landmarks[i].y for i in eye_points])
        avg_z = np.mean([face_landmarks[i].z for i in eye_points])
        return mp.framework.landmark_pb2.NormalizedLandmark(x=avg_x, y=avg_y, z=avg_z)
    
    left_eye_center = get_eye_center(left_eye_points)
    right_eye_center = get_eye_center(right_eye_points)
    
    # 손가락 끝 중앙 좌표 계산
    avg_x = np.mean([lm.x for lm in index_finger_tips])
    avg_y = np.mean([lm.y for lm in index_finger_tips])
    avg_z = np.mean([lm.z for lm in index_finger_tips])
    index_finger_center = mp.framework.landmark_pb2.NormalizedLandmark(x=avg_x, y=avg_y, z=avg_z)
    
    # 두 눈 중 하나라도 손가락 끝이 가까우면 True 반환
    left_distance = euclidean_distance(left_eye_center, index_finger_center)
    right_distance = euclidean_distance(right_eye_center, index_finger_center)
    
    # 거리 임계값 설정 (조정 가능)
    threshold_distance = 0.1
    
    if left_distance < threshold_distance or right_distance < threshold_distance:
        print(f"[CHECK] 눈 근처 거리: {left_distance:.4f}, {right_distance:.4f}")
        return True # 손이 눈 근처임을 나타냄
    return False


# 눈 만지기 행동 분석 함수
def analyze_eye_touch(frame):
    face_results = face_mesh.process(frame)
    hand_results = hands.process(frame)
    
    # 디버깅으로 추가함
    if not face_results.multi_face_landmarks:
        print("[디버그] 얼굴이 감지되지 않았습니다.")
    if not hand_results.multi_hand_landmarks:
        print("[디버그] 손이 감지되지 않았습니다.")
    
    # 얼굴과 손을 모두 인식한 경우만 분석
    if face_results.multi_face_landmarks and hand_results.multi_hand_landmarks:
        for face_landmarks in face_results.multi_face_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                # 눈 근처로 손이 가는 경우
                if is_hand_near_eye(face_landmarks.landmark, hand_landmarks.landmark):
                    return "[눈_CHECK] 눈을 만지고 있습니다!!!!!"
    return None


def analyze_eye_touch_with_queue(frame, timestamp):
    # 큐에 프레임 추가
    eye_touch_queue.append((frame, timestamp))
    
    # 큐 상태 출력
    print(f"눈 만지지 큐 내용 (최근 5개): {[ts for _, ts in list(eye_touch_queue)[-5:]]}")
    
    # 최소 2개의 프레임이 있어야 비교 가능
    if len(eye_touch_queue) >= 2:
        prev_frame, prev_timestamp = eye_touch_queue[-2]
        current_frame, current_timestamp = eye_touch_queue[-1]
        
        if current_timestamp <= prev_timestamp:
            print(f"경고: 시간 순서가 잘못되었습니다. {prev_timestamp} >= {current_timestamp}")
            return None, None

        # 실제 행동 분석 함수 호출
        message = analyze_eye_touch(frame)
        return (message, timestamp) if message else (None, None)
    
    return None, None