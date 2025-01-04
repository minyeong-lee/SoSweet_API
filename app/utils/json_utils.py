import os
import json

def save_to_json(user_id, data):
    # 감정 분석 데이터를 JSON 파일에 저장
    file_path = f"{user_id}_data.json"

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
