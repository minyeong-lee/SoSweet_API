from .konlpy import nlp_bp  # 대화 분석 블루프린트 가져오기
from .emo_analyze import emo_analyze_bp

# __all__을 통해 외부에서 import할 수 있는 모듈 정의
__all__ = ["nlp_bp"]
__all__ = ['emo_analyze_bp'] 