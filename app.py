import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="Helios Investments", layout="wide", initial_sidebar_state="expanded")

# ----------------------------------------------------------------------------
# THEME / CSS
# ----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .metric-label { font-family: 'Space Grotesk', sans-serif; }

    .stApp {
        background: radial-gradient(circle at 20% 0%, #1a0f2e 0%, #0d0d0f 45%, #0a0a0c 100%);
        color: #f2f0f5;
    }

    section[data-testid="stSidebar"] {
        background: #111114;
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    .block-container { padding-top: 2rem; padding-bottom: 3rem; }

    .card {
        background: linear-gradient(160deg, #17141f 0%, #131217 100%);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 18px;
    }

    .card-title {
        font-size: 0.8rem;
        color: #9a94ab;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }

    .big-number {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.1rem;
        font-weight: 600;
        color: #ffffff;
    }

    .delta-up { color: #4ade80; font-size: 0.85rem; font-weight: 500; }
    .delta-down { color: #f87171; font-size: 0.85rem; font-weight: 500; }

    .ticker-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .ticker-row:last-child { border-bottom: none; }
    .ticker-name { font-weight: 600; font-size: 0.9rem; color: #f2f0f5; }
    .ticker-sub { font-size: 0.72rem; color: #7a7488; }

    .cta-card {
        background: linear-gradient(120deg, #6d28d9 0%, #db2777 100%);
        border-radius: 18px;
        padding: 26px 28px;
        margin-bottom: 18px;
    }
    .cta-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; font-weight: 600; color: white; }
    .cta-sub { color: rgba(255,255,255,0.85); font-size: 0.85rem; margin-top: 4px; margin-bottom: 16px;}

    div.stButton > button {
        background: rgba(255,255,255,0.15);
        color: white;
        border: 1px solid rgba(255,255,255,0.4);
        border-radius: 10px;
        font-weight: 500;
        padding: 6px 18px;
    }
    div.stButton > button:hover { background: rgba(255,255,255,0.28); border-color: white; }

    .nav-pill {
        background: rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 4px;
        display: inline-flex;
    }

    .stRadio > div { flex-direction: row; gap: 4px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# FAKE DATA
# ----------------------------------------------------------------------------
np.random.seed(7)
months = pd.date_range("2026-01-01", periods=12, freq="M").strftime("%b")
base = np.cumsum(np.random.randn(12) * 6000) + 165000
perf = pd.DataFrame({"month": months, "value": base})

watchlist = [
    ("Spotify", "NYSE: SPOT", "$117.70", 16.3, True),
    ("Amazon", "NYSE: AMZN", "$102.80", 8.1, True),
    ("Microsoft", "NYSE: MSFT", "$85.10", 4.9, True),
    ("Nvidia", "NYSE: NVDA", "$21.10", -2.1, False),
]

portfolio = [
    ("AAPL", "104 units", "$1,721.30", 12.3),
    ("AMZN", "12 units", "$1,721.30", 12.3),
    ("MSFT", "41 units", "$1,721.30", 12.3),
    ("NVDA", "16 units", "$1,721.30", 12.3),
]

# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ✦ Helios Investments")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    nav = st.radio("", ["📊 Dashboard", "💼 Portfolio", "📈 Analysis", "🌐 Market", "👥 Community"], label_visibility="collapsed")
    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.radio(" ", ["⚙️ Settings", "🛟 Support"], label_visibility="collapsed")

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
col_a, col_b = st.columns([3, 2])
with col_a:
    st.markdown("## Welcome, Nadia")
    st.caption("Here's your investment portfolio overview")
with col_b:
    st.text_input("", placeholder="🔮  Ask Helios AI anything...", label_visibility="collapsed")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# ROW 1 — Total Holding / Watchlist / Portfolio grid
# ----------------------------------------------------------------------------
c1, c2, c3 = st.columns([1, 1.3, 1.3])

with c1:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Total Holding · 6M</div>
        <div class="big-number">$12,304.11</div>
        <div class="delta-up">▲ 8.4% this period</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="cta-card">
        <div class="cta-title">Decisions Powered by Data</div>
        <div class="cta-sub">Move beyond guesswork with AI-driven insights tailored to your strategy.</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("✨ Explore AI Insights", use_container_width=True)

with c2:
    rows = ""
    for name, sub, price, pct, up in watchlist:
        cls = "delta-up" if up else "delta-down"
        arrow = "▲" if up else "▼"
        rows += f"""
        <div class="ticker-row">
            <div><div class="ticker-name">{name}</div><div class="ticker-sub">{sub}</div></div>
            <div style="text-align:right"><div class="ticker-name">{price}</div><div class="{cls}">{arrow} {abs(pct)}%</div></div>
        </div>"""
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Watchlist</div>
        {rows}
    </div>
    """, unsafe_allow_html=True)

with c3:
    grid = "<div style='display:grid;grid-template-columns:1fr 1fr;gap:12px'>"
    for tkr, units, val, pct in portfolio:
        grid += f"""
        <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:12px;">
            <div class="ticker-sub">{tkr} · {units}</div>
            <div class="ticker-name" style="font-size:1rem;margin-top:4px">{val}</div>
            <div class="delta-up">▲ {pct}%</div>
        </div>"""
    grid += "</div>"
    st.markdown(f"""
    <div class="card">
        <div class="card-title">My Portfolio</div>
        {grid}
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# ROW 2 — Stats gauge-style card + Performance chart
# ----------------------------------------------------------------------------
c4, c5 = st.columns([1, 2])

with c4:
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=76,
        number={'suffix': "%", 'font': {'color': '#ffffff', 'size': 34}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': 'rgba(255,255,255,0.2)', 'tickfont': {'color': '#7a7488'}},
            'bar': {'color': '#a855f7'},
            'bgcolor': "rgba(255,255,255,0.04)",
            'borderwidth': 0,
        }
    ))
    gauge.update_layout(
        height=220, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", font={'color': "#f2f0f5"}
    )
    st.markdown('<div class="card"><div class="card-title">Portfolio Health Score</div>', unsafe_allow_html=True)
    st.plotly_chart(gauge, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

with c5:
    period = st.radio("", ["1D", "1W", "1M", "6M", "1Y"], index=4, horizontal=True, label_visibility="collapsed")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=perf["month"], y=perf["value"], mode="lines",
        line=dict(color="#c084fc", width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(168,85,247,0.12)"
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#7a7488"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#7a7488"),
        hovermode="x unified",
        font=dict(color="#f2f0f5"),
    )
    st.markdown('<div class="card"><div class="card-title">Portfolio Performance</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)
