import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(
    page_title="AR Collections Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── THEME STATE ───────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark = st.session_state.dark_mode

# ── THEME PALETTES ────────────────────────────────────────────────────────────
if dark:
    T = {
        "bg0": "#0e0f11",
        "bg1": "#16181c",
        "bg2": "#1c1e24",
        "bg3": "#23262e",
        "border": "#2a2d37",
        "t1": "#f0f0f0",
        "t2": "#9ca3af",
        "t3": "#4b5563",
        "t4": "#374151",
        "card_bg": "#16181c",
        "input_bg": "#1c1e24",
        "progress_bg": "#23262e",
        "row_hover": "#1c1e24",
        "stat_bg": "#0e0f11",
        "plot_grid": "#23262e",
        "toggle_bg": "#23262e",
        "toggle_icon": "☀️",
        "toggle_label": "Light mode",
    }
else:
    T = {
        "bg0": "#f4f5f7",
        "bg1": "#ffffff",
        "bg2": "#f0f1f3",
        "bg3": "#e5e7eb",
        "border": "#d1d5db",
        "t1": "#111214",
        "t2": "#4b5563",
        "t3": "#9ca3af",
        "t4": "#d1d5db",
        "card_bg": "#ffffff",
        "input_bg": "#f9fafb",
        "progress_bg": "#e5e7eb",
        "row_hover": "#f9fafb",
        "stat_bg": "#f4f5f7",
        "plot_grid": "#e5e7eb",
        "toggle_bg": "#e5e7eb",
        "toggle_icon": "🌙",
        "toggle_label": "Dark mode",
    }

ORANGE = "#ff6b35"
YELLOW = "#ffc300"
GREEN  = "#22c55e"
RED    = "#ef4444"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');

html, body, .stApp, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
    background: {T['bg0']} !important;
    color: {T['t1']} !important;
}}
.block-container {{ padding: 0 !important; max-width: 100% !important; }}
#MainMenu, footer, header,
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {{ display: none !important; }}

::-webkit-scrollbar {{ width:4px; height:4px; }}
::-webkit-scrollbar-track {{ background: {T['bg0']}; }}
::-webkit-scrollbar-thumb {{ background: {T['bg3']}; border-radius:4px; }}

/* ── Top bar ── */
.topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 13px 28px;
    background: {T['bg1']};
    border-bottom: 1px solid {T['border']};
    position: sticky;
    top: 0;
    z-index: 100;
}}
.logo {{ font-size:1.05rem; font-weight:900; color:{T['t1']}; letter-spacing:-.02em; line-height:1.2; }}
.logo span {{ color:{ORANGE}; }}
.logo-sub {{ font-size:0.54rem; font-weight:600; color:{T['t3']}; text-transform:uppercase; letter-spacing:.12em; margin-top:2px; }}
.ts-chip {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.63rem; color: {T['t2']};
    background: {T['bg2']}; border: 1px solid {T['border']};
    border-radius: 6px; padding: 5px 12px; white-space:nowrap;
}}
.topbar-right {{ display:flex; align-items:center; gap:10px; }}

