# ============================================
# 🎬 어제의 박스오피스
# KOBIS Open API + Streamlit
# ============================================

import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ============================================
# 1. 페이지 설정
# ============================================

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)


# ============================================
# 2. 제목
# ============================================

st.title("🎬 어제의 박스오피스")

st.caption(
    "한국영화진흥위원회(KOBIS) 일별 박스오피스 데이터를 "
    "한국 시간 기준 '어제' 날짜로 조회합니다."
)


# ============================================
# 3. 한국 시간 기준 '어제' 날짜 계산
# ============================================

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)

yesterday_kst = now_kst - timedelta(days=1)

# KOBIS API용 날짜
target_date = yesterday_kst.strftime("%Y%m%d")

# 화면 표시용 날짜
display_date = yesterday_kst.strftime("%Y년 %m월 %d일")


# ============================================
# 4. KOBIS API 주소
# ============================================

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# ============================================
# 5. KOBIS API 호출 함수
# ============================================

@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):

    # ----------------------------------------
    # Streamlit Secrets에서 인증키 가져오기
    # ----------------------------------------

    try:
        api_key = st.secrets["KOBIS_KEY"]

    except Exception:

        return {
            "success": False,
            "error_type": "secret",
            "message": (
                "KOBIS_KEY를 찾을 수 없습니다."
            ),
            "data": None
        }


    # ----------------------------------------
    # API 요청값
    # ----------------------------------------

    params = {
        "key": api_key,
        "targetDt": target_dt
    }


    # ----------------------------------------
    # API 요청
    # ----------------------------------------

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error_type": "network",
            "message": (
                "KOBIS API 요청 시간이 초과되었습니다. "
                "잠시 후 다시 실행해 주세요."
            ),
            "data": None
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error_type": "network",
            "message": (
                "KOBIS API에 접속하지 못했습니다."
            ),
            "data": None
        }


    # ========================================
    # 6. JSON 데이터 변환
    # ========================================

    try:

        result = response.json()

    except ValueError:

        return {
            "success": False,
            "error_type": "json",
            "message": (
                "KOBIS API가 올바른 JSON 데이터를 "
                "반환하지 않았습니다."
            ),
            "data": None
        }


    # ========================================
    # 7. KOBIS API 오류 확인
    # ========================================

    if "faultInfo" in result:

        fault_info = result["faultInfo"]

        if isinstance(fault_info, dict):

            fault_code = fault_info.get(
                "faultCode",
                ""
            )

            fault_string = fault_info.get(
                "message",
                ""
            )

            if not fault_string:

                fault_string = fault_info.get(
                    "faultString",
                    ""
                )

            error_message = (
                "KOBIS API 오류가 발생했습니다."
            )

            if fault_code:

                error_message += (
                    f"\n\n오류 코드: {fault_code}"
                )

            if fault_string:

                error_message += (
                    f"\n\n오류 내용: {fault_string}"
                )

        else:

            error_message = (
                "KOBIS API에서 오류를 반환했습니다.\n\n"
                f"{fault_info}"
            )


        return {
            "success": False,
            "error_type": "fault",
            "message": error_message,
            "data": None
        }


    # ========================================
    # 8. boxOfficeResult 확인
    # ========================================

    boxoffice_result = result.get(
        "boxOfficeResult"
    )

    if not boxoffice_result:

        return {
            "success": False,
            "error_type": "empty_result",
            "message": (
                "API 응답에 boxOfficeResult가 없습니다."
            ),
            "data": None
        }


    # ========================================
    # 9. 영화 목록 가져오기
    # ========================================

    movie_list = boxoffice_result.get(
        "dailyBoxOfficeList",
        []
    )

    if not movie_list:

        return {
            "success": False,
            "error_type": "empty",
            "message": (
                "해당 날짜의 박스오피스 데이터가 없습니다."
            ),
            "data": None
        }


    # ========================================
    # 정상 결과
    # ========================================

    return {
        "success": True,
        "error_type": None,
        "message": None,
        "data": movie_list
    }


# ============================================
# 10. API 실행
# ============================================

result = get_boxoffice(target_date)


# ============================================
# 11. 오류 처리
# ============================================

if not result["success"]:

    st.error(
        "박스오피스 데이터를 불러오지 못했습니다."
    )

    st.warning(
        result["message"]
    )


    # ----------------------------------------
    # Secrets 오류
    # ----------------------------------------

    if result["error_type"] == "secret":

        st.info(
            """
            ### 🔐 KOBIS 인증키 확인

            Streamlit Cloud에서

            **Settings → Secrets**

            로 들어간 뒤 아래처럼 입력하세요.

            ```toml
            KOBIS_KEY = "본인의_실제_KOBIS_인증키"
            ```

            ⚠️ 실제 인증키는 `main.py`에 입력하지 않습니다.
            """
        )


    # ----------------------------------------
    # API 인증 오류
    # ----------------------------------------

    elif result["error_type"] == "fault":

        st.info(
            """
            ### 🔑 KOBIS 인증키를 확인하세요.

            KOBIS에서 인증키가 잘못된 경우
            `faultInfo` 오류가 반환될 수 있습니다.
            """
        )


    # ----------------------------------------
    # 데이터 없음
    # ----------------------------------------

    elif result["error_type"] == "empty":

        st.info(
            f"""
            ### 📅 데이터 확인

            현재 조회 날짜는 **{display_date}**입니다.

            해당 날짜의 KOBIS 일별 박스오피스
            데이터가 아직 없을 수 있습니다.
            """
        )


    # ----------------------------------------
    # 네트워크 오류
    # ----------------------------------------

    elif result["error_type"] == "network":

        st.info(
            """
            ### 🌐 네트워크 확인

            인터넷 연결이나 KOBIS API 서버 상태를
            확인한 후 다시 실행해 주세요.
            """
        )


    st.stop()


# ============================================
# 12. DataFrame 생성
# ============================================

movie_list = result["data"]

df = pd.DataFrame(movie_list)


# ============================================
# 13. 숫자 데이터 숫자로 변환
# ====
