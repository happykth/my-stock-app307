import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ------------------------------
# 기본 페이지 설정
# ------------------------------
st.set_page_config(
    page_title="주가 조회 앱",
    page_icon="📈",
    layout="centered",
)

# ------------------------------
# 화면 스타일 (따뜻한 톤)
# ------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFF8E7;
    }
    div[data-testid="stMetric"] {
        background-color: #FFF1CE;
        border: 2px solid #FFC94A;
        border-radius: 16px;
        padding: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# 제목과 설명
# ------------------------------
st.title("📈 내 주식 그래프 보기")
st.write(
    "종목 코드를 입력하면 최근 1년간의 주가 흐름을 그래프로 보여드려요. "
    "예시: 삼성전자는 **005930.KS**, 애플은 **AAPL** 처럼 입력해주세요."
)

# ------------------------------
# 종목 코드 입력창
# ------------------------------
ticker_input = st.text_input(
    "종목 코드를 입력하세요",
    value="005930.KS",
    placeholder="예: 005930.KS (삼성전자), AAPL (애플)",
)

# 입력값 앞뒤 공백 제거 + 대문자로 변환 (yfinance는 대문자를 기준으로 함)
ticker = ticker_input.strip().upper()

# ------------------------------
# 조회 버튼
# ------------------------------
if st.button("조회하기", type="primary"):

    if ticker == "":
        # 아무것도 입력하지 않았을 때 안내
        st.warning("종목 코드를 입력해주세요.")
    else:
        # 로딩 중임을 알려주는 스피너
        with st.spinner(f"{ticker} 데이터를 불러오는 중이에요..."):

            # 오늘 날짜 기준으로 1년 전 날짜 계산
            end_date = datetime.today()
            start_date = end_date - timedelta(days=365)

            try:
                # yfinance로 주가 데이터 가져오기
                data = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    progress=False,
                )
            except Exception:
                data = None

        # 데이터가 비어있거나 못 불러온 경우
        if data is None or data.empty:
            st.error(
                "데이터를 불러오지 못했어요. 종목 코드가 정확한지 확인해주세요. "
                "(예: 005930.KS, AAPL)"
            )
        else:
            # yfinance 버전에 따라 컬럼이 여러 종목 형태(멀티인덱스)로 나올 수 있어
            # 안전하게 종가(Close) 컬럼만 뽑아냄
            if isinstance(data.columns, type(data.columns)) and hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
                close_prices = data["Close"][ticker]
            else:
                close_prices = data["Close"]

            # 결측치(빈 값) 제거
            close_prices = close_prices.dropna()

            # ------------------------------
            # 현재가 및 1년 등락률 계산
            # ------------------------------
            first_price = float(close_prices.iloc[0])   # 1년 전 가격
            last_price = float(close_prices.iloc[-1])    # 가장 최근 가격
            change_rate = (last_price - first_price) / first_price * 100  # 등락률(%)

            # ------------------------------
            # 지표 카드 (현재가 / 1년 등락률)
            # ------------------------------
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="현재가",
                    value=f"{last_price:,.2f}",
                )

            with col2:
                st.metric(
                    label="1년 등락률",
                    value=f"{change_rate:,.2f}%",
                    delta=f"{change_rate:,.2f}%",
                )

            # ------------------------------
            # Plotly 꺾은선 그래프 그리기
            # ------------------------------
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=close_prices.index,
                    y=close_prices.values,
                    mode="lines",
                    line=dict(color="#F4A81E", width=2),
                    name=ticker,
                )
            )

            fig.update_layout(
                title=f"{ticker} 최근 1년 주가 흐름",
                xaxis_title="날짜",
                yaxis_title="가격",
                plot_bgcolor="#FFF8E7",
                paper_bgcolor="#FFF8E7",
                font=dict(color="#7A5230"),
                hovermode="x unified",
            )

            # 그래프를 화면 너비에 맞춰 출력
            st.plotly_chart(fig, use_container_width=True)

            # 안내 문구
            st.caption("※ 본 데이터는 야후 파이낸스(yfinance) 기준이며 투자 참고용입니다.")

else:
    # 처음 앱을 열었을 때 보여줄 안내 문구
    st.info("종목 코드를 입력하고 '조회하기' 버튼을 눌러주세요.")
