from collections import namedtuple
import mediapipe as mp
import cv2
import numpy as np
import time
import heapq

# 우선순위 큐(heap)들 전역으로 정의함 (크기 제한 위함)
hand_movement_heap = []
side_movement_heap = []
eye_touch_heap = []

# MediaPipe Pose 모델, Face Mesh 모델, Hands 모델 초기화
# mp.options['input_stream_handler'] = 'ImmediateInputStreamHandler'
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False, # 프레임이 연속된 데이터 흐름으로 처리됨
    model_complexity=1,   # 모델 복잡도 (0, 1, 2)
    enable_segmentation=False,   # 세분화 비활성화
    min_detection_confidence=0.4,  # 감지 신뢰도
)
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, min_detection_confidence=0.5)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.4)



# 좌우 흔들림(baseline) 기준값을 전역으로 저장할 변수
side_movement_baseline_3d = None
rebaseline_interval = 15   # 15초마다 baseline 갱신

# 마지막으로 baseline 잡은 시각(초)
last_baseline_time = 0

# 현재 시간
current_time = time.time()

# NormalizedLandmark 정의
NormalizedLandmark = namedtuple("NormalizedLandmark", ["x", "y", "z"])


##########################################################################################################
# 공통 유틸
def get_landmarks(frame, convert_rgb=True):
    # BGR -> RGB 변환 여부를 옵션으로 둠
    if convert_rgb:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    else:
        frame_rgb = frame

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
    global hand_movement_heap , side_movement_heap , eye_touch_heap 
    hand_movement_heap .clear()
    side_movement_heap.clear()
    eye_touch_heap.clear()


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


def analyze_hand_movement_with_priority_queue(frame, timestamp):
    """
    우선순위 큐를 사용하여 (timestamp, frame) 정렬 관리,
    가장 최근 2개 프레임 비교하여 산만 손동작 여부 판단
    
    """
    # 우선순위 큐에 push하기, timestamp 오름차순으로 정렬
    heapq.heappush(hand_movement_heap, (timestamp, frame))
    
    # 크기 제한(최대 20개) -> 오래된 것부터 제거하기
    while len(hand_movement_heap) > 20:
        heapq.heappop(hand_movement_heap)
        
    # 최신 순으로 2개 꺼내서 비교하기 위해 정렬
    sorted_frames = sorted(hand_movement_heap, key=lambda x: x[0])
    prev_timestamp, prev_frame = sorted_frames[-2]
    current_timestamp, current_frame = sorted_frames[-1]

    # 실제 손 분석하기
    message = analyze_hand_movement(current_frame)
        # 기존 함수 호출 (실제 분석)
    return (message, current_timestamp) if message else (None, None)


#  몸 좌우 흔들기
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

    # baseline 없으면 세팅
    if side_movement_baseline_3d is None:
        side_movement_baseline_3d = (midpoint_x, midpoint_y, midpoint_z)
        last_baseline_time = time.time() if current_time is None else current_time
        return None
    
    # 주기적으로 baseline 다시 잡기 (예: 30초마다)
    if (time.time() - last_baseline_time) > rebaseline_interval:  # time.time() 직접 호출로 매번 시간 갱신함
        side_movement_baseline_3d = (midpoint_x, midpoint_y, midpoint_z)
        last_baseline_time = time.time()
        return None
    
    # 좌우(앞뒤) 이동 거리 계산
    base_x, base_y, base_z = side_movement_baseline_3d      

    # x,z 좌표 차이로 "좌우 흔들림" 판단 (z좌표는 카메라에 대한 상대적인 값임)
    # (y축은 상하이므로, 좌우 흔들림은 x+z만 고려하는 예시이다!!)
    # move_dist = np.sqrt((midpoint_x - base_x)**2 + (midpoint_z - base_z)**2)

    # x축 움직임에 더 큰 가중치를 부여했음!!! 개선사항
    x_weight = 1.2
    z_weight = 0.3
    move_dist = np.sqrt(
        x_weight * (midpoint_x - base_x)**2 + 
        z_weight * (midpoint_z - base_z)**2
    )


    # threshold는 실험적으로 조정
    # mediapipe의 x,z가 -1 ~ 1 범위라면 0.05는 약 5% 이동한 것
    threshold = 0.2  # 어깨 너비 대비 20% 이상 움직임만 감지

    if move_dist > threshold:
        return "[흔드는몸_CHECK] 몸을 크게 흔드는 동작 감지!"
    return None


def analyze_side_movement_with_priority_queue(frame, timestamp):
    # 우선순위 큐 이용
    heapq.heappush(side_movement_heap, (timestamp, frame))
    
    # 크기 제한
    while len(side_movement_heap) > 20:
        heapq.heappop(side_movement_heap)
    
    # 2개 미만이면 분석 불가
    if len(side_movement_heap) < 2:
        return None, None

    # print(f"현재 양쪽으로 움직이기 측정 큐 크기: {len(side_movement_queue)}")
    # print(f"좌우 움직이기 큐 내용 (최근 5개): {[ts for _, ts in list(side_movement_queue)[-5:]]}")

    # 4) 정렬 후 마지막 2개
    sorted_frames = sorted(side_movement_heap, key=lambda x: x[0])
    prev_timestamp, prev_frame = sorted_frames[-2]
    current_timestamp, current_frame = sorted_frames[-1]

    message = analyze_side_movement(current_frame)
    return (message, current_timestamp) if message else (None, None)


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
        return NormalizedLandmark(x=avg_x, y=avg_y, z=avg_z)
    
    left_eye_center = get_eye_center(left_eye_points)
    right_eye_center = get_eye_center(right_eye_points)
    
    # 손가락 끝 중앙 좌표 계산
    avg_x = np.mean([lm.x for lm in index_finger_tips])
    avg_y = np.mean([lm.y for lm in index_finger_tips])
    avg_z = np.mean([lm.z for lm in index_finger_tips])
    index_finger_center = NormalizedLandmark(x=avg_x, y=avg_y, z=avg_z)
    
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
    # if not face_results.multi_face_landmarks:
    #     print("[디버그] 얼굴이 감지되지 않았습니다.")
    # if not hand_results.multi_hand_landmarks:
    #     print("[디버그] 손이 감지되지 않았습니다.")
    
    # 얼굴과 손을 모두 인식한 경우만 분석
    if face_results.multi_face_landmarks and hand_results.multi_hand_landmarks:
        for face_landmarks in face_results.multi_face_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                # 눈 근처로 손이 가는 경우
                if is_hand_near_eye(face_landmarks.landmark, hand_landmarks.landmark):
                    return "[눈_CHECK] 눈을 만지고 있습니다!!!!!"
    return None


def analyze_eye_touch_with_priority_queue(frame, timestamp):
    """
    우선순위 큐로 (timestamp, frame)을 관리
    가장 최근 2개를 분석
    """
    heapq.heappush(eye_touch_heap, (timestamp, frame))
    while len(eye_touch_heap) > 20:
        heapq.heappop(eye_touch_heap)

    if len(eye_touch_heap) < 2:
        return None, None

    sorted_frames = sorted(eye_touch_heap, key=lambda x: x[0])
    prev_timestamp, prev_frame = sorted_frames[-2]
    current_timestamp, current_frame = sorted_frames[-1]

    message = analyze_eye_touch(current_frame)
    return (message, current_timestamp) if message else (None, None)