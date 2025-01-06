from flask import Blueprint, request, jsonify
from kiwipiepy import Kiwi

nlp_bp = Blueprint('nlp', __name__)
kiwi = Kiwi(model_type='sbg')

@nlp_bp.route('/api/nlp', methods=['POST', 'OPTIONS'])
def nlp():
    if request.method == 'OPTIONS':
        return '', 204
        
    response = '정상적인 발화\n'
    data = request.json
    script = data.get('script', '')
    
    if not script:
        return jsonify({"error": "스크립트가 넘어오지 않음"}), 400
    
    Tokens = kiwi.tokenize(script)
    if Tokens[-1].tag != 'EF': # 문장 종결 확인
        response = "종결되지 않은 문장\n"
    else:
        if Tokens[-1].form not in ['요', '죠', '세요', '에요', '어요']:
            response = "존댓말을 사용하지 않음\n"
    
    return jsonify({"message": response}), 200