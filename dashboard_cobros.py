import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="AR Collections Dashboard", layout="wide", initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg0:#111214; --bg1:#18191d; --bg2:#1f2128; --bg3:#27292f;
    --border:#2e3038;
    --orange:#ff6b35; --yellow:#ffc300; --green:#22c55e; --red:#ef4444;
    --t1:#f0f0f0; --t2:#9ca3af; --t3:#4b5563;
}
html,body,[class*="css"],.stApp { font-family:'Inter',sans-serif !important; background:var(--bg0) !important; color:var(--t1) !important; }
.block-container { padding:1.2rem 1.6rem 3rem !important; max-width:100% !important; }
#MainMenu,footer,header { visibility:hidden; }

/* Sidebar */
[data-testid="stSidebar"] { background:var(--bg1) !important; border-right:1px solid var(--border) !important; min-width:260px !important; }
[data-testid="stSidebar"] > div:first-child { padding:1.2rem 1rem !important; }
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] div,[data-testid="stSidebar"] small { color:var(--t2) !important; }

/* File uploader — fully visible in dark mode */
[data-testid="stFileUploadDropzone"] { background:var(--bg2) !important; border:1.5px dashed rgba(255,107,53,0.45) !important; border-radius:10px !important; }
[data-testid="stFileUploadDropzone"] * { color:var(--t2) !important; }
[data-testid="stFileUploadDropzone"] button { background:var(--bg3) !important; color:var(--t1) !important; border:1px solid var(--border) !important; border-radius:6px !important; }
[data-testid="collapsedControl"] { background:var(--bg2) !important; border:1px solid var(--border) !important; color:var(--t1) !important; }

/* Scrollbar */
::-webkit-scrollbar{width:4px;height:4px} ::-webkit-scrollbar-track{background:var(--bg0)} ::-webkit-scrollbar-thumb{background:var(--bg3);border-radius:4px}

/* KPI card */
.kpi { background:var(--bg1); border:1px solid var(--border); border-radius:10px; padding:18px 20px; }
.kpi-label { font-size:0.6rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:var(--t3); margin-bottom:8px; }
.kpi-value { font-size:2rem; font-weight:900; line-height:1; letter-spacing:-.03em; }
.kpi-sub { font-size:0.66rem; color:var(--t2); margin-top:7px; font-weight:500; }
.kpi-bar { margin-top:12px; height:3px; border-radius:2px; background:var(--bg3); overflow:hidden; }
.kpi-bar-fill { height:100%; border-radius:2px; }

/* Section header */
.sec-hdr { display:flex; align-items:center; gap:10px; margin:1.6rem 0 0.8rem; padding-bottom:8px; border-bottom:1px solid var(--border); }
.sec-title { font-size:0.7rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--t1); }
.sec-badge { font-size:0.57rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase; background:rgba(255,107,53,.12); color:var(--orange); border:1px solid rgba(255,107,53,.3); border-radius:4px; padding:2px 8px; }

