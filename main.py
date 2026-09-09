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
# 5. 선택한 날짜 표시
# ============================================

selected_datetime = datetime.combine(
    selected_date,
    datetime.min.time()
)

selected_display_date = (
    selected_datetime.strftime("%Y년 %m월 %d일")
)

target_date = (
    selected_datetime.strftime("%Y%m%d")
)


st.info(
    "선택한 날짜: "
    + selected_display_date
)


# ============================================
# 6. KOBIS API 주소
# ============================================

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# ============================================
# 7. KOBIS API 호출 함수
# ============================================

@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):

    # ----------------------------------------
    # Secrets에서 인증키 가져오기
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
    # API 요청
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
                "KOBIS API 요청 시간이 초과되었습니다."
            ),
            "data": None
        }

    except requests.exceptions.RequestException:

        return {
            "success": False,
            "error_type": "network",
            "message": (
                "KOBIS API에 접속하지 못했습니다."
            ),
            "data": None
        }


    # ========================================
    # 8. JSON 변환
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
    # 9. KOBIS API 오류 확인
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
    # 10. boxOfficeResult 확인
    # ========================================

    boxoffice_result = result.get(
        "boxOfficeResult"
    )

    if not boxoffice_result:

        return {
            "success": False,
            "error_type": "empty",
            "message": (
                "그날은 아직 집계 전입니다."
            ),
            "data": None
        }


    # ========================================
    # 11. 영화 목록 가져오기
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
                "그날은 아직 집계 전입니다."
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
# 12. API 실행
# ============================================

result = get_boxoffice(target_date)


# ============================================
# 13. 오류 처리
# ============================================

