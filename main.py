# ============================================
# 🎬 박스오피스
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
    page_title="박스오피스",
    page_icon="🎬",
    layout="wide"
)


# ============================================
# 2. 제목
# ============================================

st.title("🎬 박스오피스")

st.caption(
    "한국영화진흥위원회(KOBIS) 일별 박스오피스 데이터를 "
    "원하는 날짜로 조회할 수 있습니다."
)


# ============================================
# 3. 한국 시간
# ============================================

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)

yesterday_kst = (
    now_kst - timedelta(days=1)
)

yesterday_date = yesterday_kst.date()


# ============================================
# 4. 날짜 선택
# ============================================

st.subheader("📅 조회 날짜")

selected_date = st.date_input(
    "박스오피스를 조회할 날짜를 선택하세요.",
    value=yesterday_date,
    max_value=yesterday_date,
    format="YYYY-MM-DD"
)


# ============================================
# 5. 날짜 변환
# ============================================

target_date = selected_date.strftime(
    "%Y%m%d"
)

selected_display_date = selected_date.strftime(
    "%Y년 %m월 %d일"
)


st.info(
    f"📅 선택한 날짜: {selected_display_date}"
)


# ============================================
# 6. KOBIS API 주소
# ============================================

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# ============================================
# 7. KOBIS API 호출
# ============================================

@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):

    # ----------------------------------------
    # Secrets에서 KOBIS_KEY 가져오기
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
    # API 요청
    # ----------------------------------------

    params = {
        "key": api_key,
        "targetDt": target_dt
    }


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
            "message": "KOBIS API 요청 시간이 초과되었습니다.",
            "data": None
        }


    except requests.exceptions.RequestException:

        return {
            "success": False,
            "error_type": "network",
            "message": "KOBIS API에 접속하지 못했습니다.",
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
            "message": "KOBIS API 응답을 읽을 수 없습니다.",
            "data": None
        }


    # ========================================
    # 8. KOBIS API 오류
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

            message = (
                "KOBIS API 오류가 발생했습니다."
            )


            if fault_code:

                message += (
                    f"\n오류 코드: {fault_code}"
                )


            if fault_message:

                message += (
                    f"\n오류 내용: {fault_message}"
                )


        else:

            message = (
                "KOBIS API 오류: "
                + str(fault_info)
            )


        return {
            "success": False,
            "error_type": "fault",
            "message": message,
            "data": None
        }


    # ========================================
    # 9. 박스오피스 결과 확인
    # ========================================

    boxoffice_result = result.get(
        "boxOfficeResult"
    )


    if not boxoffice_result:

        return {
            "success": False,
            "error_type": "empty",
            "message": "그날은 아직 집계 전입니다.",
            "data": None
        }


    # ========================================
    # 10. 영화 목록
    # ========================================

    movie_list = boxoffice_result.get(
        "dailyBoxOfficeList",
        []
    )


    if not movie_list:

        return {
            "success": False,
            "error_type": "empty",
            "message": "그날은 아직 집계 전입니다.",
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
# 11. API 실행
# ============================================

result = get_boxoffice(
    target_date
)


# ============================================
# 12. 오류 처리
# ============================================

if not result["success"]:

    if result["error_type"] == "secret":

        st.error(
            "KOBIS_KEY를 찾을 수 없습니다."
        )

        st.info(
            "Streamlit Cloud → Settings → Secrets에서 "
            "KOBIS_KEY가 등록되어 있는지 확인하세요."
        )

        st.code(
            'KOBIS_KEY = "본인의_실제_KOBIS_인증키"',
            language="toml"
        )


    elif result["error_type"] == "empty":

        st.warning(
            "📭 그날은 아직 집계 전입니다."
        )

        st.caption(
            f"조회 날짜: {selected_display_date}"
        )


    elif result["error_type"] == "network":

        st.error(
            "KOBIS API에 접속하지 못했습니다."
        )

        st.info(
            "잠시 후 다시 실행해 주세요."
        )


    elif result["error_type"] == "fault":

        st.error(
            "KOBIS API 오류가 발생했습니다."
        )

        st.warning(
            result["message"]
        )


    else:

        st.error(
            "박스오피스 데이터를 불러오지 못했습니다."
        )

        st.warning(
            result["message"]
        )


    st.stop()


# ============================================
# 13. DataFrame 생성
# ============================================

movie_list = result["data"]

df = pd.DataFrame(
    movie_list
)


# ============================================
# 14. 숫자 데이터 변환
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

        df[column] = (
            df[column]
            .fillna(0)
            .astype(int)
        )


# ============================================
# 15. 현재 순위 기준 정렬
# ============================================

df = (
    df.sort_values(
        by="rank",
        ascending=True
    )
    .reset_index(drop=True)
)


# ============================================
# 16. 1위 영화 정보
# ============================================

first_movie = df.iloc[0]

first_movie_name = str(
    first_movie["movieNm"]
)

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
# 17. 선택 날짜 박스오피스
# ============================================

st.divider()

st.header(
    f"🎬 {selected_display_date} 박스오피스"
)


# ============================================
# 18. 1위 영화
# ============================================

st.markdown(
    f"## 🥇 1위 · {first_movie_name}"
)


# ============================================
# 19. 1위 영화 정보
# ============================================

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "🎟️ 일일 관객수",
        f"{first_audience:,}명"
    )


with col2:

    st.metric(
        "👥 누적 관객수",
        f"{first_total_audience:,}명"
    )


with col3:

    st.metric(
        "🎞️ 스크린수",
        f"{first_screen_count:,}개"
    )


st.divider()


# ============================================
# 20. 관객수 상위 5편
# ============================================

