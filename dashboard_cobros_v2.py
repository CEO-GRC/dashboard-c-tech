import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="AR Collections Intelligence", layout="wide", initial_sidebar_state="expanded")

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg0:#0d0e11; --bg1:#13141a; --bg2:#1a1c24; --bg3:#22242e;
    --border:#2a2d3a;
    --orange:#ff6b35; --yellow:#f59e0b; --green:#10b981; --red:#ef4444;
    --blue:#3b82f6; --purple:#8b5cf6;
    --t1:#f1f1f3; --t2:#8b8fa8; --t3:#404460;
}
html,body,[class*="css"],.stApp { font-family:'Inter',sans-serif !important; background:var(--bg0) !important; color:var(--t1) !important; }
.block-container { padding:1.2rem 1.6rem 3rem !important; max-width:100% !important; }
#MainMenu,footer,header { visibility:hidden; }

[data-testid="stSidebar"] { background:var(--bg1) !important; border-right:1px solid var(--border) !important; min-width:270px !important; }
[data-testid="stSidebar"] > div:first-child { padding:1.4rem 1.1rem !important; }
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,[data-testid="stSidebar"] small { color:var(--t2) !important; }

[data-testid="stFileUploadDropzone"] { background:var(--bg2) !important; border:1.5px dashed rgba(255,107,53,.4) !important; border-radius:10px !important; }
[data-testid="stFileUploadDropzone"] * { color:var(--t2) !important; }
[data-testid="stFileUploadDropzone"] button { background:var(--bg3) !important; color:var(--t1) !important; border:1px solid var(--border) !important; border-radius:6px !important; }

::-webkit-scrollbar{width:4px;height:4px} ::-webkit-scrollbar-track{background:var(--bg0)} ::-webkit-scrollbar-thumb{background:var(--bg3);border-radius:4px}

