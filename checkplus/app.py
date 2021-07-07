import os
import subprocess
import re
import base64
import sys

from flask import render_template, request, session
from flask_lambda import FlaskLambda

SITE_CODE = os.environ['SITE_CODE']
SITE_PASSWORD = os.environ['SITE_PASSWORD']
API_GATEWAY_URL = os.environ['API_GATEWAY_URL']

app = FlaskLambda(__name__)
app.secret_key = os.urandom(24)


#####################################################################################
#    페이지명 : 체크플러스 - 메인 호출 페이지
#####################################################################################
@app.route('/checkplus_main')
def checkplus_main():

    # NICE평가정보에서 발급한 안심본인인증 서비스 개발정보 (사이트코드, 사이트패스워드)
    sitecode = SITE_CODE
    sitepasswd = SITE_PASSWORD
    cb_encode_path = './CPClient_64bit'

    # 인증성공 시 결과데이터 받는 리턴URL (방식:절대주소, 필수항목:프로토콜)
    returnurl = f'https://{API_GATEWAY_URL}/checkplus_success'

    # 인증실패 시 결과데이터 받는 리턴URL (방식:절대주소, 필수항목:프로토콜)
    errorurl = f'https://{API_GATEWAY_URL}/checkplus_fail'

    # 팝업화면 설정
    authtype = ''  # 인증타입 (공백:기본 선택화면, X:공인인증서, M:핸드폰, C:카드)
    popgubun = 'Y'  # 취소버튼 (Y:있음, N:없음)
    customize = ''  # 화면타입 (공백:PC페이지, Mobile:모바일페이지)
    gender = ''  # 성별설정 (공백:기본 선택화면, 0:여자, 1:남자) 특정 및 데이타 위변조 검사에 이용하는 변수 (인증결과와 함께 전달됨)

    # 요청번호 초기화
    # :세션에 저장해 사용자
    reqseq = ''

    # 인증요청 암호화 데이터 초기화
    enc_data = ''

    # 처리결과 메세지 초기화
    returnMsg = ''

    # 요청번호 생성
    try:
        # 파이썬 버전이 3.5 미만인 경우 check_output 함수 이용
        #  reqseq = subprocess.check_output([cb_encode_path, 'SEQ', sitecode])
        reqseq = subprocess.run([cb_encode_path, 'SEQ', sitecode], capture_output=True, encoding='euc-kr').stdout
    except subprocess.CalledProcessError as e:
        # check_output 함수 이용하는 경우 1 이외의 결과는 에러로 처리됨
        reqseq = e.output.decode('euc-kr')
        print('cmd:', e.cmd, '\n output:', e.output)
    finally:
        print('reqseq:', reqseq)

    # 요청번호 세션에 저장 (세션 이용하지 않는 경우 생략)
    session['REQ_SEQ'] = reqseq

    # plain 데이터 생성 (형식 수정불가)
    plaindata = '7:REQ_SEQ' + str(len(reqseq)) + ':' + reqseq + '8:SITECODE' + str(
        len(sitecode)) + ':' + sitecode + '9:AUTH_TYPE' + str(len(authtype)) + ':' + authtype + '7:RTN_URL' + str(
        len(returnurl)) + ':' + returnurl + '7:ERR_URL' + str(len(errorurl)) + ':' + errorurl + '11:POPUP_GUBUN' + str(
        len(popgubun)) + ':' + popgubun + '9:CUSTOMIZE' + str(len(customize)) + ':' + customize + '6:GENDER' + str(
        len(gender)) + ':' + gender

    # 인증요청 암호화 데이터 생성
    try:
        # 파이썬 버전이 3.5 미만인 경우 check_output 함수 이용
        #  enc_data = subprocess.check_output([cb_encode_path, 'ENC', sitecode, sitepasswd, plaindata])
        enc_data = subprocess.run([cb_encode_path, 'ENC', sitecode, sitepasswd, plaindata], capture_output=True,
                                  encoding='euc-kr').stdout
    except subprocess.CalledProcessError as e:
        # check_output 함수 이용하는 경우 1 이외의 결과는 에러로 처리됨
        enc_data = e.output.decode('euc-kr')
        print('cmd:', e.cmd, '\n output:\n', e.output)
    finally:
        print('enc_data:\n', enc_data)

    # 화면 렌더링 변수 설정
    render_params = {}
    render_params['enc_data'] = enc_data
    render_params['returnMsg'] = returnMsg
    return render_template('checkplus_main.html', **render_params)


