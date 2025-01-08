from flask import Blueprint, request, jsonify
import json
import os


ai_act_feedback_bp = Blueprint('ai_action_feedback', __name__)

@ai_act_feedback_bp.route('/api/feedback/faceinfo', methods=['POST'])
def get_act_feedback():
    
    
    
    return None