import numpy as np
import cv2
import base64

def decode_frame_func(frame):
    # Base64 또는 bytes 데이터를 OpenCV 이미지 타입으로 변환
    if isinstance(frame, str):
        # Base64 문자열 디코딩
        frame_bytes = base64.b64decode(frame.split(',')[1] if ',' in frame else frame)
    elif isinstance(frame, bytes):
        frame_bytes = frame
    else:
        raise ValueError("Unsupported frame format. Expected str or bytes.")

    # numpy array 변환 및 디코딩
    np_array = np.frombuffer(frame_bytes, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode frame to image")
    
    return image