#####################################################################################
#    페이지명 : 체크플러스 - 성공 결과 페이지
#####################################################################################
@app.route('/checkplus_success', methods=['POST', 'GET'])
def checkplus_success():
    # NICE평가정보에서 발급한 안심본인인증 서비스 개발정보 (사이트코드, 사이트패스워드)
    sitecode = SITE_CODE
    sitepasswd = SITE_PASSWORD

    cb_encode_path = './CPClient_64bit'

    # CP요청번호 초기화
    reqseq = ''

    # 인증결과 암호화 데이터 초기화
    enc_data = ''

    # 인증결과 복호화 데이터 초기화
    plaindata = ''

    # 처리결과 메세지 초기화
    returnMsg = ''

    # 인증결과 복호화 시간 초기화
    ciphertime = ''

    # 인증결과 데이터 초기화
    requestnumber = ''  # 요청번호
    responsenumber = ''  # 본인인증 응답코드 (응답코드 문서 참조)
    authtype = ''  # 인증수단 (M:휴대폰, c:카드, X:인증서, P:삼성패스)
    name = ''  # 이름 (EUC-KR)
    utfname = ''  # 이름 (UTF-8, URL인코딩)
    birthdate = ''  # 생년월일 (YYYYMMDD)
    gender = ''  # 성별 코드 (0:여성, 1:남성)
    nationalinfo = ''  # 내/외국인 정보 (0:내국인, 1:외국인)
    dupinfo = ''  # 중복가입확인값 (64Byte, 개인식별값, DI:Duplicate Info)
    conninfo = ''  # 연계정보확인값 (88Byte, 개인식별값, CI:Connecting Info)
    mobileno = ''  # 휴대폰번호
    mobileco = ''  # 통신사 (가이드 참조)

    # NICE에서 전달받은 인증결과 암호화 데이터 취득
    try:
        # GET 요청 처리
        if request.method == 'GET':
            print('checkplus_success:GET')
            enc_data = request.args.get('EncodeData', default='', type=str)
        # POST 요청 처리
        else:
            print('checkplus_success:POST')
            result = request.form
            enc_data = result['EncodeData']
    except:
        print("ERR:", sys.exc_info()[0])
    finally:
        print('enc_data:\n', enc_data)

    ################################### 문자열 점검 ######################################
    errChars = re.findall('[^0-9a-zA-Z+/=]', enc_data)
    if len(re.findall('[^0-9a-zA-Z+/=]', enc_data)) > 0:
        print("errChars=", errChars)
        return ('문자열오류: 입력값 확인이 필요합니다')
    if (base64.b64encode(base64.b64decode(enc_data))).decode() != enc_data:
        return ('변환오류: 입력값 확인이 필요합니다')
    #####################################################################################

    # checkplus_main에서 세션에 저장한 요청번호 취득 (세션 이용하지 않는 경우 생략)
    try:
        reqseq = session['REQ_SEQ']
    except Exception as e:
        print('ERR: reqseq=', reqseq)
    finally:
        print('reqseq:', reqseq)

    if enc_data != '':
        # 인증결과 암호화 데이터 복호화 처리
        try:
            # 파이썬 버전이 3.5 미만인 경우 check_output 함수 이용
            #  plaindata = subprocess.check_output([cb_encode_path, 'DEC', sitecode, sitepasswd, enc_data])
            plaindata = subprocess.run([cb_encode_path, 'DEC', sitecode, sitepasswd, enc_data], capture_output=True,
                                       encoding='euc-kr').stdout
        except subprocess.CalledProcessError as e:
            # check_output 함수 이용하는 경우 1 이외의 결과는 에러로 처리됨
            plaindata = e.output.decode('euc-kr')
            print('cmd:', e.cmd, '\n output:\n', e.output)
        finally:
            print('plaindata:\n', plaindata)
    else:
        returnMsg = '처리할 암호화 데이타가 없습니다.'

    # 복호화 처리결과 코드 확인
    if plaindata == -1:
        returnMsg = '암/복호화 시스템 오류'
    elif plaindata == -4:
        returnMsg = '복호화 처리 오류'
    elif plaindata == -5:
        returnMsg = 'HASH값 불일치 - 복호화 데이터는 리턴됨'
    elif plaindata == -6:
        returnMsg = '복호화 데이터 오류'
    elif plaindata == -9:
        returnMsg = '입력값 오류'
    elif plaindata == -12:
        returnMsg = '사이트 비밀번호 오류'
    else:
        # 요청번호 추출
        requestnumber = GetValue(plaindata, 'REQ_SEQ')

        # 데이터 위변조 검사 (세션 이용하지 않는 경우 분기처리 생략)
        # : checkplus_main에서 세션에 저장한 요청번호와 결과 데이터의 추출값 비교하는 추가적인 보안처리
        # if reqseq == requestnumber:
        # 인증결과 복호화 시간 생성 (생략불가)
        try:
            # 파이썬 버전이 3.5 미만인 경우 check_output 함수 이용
            #  ciphertime = subprocess.check_output([cb_encode_path, 'CTS', sitecode, sitepasswd, enc_data])
            ciphertime = subprocess.run([cb_encode_path, 'CTS', sitecode, sitepasswd, enc_data], capture_output=True,
                                        encoding='euc-kr').stdout
        except subprocess.CalledProcessError as e:
            # check_output 함수 이용하는 경우 1 이외의 결과는 에러로 처리됨
            ciphertime = e.output.decode('euc-kr')
            print('cmd:', e.cmd, '\n output:', e.output)
        finally:
            print('ciphertime:', ciphertime)
        # else:
        #   returnMsg = '세션 불일치 오류'

    # 인증결과 복호화 시간 확인
    if ciphertime != '':
        #####################################################################################
        # 인증결과 데이터 추출
        # : 결과 데이터의 통신이 필요한 경우 암호화 데이터(EncodeData)로 통신 후 복호화 해주십시오
        #   복호화된 데이터를 통신하는 경우 데이터 유출에 주의해주십시오 (세션처리 권장)
        #####################################################################################

        responsenumber = GetValue(plaindata, 'RES_SEQ')
        authtype = GetValue(plaindata, 'AUTH_TYPE')
        name = GetValue(plaindata, 'NAME')
        utfname = GetValue(plaindata, 'UTF8_NAME')
        birthdate = GetValue(plaindata, 'BIRTHDATE')
        gender = GetValue(plaindata, 'GENDER')
        nationalinfo = GetValue(plaindata, 'NATIONALINFO')
        dupinfo = GetValue(plaindata, 'DI')
        conninfo = GetValue(plaindata, 'CI')
        mobileno = GetValue(plaindata, 'MOBILE_NO')
        mobileco = GetValue(plaindata, 'MOBILE_CO')

        print('responsenumber:' + responsenumber)
        print('authtype:' + authtype)
        print('name:' + name)
        print('utfname:' + utfname)
        print('birthdate:' + birthdate)
        print('gender:' + gender)
        print('nationalinfo:' + nationalinfo)
        print('dupinfo:' + dupinfo)
        print('conninfo:' + conninfo)
        print('mobileno:' + mobileno)
        print('mobileco:' + mobileco)

        returnMsg = "사용자 인증 성공"

    # 화면 렌더링 변수 설정
    render_params = {}
    render_params['plaindata'] = plaindata
    render_params['returnMsg'] = returnMsg
    render_params['ciphertime'] = ciphertime
    render_params['requestnumber'] = requestnumber
    render_params['responsenumber'] = responsenumber
    render_params['authtype'] = authtype
    render_params['name'] = name
    render_params['utfname'] = utfname
    render_params['birthdate'] = birthdate
    render_params['gender'] = gender
    render_params['nationalinfo'] = nationalinfo
    render_params['dupinfo'] = dupinfo
    render_params['conninfo'] = conninfo
    render_params['mobileno'] = mobileno
    render_params['mobileco'] = mobileco
    return render_template("checkplus_success.html", **render_params)


