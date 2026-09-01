import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    종목 코드를 입력하면 원하는 기간의 주가 흐름을 그래프로 보여드려요. 😊  
    최대 2개의 종목을 나란히 비교할 수도 있어요.  
    - 한국 주식(코스피)은 종목 코드 뒤에 **.KS** 를 붙여주세요. (예: `005930.KS` → 삼성전자)  
    - 미국 주식은 티커만 입력하면 돼요. (예: `AAPL` → 애플)
    """
)

st.divider()

# ────────────────────────────────────────────
# 종목 코드 입력창 (최대 2개, 나란히 배치)
# ────────────────────────────────────────────
input_col1, input_col2 = st.columns(2)

with input_col1:
    ticker_input_1 = st.text_input(
        "🔍 종목 1",
        value="AAPL",
        placeholder="예: 005930.KS 또는 AAPL",
    )

with input_col2:
    ticker_input_2 = st.text_input(
        "🔍 종목 2 (선택)",
        value="",
        placeholder="비교할 종목이 있다면 입력하세요",
    )

# 입력값 앞뒤 공백 제거 및 대문자로 변환 (티커는 보통 대문자로 씀)
ticker_symbol_1 = ticker_input_1.strip().upper()
ticker_symbol_2 = ticker_input_2.strip().upper()

# ────────────────────────────────────────────
# 기간 선택 버튼 (1개월 · 6개월 · 1년 · 5년)
# ────────────────────────────────────────────
st.write("📅 조회 기간을 선택하세요")

# 버튼으로 고른 기간을 기억하기 위한 세션 상태 (처음엔 1년으로 시작)
if "selected_period" not in st.session_state:
    st.session_state.selected_period = "1년"

# 기간 이름 → 조회할 일수(days) 매핑
period_days_map = {
    "1개월": 30,
    "6개월": 182,
    "1년": 365,
    "5년": 365 * 5,
}

period_col1, period_col2, period_col3, period_col4 = st.columns(4)
period_columns = [period_col1, period_col2, period_col3, period_col4]

for period_col, period_name in zip(period_columns, period_days_map.keys()):
    with period_col:
        # 현재 선택된 기간이면 강조된 버튼(primary)으로 표시
        is_selected = st.session_state.selected_period == period_name
        if st.button(
            period_name,
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state.selected_period = period_name
            st.rerun()

selected_period_name = st.session_state.selected_period
selected_days = period_days_map[selected_period_name]

st.divider()


# ────────────────────────────────────────────
# 주가 데이터를 가져오고 통계를 계산하는 함수
# ────────────────────────────────────────────
def get_stock_data(ticker_symbol: str, days: int):
    """종목 코드와 기간(일수)을 받아 주가 데이터와 통계를 반환해요."""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    stock = yf.Ticker(ticker_symbol)
    df = stock.history(start=start_date, end=end_date)

    if df.empty:
        return None

    try:
        company_name = stock.info.get("longName", ticker_symbol)
    except Exception:
        company_name = ticker_symbol

    current_price = df["Close"].iloc[-1]
    start_price = df["Close"].iloc[0]
    change_rate = (current_price - start_price) / start_price * 100

    max_price = df["Close"].max()
    min_price = df["Close"].min()
    avg_price = df["Close"].mean()

    # 한국 주식이면 원, 그 외에는 달러로 통화 단위 결정
    is_korean_stock = ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ")
    currency_unit = "원" if is_korean_stock else "달러"
    price_format = "{:,.0f}" if is_korean_stock else "{:,.2f}"

    return {
        "df": df,
        "company_name": company_name,
        "current_price": current_price,
        "change_rate": change_rate,
        "max_price": max_price,
        "min_price": min_price,
        "avg_price": avg_price,
        "currency_unit": currency_unit,
        "price_format": price_format,
    }


def show_metric_cards(data: dict):
    """현재가·등락률·최고가·최저가·평균가 카드를 화면에 보여줘요."""
    unit = data["currency_unit"]
    fmt = data["price_format"]

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.metric("현재가", f"{fmt.format(data['current_price'])} {unit}")
    with row1_col2:
        st.metric(
            f"{selected_period_name} 등락률",
            f"{data['change_rate']:+.2f}%",
            delta=f"{data['change_rate']:+.2f}%",
        )

    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        st.metric("최고가", f"{fmt.format(data['max_price'])} {unit}")
    with row2_col2:
        st.metric("최저가", f"{fmt.format(data['min_price'])} {unit}")
    with row2_col3:
        st.metric("평균가", f"{fmt.format(data['avg_price'])} {unit}")


# ────────────────────────────────────────────
# 데이터 조회 & 화면 표시
# ────────────────────────────────────────────
if not ticker_symbol_1:
    st.info("👆 위 입력창에 종목 코드를 입력해주세요!")
else:
    try:
        # 종목 1 데이터 조회 (필수)
        data_1 = get_stock_data(ticker_symbol_1, selected_days)

        # 종목 2 데이터 조회 (입력했을 때만)
        data_2 = get_stock_data(ticker_symbol_2, selected_days) if ticker_symbol_2 else None

        if data_1 is None:
            st.error(f"😥 '{ticker_symbol_1}' 종목의 데이터를 찾을 수 없어요. 코드를 다시 확인해주세요.")
        elif ticker_symbol_2 and data_2 is None:
            st.error(f"😥 '{ticker_symbol_2}' 종목의 데이터를 찾을 수 없어요. 코드를 다시 확인해주세요.")
        else:
            # ── 그래프 (2개 종목이면 보조 y축으로 함께 표시) ──
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            fig.add_trace(
                go.Scatter(
                    x=data_1["df"].index,
                    y=data_1["df"]["Close"],
                    mode="lines",
                    name=f"{data_1['company_name']} ({ticker_symbol_1})",
                    line=dict(color="#FF8C42", width=2),  # 따뜻한 오렌지 색상
                ),
                secondary_y=False,
            )

            if data_2 is not None:
                fig.add_trace(
                    go.Scatter(
                        x=data_2["df"].index,
                        y=data_2["df"]["Close"],
                        mode="lines",
                        name=f"{data_2['company_name']} ({ticker_symbol_2})",
                        line=dict(color="#4A90D9", width=2),  # 대비되는 파란색
                    ),
                    secondary_y=True,  # 통화·가격 단위가 다를 수 있어 보조 y축 사용
                )
                fig.update_yaxes(title_text=f"{ticker_symbol_1} 종가 ({data_1['currency_unit']})", secondary_y=False)
                fig.update_yaxes(title_text=f"{ticker_symbol_2} 종가 ({data_2['currency_unit']})", secondary_y=True)
                chart_title = f"{data_1['company_name']} vs {data_2['company_name']} · {selected_period_name} 주가 추이"
            else:
                fig.update_yaxes(title_text=f"종가 ({data_1['currency_unit']})", secondary_y=False)
                chart_title = f"{data_1['company_name']} · {selected_period_name} 주가 추이"

            fig.update_layout(
                title=chart_title,
                xaxis_title="날짜",
                template="plotly_white",
                hovermode="x unified",
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )

            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # ── 지표 카드 (종목별로 나란히) ──
            if data_2 is not None:
                card_col1, card_col2 = st.columns(2)
                with card_col1:
                    st.subheader(f"🏢 {data_1['company_name']} ({ticker_symbol_1})")
                    show_metric_cards(data_1)
                with card_col2:
                    st.subheader(f"🏢 {data_2['company_name']} ({ticker_symbol_2})")
                    show_metric_cards(data_2)
            else:
                st.subheader(f"🏢 {data_1['company_name']} ({ticker_symbol_1})")
                show_metric_cards(data_1)

            st.caption("📌 데이터 출처: Yahoo Finance (yfinance) · 투자 판단에 대한 책임은 본인에게 있습니다.")

    except Exception as e:
        # 예상치 못한 오류가 발생했을 때 사용자에게 친절하게 안내
        st.error(f"⚠️ 데이터를 불러오는 중 문제가 발생했어요: {e}")
