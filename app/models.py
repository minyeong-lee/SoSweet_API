from app.utils.db import get_db
from datetime import datetime, timezone

def save_emotion(user_id, frame, emotion_scores, dominant_emotion):
    db = get_db()
    emotions_collection = db['emotions']
    
    data = {
        "frame": frame,
        "emotion_scores": emotion_scores,
        "dominant_emotion": dominant_emotion,
        "timestamp": datetime.now(timezone.utc)
    }

    emotions_collection.update_one(
        {"user_id": user_id},
        {"$push": {"emotions": data}},
        upsert=True
    )
