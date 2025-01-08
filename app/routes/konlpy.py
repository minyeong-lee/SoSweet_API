from flask import Blueprint, request, jsonify
from kiwipiepy import Kiwi

nlp_bp = Blueprint('nlp', __name__)
kiwi = Kiwi(model_type='sbg')

@nlp_bp.route('/api/nlp', methods=['POST', 'OPTIONS'])
def nlp():
    if request.method == 'OPTIONS':
        return '', 204
        
    response = ''
    data = request.json
    script = data.get('script', '')
    filler_count = 0
    
    if not script:
        return jsonify({"error": "스크립트가 넘어오지 않음"}), 400
    
    Tokens = kiwi.tokenize(script)
    
    for temp in Tokens :
        if temp.form in ['어'] and temp.tag == 'IC': #filler words를 많이 반복한 경우우
            filler_count += 1
            if (filler_count > 2):
                response += "과도한 추임새. 추임새가 3회 이상 반복되었습니다.\n"
                filler_count = 0
                break
        
    if Tokens[-1].tag != 'EF': # 문장 종결 확인
        response += "종결되지 않은 문장\n"
    
    else:
        if Tokens[-1].form not in ['요', '죠', '세요', '에요', '어요', '네요'] and Tokens[-1].len != 3:
            response += "존댓말을 사용하지 않음\n"
            

    
    return jsonify({"message": response}), 200