.kpi { background:var(--bg1); border:1px solid var(--border); border-radius:12px; padding:20px 22px; position:relative; overflow:hidden; }
.kpi::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
.kpi.orange::before { background:linear-gradient(90deg,#ff6b35,transparent); }
.kpi.green::before  { background:linear-gradient(90deg,#10b981,transparent); }
.kpi.red::before    { background:linear-gradient(90deg,#ef4444,transparent); }
.kpi.yellow::before { background:linear-gradient(90deg,#f59e0b,transparent); }
.kpi.blue::before   { background:linear-gradient(90deg,#3b82f6,transparent); }
.kpi.purple::before { background:linear-gradient(90deg,#8b5cf6,transparent); }
.kpi-label { font-size:0.58rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--t3); margin-bottom:10px; }
.kpi-value { font-size:1.9rem; font-weight:900; line-height:1; letter-spacing:-.04em; }
.kpi-sub { font-size:0.64rem; color:var(--t2); margin-top:8px; font-weight:500; }
.kpi-bar { margin-top:14px; height:3px; border-radius:2px; background:var(--bg3); overflow:hidden; }
.kpi-bar-fill { height:100%; border-radius:2px; }
.kpi-badge { display:inline-block; font-size:0.55rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase; border-radius:4px; padding:2px 7px; margin-top:8px; }

.sec-hdr { display:flex; align-items:center; gap:10px; margin:2rem 0 1rem; padding-bottom:10px; border-bottom:1px solid var(--border); }
.sec-title { font-size:0.68rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:var(--t1); }
.sec-badge { font-size:0.55rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase; background:rgba(255,107,53,.1); color:var(--orange); border:1px solid rgba(255,107,53,.25); border-radius:4px; padding:2px 8px; }

.main-header { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:1.6rem; }
.main-title { font-size:1.6rem; font-weight:900; letter-spacing:-.04em; color:var(--t1); line-height:1; }
.main-title .acc { color:var(--orange); }
.main-sub { font-size:0.6rem; font-weight:600; color:var(--t3); text-transform:uppercase; letter-spacing:.12em; margin-top:6px; }
.ts-chip { font-family:'JetBrains Mono',monospace; font-size:0.63rem; color:var(--t2); background:var(--bg2); border:1px solid var(--border); border-radius:6px; padding:5px 12px; }

.empty-state { margin:4rem auto; max-width:420px; background:var(--bg1); border:1px solid var(--border); border-radius:16px; padding:3.5rem 2.5rem; text-align:center; }

[data-testid="stDataFrame"] { border-radius:10px !important; border:1px solid var(--border) !important; overflow:hidden !important; }
[data-testid="stDataFrame"] thead th { background:var(--bg2) !important; color:var(--t3) !important; font-size:0.58rem !important; letter-spacing:.1em !important; text-transform:uppercase !important; font-family:'JetBrains Mono',monospace !important; font-weight:700 !important; }
[data-testid="stDataFrame"] tbody td { font-family:'JetBrains Mono',monospace !important; font-size:0.76rem !important; color:var(--t1) !important; }

.stDownloadButton>button { background:linear-gradient(135deg,#ff6b35,#e0522a) !important; color:#fff !important; border:none !important; border-radius:8px !important; font-size:0.73rem !important; font-weight:700 !important; letter-spacing:.05em !important; padding:.55rem 1.4rem !important; }
.stDownloadButton>button:hover { opacity:.85; }

.stAlert { background:rgba(255,107,53,.06) !important; border:1px solid rgba(255,107,53,.2) !important; border-radius:8px !important; color:var(--t1) !important; }

[data-testid="stMetric"] { background:var(--bg1) !important; border:1px solid var(--border) !important; border-radius:10px !important; padding:16px 18px !important; }
[data-testid="stMetricLabel"] { color:var(--t3) !important; font-size:0.58rem !important; font-weight:700 !important; letter-spacing:.12em !important; text-transform:uppercase !important; }
[data-testid="stMetricValue"] { color:var(--t1) !important; font-size:1.5rem !important; font-weight:900 !important; letter-spacing:-.02em !important; }
[data-testid="stMetricDelta"] { font-size:0.66rem !important; }

.stProgress > div > div > div { background:var(--bg3) !important; border-radius:3px !important; }
.stProgress > div > div > div > div { border-radius:3px !important; }

.risk-pill { display:inline-block; font-size:0.6rem; font-weight:700; border-radius:20px; padding:2px 10px; letter-spacing:.05em; text-transform:uppercase; }
.risk-high   { background:rgba(239,68,68,.15); color:#ef4444; border:1px solid rgba(239,68,68,.3); }
.risk-med    { background:rgba(245,158,11,.15); color:#f59e0b; border:1px solid rgba(245,158,11,.3); }
.risk-low    { background:rgba(16,185,129,.15); color:#10b981; border:1px solid rgba(16,185,129,.3); }

/* Tab styling */
[data-testid="stTabs"] [data-baseweb="tab-list"] { background:var(--bg1); border-radius:8px; border:1px solid var(--border); padding:4px; gap:2px; }
[data-testid="stTabs"] [data-baseweb="tab"] { background:transparent !important; color:var(--t2) !important; border-radius:6px !important; font-size:0.7rem !important; font-weight:600 !important; letter-spacing:.06em !important; text-transform:uppercase !important; }
[data-testid="stTabs"] [aria-selected="true"] { background:var(--bg3) !important; color:var(--t1) !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ─────────────────────────────────────────────────────────────────
def clean_money(s):
    return pd.to_numeric(
        s.astype(str).str.replace(r'[\$,\s]', '', regex=True).str.strip(),
        errors='coerce'
    ).fillna(0)

def to_excel_bytes(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Collections')
    return out.getvalue()

def fmt(v):    return f"${v:,.2f}"
def fmtk(v):   return f"${v/1000:,.1f}K" if abs(v) >= 1000 else f"${v:,.0f}"
def pct(p, t): return round(p / t * 100, 1) if t else 0

THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color='#8b8fa8', size=10),
    margin=dict(l=8, r=8, t=36, b=8),
)
BUCKET_COLORS = ['#10b981','#f59e0b','#f97316','#ff6b35','#ef4444','#dc2626','#991b1b']


# ── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='margin-bottom:1.6rem;padding-bottom:1.4rem;border-bottom:1px solid #2a2d3a'>
        <div style='font-size:1.05rem;font-weight:900;color:#f1f1f3;letter-spacing:-.025em;line-height:1.3'>
            ⚡ Collections<br><span style='color:#ff6b35'>Intelligence</span>
        </div>
        <div style='font-size:0.56rem;color:#404460;text-transform:uppercase;letter-spacing:.14em;margin-top:6px'>AR Analytics Platform · v2.0</div>
    </div>
    <div style='font-size:0.58rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#404460;margin-bottom:8px'>📂 Upload Aging Report</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("", type=["xlsx"], label_visibility="collapsed")

    st.markdown("""
    <div style='margin-top:1.8rem;padding-top:1.4rem;border-top:1px solid #2a2d3a'>
        <div style='font-size:0.58rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#404460;margin-bottom:10px'>Filters</div>
    </div>
    """, unsafe_allow_html=True)

    filter_collector = st.multiselect("Collector", [], placeholder="All collectors...")
    filter_region    = st.multiselect("Region", [], placeholder="All regions...")
    filter_risk      = st.multiselect("Risk Category", [], placeholder="All categories...")

    st.markdown("""
    <div style='margin-top:1.8rem;padding-top:1.4rem;border-top:1px solid #2a2d3a'>
        <div style='font-size:0.64rem;color:#6b7080;line-height:1.75'>
            Upload the SAP Aging Report in <strong style='color:#9ca3af'>.xlsx</strong> format.<br>
            Auto-detects all aging buckets, collectors, risk tiers, and credit limits.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── HEADER ───────────────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%d %b %Y  ·  %H:%M")
st.markdown(f"""
<div class='main-header'>
    <div>
        <div class='main-title'>Collections <span class='acc'>Dashboard</span></div>
        <div class='main-sub'>AR Performance · Risk Exposure · Collector SLA</div>
    </div>
    <div class='ts-chip'>🕐 {now_str}</div>
</div>
<div style='border-bottom:1px solid #2a2d3a;margin-bottom:1.6rem'></div>
""", unsafe_allow_html=True)


# ── EMPTY STATE ──────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown("""
    <div class='empty-state'>
        <div style='font-size:2.6rem;margin-bottom:1.2rem'>📊</div>
        <div style='font-size:1.05rem;font-weight:800;color:#f1f1f3;margin-bottom:8px'>No data loaded</div>
        <div style='font-size:0.74rem;color:#8b8fa8;line-height:1.7'>Upload your SAP Aging Report from the left panel to start the analysis. Supports buckets up to 365+ days.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── LOAD & PARSE ─────────────────────────────────────────────────────────────
df_raw = pd.read_excel(uploaded_file)
df_raw.columns = [str(c).strip().replace('\n', ' ') for c in df_raw.columns]

# Column mapping (flexible)
def find_col(df, patterns):
    for p in patterns:
        for c in df.columns:
            if p.lower() in c.lower():
                return c
    return None

COL_PAYER     = find_col(df_raw, ['Payer']) or df_raw.columns[0]
COL_COLLECTOR = find_col(df_raw, ['Collector'])
COL_LOCATION  = find_col(df_raw, ['Location'])
COL_REGION    = find_col(df_raw, ['Region'])
COL_COMPANY   = find_col(df_raw, ['Company Code'])
COL_TERMS     = find_col(df_raw, ['Payment terms', 'Terms'])
COL_RISK      = find_col(df_raw, ['Cr/Mgt Risk Category', 'Risk'])
COL_CREDIT_LMT= find_col(df_raw, ['Credit Limits', 'Credit Limit'])
COL_TOTAL     = find_col(df_raw, ['Total'])
COL_CURRENT   = find_col(df_raw, ['Current'])

AGING_BUCKETS = {
    '1-30d':     find_col(df_raw, ['1 - 30', '1-30']),
    '31-60d':    find_col(df_raw, ['31 - 60', '31-60']),
    '61-90d':    find_col(df_raw, ['61 - 90', '61-90']),
    '91-120d':   find_col(df_raw, ['91 - 120', '91-120']),
    '121-180d':  find_col(df_raw, ['121 - 180', '121-180']),
    '181-365d':  find_col(df_raw, ['181 - 365', '181-365']),
    '365+d':     find_col(df_raw, ['> 365', '>365', '365+']),
}
AGING_BUCKETS = {k: v for k, v in AGING_BUCKETS.items() if v}

if not COL_TOTAL or not COL_CURRENT:
    st.error("⚠️ Could not find Total / Current columns. Please verify the file format.")
    st.stop()

try:
    df = df_raw.copy()

    # Clean money columns
    money_cols = [COL_TOTAL, COL_CURRENT, COL_CREDIT_LMT] + list(AGING_BUCKETS.values())
    for c in money_cols:
        if c and c in df.columns:
            df[c] = clean_money(df[c])

    df['_Past_Due'] = (df[COL_TOTAL] - df[COL_CURRENT]).clip(lower=0)
    for bname, bcol in AGING_BUCKETS.items():
        df[f'_B_{bname}'] = df[bcol].clip(lower=0)

    # ── SIDEBAR FILTER POPULATION ────────────────────────────────────────
    collectors = sorted(df[COL_COLLECTOR].dropna().unique().tolist()) if COL_COLLECTOR else []
    regions    = sorted(df[COL_REGION].dropna().unique().tolist()) if COL_REGION else []
    risks      = sorted(df[COL_RISK].dropna().unique().tolist()) if COL_RISK else []

    with st.sidebar:
        if collectors:
            filter_collector2 = st.multiselect("Collector", collectors, key='col2', placeholder="All collectors...")
        else:
            filter_collector2 = []
        if regions:
            filter_region2 = st.multiselect("Region", regions, key='reg2', placeholder="All regions...")
        else:
            filter_region2 = []
        if risks:
            filter_risk2 = st.multiselect("Risk Category", risks, key='risk2', placeholder="All categories...")
        else:
            filter_risk2 = []

    dff = df.copy()
    if filter_collector2 and COL_COLLECTOR: dff = dff[dff[COL_COLLECTOR].isin(filter_collector2)]
    if filter_region2    and COL_REGION:    dff = dff[dff[COL_REGION].isin(filter_region2)]
    if filter_risk2      and COL_RISK:      dff = dff[dff[COL_RISK].isin(filter_risk2)]

    # ── METRICS ──────────────────────────────────────────────────────────
    total_ar       = dff[COL_TOTAL].sum()
    total_current  = dff[COL_CURRENT].sum()
    total_past_due = dff['_Past_Due'].sum()
    pct_past_due   = pct(total_past_due, total_ar)
    pct_curr       = pct(total_current, total_ar)
    n_total        = len(dff)
    df_sla         = dff[dff['_Past_Due'] > 0.01].copy().sort_values('_Past_Due', ascending=False)
    n_overdue      = len(df_sla)
    n_current_accs = n_total - n_overdue
    avg_overdue    = total_past_due / n_overdue if n_overdue else 0
    max_overdue    = df_sla['_Past_Due'].max() if not df_sla.empty else 0
    top5_total     = df_sla.head(5)['_Past_Due'].sum()
    pct_top5       = pct(top5_total, total_past_due)

    credit_utilization = 0
    if COL_CREDIT_LMT:
        total_limit = dff[COL_CREDIT_LMT].sum()
        credit_utilization = pct(total_ar, total_limit)

    bucket_totals = {b: dff[f'_B_{b}'].sum() for b in AGING_BUCKETS}
    total_aged_90_plus = sum(v for k, v in bucket_totals.items() if any(x in k for x in ['91','121','181','365']))
    pct_90_plus = pct(total_aged_90_plus, total_past_due)

    # ── DSO ──────────────────────────────────────────────────────────────
    # Approximate DSO: (Total AR / Total AR) * 30 proxy — weight by bucket midpoints
    bucket_days = {'1-30d':15,'31-60d':45,'61-90d':75,'91-120d':105,'121-180d':150,'181-365d':270,'365+d':400}
    weighted_days = sum(bucket_totals.get(b,0)*d for b,d in bucket_days.items())
    total_aged = sum(bucket_totals.values()) or 1
    avg_days_overdue = weighted_days / total_aged if total_aged else 0


    # ════════════════════════════════════════════════════════════════════
    # ROW 1 — 6 KPI CARDS
    # ════════════════════════════════════════════════════════════════════
    k1, k2, k3, k4, k5, k6 = st.columns(6, gap="small")

    with k1:
        st.markdown(f"""
        <div class='kpi orange'>
            <div class='kpi-label'>Total AR Portfolio</div>
            <div class='kpi-value' style='color:#f1f1f3'>{fmtk(total_ar)}</div>
            <div class='kpi-sub'>{n_total} active accounts</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:100%;background:#ff6b35'></div></div>
        </div>""", unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class='kpi green'>
            <div class='kpi-label'>Current (On Time)</div>
            <div class='kpi-value' style='color:#10b981'>{fmtk(total_current)}</div>
            <div class='kpi-sub'>{n_current_accs} accts · {pct_curr}% of AR</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_curr}%;background:#10b981'></div></div>
        </div>""", unsafe_allow_html=True)

    with k3:
        color_pd = '#ef4444' if pct_past_due > 20 else '#f59e0b' if pct_past_due > 10 else '#10b981'
        st.markdown(f"""
        <div class='kpi red'>
            <div class='kpi-label'>Past Due Exposure</div>
            <div class='kpi-value' style='color:{color_pd}'>{fmtk(total_past_due)}</div>
            <div class='kpi-sub'>{n_overdue} accts · {pct_past_due}% at risk</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{min(pct_past_due,100)}%;background:{color_pd}'></div></div>
        </div>""", unsafe_allow_html=True)

    with k4:
        color_90 = '#ef4444' if pct_90_plus > 30 else '#f59e0b' if pct_90_plus > 15 else '#10b981'
        st.markdown(f"""
        <div class='kpi yellow'>
            <div class='kpi-label'>90+ Days Critical</div>
            <div class='kpi-value' style='color:{color_90}'>{fmtk(total_aged_90_plus)}</div>
            <div class='kpi-sub'>{pct_90_plus}% of overdue · high risk</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{min(pct_90_plus,100)}%;background:{color_90}'></div></div>
        </div>""", unsafe_allow_html=True)

    with k5:
        color_dso = '#ef4444' if avg_days_overdue > 90 else '#f59e0b' if avg_days_overdue > 45 else '#10b981'
        st.markdown(f"""
        <div class='kpi blue'>
            <div class='kpi-label'>Avg Days Overdue</div>
            <div class='kpi-value' style='color:{color_dso}'>{avg_days_overdue:.0f}d</div>
            <div class='kpi-sub'>weighted avg across buckets</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{min(avg_days_overdue/180*100,100):.0f}%;background:{color_dso}'></div></div>
        </div>""", unsafe_allow_html=True)

    with k6:
        color_cu = '#ef4444' if credit_utilization > 90 else '#f59e0b' if credit_utilization > 70 else '#10b981'
        cu_label = f"{credit_utilization:.1f}%" if COL_CREDIT_LMT else "N/A"
        st.markdown(f"""
        <div class='kpi purple'>
            <div class='kpi-label'>Credit Utilization</div>
            <div class='kpi-value' style='color:{color_cu}'>{cu_label}</div>
            <div class='kpi-sub'>AR vs Credit Limit</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{min(credit_utilization,100):.0f}%;background:{color_cu}'></div></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)


    # ════════════════════════════════════════════════════════════════════
    # TABS — Main sections
    # ════════════════════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs(["📈  Aging Analysis", "👤  Collector View", "⚠️  Risk & Credit", "📋  Action List"])


    # ── TAB 1: AGING ANALYSIS ────────────────────────────────────────────
    with tab1:
        st.markdown("""
        <div class='sec-hdr'>
            <span class='sec-title'>Aging Distribution</span>
            <span class='sec-badge'>BUCKET BREAKDOWN</span>
        </div>""", unsafe_allow_html=True)

        c_bar, c_donut, c_trend = st.columns([4, 2, 2], gap="small")

        with c_bar:
            bnames  = list(bucket_totals.keys())
            bamounts= list(bucket_totals.values())
            colors  = BUCKET_COLORS[:len(bnames)]
            fig_bar = go.Figure(go.Bar(
                x=bnames, y=bamounts,
                marker=dict(color=colors, line=dict(width=0)),
                text=[fmtk(v) for v in bamounts],
                textposition='outside',
                textfont=dict(family='JetBrains Mono', size=9, color='#8b8fa8'),
            ))
            fig_bar.update_layout(
                **THEME,
                title=dict(text="Overdue balance by aging bucket", font=dict(size=11, color='#8b8fa8'), x=0),
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10, color='#8b8fa8')),
                yaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False,
                           tickprefix='$', tickformat=',.0f', tickfont=dict(size=9)),
                bargap=0.35,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_donut:
            fig_donut = go.Figure(go.Pie(
                labels=['Current','Past Due'],
                values=[total_current, total_past_due],
                hole=0.7,
                marker=dict(colors=['#10b981','#ef4444'], line=dict(width=0)),
                textinfo='percent',
                textfont=dict(family='Inter', size=11, color='#f1f1f3'),
                pull=[0,0.04],
            ))
            fig_donut.update_layout(
                **THEME,
                title=dict(text="Portfolio health", font=dict(size=11, color='#8b8fa8'), x=0),
                showlegend=True,
                legend=dict(orientation='h', x=0.05, y=-0.15, font=dict(size=10, color='#8b8fa8'), bgcolor='rgba(0,0,0,0)'),
                annotations=[dict(
                    text=f"<b>{pct_past_due:.0f}%</b><br><span style='font-size:10px'>overdue</span>",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(family='Inter', size=14, color='#ef4444'),
                )],
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with c_trend:
            # Waterfall-style risk breakdown
            breakdown_labels = ['Current'] + list(bucket_totals.keys())
            breakdown_vals   = [total_current] + list(bucket_totals.values())
            breakdown_colors = ['#10b981'] + BUCKET_COLORS[:len(bucket_totals)]
            fig_risk = go.Figure(go.Bar(
                x=breakdown_vals, y=breakdown_labels, orientation='h',
                marker=dict(color=breakdown_colors, line=dict(width=0)),
                text=[fmtk(v) for v in breakdown_vals],
                textposition='outside',
                textfont=dict(family='JetBrains Mono', size=8, color='#8b8fa8'),
            ))
            fig_risk.update_layout(
                **THEME,
                title=dict(text="Balance by aging tier", font=dict(size=11, color='#8b8fa8'), x=0),
                showlegend=False,
                xaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False, tickprefix='$', tickformat=',.0f', tickfont=dict(size=8)),
                yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9, color='#8b8fa8')),
            )
            st.plotly_chart(fig_risk, use_container_width=True)

        # Aging composition details
        st.markdown("""
        <div class='sec-hdr' style='margin-top:1rem'>
            <span class='sec-title'>Aging Composition Detail</span>
            <span class='sec-badge'>% MIX</span>
        </div>""", unsafe_allow_html=True)

        comp_cols = st.columns(len(bucket_totals), gap="small")
        for i, (bname, bval) in enumerate(bucket_totals.items()):
            bpct = pct(bval, total_past_due)
            bcolor = BUCKET_COLORS[i] if i < len(BUCKET_COLORS) else '#ef4444'
            with comp_cols[i]:
                st.markdown(f"""
                <div class='kpi' style='padding:14px 16px;text-align:center'>
                    <div class='kpi-label'>{bname}</div>
                    <div style='font-size:1.4rem;font-weight:900;color:{bcolor};letter-spacing:-.03em'>{fmtk(bval)}</div>
                    <div style='font-size:0.62rem;color:#8b8fa8;margin-top:4px'>{bpct}% of overdue</div>
                    <div class='kpi-bar' style='margin-top:10px'><div class='kpi-bar-fill' style='width:{bpct}%;background:{bcolor}'></div></div>
                </div>""", unsafe_allow_html=True)


    # ── TAB 2: COLLECTOR VIEW ────────────────────────────────────────────
    with tab2:
        st.markdown("""
        <div class='sec-hdr'>
            <span class='sec-title'>Collector Performance</span>
            <span class='sec-badge'>SLA MANAGEMENT</span>
        </div>""", unsafe_allow_html=True)

        if COL_COLLECTOR:
            col_grp = dff.groupby(COL_COLLECTOR).agg(
                Total_AR     = (COL_TOTAL, 'sum'),
                Total_PD     = ('_Past_Due', 'sum'),
                Accounts     = (COL_TOTAL, 'count'),
                OD_Accounts  = ('_Past_Due', lambda x: (x > 0.01).sum()),
            ).reset_index()
            col_grp['% Past Due'] = col_grp.apply(lambda r: pct(r['Total_PD'], r['Total_AR']), axis=1)
            col_grp['Avg Overdue'] = col_grp.apply(lambda r: r['Total_PD']/r['OD_Accounts'] if r['OD_Accounts'] else 0, axis=1)
            col_grp = col_grp.sort_values('Total_PD', ascending=False)

            c_coll1, c_coll2 = st.columns([3, 2], gap="small")

            with c_coll1:
                fig_coll = go.Figure()
                fig_coll.add_trace(go.Bar(
                    name='Current', x=col_grp[COL_COLLECTOR],
                    y=col_grp['Total_AR'] - col_grp['Total_PD'],
                    marker_color='#10b981', marker_line_width=0,
                ))
                fig_coll.add_trace(go.Bar(
                    name='Past Due', x=col_grp[COL_COLLECTOR],
                    y=col_grp['Total_PD'],
                    marker_color='#ef4444', marker_line_width=0,
                ))
                fig_coll.update_layout(
                    **THEME,
                    barmode='stack',
                    title=dict(text="AR breakdown by collector", font=dict(size=11, color='#8b8fa8'), x=0),
                    legend=dict(orientation='h', x=0, y=1.12, font=dict(size=10, color='#8b8fa8'), bgcolor='rgba(0,0,0,0)'),
                    xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9, color='#8b8fa8')),
                    yaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False, tickprefix='$', tickformat=',.0f', tickfont=dict(size=9)),
                    bargap=0.3,
                )
                st.plotly_chart(fig_coll, use_container_width=True)

            with c_coll2:
                fig_scatter = go.Figure(go.Scatter(
                    x=col_grp['Accounts'],
                    y=col_grp['% Past Due'],
                    mode='markers+text',
                    marker=dict(
                        size=col_grp['Total_PD'].apply(lambda v: max(12, min(40, v/total_past_due*80 if total_past_due else 12))),
                        color=col_grp['% Past Due'],
                        colorscale=[[0,'#10b981'],[0.5,'#f59e0b'],[1,'#ef4444']],
                        line=dict(width=0),
                        showscale=False,
                    ),
                    text=col_grp[COL_COLLECTOR].str[:10],
                    textposition='top center',
                    textfont=dict(size=8, color='#8b8fa8'),
                ))
                fig_scatter.update_layout(
                    **THEME,
                    title=dict(text="Accounts vs % Past Due (bubble = exposure)", font=dict(size=11, color='#8b8fa8'), x=0),
                    xaxis=dict(title=dict(text="# Accounts", font=dict(size=9)), showgrid=True, gridcolor='#22242e', zeroline=False, tickfont=dict(size=9)),
                    yaxis=dict(title=dict(text="% Past Due", font=dict(size=9)), showgrid=True, gridcolor='#22242e', zeroline=False, tickfont=dict(size=9), ticksuffix='%'),
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

            # Collector table
            st.markdown("""<div class='sec-hdr' style='margin-top:.5rem'>
                <span class='sec-title'>Collector Summary Table</span>
                <span class='sec-badge'>DETAIL</span>
            </div>""", unsafe_allow_html=True)

            disp_coll = col_grp.copy()
            disp_coll['Total AR']     = disp_coll['Total_AR'].apply(fmt)
            disp_coll['Past Due']     = disp_coll['Total_PD'].apply(fmt)
            disp_coll['Avg Overdue']  = disp_coll['Avg Overdue'].apply(fmt)
            disp_coll['% Past Due']   = disp_coll['% Past Due'].apply(lambda x: f"{x:.1f}%")
            disp_coll = disp_coll.rename(columns={COL_COLLECTOR:'Collector','Accounts':'# Accts','OD_Accounts':'# Overdue'})
            disp_coll = disp_coll[['Collector','# Accts','# Overdue','Total AR','Past Due','% Past Due','Avg Overdue']]
            st.dataframe(disp_coll, use_container_width=True, hide_index=True)
        else:
            st.info("No Collector column found in this file.")

        # Region breakdown
        if COL_REGION:
            st.markdown("""<div class='sec-hdr'>
                <span class='sec-title'>Regional Breakdown</span>
                <span class='sec-badge'>GEOGRAPHY</span>
            </div>""", unsafe_allow_html=True)

            reg_grp = dff.groupby(COL_REGION).agg(
                Total_AR=('_Past_Due','sum'),  # reuse same pattern
                Accounts=(COL_TOTAL,'count'),
            ).reset_index().sort_values('Total_AR', ascending=True)

            fig_reg = go.Figure(go.Bar(
                y=reg_grp[COL_REGION], x=reg_grp['Total_AR'], orientation='h',
                marker=dict(color=reg_grp['Total_AR'],
                            colorscale=[[0,'#3b82f6'],[0.5,'#f59e0b'],[1,'#ef4444']],
                            line=dict(width=0)),
                text=reg_grp['Total_AR'].apply(fmtk),
                textposition='outside',
                textfont=dict(family='JetBrains Mono', size=8, color='#8b8fa8'),
            ))
            fig_reg.update_layout(
                **THEME,
                title=dict(text="Past Due by Region", font=dict(size=11, color='#8b8fa8'), x=0),
                showlegend=False,
                xaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False, tickprefix='$', tickformat=',.0f', tickfont=dict(size=8)),
                yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9, color='#9ca3af')),
            )
            st.plotly_chart(fig_reg, use_container_width=True)


    # ── TAB 3: RISK & CREDIT ─────────────────────────────────────────────
    with tab3:
        st.markdown("""
        <div class='sec-hdr'>
            <span class='sec-title'>Risk Exposure Analysis</span>
            <span class='sec-badge'>CREDIT RISK</span>
        </div>""", unsafe_allow_html=True)

        if COL_RISK:
            c_r1, c_r2 = st.columns([2, 3], gap="small")

            risk_grp = dff.groupby(COL_RISK).agg(
                Total_AR  = (COL_TOTAL, 'sum'),
                Past_Due  = ('_Past_Due', 'sum'),
                Accounts  = (COL_TOTAL, 'count'),
            ).reset_index().sort_values('Past_Due', ascending=False)

            with c_r1:
                risk_colors = []
                for r in risk_grp[COL_RISK]:
                    rs = str(r).upper()
                    if any(x in rs for x in ['HIGH','H/']):    risk_colors.append('#ef4444')
                    elif any(x in rs for x in ['MED','M/']):   risk_colors.append('#f59e0b')
                    else:                                       risk_colors.append('#10b981')

                fig_risk_pie = go.Figure(go.Pie(
                    labels=risk_grp[COL_RISK],
                    values=risk_grp['Past_Due'],
                    hole=0.6,
                    marker=dict(colors=risk_colors, line=dict(width=0)),
                    textinfo='percent+label',
                    textfont=dict(family='Inter', size=9, color='#f1f1f3'),
                ))
                fig_risk_pie.update_layout(
                    **THEME,
                    title=dict(text="Past Due by Risk Category", font=dict(size=11, color='#8b8fa8'), x=0),
                    showlegend=False,
                )
                st.plotly_chart(fig_risk_pie, use_container_width=True)

            with c_r2:
                fig_risk_bar = go.Figure(go.Bar(
                    x=risk_grp[COL_RISK], y=risk_grp['Past_Due'],
                    marker=dict(color=risk_colors, line=dict(width=0)),
                    text=risk_grp['Past_Due'].apply(fmtk),
                    textposition='outside',
                    textfont=dict(family='JetBrains Mono', size=9, color='#8b8fa8'),
                    customdata=risk_grp[['Total_AR','Accounts']].values,
                    hovertemplate="<b>%{x}</b><br>Past Due: %{y:$,.0f}<br>Total AR: %{customdata[0]:$,.0f}<br>Accounts: %{customdata[1]}<extra></extra>",
                ))
                fig_risk_bar.update_layout(
                    **THEME,
                    title=dict(text="Past Due amount by Risk Tier", font=dict(size=11, color='#8b8fa8'), x=0),
                    showlegend=False,
                    xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10, color='#9ca3af')),
                    yaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False, tickprefix='$', tickformat=',.0f', tickfont=dict(size=9)),
                    bargap=0.35,
                )
                st.plotly_chart(fig_risk_bar, use_container_width=True)

            # Risk KPIs
            risk_k1, risk_k2, risk_k3 = st.columns(3, gap="small")
            high_risk = risk_grp[risk_grp[COL_RISK].astype(str).str.upper().str.contains('HIGH|H/', na=False)]['Past_Due'].sum()
            med_risk  = risk_grp[risk_grp[COL_RISK].astype(str).str.upper().str.contains('MED|M/', na=False)]['Past_Due'].sum()
            low_risk  = total_past_due - high_risk - med_risk

            with risk_k1:
                st.markdown(f"""<div class='kpi red'>
                    <div class='kpi-label'>High Risk Exposure</div>
                    <div class='kpi-value' style='color:#ef4444'>{fmtk(high_risk)}</div>
                    <div class='kpi-sub'>{pct(high_risk, total_past_due):.1f}% of overdue</div>
                </div>""", unsafe_allow_html=True)
            with risk_k2:
                st.markdown(f"""<div class='kpi yellow'>
                    <div class='kpi-label'>Medium Risk Exposure</div>
                    <div class='kpi-value' style='color:#f59e0b'>{fmtk(med_risk)}</div>
                    <div class='kpi-sub'>{pct(med_risk, total_past_due):.1f}% of overdue</div>
                </div>""", unsafe_allow_html=True)
            with risk_k3:
                st.markdown(f"""<div class='kpi green'>
                    <div class='kpi-label'>Low Risk Exposure</div>
                    <div class='kpi-value' style='color:#10b981'>{fmtk(low_risk)}</div>
                    <div class='kpi-sub'>{pct(low_risk, total_past_due):.1f}% of overdue</div>
                </div>""", unsafe_allow_html=True)

        else:
            st.info("No Risk Category column detected in this file.")

        # Credit Limit vs AR
        if COL_CREDIT_LMT:
            st.markdown("""<div class='sec-hdr' style='margin-top:1.5rem'>
                <span class='sec-title'>Credit Limit Utilization</span>
                <span class='sec-badge'>CREDIT MGMT</span>
            </div>""", unsafe_allow_html=True)

            dff_cl = dff[dff[COL_CREDIT_LMT] > 0].copy()
            dff_cl['_Utilization'] = dff_cl[COL_TOTAL] / dff_cl[COL_CREDIT_LMT] * 100
            dff_cl['_Avail'] = (dff_cl[COL_CREDIT_LMT] - dff_cl[COL_TOTAL]).clip(lower=0)

            over_limit = dff_cl[dff_cl['_Utilization'] > 100]
            near_limit = dff_cl[(dff_cl['_Utilization'] >= 80) & (dff_cl['_Utilization'] <= 100)]

            cl1, cl2, cl3 = st.columns(3, gap="small")
            with cl1:
                st.markdown(f"""<div class='kpi orange'>
                    <div class='kpi-label'>Total Credit Limit</div>
                    <div class='kpi-value' style='color:#ff6b35'>{fmtk(dff_cl[COL_CREDIT_LMT].sum())}</div>
                    <div class='kpi-sub'>{credit_utilization:.1f}% utilized overall</div>
                </div>""", unsafe_allow_html=True)
            with cl2:
                st.markdown(f"""<div class='kpi red'>
                    <div class='kpi-label'>Over Credit Limit</div>
                    <div class='kpi-value' style='color:#ef4444'>{len(over_limit)}</div>
                    <div class='kpi-sub'>accounts exceeding limit</div>
                </div>""", unsafe_allow_html=True)
            with cl3:
                st.markdown(f"""<div class='kpi yellow'>
                    <div class='kpi-label'>Near Limit (80-100%)</div>
                    <div class='kpi-value' style='color:#f59e0b'>{len(near_limit)}</div>
                    <div class='kpi-sub'>accounts at risk of breach</div>
                </div>""", unsafe_allow_html=True)

            # Top utilization accounts
            top_util = dff_cl.nlargest(10, '_Utilization')[[COL_PAYER, COL_CREDIT_LMT, COL_TOTAL, '_Utilization', '_Past_Due']].copy()
            top_util.columns = ['Customer','Credit Limit','Total AR','Utilization %','Past Due']
            top_util['Credit Limit'] = top_util['Credit Limit'].apply(fmt)
            top_util['Total AR']     = top_util['Total AR'].apply(fmt)
            top_util['Past Due']     = top_util['Past Due'].apply(fmt)
            top_util['Utilization %']= top_util['Utilization %'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(top_util, use_container_width=True, hide_index=True, height=280)


    # ── TAB 4: ACTION LIST ───────────────────────────────────────────────
    with tab4:
        st.markdown(f"""
        <div class='sec-hdr'>
            <span class='sec-title'>Priority Action List</span>
            <span class='sec-badge'>SLA TOUCH GOAL · {n_overdue} ACCOUNTS</span>
        </div>""", unsafe_allow_html=True)

        # Summary strip
        a1, a2, a3, a4 = st.columns(4, gap="small")
        with a1:
            st.markdown(f"""<div class='kpi yellow'>
                <div class='kpi-label'>Accounts to Contact</div>
                <div class='kpi-value' style='color:#f59e0b'>{n_overdue}</div>
                <div class='kpi-sub'>overdue accounts this cycle</div>
            </div>""", unsafe_allow_html=True)
        with a2:
            st.markdown(f"""<div class='kpi red'>
                <div class='kpi-label'>Total Exposure</div>
                <div class='kpi-value' style='color:#ef4444'>{fmtk(total_past_due)}</div>
                <div class='kpi-sub'>{pct_past_due}% of portfolio</div>
            </div>""", unsafe_allow_html=True)
        with a3:
            st.markdown(f"""<div class='kpi orange'>
                <div class='kpi-label'>Avg per Account</div>
                <div class='kpi-value' style='color:#ff6b35'>{fmtk(avg_overdue)}</div>
                <div class='kpi-sub'>average overdue balance</div>
            </div>""", unsafe_allow_html=True)
        with a4:
            st.markdown(f"""<div class='kpi blue'>
                <div class='kpi-label'>Top 5 Concentration</div>
                <div class='kpi-value' style='color:#3b82f6'>{pct_top5:.1f}%</div>
                <div class='kpi-sub'>{fmtk(top5_total)} in top 5 accounts</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

        # Top debtors chart
        top_n = min(15, len(df_sla))
        top_df = df_sla.head(top_n)
        customers = (top_df[COL_PAYER].astype(str).str[:20].tolist()
                     if COL_PAYER in top_df.columns else [f"#{i}" for i in range(top_n)])
        amounts = top_df['_Past_Due'].tolist()
        fig_h = go.Figure(go.Bar(
            y=customers[::-1], x=amounts[::-1], orientation='h',
            marker=dict(
                color=amounts[::-1],
                colorscale=[[0,'#f59e0b'],[0.5,'#ff6b35'],[1,'#ef4444']],
                line=dict(width=0),
            ),
            text=[fmtk(v) for v in amounts[::-1]],
            textposition='outside',
            textfont=dict(family='JetBrains Mono', size=8, color='#8b8fa8'),
        ))
        fig_h.update_layout(
            **THEME,
            title=dict(text=f"Top {top_n} accounts by past due balance", font=dict(size=11, color='#8b8fa8'), x=0),
            showlegend=False,
            margin=dict(l=8, r=60, t=36, b=8),
            xaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=8)),
            yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9, color='#9ca3af')),
        )
        st.plotly_chart(fig_h, use_container_width=True)

        # Full action table
        st.markdown("""<div class='sec-hdr' style='margin-top:0'>
            <span class='sec-title'>Full Collection List</span>
            <span class='sec-badge'>DOWNLOAD READY</span>
        </div>""", unsafe_allow_html=True)

        # Build display table
        show_cols = [c for c in [
            COL_PAYER, COL_COLLECTOR, COL_LOCATION, COL_REGION,
            COL_TERMS, COL_RISK, COL_TOTAL, '_Past_Due',
        ] + [f'_B_{b}' for b in AGING_BUCKETS] if c and c in df_sla.columns]

        action_df = df_sla[show_cols].copy()

        rename_map = {
            COL_PAYER:'Customer', COL_COLLECTOR:'Collector',
            COL_LOCATION:'Location', COL_REGION:'Region',
            COL_TERMS:'Payment Terms', COL_RISK:'Risk Category',
            COL_TOTAL:'Total AR', '_Past_Due':'Past Due',
        }
        rename_map.update({f'_B_{b}': b for b in AGING_BUCKETS})
        action_df = action_df.rename(columns={k:v for k,v in rename_map.items() if k in action_df.columns})

        money_disp = ['Total AR','Past Due'] + list(AGING_BUCKETS.keys())
        for mc in money_disp:
            if mc in action_df.columns:
                action_df[mc] = action_df[mc].apply(fmt)

        btn_col, _ = st.columns([2, 5])
        with btn_col:
            # Build export df (clean, not formatted)
            export_df = df_sla[show_cols].copy().rename(columns={k:v for k,v in rename_map.items() if k in df_sla[show_cols].columns})
            st.download_button(
                label="📥 Download Collection List (Excel)",
                data=to_excel_bytes(export_df),
                file_name=f'Collections_SLA_{pd.Timestamp.now().strftime("%Y-%m-%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

        st.dataframe(action_df, use_container_width=True, hide_index=True, height=420)

        st.info(f"💡 **{n_overdue} accounts** require action this cycle · "
                f"Total overdue: **{fmt(total_past_due)}** ({pct_past_due}% of portfolio) · "
                f"Avg per account: **{fmt(avg_overdue)}** · "
                f"90+ day critical: **{fmtk(total_aged_90_plus)}** ({pct_90_plus}%)")

except Exception as e:
    st.error(f"❌ Error processing file: {e}")
    st.exception(e)