st.subheader(
    "📊 관객수 상위 5편"
)


# ============================================
# 21. 관객수 기준 상위 5편 선정
# ============================================

top5 = (
    df.sort_values(
        by="audiCnt",
        ascending=False
    )
    .head(5)
    .copy()
)


# ============================================
# 22. 관객수 오름차순
#
# 적은 관객수
#       ↓
# 많은 관객수
# ============================================

top5 = (
    top5.sort_values(
        by="audiCnt",
        ascending=True
    )
    .reset_index(drop=True)
)


# ============================================
# 23. 그래프용 데이터
# ============================================

chart_df = top5[
    [
        "movieNm",
        "audiCnt"
    ]
].copy()


# ============================================
# 24. 관객수 표시용 텍스트
# ============================================

chart_df["관객수"] = (
    chart_df["audiCnt"]
    .apply(
        lambda x: f"{int(x):,}명"
    )
)


# ============================================
# 25. Vega-Lite 차트
#
# 마우스를 막대에 올리면
# 영화명 + 관객수가 표시됩니다.
# ============================================

chart_spec = {

    "mark": {
        "type": "bar",
        "cornerRadiusEnd": 4
    },

    "encoding": {

        # ------------------------------------
        # X축 = 관객수
        # ------------------------------------

        "x": {
            "field": "audiCnt",
            "type": "quantitative",
            "title": "관객수",
            "axis": {
                "format": ",d"
            }
        },


        # ------------------------------------
        # Y축 = 영화명
        # 오름차순 유지
        # ------------------------------------

        "y": {
            "field": "movieNm",
            "type": "nominal",
            "title": "영화",
            "sort": {
                "field": "audiCnt",
                "order": "ascending"
            }
        },


        # ------------------------------------
        # 마우스를 올렸을 때 표시할 정보
        # ------------------------------------

        "tooltip": [

            {
                "field": "movieNm",
                "type": "nominal",
                "title": "영화"
            },

            {
                "field": "audiCnt",
                "type": "quantitative",
                "title": "관객수",
                "format": ",d"
            }

        ]

    },

    # ----------------------------------------
    # 차트 높이
    # ----------------------------------------

    "height": 300

}


st.vega_lite_chart(
    chart_df,
    chart_spec,
    use_container_width=True
)


# ============================================
# 26. 그래프 안내
# ============================================

st.caption(
    "※ 막대에 마우스를 올리면 영화명과 관객수가 표시됩니다."
)

st.caption(
    "※ 관객수가 적은 영화부터 많은 영화 순으로 표시합니다."
)


st.divider()


# ============================================
# 27. 전체 박스오피스
# ============================================

st.subheader(
    "🎬 전체 박스오피스"
)


# ============================================
# 28. 표용 데이터 생성
# ============================================

table_df = df[
    [
        "rank",
        "movieNm",
        "rankInten",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()


# ============================================
# 29. 영화명 트로피
# ============================================

def make_movie_name(row):

    movie_name = str(
        row["movieNm"]
    )

    total_audience = int(
        row["audiAcc"]
    )


    if total_audience >= 1_000_000:

        return "🏆 " + movie_name


    return movie_name


table_df["movieNm"] = table_df.apply(
    make_movie_name,
    axis=1
)


# ============================================
# 30. 순위 변동 표시
# ============================================

def make_rank_change(value):

    value = int(value)


    if value > 0:

        return f"↑ {value}"


    elif value < 0:

        return f"↓ {abs(value)}"


    else:

        return "-"


table_df["rankInten"] = (
    table_df["rankInten"]
    .apply(make_rank_change)
)


# ============================================
# 31. 컬럼명 변경
# ============================================

table_df = table_df.rename(
    columns={
        "rank": "순위",
        "movieNm": "영화명",
        "rankInten": "전일 대비",
        "openDt": "개봉일",
        "audiCnt": "관객수",
        "audiAcc": "누적관객",
        "scrnCnt": "스크린수"
    }
)


# ============================================
# 32. 숫자 표시
# ============================================

table_df["관객수"] = (
    table_df["관객수"]
    .apply(
        lambda x: f"{int(x):,}명"
    )
)


table_df["누적관객"] = (
    table_df["누적관객"]
    .apply(
        lambda x: f"{int(x):,}명"
    )
)


table_df["스크린수"] = (
    table_df["스크린수"]
    .apply(
        lambda x: f"{int(x):,}개"
    )
)


# ============================================
# 33. 순위 변동 색상
# ============================================

def color_rank_change(value):

    value = str(value)


    if value.startswith("↑"):

        return (
            "color: red; "
            "font-weight: bold"
        )


    if value.startswith("↓"):

        return (
            "color: blue; "
            "font-weight: bold"
        )


    return "color: gray"


styled_table = (
    table_df.style
    .map(
        color_rank_change,
        subset=["전일 대비"]
    )
)


# ============================================
# 34. 전체 박스오피스 표
# ============================================

st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True
)


# ============================================
# 35. 범례
# ============================================

st.divider()

st.markdown(
    "🔺 **빨간 ↑** : 전날보다 순위 상승  ·  "
    "🔻 **파란 ↓** : 전날보다 순위 하락  ·  "
    "➖ **-** : 순위 변동 없음  ·  "
    "🏆 **누적 100만 관객 이상**"
)


# ============================================
# 36. 안내
# ============================================

st.caption(
    "※ 오늘 날짜는 아직 집계 전이므로 선택할 수 없습니다."
)

st.caption(
    "※ 순위 변동은 KOBIS의 rankInten 값을 사용합니다."
)

st.caption(
    "※ 누적관객이 1,000,000명 이상인 영화에는 🏆가 표시됩니다."
)