/* Download button */
.stDownloadButton>button { background:linear-gradient(135deg,#ff6b35,#e05a28) !important; color:#fff !important; border:none !important; border-radius:7px !important; font-size:0.75rem !important; font-weight:700 !important; letter-spacing:.04em !important; padding:.5rem 1.4rem !important; }
.stDownloadButton>button:hover { opacity:.85; }

/* Table */
[data-testid="stDataFrame"] { border-radius:10px !important; border:1px solid var(--border) !important; overflow:hidden !important; }
[data-testid="stDataFrame"] thead th { background:var(--bg2) !important; color:var(--t3) !important; font-size:0.6rem !important; letter-spacing:.1em !important; text-transform:uppercase !important; font-family:'JetBrains Mono',monospace !important; font-weight:700 !important; }
[data-testid="stDataFrame"] tbody td { font-family:'JetBrains Mono',monospace !important; font-size:0.78rem !important; color:var(--t1) !important; }

/* Info box */
.stAlert { background:rgba(255,107,53,.07) !important; border:1px solid rgba(255,107,53,.22) !important; border-radius:8px !important; color:var(--t1) !important; }

/* Main header */
.main-header { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:1.2rem; }
.main-title { font-size:1.5rem; font-weight:900; letter-spacing:-.03em; color:var(--t1); line-height:1; }
.main-title .acc { color:var(--orange); }
.main-sub { font-size:0.62rem; font-weight:600; color:var(--t3); text-transform:uppercase; letter-spacing:.1em; margin-top:5px; }
.ts-chip { font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:var(--t2); background:var(--bg2); border:1px solid var(--border); border-radius:6px; padding:5px 12px; white-space:nowrap; }

/* Empty state */
.empty-state { margin:3rem auto; max-width:400px; background:var(--bg1); border:1px solid var(--border); border-radius:14px; padding:3rem 2rem; text-align:center; }

/* Metric overrides — force dark theme on native st.metric */
[data-testid="stMetric"] { background:var(--bg1); border:1px solid var(--border); border-radius:10px; padding:16px 18px !important; }
[data-testid="stMetricLabel"] { color:var(--t3) !important; font-size:0.6rem !important; font-weight:700 !important; letter-spacing:.12em !important; text-transform:uppercase !important; }
[data-testid="stMetricValue"] { color:var(--t1) !important; font-size:1.6rem !important; font-weight:900 !important; letter-spacing:-.02em !important; font-family:'Inter',sans-serif !important; }
[data-testid="stMetricDelta"] { font-size:0.68rem !important; }

/* Progress bar */
.stProgress > div > div > div { background:var(--bg3) !important; border-radius:3px !important; }
.stProgress > div > div > div > div { border-radius:3px !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def limpiar_dinero(serie):
    return pd.to_numeric(serie.astype(str).str.replace('$','').str.replace(',','').str.strip(), errors='coerce').fillna(0)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Collection_List')
    return output.getvalue()

def fmt(v): return f"${v:,.2f}"
def pct(p, t): return round(p / t * 100, 1) if t else 0

THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color='#6b7280', size=10),
    margin=dict(l=8, r=8, t=30, b=8),
)
BUCKET_COLORS = ['#22c55e','#ffc300','#f97316','#ff6b35','#ef4444']


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='margin-bottom:1.4rem;padding-bottom:1.2rem;border-bottom:1px solid #2e3038'>
            <div style='font-size:1rem;font-weight:900;color:#f0f0f0;letter-spacing:-.02em;line-height:1.25'>
                ⚡ Collections<br><span style='color:#ff6b35'>Intelligence</span>
            </div>
            <div style='font-size:0.58rem;color:#4b5563;text-transform:uppercase;letter-spacing:.12em;margin-top:6px'>AR Analytics Platform</div>
        </div>
        <div style='font-size:0.6rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#4b5563;margin-bottom:8px'>📂 Aging Report (Excel)</div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["xlsx"], label_visibility="collapsed")
    st.markdown("""
        <div style='margin-top:1.6rem;padding-top:1.2rem;border-top:1px solid #2e3038'>
            <div style='font-size:0.58rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#4b5563;margin-bottom:8px'>Instructions</div>
            <div style='font-size:0.7rem;color:#6b7280;line-height:1.7'>
                Upload your Aging report in <strong style='color:#9ca3af'>.xlsx</strong> format.<br>
                The system auto-detects <em>Total AR, Current, Terms and Customer</em> columns.
            </div>
        </div>
    """, unsafe_allow_html=True)


# ── HEADER ────────────────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%d %b %Y  ·  %H:%M")
st.markdown(f"""
<div class='main-header'>
    <div>
        <div class='main-title'>Collections <span class='acc'>Dashboard</span></div>
        <div class='main-sub'>Collections Performance &amp; SLA Management</div>
    </div>
    <div class='ts-chip'>🕐 {now_str}</div>
</div>
<div style='border-bottom:1px solid #2e3038;margin-bottom:1.4rem'></div>
""", unsafe_allow_html=True)


