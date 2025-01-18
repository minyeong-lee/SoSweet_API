from flask import Blueprint, request, jsonify
from kiwipiepy import Kiwi
from kiwipiepy.utils import Stopwords

nlp_bp = Blueprint('nlp', __name__)
kiwi = Kiwi(model_type='sbg')

@nlp_bp.route('/api/nlp', methods=['POST', 'OPTIONS'])
def nlp():
    if request.method == 'OPTIONS':
        return '', 204
    
    #한국인이 자주 쓰는 filler word: '이건'의 경우 '이거/NP' + 'ㄴ/JX'로 잡힘
    kiwi.add_user_word('이건', 'IC')
    
    #발화에 대한 키워드 dict
    keyword_dict = dict()
    
    #불용어 관리
    stopwords = Stopwords()
    
    stopwords.add(('최근', 'NNG'))
    stopwords.add(('요즘', 'NNG'))
    stopwords.add(('다음', 'NNG'))
    stopwords.add(('장르', 'NNG'))
    stopwords.add(('가이드', 'NNG'))
    stopwords.add(('메세지', 'NNG'))
    stopwords.add(('안녕', 'NNG'))
    stopwords.add(('준비', 'NNG'))
    stopwords.add(('감명', 'NNG'))
    stopwords.add(('추천', 'NNG'))
    stopwords.add(('실시간', 'NNG'))
    
    response = ''
    data = request.json
    script = data.get('script', '')
    filler_count = 0
    noword_count = 0
    
    noword_flag = False
    filler_flag = False
    noend_flag = False
    nopolite_flag = False
    
    if not script:
        return jsonify({"error": "스크립트가 넘어오지 않음"}), 400
    
    Tokens = kiwi.tokenize(script, stopwords = stopwords)
    
    for temp in Tokens :
        if temp.form in ['음', '어'] and temp.tag == 'IC': #말을 더듬는 경우
            noword_count += 1
        if temp.form in ['아니', '근데', '이건', '진짜', '이거', '좀']: #한국인이 많이 쓰는 filler word
            filler_count += 1
        if temp.tag == 'NNG': # 키워드 세기
            if temp.form not in keyword_dict:
                keyword_dict[temp.form] = 1
            else:
                keyword_dict[temp.form] += 1
            
    if (noword_count > 1):
        response += "말 더듬기 "
        noword_count = 0
        noword_flag = True
    if (filler_count > 4):
        response += "지나친 추임새 "
        filler_count = 0
        filler_flag = True
                
        
    if Tokens[-1].tag != 'EF' and Tokens[-1].tag != 'JX': # 문장 종결 확인: '취미요'같은 경우 '요'를 보조사(JX)로 잡음
        response += "종결되지 않은 문장\n"
        noend_flag = True
    else:
        if Tokens[-1].form not in ['요', '죠', '세요', '에요', '어요', '네요', '나요'] and Tokens[-1].len != 3:
            response += "존댓말 사용 안함\n"
            nopolite_flag = True
            
    print(keyword_dict)

    
    return jsonify({"noword_flag": noword_flag, "filler_flag": filler_flag, "noend_flag": noend_flag, "nopolite_flag": nopolite_flag, "keyword_dict": keyword_dict}), 200