import numpy as np
import cv2
import base64

def decode_frame_func(frame):
    try:
        # data_url 에서 base64 데이터 추출
        if ',' in frame:
            base64_data = frame.split(',')[1]
        else:
            raise ValueError("올바르지 않은 Data URL 형식입니다.")
        
        # Base64 디코딩하여 numpy array로 변환
        img_data = base64.b64decode(base64_data)
        np_img = np.frombuffer(img_data, dtype=np.uint8)
        decoded_frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        
        if decoded_frame is None:
            raise ValueError("이미지 디코딩 실패")
        
        print(f"[디버그] 디코딩된 이미지 해상도: {decoded_frame.shape}")
        
        decoded_frame = cv2.resize(decoded_frame, (640, 480), interpolation=cv2.INTER_AREA)
        
        # BGR -> RGB 변환
        decoded_frame_rgb = cv2.cvtColor(decoded_frame, cv2.COLOR_BGR2RGB)
        
        return decoded_frame_rgb
    except Exception as e:
        raise ValueError(f"Frame decoding 실패: {str(e)}")
    

# width와 height는 해상도 설정할 값임 (픽셀 단위)