#####################################################################################
#    페이지명 : 체크플러스 - 실패 결과 페이지
#####################################################################################
@app.route('/checkplus_fail', methods=['POST', 'GET'])
def checkplus_fail():
    # NICE평가정보에서 발급한 안심본인인증 서비스 개발정보 (사이트코드, 사이트패스워드)
    sitecode = SITE_CODE
    sitepasswd = SITE_PASSWORD

    cb_encode_path = './CPClient_64bit'

    # 인증결과 암호화 데이터 초기화
    enc_data = ''

    # 인증결과 복호화 데이터 초기화
    plaindata = ''

    # 처리결과 메세지 초기화
    returnMsg = ''

    # 인증결과 복호화 시간 초기화
    ciphertime = ''

    # 인증결과 데이터 초기화
    requestnumber = ''  # 요청번호
    errcode = ''  # 본인인증 응답코드 (응답코드 문서 참조)
    authtype = ''  # 인증수단 (M:휴대폰, c:카드, X:인증서, P:삼성패스)

    # NICE에서 전달받은 인증결과 암호화 데이터 취득
    result = request.form
    try:
        enc_data = result['EncodeData']
    except KeyError as e:
        print(e)
    finally:
        print('enc_data:\n', enc_data)

        ################################### 문자열 점검 ######################################
    errChars = re.findall('[^0-9a-zA-Z+/=]', enc_data)
    if len(re.findall('[^0-9a-zA-Z+/=]', enc_data)) > 0:
        print("errChars=", errChars)
        return ('문자열오류: 입력값 확인이 필요합니다')
    if (base64.b64encode(base64.b64decode(enc_data))).decode() != enc_data:
        return ('변환오류: 입력값 확인이 필요합니다')
    #####################################################################################

    if enc_data != '':
        try:
            # 인증결과 암호화 데이터 복호화 처리
            #  plaindata = subprocess.check_output([cb_encode_path, 'DEC', sitecode, sitepasswd, enc_data])
            plaindata = subprocess.run([cb_encode_path, 'DEC', sitecode, sitepasswd, enc_data], capture_output=True,
                                       encoding='euc-kr').stdout
        except subprocess.CalledProcessError as e:
            # check_output 함수 이용하는 경우 1 이외의 결과는 에러로 처리됨
            plaindata = e.output.decode('euc-kr')
            print('cmd:', e.cmd, '\n output:\n', e.output)
        finally:
            print('plaindata:\n', plaindata)
    else:
        returnMsg = '처리할 암호화 데이타가 없습니다.'

    # 복호화 처리결과 코드 확인
    if plaindata == -1:
        returnMsg = '암/복호화 시스템 오류'
    elif plaindata == -4:
        returnMsg = '복호화 처리 오류'
    elif plaindata == -5:
        returnMsg = 'HASH값 불일치 - 복호화 데이터는 리턴됨'
    elif plaindata == -6:
        returnMsg = '복호화 데이터 오류'
    elif plaindata == -9:
        returnMsg = '입력값 오류'
    elif plaindata == -12:
        returnMsg = '사이트 비밀번호 오류'
    else:
        # 인증결과 복호화 시간 생성
        try:
            # 파이썬 버전이 3.5 미만인 경우 check_output 함수 이용
            #  ciphertime = subprocess.check_output([cb_encode_path, 'CTS', sitecode, sitepasswd, enc_data])
            ciphertime = subprocess.run([cb_encode_path, 'CTS', sitecode, sitepasswd, enc_data], capture_output=True,
                                        encoding='euc-kr').stdout
        except subprocess.CalledProcessError as e:
            # check_output 함수 이용하는 경우 1 이외의 결과는 에러로 처리됨
            ciphertime = e.output.decode('euc-kr')
            print('cmd:', e.cmd, '\n output:', e.output)
        finally:
            print('ciphertime:', ciphertime)

        # 인증결과 데이터 추출
        requestnumber = GetValue(plaindata, 'REQ_SEQ')
        errcode = GetValue(plaindata, 'ERR_CODE')
        authtype = GetValue(plaindata, 'AUTH_TYPE')

        print('requestnumber:' + requestnumber)
        print('errcode:' + errcode)
        print('authtype:' + authtype)

    # 화면 렌더링 변수 설정
    render_params = {}
    render_params['plaindata'] = plaindata
    render_params['returnMsg'] = returnMsg
    render_params['ciphertime'] = ciphertime
    render_params['requestnumber'] = requestnumber
    render_params['errcode'] = errcode
    render_params['authtype'] = authtype
    return render_template("checkplus_fail.html", **render_params)


# 인증결과 데이터 추출 함수
def GetValue(plaindata, key):
    value = ''
    keyIndex = -1
    valLen = 0

    # 복호화 데이터 분할
    arrData = plaindata.split(':')
    cnt = len(arrData)
    for i in range(cnt):
        item = arrData[i]
        itemKey = re.sub('[\d]+$', '', item)

        # 키값 검색
        if itemKey == key:
            keyIndex = i

            # 데이터 길이값 추출
            valLen = int(item.replace(key, '', 1))

            if key != 'NAME':
                # 실제 데이터 추출
                value = arrData[keyIndex + 1][:valLen]
            else:
                # 이름 데이터 추출 (한글 깨짐 대응)
                value = re.sub('[\d]+$', '', arrData[keyIndex + 1])

            break

    return value
