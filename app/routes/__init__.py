from .konlpy import nlp_bp  # 대화 분석 블루프린트 가져오기
from .frame_analyze import frame_analyze_bp
from .emotion_feedback import emo_feedback_bp
from .action_feedback import act_feedback_bp
from .ai_action_feedback import ai_act_feedback_bp
from .ai_emotion_feedback import ai_emo_feedback_bp
from .ai_action_feedback import ai_act_feedback_bp

__all__ = [
    "nlp_bp", 
    "frame_analyze_bp", 
    "emo_feedback_bp", 
    "act_feedback_bp",
    "ai_act_feedback_bp",
    "ai_emo_feedback_bp",
    "ai_frame_analyze_bp",
    ]