if not result["success"]:

    if result["error_type"] == "secret":

        st.error(
            "KOBIS_KEY를 찾을 수 없습니다."
        )

        st.info(
            "Streamlit Cloud의 Settings → Secrets에서 "
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
            "조회 날짜: "
            + selected_display_date
        )


    elif result["error_type"] == "fault":

        st.error(
            "KOBIS API 오류가 발생했습니다."
        )

        st.warning(
            result["message"]
        )


    elif result["error_type"] == "network":

        st.error(
            "KOBIS API에 접속하지 못했습니다."
        )

        st.info(
            "잠시 후 다시 실행해 주세요."
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
# 14. DataFrame 생성
# ============================================

movie_list = result["data"]

df = pd.DataFrame(movie_list)


# ============================================
# 15. 숫자 데이터 변환
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
# 16. 순위 기준 정렬
# ============================================

df = (
    df.sort_values(
        by="rank",
        ascending=True
    )
    .reset_index(drop=True)
)


# ============================================
# 17. 1위 영화 정보
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
# 18. 조회 날짜 제목
# ============================================

st.divider()

st.header(
    "🎬 "
    + selected_display_date
    + " 박스오피스"
)


# ============================================
# 19. 1위 영화
# ============================================

st.markdown(
    "## 🏆 1위 · "
    + first_movie_name
)


# ============================================
# 20. 1위 영화 정보
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
# 21. 관객수 상위 5편
# ============================================

st.subheader(
    "📊 관객수 상위 5편"
)


# ============================================
# 22. 관객수가 많은 5편 선택
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
# 23. 관객수 오름차순으로 다시 정렬
#
# 적은 관객수
#      ↓
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
# 24. 최대 관객수
# ============================================

max_audience = int(
    top5["audiCnt"].max()
)

if max_audience <= 0:

    max_audience = 1


# ============================================
# 25. 상위 5편 그래프
# ============================================

for index, row in top5.iterrows():

    movie_name = str(
        row["movieNm"]
    )

    audience = int(
        row["audiCnt"]
    )

    bar_width = (
        audience / max_audience
    )


    col_name, col_bar, col_value = st.columns(
        [2.5, 7, 1.5]
    )


    with col_name:

        st.write(
            movie_name
        )


    with col_bar:

        st.progress(
            bar_width
        )


    with col_value:

        st.write(
            f"{audience:,}명"
        )


# ============================================
# 26. 그래프 안내
# ============================================

st.caption(
    "※ 상위 5편을 선정한 후 "
    "관객수가 적은 영화부터 많은 순으로 표시합니다."
)


st.divider()


# ============================================
# 27. 전체 박스오피스 표
# ============================================

st.subheader(
    "🎬 전체 박스오피스"
)


# ============================================
# 28. HTML 표 만들기
#
# HTML을 사용하는 이유:
# ↑ 빨간색
# ↓ 파란색
# 을 정확하게 표시하기 위해서입니다.
# ============================================

html = """
<table style="
    width: 100%;
    border-collapse: collapse;
    font-size: 15px;
">
<thead>
<tr>
    <th style="
        text-align: center;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    ">순위</th>

    <th style="
        text-align: left;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    ">영화명</th>

    <th style="
        text-align: center;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    ">전일 대비</th>

    <th style="
        text-align: center;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    ">개봉일</th>

    <th style="
        text-align: right;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    ">관객수</th>

    <th style="
        text-align: right;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    ">누적관객</th>

    <th style="
        text-align: right;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    ">스크린수</th>
</tr>
</thead>
<tbody>
"""


# ============================================
# 29. 영화별 표 데이터 생성
# ============================================

for index, row in df.iterrows():

    rank = int(
        row["rank"]
    )

    movie_name = str(
        row["movieNm"]
    )

    rank_inten = int(
        row["rankInten"]
    )

    open_date = str(
        row["openDt"]
    )

    audience = int(
        row["audiCnt"]
    )

    total_audience = int(
        row["audiAcc"]
    )

    screen_count = int(
        row["scrnCnt"]
    )


    # ========================================
    # 30. 100만 관객 트로피
    # ========================================

    if total_audience >= 1_000_000:

        movie_display_name = (
            "🏆 "
            + movie_name
        )

    else:

        movie_display_name = movie_name


    # ========================================
    # 31. 순위 변동 표시
    # ========================================

    if rank_inten > 0:

        rank_display = (
            '<span style="'
            'color: red; '
            'font-weight: bold;'
            '">↑ '
            + str(rank_inten)
            + "</span>"
        )


    elif rank_inten < 0:

        rank_display = (
            '<span style="'
            'color: blue; '
            'font-weight: bold;'
            '">↓ '
            + str(abs(rank_inten))
            + "</span>"
        )


    else:

        rank_display = (
            '<span style="'
            'color: gray;'
            '">-</span>'
        )


    # ========================================
    # 32. 행 추가
    # ========================================

    html += (
        "<tr>"
        "<td style="
        "'text-align:center;"
        "padding:10px;"
        "border-bottom:1px solid #eee;'>"
        + str(rank)
        + "</td>"

        "<td style="
        "'text-align:left;"
        "padding:10px;"
        "border-bottom:1px solid #eee;"
        "font-weight:500;'>"
        + movie_display_name
        + "</td>"

        "<td style="
        "'text-align:center;"
        "padding:10px;"
        "border-bottom:1px solid #eee;'>"
        + rank_display
        + "</td>"

        "<td style="
        "'text-align:center;"
        "padding:10px;"
        "border-bottom:1px solid #eee;'>"
        + open_date
        + "</td>"

        "<td style="
        "'text-align:right;"
        "padding:10px;"
        "border-bottom:1px solid #eee;'>"
        + f"{audience:,}"
        + "명</td>"

        "<td style="
        "'text-align:right;"
        "padding:10px;"
        "border-bottom:1px solid #eee;'>"
        + f"{total_audience:,}"
        + "명</td>"

        "<td style="
        "'text-align:right;"
        "padding:10px;"
        "border-bottom:1px solid #eee;'>"
        + f"{screen_count:,}"
        + "개</td>"

        "</tr>"
    )


# ============================================
# 33. HTML 표 닫기
# ============================================

html += """
</tbody>
</table>
"""


# ============================================
# 34. 표 표시
# ============================================

st.markdown(
    html,
    unsafe_allow_html=True
)


# ============================================
# 35. 범례
# ============================================

st.divider()

st.markdown(
    "🔺 **빨간색 ↑** : 전날보다 순위 상승  ·  "
    "🔻 **파란색 ↓** : 전날보다 순위 하락  ·  "
    "🏆 **누적 100만 관객 이상**"
)


# ============================================
# 36. 데이터 안내
# ============================================

st.caption(
    "※ 조회 날짜는 한국 시간 기준으로 선택합니다."
)

st.caption(
    "※ 오늘 날짜는 아직 집계 전이므로 선택할 수 없습니다."
)

st.caption(
    "※ 순위 변동은 KOBIS의 rankInten 값을 사용합니다."
)
