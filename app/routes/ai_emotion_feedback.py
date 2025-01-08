from flask import Blueprint, request, jsonify
import json
import os
from app.utils.feedback_utils import calculate_emo_result, convert_to_korean

ai_emo_feedback_bp = Blueprint('ai_emotion_feedback', __name__)

@ai_emo_feedback_bp.route('/', methods=[''])
def ai_emo_feedback():
    
    
    return None