/* ── Toggle button ── */
div[data-testid="stButton"] > button.toggle-btn,
.stButton > button {{
    background: {T['toggle_bg']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 8px !important;
    color: {T['t1']} !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    padding: 5px 14px !important;
    cursor: pointer !important;
    letter-spacing: .02em;
    transition: background .15s;
    white-space: nowrap;
}}
.stButton > button:hover {{
    background: {T['bg3']} !important;
    border-color: {ORANGE} !important;
}}

/* ── Main wrap ── */
.main-wrap {{ padding: 18px 28px 50px; background: {T['bg0']}; }}

/* ── Section header ── */
.sec-hdr {{
    display:flex; align-items:center; gap:10px;
    margin: 22px 0 12px; padding-bottom:8px;
    border-bottom: 1px solid {T['border']};
}}
.sec-title {{
    font-size:0.67rem; font-weight:700;
    letter-spacing:.1em; text-transform:uppercase; color:{T['t1']};
}}
.sec-badge {{
    font-size:0.54rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
    background: rgba(255,107,53,.12); color:{ORANGE};
    border:1px solid rgba(255,107,53,.3); border-radius:4px; padding:2px 8px;
}}

/* ── KPI card ── */
.kpi {{
    background:{T['card_bg']}; border:1px solid {T['border']};
    border-radius:10px; padding:18px 20px;
}}
.kpi-label {{
    font-size:0.57rem; font-weight:700; letter-spacing:.12em;
    text-transform:uppercase; color:{T['t3']}; margin-bottom:8px;
}}
.kpi-value {{
    font-size:1.85rem; font-weight:900; line-height:1; letter-spacing:-.03em;
}}
.kpi-sub {{ font-size:0.63rem; color:{T['t2']}; margin-top:7px; font-weight:500; }}
.kpi-bar {{ margin-top:12px; height:2px; border-radius:2px; background:{T['progress_bg']}; overflow:hidden; }}
.kpi-bar-fill {{ height:100%; border-radius:2px; }}

/* ── Expander ── */
[data-testid="stExpander"] {{
    background: {T['card_bg']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    overflow: hidden;
}}
[data-testid="stExpander"] summary {{
    color: {T['t1']} !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: .05em;
    padding: 12px 16px !important;
    background: {T['bg2']} !important;
}}
[data-testid="stExpander"] summary:hover {{ background:{T['bg3']} !important; }}
[data-testid="stExpander"] > div {{ padding: 14px 16px !important; background:{T['card_bg']} !important; }}

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {{
    background: {T['input_bg']} !important;
    border: 1.5px dashed rgba(255,107,53,.45) !important;
    border-radius: 10px !important;
}}
[data-testid="stFileUploadDropzone"] * {{ color:{T['t2']} !important; background:transparent !important; }}
[data-testid="stFileUploadDropzone"] button {{
    background:{T['bg3']} !important; color:{T['t1']} !important;
    border:1px solid {T['border']} !important; border-radius:6px !important;
}}
[data-testid="stFileUploadDropzone"] svg {{ opacity:.5; }}

/* ── Download button ── */
.stDownloadButton > button {{
    background: linear-gradient(135deg,#ff6b35,#d95a25) !important;
    color:#fff !important; border:none !important; border-radius:8px !important;
    font-size:0.74rem !important; font-weight:700 !important;
    letter-spacing:.04em !important; padding:.48rem 1.3rem !important;
}}
.stDownloadButton > button:hover {{ opacity:.85 !important; }}

/* ── Table ── */
[data-testid="stDataFrame"] {{
    border-radius:10px !important; border:1px solid {T['border']} !important; overflow:hidden !important;
}}
[data-testid="stDataFrame"] thead th {{
    background:{T['bg2']} !important; color:{T['t3']} !important;
    font-size:0.57rem !important; letter-spacing:.1em !important;
    text-transform:uppercase !important;
    font-family:'JetBrains Mono',monospace !important; font-weight:700 !important;
}}
[data-testid="stDataFrame"] tbody td {{
    font-family:'JetBrains Mono',monospace !important;
    font-size:0.76rem !important; color:{T['t1']} !important;
}}

/* ── Progress bars ── */
[data-testid="stProgressBar"] > div {{
    background:{T['progress_bg']} !important; border-radius:3px;
}}
[data-testid="stProgressBar"] > div > div {{
    background:{ORANGE} !important; border-radius:3px;
}}

/* ── Alert ── */
.stAlert {{
    background:rgba(255,107,53,.07) !important;
    border:1px solid rgba(255,107,53,.2) !important;
    border-radius:8px !important; color:{T['t1']} !important;
}}

/* ── Generic text ── */
p, .stMarkdown p {{ color:{T['t2']} !important; font-size:0.75rem; }}
label {{ color:{T['t2']} !important; }}
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def limpiar_dinero(s):
    return pd.to_numeric(
        s.astype(str).str.replace('$','').str.replace(',','').str.strip(),
        errors='coerce'
    ).fillna(0)

def to_excel(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Collection_List')
    return out.getvalue()

def fmt(v):    return f"${v:,.2f}"
def pct(p, t): return round(p / t * 100, 1) if t else 0

THEME_PLOT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter,sans-serif', color=T['t3'], size=10),
    margin=dict(l=8, r=8, t=30, b=8),
)
B_COLORS = [GREEN, YELLOW, '#f97316', ORANGE, RED]


# ── TOP BAR ───────────────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%d %b %Y  ·  %H:%M")

# Render topbar HTML + put toggle button inline via columns trick
bar_left, bar_right = st.columns([6, 1])
with bar_left:
    st.markdown(f"""
    <div style='
        background:{T['bg1']};
        border-bottom:1px solid {T['border']};
        padding:13px 28px 13px 0;
        display:flex; align-items:center; gap:20px;
    '>
        <div>
            <div class='logo'>⚡ Collections <span>Intelligence</span></div>
            <div class='logo-sub'>AR Analytics Platform</div>
        </div>
        <div class='ts-chip'>🕐 {now_str}</div>
    </div>
    """, unsafe_allow_html=True)

with bar_right:
    st.markdown(f"<div style='background:{T['bg1']};border-bottom:1px solid {T['border']};padding:13px 28px 13px 0;display:flex;align-items:center;justify-content:flex-end;height:100%'>", unsafe_allow_html=True)
    toggle_label = f"{T['toggle_icon']}  {T['toggle_label']}"
    if st.button(toggle_label, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Thin separator line
st.markdown(f"<div style='height:1px;background:{T['border']};margin:0'></div>", unsafe_allow_html=True)

# Main content wrapper
st.markdown(f"<div style='padding:18px 28px 50px;background:{T['bg0']}'>", unsafe_allow_html=True)


# ── UPLOAD PANEL (collapsible) ────────────────────────────────────────────────
with st.expander("📂  Upload Aging Report  —  click to expand / collapse", expanded=True):
    col_up, col_info = st.columns([2, 3], gap="large")
    with col_up:
        uploaded_file = st.file_uploader(
            "Drop your Excel Aging report here",
            type=["xlsx"],
            help="Supports .xlsx files. Auto-detects Total AR, Current, Terms and Customer columns."
        )
    with col_info:
        st.markdown(f"""
        <div style='padding-top:6px'>
            <div style='font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:{T['t3']};margin-bottom:10px'>Expected Columns</div>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px'>
                <div style='background:{T['bg2']};border:1px solid {T['border']};border-radius:7px;padding:8px 12px'>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{ORANGE};font-weight:700'>Total AR</div>
                    <div style='font-size:0.6rem;color:{T['t3']};margin-top:2px'>Total receivables</div>
                </div>
                <div style='background:{T['bg2']};border:1px solid {T['border']};border-radius:7px;padding:8px 12px'>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{GREEN};font-weight:700'>Current</div>
                    <div style='font-size:0.6rem;color:{T['t3']};margin-top:2px'>On-time balance</div>
                </div>
                <div style='background:{T['bg2']};border:1px solid {T['border']};border-radius:7px;padding:8px 12px'>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T['t2']};font-weight:700'>Customer</div>
                    <div style='font-size:0.6rem;color:{T['t3']};margin-top:2px'>Account name</div>
                </div>
                <div style='background:{T['bg2']};border:1px solid {T['border']};border-radius:7px;padding:8px 12px'>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T['t2']};font-weight:700'>Terms</div>
                    <div style='font-size:0.6rem;color:{T['t3']};margin-top:2px'>Payment terms</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── EMPTY STATE ───────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown(f"""
    <div style='margin:3rem auto;max-width:440px;background:{T['card_bg']};
                border:1px solid {T['border']};border-radius:14px;
                padding:3rem 2rem;text-align:center'>
        <div style='font-size:2.2rem;margin-bottom:1rem'>📊</div>
        <div style='font-size:1rem;font-weight:800;color:{T['t1']};margin-bottom:8px'>No data loaded</div>
        <div style='font-size:0.76rem;color:{T['t2']};line-height:1.65'>
            Upload your Aging report using the panel above to start the portfolio analysis.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ── LOAD & PROCESS ────────────────────────────────────────────────────────────
df = pd.read_excel(uploaded_file)
df.columns = [str(c).strip() for c in df.columns]

col_total    = next((c for c in df.columns if "Total AR" in c), None)
col_customer = 'Customer'
col_terms    = 'Terms'
col_current  = 'Current'

if not col_total or col_current not in df.columns:
    st.error("⚠️ Required columns not found (Total AR, Current). Please check the file format.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

try:
    df[col_total]   = limpiar_dinero(df[col_total])
    df[col_current] = limpiar_dinero(df[col_current])
    df['Past_Due']  = (df[col_total] - df[col_current]).clip(lower=0)

    total_ar      = df[col_total].sum()
    total_current = df[col_current].sum()
    total_pd      = total_ar - total_current
    pct_pd        = pct(total_pd, total_ar)
    pct_cur       = pct(total_current, total_ar)

    df_sla     = df[df['Past_Due'] > 0.01].copy().sort_values('Past_Due', ascending=False)
    n_overdue  = len(df_sla)
    n_total    = len(df)
    n_current  = n_total - n_overdue

    top5_total = df_sla.head(5)['Past_Due'].sum() if not df_sla.empty else 0
    pct_top5   = pct(top5_total, total_pd)
    avg_pd     = total_pd / n_overdue if n_overdue else 0
    max_pd     = df_sla['Past_Due'].max() if not df_sla.empty else 0

    buckets_map = {
        '1-30 Days':   next((c for c in df.columns if "1-30"  in c), None),
        '31-60 Days':  next((c for c in df.columns if "31-60" in c), None),
        '61-90 Days':  next((c for c in df.columns if "61-90" in c), None),
        '91-120 Days': next((c for c in df.columns if "91-120" in c), None),
        '121+ Days':   [c for c in df.columns if any(x in c for x in ["121","181","> 365"])],
    }
    bucket_vals = {}
    for name, col in buckets_map.items():
        if isinstance(col, list): bucket_vals[name] = sum(limpiar_dinero(df[c]).sum() for c in col)
        elif col:                 bucket_vals[name] = limpiar_dinero(df[col]).sum()
        else:                     bucket_vals[name] = 0


    # ── KPI CARDS ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='sec-hdr'>
        <span class='sec-title'>Portfolio Overview</span>
        <span class='sec-badge'>LIVE</span>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>Total Portfolio (AR)</div>
            <div class='kpi-value' style='color:{T['t1']}'>{fmt(total_ar)}</div>
            <div class='kpi-sub'>{n_total} active accounts</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:100%;background:{ORANGE}'></div></div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>Current (On Time)</div>
            <div class='kpi-value' style='color:{GREEN}'>{fmt(total_current)}</div>
            <div class='kpi-sub'>{n_current} accounts · {pct_cur}% of total</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_cur}%;background:{GREEN}'></div></div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>Past Due (Overdue)</div>
            <div class='kpi-value' style='color:{RED}'>{fmt(total_pd)}</div>
            <div class='kpi-sub'>{n_overdue} accounts · {pct_pd}% of total</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_pd}%;background:{RED}'></div></div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>Top 5 Debtors</div>
            <div class='kpi-value' style='color:{YELLOW}'>{fmt(top5_total)}</div>
            <div class='kpi-sub'>{pct_top5}% of total overdue</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{min(pct_top5,100)}%;background:{YELLOW}'></div></div>
        </div>""", unsafe_allow_html=True)


    # ── CHARTS ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='sec-hdr'>
        <span class='sec-title'>Aging Distribution</span>
        <span class='sec-badge'>ANALYSIS</span>
    </div>""", unsafe_allow_html=True)

    ch1, ch2, ch3 = st.columns([3, 2, 2], gap="small")

    with ch1:
        bnames  = list(bucket_vals.keys())
        bamount = list(bucket_vals.values())
        fig_bar = go.Figure(go.Bar(
            x=bnames, y=bamount,
            marker=dict(color=B_COLORS, line=dict(width=0)),
            text=[f"${v/1000:.1f}K" if v >= 1000 else f"${v:.0f}" for v in bamount],
            textposition='outside',
            textfont=dict(family='JetBrains Mono', size=9, color=T['t3']),
        ))
        fig_bar.update_layout(
            **THEME_PLOT,
            title=dict(text="Overdue by time bucket", font=dict(size=11, color=T['t3']), x=0),
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10, color=T['t3'])),
            yaxis=dict(showgrid=True, gridcolor=T['plot_grid'], zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=9)),
            bargap=0.38,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with ch2:
        fig_d = go.Figure(go.Pie(
            labels=['Current', 'Past Due'], values=[total_current, total_pd],
            hole=0.68, marker=dict(colors=[GREEN, RED], line=dict(width=0)),
            textinfo='percent', textfont=dict(family='Inter', size=10, color=T['t1']),
        ))
        fig_d.update_layout(
            **THEME_PLOT,
            title=dict(text="Portfolio health", font=dict(size=11, color=T['t3']), x=0),
            showlegend=True,
            legend=dict(orientation='h', x=0.05, y=-0.12,
                        font=dict(size=10, color=T['t2']), bgcolor='rgba(0,0,0,0)'),
            annotations=[dict(
                text=f"<b>{pct_pd:.0f}%</b><br>overdue",
                x=0.5, y=0.5, showarrow=False,
                font=dict(family='Inter', size=14, color=RED),
            )],
        )
        st.plotly_chart(fig_d, use_container_width=True)

    with ch3:
        top_n  = min(8, len(df_sla))
        top_df = df_sla.head(top_n)
        custs  = (top_df[col_customer].astype(str).str[:16].tolist()
                  if col_customer in top_df.columns else [f"#{i}" for i in range(top_n)])
        amts   = top_df['Past_Due'].tolist()
        fig_h  = go.Figure(go.Bar(
            y=custs[::-1], x=amts[::-1], orientation='h',
            marker=dict(color=amts[::-1],
                        colorscale=[[0, YELLOW], [0.5, ORANGE], [1, RED]],
                        line=dict(width=0)),
            text=[f"${v:,.0f}" for v in amts[::-1]],
            textposition='outside',
            textfont=dict(family='JetBrains Mono', size=8, color=T['t3']),
        ))
        fig_h.update_layout(
            **THEME_PLOT,
            title=dict(text=f"Top {top_n} debtors", font=dict(size=11, color=T['t3']), x=0),
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor=T['plot_grid'], zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=8)),
            yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9, color=T['t2'])),
        )
        st.plotly_chart(fig_h, use_container_width=True)


    # ── BREAKDOWN ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='sec-hdr'>
        <span class='sec-title'>Portfolio Breakdown</span>
        <span class='sec-badge'>COMPOSITION</span>
    </div>""", unsafe_allow_html=True)

    bk1, bk2, bk3 = st.columns(3, gap="small")

    with bk1:
        st.markdown(f"<div class='kpi'><div class='kpi-label'>Aging Composition</div></div>", unsafe_allow_html=True)
        total_b = sum(bucket_vals.values()) or 1
        b_color_list = [GREEN, YELLOW, '#f97316', ORANGE, RED]
        for (name, val), color in zip(bucket_vals.items(), b_color_list):
            p = int(pct(val, total_b))
            r1, r2 = st.columns([3, 1])
            with r1:
                st.markdown(f"<span style='font-size:0.67rem;color:{T['t2']}'>{name}</span>", unsafe_allow_html=True)
                st.progress(p)
            with r2:
                st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.68rem;font-weight:700;color:{color};padding-top:6px;text-align:right'>${val/1000:.1f}K</div>", unsafe_allow_html=True)

    with bk2:
        pct_ov = int(pct(n_overdue, n_total))
        st.markdown(f"<div class='kpi'><div class='kpi-label'>Account Status</div></div>", unsafe_allow_html=True)
        r1, r2 = st.columns([3, 1])
        with r1:
            st.markdown(f"<span style='font-size:0.67rem;color:{T['t2']}'>Current</span>", unsafe_allow_html=True)
            st.progress(100 - pct_ov)
        with r2:
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.68rem;font-weight:700;color:{GREEN};padding-top:6px;text-align:right'>{n_current}</div>", unsafe_allow_html=True)
        r3, r4 = st.columns([3, 1])
        with r3:
            st.markdown(f"<span style='font-size:0.67rem;color:{T['t2']}'>Overdue</span>", unsafe_allow_html=True)
            st.progress(pct_ov)
        with r4:
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.68rem;font-weight:700;color:{RED};padding-top:6px;text-align:right'>{n_overdue}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div style='font-size:0.56rem;color:{T['t3']};text-transform:uppercase;letter-spacing:.08em'>Avg overdue</div>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.82rem;font-weight:700;color:{ORANGE};margin-top:2px'>{fmt(avg_pd)}</div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div style='font-size:0.56rem;color:{T['t3']};text-transform:uppercase;letter-spacing:.08em'>Max single</div>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.82rem;font-weight:700;color:{RED};margin-top:2px'>{fmt(max_pd)}</div>
            """, unsafe_allow_html=True)

    with bk3:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>SLA Touch Goal</div>
            <div class='kpi-value' style='color:{YELLOW};font-size:2.3rem'>{n_overdue}</div>
            <div class='kpi-sub'>accounts to contact this week</div>
            <div style='margin-top:14px;padding:10px;background:{T['stat_bg']};border-radius:7px;display:flex;justify-content:space-between;align-items:center'>
                <span style='font-size:0.63rem;color:{T['t2']}'>Total exposure</span>
                <span style='font-family:JetBrains Mono,monospace;font-size:0.77rem;font-weight:700;color:{ORANGE}'>{fmt(total_pd)}</span>
            </div>
            <div style='margin-top:6px;padding:10px;background:{T['stat_bg']};border-radius:7px;display:flex;justify-content:space-between;align-items:center'>
                <span style='font-size:0.63rem;color:{T['t2']}'>% portfolio at risk</span>
                <span style='font-family:JetBrains Mono,monospace;font-size:0.77rem;font-weight:700;color:{RED}'>{pct_pd}%</span>
            </div>
        </div>""", unsafe_allow_html=True)


    # ── PRIORITY ACTION LIST ───────────────────────────────────────────────────
    st.markdown(f"""
    <div class='sec-hdr'>
        <span class='sec-title'>Priority Action List</span>
        <span class='sec-badge'>100% TOUCH GOAL · {n_overdue} ACCOUNTS</span>
    </div>""", unsafe_allow_html=True)

    cols_show = [c for c in [col_customer, 'Past_Due', col_terms, col_total] if c in df_sla.columns]
    reporte   = df_sla[cols_show].copy()

    btn_col, _ = st.columns([2, 5])
    with btn_col:
        st.download_button(
            label="📥 Download Collection List (Excel)",
            data=to_excel(reporte),
            file_name=f'SLA_Collections_{pd.Timestamp.now().strftime("%Y-%m-%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    disp = reporte.copy()
    if 'Past_Due' in disp.columns: disp['Past_Due'] = disp['Past_Due'].apply(lambda x: f"${x:,.2f}")
    if col_total  in disp.columns: disp[col_total]  = disp[col_total].apply(lambda x: f"${x:,.2f}")
    disp.rename(columns={'Past_Due': 'Past Due', col_total: 'Total AR'}, inplace=True)
    st.dataframe(disp, use_container_width=True, hide_index=True, height=380)

    st.info(f"💡 **{n_overdue} accounts** need action · Total overdue: **{fmt(total_pd)}** ({pct_pd}% of portfolio) · Avg per account: **{fmt(avg_pd)}**")

except Exception as e:
    st.error(f"❌ Error processing file: {e}")
    st.exception(e)

st.markdown("</div>", unsafe_allow_html=True)
