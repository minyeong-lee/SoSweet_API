import mediapipe as mp
import cv2
import numpy as np
import time
import heapq
from collections import namedtuple


# NormalizedLandmark 정의
NormalizedLandmark = namedtuple("NormalizedLandmark", ["x", "y", "z"])

class ActionAnalyzer:
    def __init__(self):
        # 기본 초기화
        # 우선순위 큐
        self.hand_movement_heap = []
        self.side_movement_heap = []
        self.eye_touch_heap = []

        # 좌우 움직임 baseline
        self.side_movement_baseline_3d = None  # 좌우 흔들림(baseline) 기준값을 전역으로 저장할 변수
        self.last_baseline_time = time.time()  # 마지막 baseline 기준 시간 설정
        self.rebaseline_interval = 15  # 15초마다 baseline 갱신

        # MediaPipe Pose 모델 초기화
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False, # 프레임을 매번 독립적으로 전달하는 구조에 권장
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.4  # 얼굴 및 손 동작 인식 정확도 조절
        )

        # MediaPipe Face Mesh 모델 초기화
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            # static_image_mode=True,
            max_num_faces=1,  # 인식할 최대 얼굴 수
            min_detection_confidence=0.5
        )

        # MediaPipe Hands 모델 초기화
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            # static_image_mode=True,
            max_num_hands=2,  # 인식할 최대 손 개수
            min_detection_confidence=0.4
        )

        self.rebaseline_interval = 15  # 15초마다 baseline 갱신
        self.current_time = time.time()

    def reset_all_queues(self):
        self.hand_movement_heap.clear()
        self.side_movement_heap.clear()
        self.eye_touch_heap.clear()
        self.side_movement_baseline_3d = None
        self.last_baseline_time = time.time()


    # 공통 유틸
    def get_landmarks(self, frame_bgr):
        """
            BGR 프레임을 입력으로 받아,
            1) (640,480) 리사이즈
            2) BGR->RGB
            3) Pose 추론
            4) 리턴(landmarks or None)
        """
        if frame_bgr is None or not frame_bgr.any():
            return None

        # 리사이즈 전에 np.uint8 형으로 맞추기
        if frame_bgr.dtype != np.uint8:
            frame_bgr = frame_bgr.astype(np.uint8)

        frame_bgr = np.ascontiguousarray(frame_bgr) # 메모리 연속성 보장
        frame_bgr = cv2.resize(frame_bgr, (640, 480), interpolation=cv2.INTER_LINEAR) # 리사이즈 (원본의 160,120에서 640,480으로)

        # BGR -> RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        results = self.pose.process(frame_rgb) # 관절(랜드마크) 정보 얻기
        if results.pose_landmarks:
            return results.pose_landmarks.landmark # landmark 객체 그대로 반환
        else:
            return None


    def get_hand_and_face_results(self, frame_bgr):
        """
        BGR 프레임 -> (640,480) 리사이즈 -> RGB
        face_mesh.process, hands.process 결과 리턴
        """
        if frame_bgr is None or not frame_bgr.any():
            return None, None

        if frame_bgr.dtype != np.uint8:
            frame_bgr = frame_bgr.astype(np.uint8)

        frame_bgr = np.ascontiguousarray(frame_bgr)
        frame_bgr = cv2.resize(frame_bgr, (640, 480), interpolation=cv2.INTER_LINEAR)
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        face_results = self.face_mesh.process(frame_rgb)
        hand_results = self.hands.process(frame_rgb)
        return face_results, hand_results


    @staticmethod
    def get_midpoint_y(landmarks):
        # landmarks는 MediaPipe의 NormalizedLandmark 객체 리스트로,
        # None 대신 빈 리스트나 잘못된 인덱스로 인한 IndexError를 발생시킴
        if landmarks is None or len(landmarks) < 13:
                return None
        
        # 9,10 => 입술  / 11,12 => 어깨
        mouth_y = (landmarks[9].y + landmarks[10].y) / 2
        shoulder_y = (landmarks[11].y + landmarks[12].y) / 2
        return (mouth_y + shoulder_y) / 2


    def calculate_threshold(self, landmarks):
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        shoulder_width = np.sqrt((left_shoulder.x - right_shoulder.x) ** 2 +
                            (left_shoulder.y - right_shoulder.y) ** 2)
        return 0.1 * shoulder_width  # 어깨 너비의 10%를 임계값으로 설정 (거리 멀거나 가까운 사용자에 대해 임계값 동적으로 조정)


    # 얼굴 - 손 감지 공통 함수
    def euclidean_distance(self, point1, point2):
        return np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2 + (point1.z - point2.z) ** 2)


    #########################################################################################################

    def analyze_hand_movement(self, frame_bgr):
        # 손이 중간선 위로 올라가 산만한 행동을 감지
        pose_landmarks = self.get_landmarks(frame_bgr)
        if pose_landmarks is None or len(pose_landmarks) < 17:
            return None

        # 입 중심과 어깨 중심의 중간값 계산
        midpoint_y = self.get_midpoint_y(pose_landmarks)
        if midpoint_y is None:
            return None # 랜드마크 제대로 추출 안되면 종료하기
        
        if len(pose_landmarks) < 17:
            return None
        
        # 손목의 y 좌표
        left_hand_y = pose_landmarks[15].y  # 왼쪽 손목
        right_hand_y = pose_landmarks[16].y  # 오른쪽 손목

        # 손목이 중간값보다 위에 있는지 확인
        if left_hand_y < midpoint_y or right_hand_y < midpoint_y:
            return "[손_CHECK] 손이 너무 산만합니다!"
        return None


    def analyze_hand_movement_with_priority_queue(self, frame_bgr, timestamp):
        """
        우선순위 큐를 사용하여 (timestamp, frame) 정렬 관리,
        가장 최근 2개 프레임 비교하여 산만 손동작 여부 판단
        
        """
        # 우선순위 큐에 push하기, timestamp 오름차순으로 정렬
        heapq.heappush(self.hand_movement_heap, (timestamp, frame_bgr))
        
        # 크기 제한(최대 20개) -> 오래된 것부터 제거하기
        while len(self.hand_movement_heap) > 20:
            heapq.heappop(self.hand_movement_heap)
        
        # 2개 미만이면 분석 불가
        if len(self.hand_movement_heap) < 2:
            return None, None
        
        # 정렬 -> 최신 프레임
        sorted_frames = sorted(self.hand_movement_heap, key=lambda x: x[0])
        _, latest_frame  = sorted_frames[-1]
        
        message = self.analyze_hand_movement(latest_frame )
        return (message, timestamp) if message else (None, None)


    #  몸 좌우 흔들기
    def analyze_side_movement(self, frame_bgr):
        landmarks = self.get_landmarks(frame_bgr)

        if landmarks is None:
            return None
        
        if len(landmarks) < 13:
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
        if self.side_movement_baseline_3d is None:
            self.side_movement_baseline_3d = (midpoint_x, midpoint_y, midpoint_z)
            self.last_baseline_time = time.time()
            return None
        
        # 주기적으로 baseline 다시 잡기 (예: 30초마다)
        if (time.time() - self.last_baseline_time) > self.rebaseline_interval:  # time.time() 직접 호출로 매번 시간 갱신함
            self.side_movement_baseline_3d = (midpoint_x, midpoint_y, midpoint_z)
            self.last_baseline_time = time.time()
            return None
        
        # 좌우(앞뒤) 이동 거리 계산
        base_x, base_y, base_z = self.side_movement_baseline_3d      

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


    def analyze_side_movement_with_priority_queue(self, frame_bgr, timestamp):
        # 우선순위 큐 이용
        heapq.heappush(self.side_movement_heap, (timestamp, frame_bgr))
        
        # 크기 제한
        while len(self.side_movement_heap) > 20:
            heapq.heappop(self.side_movement_heap)
        
        # 2개 미만이면 분석 불가
        if len(self.side_movement_heap) < 2:
            return None, None

        # print(f"현재 양쪽으로 움직이기 측정 큐 크기: {len(side_movement_queue)}")
        # print(f"좌우 움직이기 큐 내용 (최근 5개): {[ts for _, ts in list(side_movement_queue)[-5:]]}")

        # 4) 정렬 후 마지막 2개
        sorted_frames = sorted(self.side_movement_heap, key=lambda x: x[0])
        _, latest_frame = sorted_frames[-1]

        message = self.analyze_side_movement(latest_frame)
        return (message, timestamp) if message else (None, None)


    # 눈과 손의 거리 확인 함수
    def is_hand_near_eye(self, face_landmarks, hand_landmarks):
        # Face mesh는 468개 점 (정확히는 478점일 수도 있음), 안전하게 400 이상 체크
        if len(face_landmarks) < 400 or len(hand_landmarks) < 17:  # 대략 468개가 풀 페이스
            return False

        left_eye_points = [33, 133, 159, 145]  # 왼쪽 눈 주요 랜드마크
        right_eye_points = [362, 263, 386, 374]  # 오른쪽 눈 주요 랜드마크

        # 검지, 중지, 약지 tips (인덱스: 8, 12, 16)
        # 최대 21개(0~20) => 이하 체크
        if len(hand_landmarks) < 17:
            return False
        
        index_finger_tips = [hand_landmarks[8], hand_landmarks[12], hand_landmarks[16]]  # 검지, 중지, 약지
        
        
        # 평균 좌표 계산하여 눈 영역 생성
        def get_eye_center(eye_idxs):
            valid_points = [face_landmarks[i] for i in eye_idxs]
            if valid_points is None:  # 유효한 점이 없다면 None 반환
                return None
            avg_x = np.mean([point.x for point in valid_points])
            avg_y = np.mean([point.y for point in valid_points])
            avg_z = np.mean([point.z for point in valid_points])
            return NormalizedLandmark(x=avg_x, y=avg_y, z=avg_z)
        
        left_eye_center = get_eye_center(left_eye_points)
        right_eye_center = get_eye_center(right_eye_points)
        
        if left_eye_center is None or right_eye_center is None:
            print("[오류] 얼굴 랜드마크 정보 부족")
            return False
        
        # 손가락 끝 중앙 좌표 계산
        valid_finger_points = [lm for lm in index_finger_tips if lm is not None]
        if not valid_finger_points:
            print("[오류] 손가락 랜드마크 정보 부족")
            return False
        
        # 손가락 끝 중앙 좌표 계산
        avg_x = np.mean([lm.x for lm in valid_finger_points])
        avg_y = np.mean([lm.y for lm in valid_finger_points])
        avg_z = np.mean([lm.z for lm in valid_finger_points])
        finger_center = NormalizedLandmark(x=avg_x, y=avg_y, z=avg_z)
        
        # 두 눈 중 하나라도 손가락 끝이 가까우면 True 반환
        left_distance = self.euclidean_distance(left_eye_center, finger_center)
        right_distance = self.euclidean_distance(right_eye_center, finger_center)
        
        # 거리 임계값 설정 (조정 가능)
        threshold_distance = 0.1
        
        if left_distance < threshold_distance or right_distance < threshold_distance:
            print(f"[CHECK] 눈 근처 거리: {left_distance:.4f}, {right_distance:.4f}")
            return True # 손이 눈 근처임을 나타냄
        return False


    # 눈 만지기 행동 분석 함수
    def analyze_eye_touch(self, frame_bgr):
        # BGR -> RGB
        if frame_bgr is None or not frame_bgr.any():
            return None
        
        frame_bgr = np.ascontiguousarray(frame_bgr, dtype=np.uint8)
        frame_bgr = cv2.resize(frame_bgr, (640, 480), interpolation=cv2.INTER_LINEAR)
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
        face_results = self.face_mesh.process(frame_rgb)
        hand_results = self.hands.process(frame_rgb)                           
        
        # 디버깅으로 추가함
        # if not face_results.multi_face_landmarks:
        #     print("[디버그] 얼굴이 감지되지 않았습니다.")
        # if not hand_results.multi_hand_landmarks:
        #     print("[디버그] 손이 감지되지 않았습니다.")
        
        # 얼굴과 손을 모두 인식한 경우만 분석
        if (
            face_results.multi_face_landmarks is None 
            or len(face_results.multi_face_landmarks) == 0
            or hand_results.multi_hand_landmarks is None
            or len(hand_results.multi_hand_landmarks) == 0
        ):
            return None


        for face_lms in face_results.multi_face_landmarks:
            for hand_lms in hand_results.multi_hand_landmarks:
                if self.is_hand_near_eye(face_lms.landmark, hand_lms.landmark):
                    return "[눈_CHECK] 눈을 만지고 있습니다!!!!!"
        return None



    def analyze_eye_touch_with_priority_queue(self, frame_bgr, timestamp):
        """
        우선순위 큐로 (timestamp, frame)을 관리
        가장 최근 2개를 분석
        """
        heapq.heappush(self.eye_touch_heap, (timestamp, frame_bgr))
        while len(self.eye_touch_heap) > 20:
            heapq.heappop(self.eye_touch_heap)

        if len(self.eye_touch_heap) < 2:
            return None, None

        sorted_frames = sorted(self.eye_touch_heap, key=lambda x: x[0])
        _, latest_frame = sorted_frames[-1]

        message = self.analyze_eye_touch(latest_frame)
        return (message, timestamp) if message else (None, None)