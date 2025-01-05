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
        return decoded_frame
    except Exception as e:
        raise ValueError(f"Frame decoding 실패: {str(e)}")