# ── EMPTY STATE ───────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown("""
    <div class='empty-state'>
        <div style='font-size:2.4rem;margin-bottom:1rem'>📊</div>
        <div style='font-size:1rem;font-weight:800;color:#f0f0f0;margin-bottom:6px'>No data loaded</div>
        <div style='font-size:0.76rem;color:#9ca3af;line-height:1.65'>Upload your Aging report from the left panel to start the portfolio analysis.</div>
    </div>
    """, unsafe_allow_html=True)
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
    st.stop()

try:
    df[col_total]   = limpiar_dinero(df[col_total])
    df[col_current] = limpiar_dinero(df[col_current])
    df['Past_Due']  = (df[col_total] - df[col_current]).clip(lower=0)

    total_ar        = df[col_total].sum()
    total_current   = df[col_current].sum()
    total_past_due  = total_ar - total_current
    pct_past_due    = pct(total_past_due, total_ar)
    pct_current     = pct(total_current, total_ar)

    df_sla      = df[df['Past_Due'] > 0.01].copy().sort_values('Past_Due', ascending=False)
    n_overdue   = len(df_sla)
    n_total     = len(df)
    n_current   = n_total - n_overdue

    top5_total  = df_sla.head(5)['Past_Due'].sum() if not df_sla.empty else 0
    pct_top5    = pct(top5_total, total_past_due)
    avg_overdue = total_past_due / n_overdue if n_overdue else 0
    max_overdue = df_sla['Past_Due'].max() if not df_sla.empty else 0

    # Aging buckets
    buckets_map = {
        '1-30 Days':   next((c for c in df.columns if "1-30"  in c), None),
        '31-60 Days':  next((c for c in df.columns if "31-60" in c), None),
        '61-90 Days':  next((c for c in df.columns if "61-90" in c), None),
        '91-120 Days': next((c for c in df.columns if "91-120" in c), None),
        '121+ Days':   [c for c in df.columns if any(x in c for x in ["121","181","> 365"])],
    }
    bucket_vals = {}
    for name, col in buckets_map.items():
        if isinstance(col, list):
            bucket_vals[name] = sum(limpiar_dinero(df[c]).sum() for c in col)
        elif col:
            bucket_vals[name] = limpiar_dinero(df[col]).sum()
        else:
            bucket_vals[name] = 0


    # ── ROW 1: KPI CARDS ─────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4, gap="small")

    with c1:
        st.markdown(f"""
        <div class='kpi'>
            <div class='kpi-label'>Total Portfolio (AR)</div>
            <div class='kpi-value' style='color:#f0f0f0'>{fmt(total_ar)}</div>
            <div class='kpi-sub'>{n_total} active accounts</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:100%;background:#ff6b35'></div></div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class='kpi'>
            <div class='kpi-label'>Current (On Time)</div>
            <div class='kpi-value' style='color:#22c55e'>{fmt(total_current)}</div>
            <div class='kpi-sub'>{n_current} accounts · {pct_current}% of total</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_current}%;background:#22c55e'></div></div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class='kpi'>
            <div class='kpi-label'>Past Due (Overdue)</div>
            <div class='kpi-value' style='color:#ef4444'>{fmt(total_past_due)}</div>
            <div class='kpi-sub'>{n_overdue} accounts · {pct_past_due}% of total</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_past_due}%;background:#ef4444'></div></div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class='kpi'>
            <div class='kpi-label'>Top 5 Debtors</div>
            <div class='kpi-value' style='color:#ffc300'>{fmt(top5_total)}</div>
            <div class='kpi-sub'>{pct_top5}% of total overdue</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_top5}%;background:#ffc300'></div></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)


    # ── ROW 2: CHARTS ────────────────────────────────────────────────────────
    st.markdown("""
    <div class='sec-hdr'>
        <span class='sec-title'>Aging Distribution</span>
        <span class='sec-badge'>AGING ANALYSIS</span>
    </div>""", unsafe_allow_html=True)

    col_chart1, col_chart2, col_chart3 = st.columns([3, 2, 2], gap="small")

    with col_chart1:
        bnames  = list(bucket_vals.keys())
        bamount = list(bucket_vals.values())
        fig_bar = go.Figure(go.Bar(
            x=bnames, y=bamount,
            marker=dict(color=BUCKET_COLORS, line=dict(width=0)),
            text=[f"${v/1000:.1f}K" if v >= 1000 else f"${v:.0f}" for v in bamount],
            textposition='outside',
            textfont=dict(family='JetBrains Mono', size=9, color='#6b7280'),
        ))
        fig_bar.update_layout(
            **THEME,
            title=dict(text="Overdue by time bucket", font=dict(size=11, color='#6b7280'), x=0),
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10, color='#6b7280')),
            yaxis=dict(showgrid=True, gridcolor='#27292f', zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=9)),
            bargap=0.38,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        fig_donut = go.Figure(go.Pie(
            labels=['Current', 'Past Due'],
            values=[total_current, total_past_due],
            hole=0.68,
            marker=dict(colors=['#22c55e', '#ef4444'], line=dict(width=0)),
            textinfo='percent',
            textfont=dict(family='Inter', size=10, color='#f0f0f0'),
        ))
        fig_donut.update_layout(
            **THEME,
            title=dict(text="Portfolio health", font=dict(size=11, color='#6b7280'), x=0),
            showlegend=True,
            legend=dict(orientation='h', x=0.1, y=-0.15,
                        font=dict(size=10, color='#9ca3af'), bgcolor='rgba(0,0,0,0)'),
            annotations=[dict(
                text=f"<b>{pct_past_due:.0f}%</b><br>overdue",
                x=0.5, y=0.5, showarrow=False,
                font=dict(family='Inter', size=14, color='#ef4444'),
            )],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_chart3:
        top_n = min(8, len(df_sla))
        top_df = df_sla.head(top_n)
        customers = (top_df[col_customer].astype(str).str[:16].tolist()
                     if col_customer in top_df.columns else [f"#{i}" for i in range(top_n)])
        amounts = top_df['Past_Due'].tolist()
        fig_h = go.Figure(go.Bar(
            y=customers[::-1], x=amounts[::-1], orientation='h',
            marker=dict(color=amounts[::-1],
                        colorscale=[[0,'#ffc300'],[0.5,'#ff6b35'],[1,'#ef4444']],
                        line=dict(width=0)),
            text=[f"${v:,.0f}" for v in amounts[::-1]],
            textposition='outside',
            textfont=dict(family='JetBrains Mono', size=8, color='#6b7280'),
        ))
        fig_h.update_layout(
            **THEME,
            title=dict(text=f"Top {top_n} debtors", font=dict(size=11, color='#6b7280'), x=0),
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='#27292f', zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=8)),
            yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9, color='#9ca3af')),
        )
        st.plotly_chart(fig_h, use_container_width=True)


    # ── ROW 3: BREAKDOWN (native Streamlit, no raw HTML cards) ───────────────
    st.markdown("""
    <div class='sec-hdr'>
        <span class='sec-title'>Portfolio Breakdown</span>
        <span class='sec-badge'>COMPOSITION</span>
    </div>""", unsafe_allow_html=True)

    bk1, bk2, bk3 = st.columns(3, gap="small")

    # Card 1 — Aging composition
    with bk1:
        st.markdown("<div class='kpi'>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-label'>Aging Composition</div>", unsafe_allow_html=True)
        total_b = sum(bucket_vals.values()) or 1
        b_colors_map = {
            '1-30 Days':'#22c55e','31-60 Days':'#ffc300',
            '61-90 Days':'#f97316','91-120 Days':'#ff6b35','121+ Days':'#ef4444'
        }
        for name, val in bucket_vals.items():
            p = pct(val, total_b)
            col_l, col_r = st.columns([3, 1])
            with col_l:
                st.markdown(f"<span style='font-size:0.7rem;color:#9ca3af;font-weight:500'>{name}</span>", unsafe_allow_html=True)
                st.progress(int(p))
            with col_r:
                st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.72rem;font-weight:700;color:#f0f0f0;text-align:right;padding-top:4px'>${val/1000:.1f}K</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Card 2 — Account stats
    with bk2:
        st.markdown("<div class='kpi'>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-label'>Account Statistics</div>", unsafe_allow_html=True)
        pct_cv = pct(n_overdue, n_total)

        col_l, col_r = st.columns([3, 1])
        with col_l:
            st.markdown("<span style='font-size:0.7rem;color:#9ca3af'>Current</span>", unsafe_allow_html=True)
            st.progress(int(100 - pct_cv))
        with col_r:
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.72rem;font-weight:700;color:#22c55e;text-align:right;padding-top:4px'>{n_current}</div>", unsafe_allow_html=True)

        col_l2, col_r2 = st.columns([3, 1])
        with col_l2:
            st.markdown("<span style='font-size:0.7rem;color:#9ca3af'>Overdue</span>", unsafe_allow_html=True)
            st.progress(int(pct_cv))
        with col_r2:
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.72rem;font-weight:700;color:#ef4444;text-align:right;padding-top:4px'>{n_overdue}</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:14px;padding-top:10px;border-top:1px solid #2e3038'></div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div>
                <div style='font-size:0.58rem;color:#4b5563;text-transform:uppercase;letter-spacing:.08em'>Avg overdue</div>
                <div style='font-family:JetBrains Mono,monospace;font-size:0.85rem;font-weight:700;color:#ff6b35;margin-top:3px'>{fmt(avg_overdue)}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div>
                <div style='font-size:0.58rem;color:#4b5563;text-transform:uppercase;letter-spacing:.08em'>Max single</div>
                <div style='font-family:JetBrains Mono,monospace;font-size:0.85rem;font-weight:700;color:#ef4444;margin-top:3px'>{fmt(max_overdue)}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Card 3 — SLA summary
    with bk3:
        st.markdown(f"""
        <div class='kpi'>
            <div class='kpi-label'>SLA Touch Goal</div>
            <div class='kpi-value' style='color:#ffc300;font-size:2.4rem'>{n_overdue}</div>
            <div class='kpi-sub'>accounts to contact this week</div>
            <div style='margin-top:12px;padding:10px;background:#111214;border-radius:7px;display:flex;justify-content:space-between;align-items:center'>
                <span style='font-size:0.66rem;color:#6b7280'>Total exposure</span>
                <span style='font-family:JetBrains Mono,monospace;font-size:0.8rem;font-weight:700;color:#ff6b35'>{fmt(total_past_due)}</span>
            </div>
            <div style='margin-top:6px;padding:10px;background:#111214;border-radius:7px;display:flex;justify-content:space-between;align-items:center'>
                <span style='font-size:0.66rem;color:#6b7280'>% portfolio at risk</span>
                <span style='font-family:JetBrains Mono,monospace;font-size:0.8rem;font-weight:700;color:#ef4444'>{pct_past_due}%</span>
            </div>
        </div>""", unsafe_allow_html=True)


    # ── ROW 4: SLA TABLE ─────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='sec-hdr'>
        <span class='sec-title'>Priority Action List</span>
        <span class='sec-badge'>100% TOUCH GOAL · {n_overdue} ACCOUNTS</span>
    </div>""", unsafe_allow_html=True)

    cols_show = [c for c in [col_customer, 'Past_Due', col_terms, col_total] if c in df_sla.columns]
    reporte_agente = df_sla[cols_show].copy()

    btn_col, _ = st.columns([2, 5])
    with btn_col:
        st.download_button(
            label="📥 Download Collection List (Excel)",
            data=to_excel(reporte_agente),
            file_name=f'SLA_Collections_{pd.Timestamp.now().strftime("%Y-%m-%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    display_df = reporte_agente.copy()
    if 'Past_Due' in display_df.columns:
        display_df['Past_Due'] = display_df['Past_Due'].apply(lambda x: f"${x:,.2f}")
    if col_total in display_df.columns:
        display_df[col_total] = display_df[col_total].apply(lambda x: f"${x:,.2f}")
    display_df.rename(columns={'Past_Due': 'Past Due', col_total: 'Total AR'}, inplace=True)

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=380)

    st.info(f"💡 **{n_overdue} accounts** require action · Total overdue: **{fmt(total_past_due)}** ({pct_past_due}% of portfolio) · Avg per account: **{fmt(avg_overdue)}**")

except Exception as e:
    st.error(f"❌ Error processing file: {e}")
    st.exception(e)
