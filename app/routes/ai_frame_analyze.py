from flask import Blueprint, request, jsonify
import json
import os


ai_frame_analyze_bp = Blueprint('ai_frame_analyze', __name__)

@ai_frame_analyze_bp.route('/api/feedback/faceinfo', methods=['POST'])
def ai_frame_analyze():
    
    
    return None