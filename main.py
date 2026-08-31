import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ────────────────────────────────────────────
# 페이지 기본 설정
# ────────────────────────────────────────────
st.set_page_config(
    page_title="주가 조회 앱",
    page_icon="📈",
    layout="centered",
)

# ────────────────────────────────────────────
# 제목 & 설명
# ────────────────────────────────────────────
st.title("📈 주가 조회 앱")
st.markdown(
    """
    종목 코드를 입력하면 최근 1년간의 주가 흐름을 그래프로 보여드려요. 😊  
    - 한국 주식(코스피)은 종목 코드 뒤에 **.KS** 를 붙여주세요. (예: `005930.KS` → 삼성전자)  
    - 미국 주식은 티커만 입력하면 돼요. (예: `AAPL` → 애플)
    """
)

st.divider()

# ────────────────────────────────────────────
# 종목 코드 입력창
# ────────────────────────────────────────────
ticker_input = st.text_input(
    "🔍 종목 코드를 입력하세요",
    value="AAPL",
    placeholder="예: 005930.KS 또는 AAPL",
)

# 입력값 앞뒤 공백 제거 및 대문자로 변환 (티커는 보통 대문자로 씀)
ticker_symbol = ticker_input.strip().upper()

# ────────────────────────────────────────────
# 데이터 불러오기 & 화면 표시
# ────────────────────────────────────────────
if ticker_symbol:
    try:
        # 오늘 날짜 기준으로 최근 1년치 기간 계산
        end_date = datetime.today()
        start_date = end_date - timedelta(days=365)

        # yfinance로 주가 데이터 가져오기
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(start=start_date, end=end_date)

        # 데이터가 비어있으면 잘못된 종목 코드일 가능성이 높음
        if df.empty:
            st.error("😥 해당 종목의 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해주세요.")
        else:
            # 종목 이름 가져오기 (없으면 입력한 코드 그대로 사용)
            try:
                company_name = stock.info.get("longName", ticker_symbol)
            except Exception:
                company_name = ticker_symbol

            # 현재가(가장 최근 종가)와 1년 전 가격
            current_price = df["Close"].iloc[-1]
            start_price = df["Close"].iloc[0]

            # 1년 등락률 계산 (%)
            change_rate = (current_price - start_price) / start_price * 100

            # 통화 단위 결정 (한국 주식이면 원, 그 외에는 달러로 표시)
            is_korean_stock = ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ")
            currency_unit = "원" if is_korean_stock else "달러"
            price_format = "{:,.0f}" if is_korean_stock else "{:,.2f}"

            st.subheader(f"🏢 {company_name} ({ticker_symbol})")

            # ── 지표 카드 (현재가, 1년 등락률) ──
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="현재가",
                    value=f"{price_format.format(current_price)} {currency_unit}",
                )

            with col2:
                st.metric(
                    label="1년 등락률",
                    value=f"{change_rate:+.2f}%",
                    delta=f"{change_rate:+.2f}%",
                )

            st.divider()

            # ── Plotly 꺾은선 그래프 ──
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["Close"],
                    mode="lines",
                    name="종가",
                    line=dict(color="#FF8C42", width=2),  # 따뜻한 오렌지 색상
                    fill="tozeroy",
                    fillcolor="rgba(255, 140, 66, 0.1)",
                )
            )

            fig.update_layout(
                title=f"{company_name} 최근 1년 주가 추이",
                xaxis_title="날짜",
                yaxis_title=f"종가 ({currency_unit})",
                template="plotly_white",
                hovermode="x unified",
                height=450,
            )

            st.plotly_chart(fig, use_container_width=True)

            st.caption("📌 데이터 출처: Yahoo Finance (yfinance) · 투자 판단에 대한 책임은 본인에게 있습니다.")

    except Exception as e:
        # 예상치 못한 오류가 발생했을 때 사용자에게 친절하게 안내
        st.error(f"⚠️ 데이터를 불러오는 중 문제가 발생했어요: {e}")
else:
    st.info("👆 위 입력창에 종목 코드를 입력해주세요!")
