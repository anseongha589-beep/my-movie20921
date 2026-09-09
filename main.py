# ============================================
# 🎬 어제의 박스오피스
# KOBIS Open API + Streamlit
# ============================================

import streamlit as st
import pandas as pd
import requests
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
# 3. 한국 시간 기준으로 어제 날짜 계산
# ============================================

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)

# 오늘에서 하루 빼기
yesterday_kst = now_kst - timedelta(days=1)

# KOBIS API용 날짜
# 예: 20260908
target_date = yesterday_kst.strftime("%Y%m%d")

# 화면 표시용 날짜
# 예: 2026년 09월 08일
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
    # API 호출
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

    # ----------------------------------------
    # JSON 변환
    # ----------------------------------------

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
    # 6. KOBIS API 오류 확인
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
    # 7. boxOfficeResult 확인
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
    # 8. 영화 목록 가져오기
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
# 9. API 호출
# ============================================

result = get_boxoffice(target_date)


# ============================================
# 10. API 오류 처리
# ============================================

if not result["success"]:

    st.error(
        "박스오피스 데이터를 불러오지 못했습니다."
    )

    st.warning(
        result["message"]
    )

    if result["error_type"] == "secret":

        st.info(
            """
            **Streamlit Cloud Secrets를 확인하세요.**

            Streamlit Cloud의

            **Settings → Secrets**

            에서 아래처럼 입력해야 합니다.

            ```toml
            KOBIS_KEY = "본인의_실제_인증키"
            ```

            인증키 자체는 `main.py`에 입력하지 않습니다.
            """
        )

    elif result["error_type"] == "fault":

        st.info(
            """
            **KOBIS 인증키를 확인하세요.**

            KOBIS에서 인증키가 잘못된 경우
            `faultInfo` 오류를 반환할 수 있습니다.
            """
        )

    elif result["error_type"] == "empty":

        st.info(
            f"""
            현재 조회 날짜는 **{display_date}**입니다.

            해당 날짜의 KOBIS 일별 박스오피스
            데이터가 아직 없을 수 있습니다.
            """
        )

    elif result["error_type"] == "network":

        st.info(
            """
            인터넷 연결 또는 KOBIS API 서버 상태를
            확인한 후 다시 실행해 주세요.
            """
        )

    st.stop()


# ============================================
# 11. 데이터를 DataFrame으로 변환
# ============================================

movie_list = result["data"]

df = pd.DataFrame(movie_list)


# ============================================
# 12. 숫자 데이터 숫자로 변환
# ============================================

numeric_columns = [
    "rank",
    "rankInten",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
    "showCnt"
]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0).astype(int)


# ============================================
# 13. 전체 박스오피스 순위 정렬
# 1위 → 2위 → 3위 ...
# ============================================

df = (
    df.sort_values(
        by="rank",
        ascending=True
    )
    .reset_index(drop=True)
)


# ============================================
# 14. 1위 영화 정보
# ============================================

first_movie = df.iloc[0]

first_movie_name = first_movie["movieNm"]

first_audience = int(
    first_movie["audiCnt"]
)

first_total_audience = int(
    first_movie["audiAcc"]
)

first_screen_count = int(
    first_movie["scrnCnt"]
)


# ============================================
# 15. 조회 날짜
# ============================================

st.subheader(
    f"📅 {display_date} 박스오피스"
)

st.caption(
    f"KOBIS 조회 날짜: {target_date} · "
    f"현재 한국 시간: "
    f"{now_kst.strftime('%Y-%m-%d %H:%M')}"
)


# ============================================
# 16. 1위 영화
# ============================================

st.markdown(
    f"## 🏆 1위 · {first_movie_name}"
)


# ============================================
# 17. 주요 정보
# ============================================

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        label="🎟️ 일일 관객수",
        value=f"{first_audience:,}명"
    )


with col2:

    st.metric(
        label="👥 누적 관객수",
        value=f"{first_total_audience:,}명"
    )


with col3:

    st.metric(
        label="🎞️ 스크린수",
        value=f"{first_screen_count:,}개"
    )


st.divider()


# ============================================
# 18. 관객수 상위 5편
# ============================================

st.subheader("📊 관객수 상위 5편")


# 먼저 관객수가 많은 순서로 상위 5편을 뽑고
# 그 다음 그래프에서는 오름차순으로 정렬합니다.

top5 = (
    df.sort_values(
        by="audiCnt",
        ascending=False
    )
    .head(5)
    .sort_values(
        by="audiCnt",
        ascending=True
    )
    .copy()
)


# ============================================
# 19. 그래프 데이터
# ============================================

chart_data = top5[
    ["movieNm", "audiCnt"]
].set_index(
    "movieNm"
)


# ============================================
# 20. 막대그래프
# 오름차순
# 적은 관객수 → 많은 관객수
# ============================================

st.bar_chart(
    chart_data,
    x_label="영화",
    y_label="관객수"
)


st.caption(
    "※ 상위 5편을 선정한 뒤 관객수가 적은 영화부터 "
    "많은 영화 순으로 표시합니다."
)


st.divider()


# ============================================
# 21. 전체 박스오피스
# ============================================

st.subheader("🎬 전체 박스오피스")


# ============================================
# 22. 표에 표시할 데이터
# ============================================

table_df = df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()


# ============================================
# 23. 컬럼 이름 변경
# ============================================

table_df = table_df.rename(
    columns={
        "rank": "순위",
        "movieNm": "영화명",
        "openDt": "개봉일",
        "audiCnt": "관객수",
        "audiAcc": "누적관객",
        "scrnCnt": "스크린수"
    }
)


# ============================================
# 24. 데이터 표 표시
# ============================================

st.dataframe(
    table_df.style.format(
        {
            "순위": "{:,.0f}",
            "관객수": "{:,.0f}",
            "누적관객": "{:,.0f}",
            "스크린수": "{:,.0f}"
        }
    ),
    use_container_width=True,
    hide_index=True
)


# ============================================
# 25. 데이터 안내
# ============================================

st.caption(
    "※ 관객수·누적관객·스크린수는 KOBIS API 데이터를 "
    "숫자로 변환하여 표시합니다."
)

st.caption(
    "※ 같은 날짜의 API 결과는 약 1시간 동안 캐시됩니다."
)
