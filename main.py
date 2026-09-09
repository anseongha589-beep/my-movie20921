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
# 3. 한국 시간 기준 '어제' 날짜 계산
# ============================================

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)

yesterday_kst = now_kst - timedelta(days=1)

target_date = yesterday_kst.strftime("%Y%m%d")

display_date = yesterday_kst.strftime("%Y년 %m월 %d일")


# ============================================
# 4. KOBIS API 주소
# ============================================

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# ============================================
# 5. KOBIS API 호출
# ============================================

@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):

    # ----------------------------------------
    # 인증키 가져오기
    # ----------------------------------------

    try:
        api_key = st.secrets["KOBIS_KEY"]

    except Exception:

        return {
            "success": False,
            "error_type": "secret",
            "message": "KOBIS_KEY를 찾을 수 없습니다.",
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
            timeout=15
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
    # 6. JSON 변환
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
    # 7. API 오류 확인
    # ========================================

    if "faultInfo" in result:

        fault_info = result["faultInfo"]

        if isinstance(fault_info, dict):

            fault_code = fault_info.get(
                "faultCode",
                ""
            )

            fault_message = fault_info.get(
                "message",
                ""
            )

            if not fault_message:

                fault_message = fault_info.get(
                    "faultString",
                    ""
                )

            error_message = (
                "KOBIS API 오류가 발생했습니다."
            )

            if fault_code:

                error_message += (
                    "\n오류 코드: "
                    + str(fault_code)
                )

            if fault_message:

                error_message += (
                    "\n오류 내용: "
                    + str(fault_message)
                )

        else:

            error_message = (
                "KOBIS API 오류: "
                + str(fault_info)
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
                display_date
                + "의 박스오피스 데이터가 없습니다."
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


    if result["error_type"] == "secret":

        st.info(
            "Streamlit Cloud의 Settings → Secrets에서 "
            "KOBIS_KEY가 등록되어 있는지 확인하세요."
        )

        st.code(
            'KOBIS_KEY = "본인의_실제_KOBIS_인증키"',
            language="toml"
        )


    elif result["error_type"] == "fault":

        st.info(
            "KOBIS 인증키가 정확한지 확인하세요."
        )


    elif result["error_type"] == "empty":

        st.info(
            "조회 날짜: "
            + display_date
        )


    elif result["error_type"] == "network":

        st.info(
            "KOBIS API 서버에 잠시 접속하지 못했습니다. "
            "잠시 후 다시 실행해 주세요."
        )


    st.stop()


# ============================================
# 12. DataFrame 생성
# ============================================

movie_list = result["data"]

df = pd.DataFrame(movie_list)


# ============================================
# 13. 숫자 데이터 변환
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
        )

        df[column] = df[column].fillna(0)

        df[column] = df[column].astype(int)


# ============================================
# 14. 전체 순위 정렬
# 1위 → 2위 → 3위
# ============================================

df = df.sort_values(
    by="rank",
    ascending=True
).reset_index(drop=True)


# ============================================
# 15. 1위 영화 정보
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
# 16. 날짜 표시
# ============================================

st.subheader(
    "📅 " + display_date + " 박스오피스"
)

st.caption(
    "KOBIS 조회 날짜: "
    + target_date
    + " · 현재 한국 시간: "
    + now_kst.strftime("%Y-%m-%d %H:%M")
)


# ============================================
# 17. 1위 영화
# ============================================

st.markdown(
    "## 🏆 1위 · " + first_movie_name
)


# ============================================
# 18. 1위 영화 정보
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
# 19. 관객수 상위 5편
# ============================================

st.subheader(
    "📊 관객수 상위 5편"
)


# --------------------------------------------
# 관객수가 많은 영화 5편을 먼저 선택
# --------------------------------------------

top5 = (
    df.sort_values(
        by="audiCnt",
        ascending=False
    )
    .head(5)
    .copy()
)


# --------------------------------------------
# 선택된 5편을 관객수 적은 순으로 정렬
# --------------------------------------------

top5 = (
    top5.sort_values(
        by="audiCnt",
        ascending=True
    )
    .reset_index(drop=True)
)


# ============================================
# 20. 그래프 데이터
# ============================================

chart_data = top5[
    [
        "movieNm",
        "audiCnt"
    ]
].copy()


# ============================================
# 21. 영화명을 인덱스로 설정
# ============================================

chart_data = chart_data.set_index(
    "movieNm"
)


# ============================================
# 22. 가로 막대그래프
# ============================================

st.bar_chart(
    chart_data,
    horizontal=True,
    use_container_width=True,
    x_label="관객수",
    y_label="영화"
)


st.caption(
    "※ 상위 5편을 선정한 뒤 "
    "관객수가 적은 영화부터 많은 순으로 표시합니다."
)


st.divider()


# ============================================
# 23. 상위 5편 상세 정보
# ============================================

st.subheader(
    "🏆 관객수 상위 5편 상세"
)


top5_table = top5[
    [
        "rank",
        "movieNm",
        "audiCnt",
        "audiAcc"
    ]
].copy()


top5_table = top5_table.rename(
    columns={
        "rank": "순위",
        "movieNm": "영화명",
        "audiCnt": "관객수",
        "audiAcc": "누적관객"
    }
)


# 숫자에 쉼표 추가
top5_table["관객수"] = top5_table[
    "관객수"
].apply(
    lambda x: f"{x:,}명"
)

top5_table["누적관객"] = top5_table[
    "누적관객"
].apply(
    lambda x: f"{x:,}명"
)


st.dataframe(
    top5_table,
    use_container_width=True,
    hide_index=True
)


st.divider()


# ============================================
# 24. 전체 박스오피스
# ============================================

st.subheader(
    "🎬 전체 박스오피스"
)


# ============================================
# 25. 전체 표 데이터
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
# 26. 컬럼 이름 변경
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
# 27. 전체 박스오피스 표
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
# 28. 안내
# ============================================

st.caption(
    "※ 관객수·누적관객·스크린수는 "
    "KOBIS API 데이터를 숫자로 변환하여 표시합니다."
)

st.caption(
    "※ 같은 날짜의 API 결과는 약 1시간 동안 캐시됩니다."
)
