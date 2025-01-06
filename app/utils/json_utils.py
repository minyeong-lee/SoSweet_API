import os
import json

# 공통 JSON 저장 함수
def save_to_json(directory:str, filename: str, data: dict):
    # 디렉토리가 없다면 생성하기
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, f"{filename}.json")
    
    # 기존 데이터 불러오기
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = []
    
    # 새 데이터 추가
    existing_data.append(data)
    
    # JSON 파일 저장
    with open(file_path, "w") as f:
        json.dump(existing_data, f, indent=4)


# actions 저장 함수
def save_action_data(user_id: str, data: dict):
    save_to_json("analysis_data/actions", user_id, data)

# emotions 저장 함수
def save_emotion_data(room_id: str, user_id: str, data: dict):
    save_to_json(f"analysis_data/emotions/{room_id}", user_id, data)