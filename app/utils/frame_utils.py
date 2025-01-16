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
            
        if decoded_frame.size == 0:  # 빈 배열 체크
            raise ValueError("빈 이미지 데이터")
        
        # print(f"[디버그] 디코딩된 이미지 해상도: {decoded_frame.shape}")
        return decoded_frame
        
    except Exception as e:
        raise ValueError(f"Frame decoding 실패: {str(e)}")
    

# width와 height는 해상도 설정할 값임 (픽셀 단위)

# date_url 형태로 클라이언트에서 들어온 데이터를 Base64 decoding 후 OpenCV BGR 이미지(ndarray)로 반환한다