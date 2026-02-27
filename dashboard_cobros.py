import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(
    page_title="AR Collections Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg0:#0d0e11; --bg1:#13141a; --bg2:#1a1c24; --bg3:#22242e;
    --border:#2a2d3a;
    --orange:#ff6b35; --yellow:#f59e0b; --green:#10b981;
    --red:#ef4444; --blue:#3b82f6; --purple:#8b5cf6;
    --t1:#f1f1f3; --t2:#8b8fa8; --t3:#404460;
}

/* ── Base ── */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background: var(--bg0) !important;
    color: var(--t1) !important;
}
.block-container { padding: 1.4rem 2rem 3rem !important; max-width: 100% !important; }

/* Hide only Streamlit branding — NOT the sidebar toggle */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg1) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] section { padding: 1.4rem 1.2rem !important; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] small { color: var(--t2) !important; }

/* Sidebar collapse button — keep visible & styled */
[data-testid="collapsedControl"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--t1) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {
    background: var(--bg2) !important;
    border: 1.5px dashed rgba(255,107,53,.45) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploadDropzone"] * { color: var(--t2) !important; }
[data-testid="stFileUploadDropzone"] button {
    background: var(--bg3) !important;
    color: var(--t1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg0); }
::-webkit-scrollbar-thumb { background: var(--bg3); border-radius: 4px; }

/* ── KPI cards ── */
.kpi {
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    height: 100%;
}
.kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.kpi.orange::before { background: linear-gradient(90deg,#ff6b35,transparent); }
.kpi.green::before  { background: linear-gradient(90deg,#10b981,transparent); }
.kpi.red::before    { background: linear-gradient(90deg,#ef4444,transparent); }
.kpi.yellow::before { background: linear-gradient(90deg,#f59e0b,transparent); }
.kpi.blue::before   { background: linear-gradient(90deg,#3b82f6,transparent); }
.kpi.purple::before { background: linear-gradient(90deg,#8b5cf6,transparent); }
.kpi-label {
    font-size: 0.56rem; font-weight: 700;
    letter-spacing: .14em; text-transform: uppercase;
    color: var(--t3); margin-bottom: 10px;
}
.kpi-value { font-size: 1.75rem; font-weight: 900; line-height: 1; letter-spacing: -.04em; }
.kpi-sub   { font-size: 0.62rem; color: var(--t2); margin-top: 7px; font-weight: 500; }
.kpi-bar   { margin-top: 12px; height: 3px; border-radius: 2px; background: var(--bg3); overflow: hidden; }
.kpi-bar-fill { height: 100%; border-radius: 2px; }

/* ── Section header ── */
.sec-hdr {
    display: flex; align-items: center; gap: 10px;
    margin: 1.8rem 0 1rem; padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}
.sec-title { font-size: 0.66rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--t1); }
.sec-badge {
    font-size: 0.54rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase;
    background: rgba(255,107,53,.1); color: var(--orange);
    border: 1px solid rgba(255,107,53,.25); border-radius: 4px; padding: 2px 8px;
}

/* ── Main header ── */
.main-title { font-size: 1.5rem; font-weight: 900; letter-spacing: -.04em; color: var(--t1); line-height: 1; }
.main-title .acc { color: var(--orange); }
.main-sub  { font-size: 0.58rem; font-weight: 600; color: var(--t3); text-transform: uppercase; letter-spacing: .12em; margin-top: 5px; }
.ts-chip {
    font-family: 'JetBrains Mono', monospace; font-size: 0.62rem;
    color: var(--t2); background: var(--bg2);
    border: 1px solid var(--border); border-radius: 6px; padding: 5px 12px;
    white-space: nowrap;
}

/* ── Empty state ── */
.empty-state {
    margin: 5rem auto; max-width: 400px; background: var(--bg1);
    border: 1px solid var(--border); border-radius: 16px;
    padding: 3rem 2.5rem; text-align: center;
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] thead th {
    background: var(--bg2) !important; color: var(--t3) !important;
    font-size: 0.57rem !important; letter-spacing: .1em !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important; font-weight: 700 !important;
}
[data-testid="stDataFrame"] tbody td {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important; color: var(--t1) !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: linear-gradient(135deg,#ff6b35,#d94e1f) !important;
    color: #fff !important; border: none !important;
    border-radius: 8px !important; font-size: 0.72rem !important;
    font-weight: 700 !important; letter-spacing: .05em !important;
    padding: .5rem 1.4rem !important; transition: opacity .2s !important;
}
.stDownloadButton > button:hover { opacity: .82; }

/* ── Alerts ── */
.stAlert {
    background: rgba(255,107,53,.06) !important;
    border: 1px solid rgba(255,107,53,.2) !important;
    border-radius: 8px !important; color: var(--t1) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--bg1); border-radius: 8px;
    border: 1px solid var(--border); padding: 4px; gap: 2px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important; color: var(--t2) !important;
    border-radius: 6px !important; font-size: 0.68rem !important;
    font-weight: 600 !important; letter-spacing: .06em !important;
    text-transform: uppercase !important; padding: 6px 16px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--bg3) !important; color: var(--t1) !important;
}

/* ── Progress ── */
.stProgress > div > div > div { background: var(--bg3) !important; border-radius: 3px !important; }
.stProgress > div > div > div > div { border-radius: 3px !important; }

/* ── Multiselect ── */
[data-testid="stMultiSelect"] > div {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
[data-testid="stMultiSelect"] span { color: var(--t1) !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ──────────────────────────────────────────────────────────────────
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

def safe_color_list(values, low='#10b981', mid='#f59e0b', high='#ef4444'):
    """Return per-bar colors avoiding colorscale crash on uniform data."""
    mn, mx = min(values), max(values)
    if mn == mx:
        return [mid] * len(values)
    result = []
    for v in values:
        ratio = (v - mn) / (mx - mn)
        if ratio < 0.33:   result.append(low)
        elif ratio < 0.66: result.append(mid)
        else:              result.append(high)
    return result

THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color='#8b8fa8', size=10),
    margin=dict(l=8, r=8, t=36, b=8),
)
BUCKET_COLORS = ['#10b981','#f59e0b','#f97316','#ff6b35','#ef4444','#dc2626','#991b1b']

def find_col(df, patterns):
    for p in patterns:
        for c in df.columns:
            if p.lower() in c.lower():
                return c
    return None

@st.cache_data
def load_data(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes))
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    return df


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='margin-bottom:1.4rem;padding-bottom:1.2rem;border-bottom:1px solid #2a2d3a'>
        <div style='font-size:1rem;font-weight:900;color:#f1f1f3;letter-spacing:-.025em;line-height:1.3'>
            ⚡ Collections<br><span style='color:#ff6b35'>Intelligence</span>
        </div>
        <div style='font-size:0.54rem;color:#404460;text-transform:uppercase;letter-spacing:.14em;margin-top:5px'>
            AR Analytics · v2.0
        </div>
    </div>
    <div style='font-size:0.56rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
                color:#404460;margin-bottom:8px'>📂 Aging Report (.xlsx)</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload file", type=["xlsx"], label_visibility="collapsed")

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.56rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
                color:#404460;margin-bottom:8px'>🔍 Filters</div>
    """, unsafe_allow_html=True)

    col_ph  = st.empty()
    reg_ph  = st.empty()
    risk_ph = st.empty()

    st.markdown("""
    <div style='margin-top:1.4rem;padding-top:1.2rem;border-top:1px solid #2a2d3a;
                font-size:0.62rem;color:#505470;line-height:1.8'>
        Upload the SAP Aging Report in <b style='color:#8b8fa8'>.xlsx</b> format.<br>
        Buckets, collectors, risk tiers and credit limits are auto-detected.
    </div>
    """, unsafe_allow_html=True)


# ── HEADER ────────────────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%d %b %Y  ·  %H:%M")
hcol1, hcol2 = st.columns([6, 1])
with hcol1:
    st.markdown("""
    <div style='margin-bottom:.4rem'>
        <div class='main-title'>Collections <span class='acc'>Dashboard</span></div>
        <div class='main-sub'>AR Performance · Risk Exposure · Collector SLA</div>
    </div>""", unsafe_allow_html=True)
with hcol2:
    st.markdown(f"<div class='ts-chip' style='text-align:right;margin-top:4px'>🕐 {now_str}</div>",
                unsafe_allow_html=True)
st.markdown("<hr style='border:none;border-top:1px solid #2a2d3a;margin:.6rem 0 1.4rem'>",
            unsafe_allow_html=True)


# ── EMPTY STATE ───────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown("""
    <div class='empty-state'>
        <div style='font-size:2.8rem;margin-bottom:1rem'>📊</div>
        <div style='font-size:1rem;font-weight:800;color:#f1f1f3;margin-bottom:8px'>No data loaded</div>
        <div style='font-size:0.72rem;color:#8b8fa8;line-height:1.75'>
            Upload your SAP Aging Report from the left panel<br>to start the portfolio analysis.
        </div>
    </div>""", unsafe_allow_html=True)
    st.stop()


# ── LOAD ──────────────────────────────────────────────────────────────────────
try:
    df_raw = load_data(uploaded_file.read())
except Exception as e:
    st.error(f"❌ Could not read file: {e}")
    st.stop()

COL_PAYER  = find_col(df_raw, ['Payer','Customer','Client'])
COL_COLL   = find_col(df_raw, ['Collector'])
COL_LOC    = find_col(df_raw, ['Location'])
COL_REG    = find_col(df_raw, ['Region'])
COL_TERMS  = find_col(df_raw, ['Payment terms','Terms'])
COL_RISK   = find_col(df_raw, ['Cr/Mgt Risk','Risk Category','Risk'])
COL_CLIMIT = find_col(df_raw, ['Credit Limits','Credit Limit'])
COL_TOTAL  = find_col(df_raw, ['Total'])
COL_CURR   = find_col(df_raw, ['Current'])

BUCKETS = {}
for label, patterns in [
    ('1-30d',    ['1 - 30','1-30']),
    ('31-60d',   ['31 - 60','31-60']),
    ('61-90d',   ['61 - 90','61-90']),
    ('91-120d',  ['91 - 120','91-120']),
    ('121-180d', ['121 - 180','121-180']),
    ('181-365d', ['181 - 365','181-365']),
    ('365+d',    ['> 365','>365','365+']),
]:
    col = find_col(df_raw, patterns)
    if col:
        BUCKETS[label] = col

if not COL_TOTAL or not COL_CURR:
    st.error("⚠️ Could not find **Total** / **Current** columns. Check the file format.")
    st.dataframe(df_raw.head(3))
    st.stop()


# ── PROCESS ───────────────────────────────────────────────────────────────────
df = df_raw.copy()
for c in [c for c in [COL_TOTAL, COL_CURR, COL_CLIMIT] + list(BUCKETS.values()) if c]:
    df[c] = clean_money(df[c])

df['_PD'] = (df[COL_TOTAL] - df[COL_CURR]).clip(lower=0)
for bname, bcol in BUCKETS.items():
    df[f'_B_{bname}'] = df[bcol].clip(lower=0)


# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
cols_list = sorted(df[COL_COLL].dropna().unique().tolist())  if COL_COLL  else []
regs_list = sorted(df[COL_REG].dropna().unique().tolist())   if COL_REG   else []
risk_list = sorted(df[COL_RISK].dropna().unique().tolist())  if COL_RISK  else []

with col_ph:
    sel_coll = st.multiselect("Collector", cols_list, placeholder="All collectors")
with reg_ph:
    sel_reg  = st.multiselect("Region", regs_list, placeholder="All regions")
with risk_ph:
    sel_risk = st.multiselect("Risk Category", risk_list, placeholder="All categories")

dff = df.copy()
if sel_coll and COL_COLL:  dff = dff[dff[COL_COLL].isin(sel_coll)]
if sel_reg  and COL_REG:   dff = dff[dff[COL_REG].isin(sel_reg)]
if sel_risk and COL_RISK:  dff = dff[dff[COL_RISK].isin(sel_risk)]


# ── METRICS ───────────────────────────────────────────────────────────────────
total_ar  = dff[COL_TOTAL].sum()
total_cur = dff[COL_CURR].sum()
total_pd  = dff['_PD'].sum()
pct_pd    = pct(total_pd, total_ar)
pct_cur   = pct(total_cur, total_ar)
n_total   = len(dff)
df_sla    = dff[dff['_PD'] > 0.01].copy().sort_values('_PD', ascending=False)
n_od      = len(df_sla)
n_ok      = n_total - n_od
avg_od    = total_pd / n_od if n_od else 0
top5      = df_sla.head(5)['_PD'].sum()
pct_top5  = pct(top5, total_pd)

cr_util   = 0.0
if COL_CLIMIT:
    cl_sum  = dff[COL_CLIMIT].sum()
    cr_util = pct(total_ar, cl_sum)

bkt = {b: dff[f'_B_{b}'].sum() for b in BUCKETS}
pd_90p   = sum(v for k,v in bkt.items() if any(x in k for x in ['91','121','181','365+']))
pct_90p  = pct(pd_90p, total_pd)

midpoints = {'1-30d':15,'31-60d':45,'61-90d':75,'91-120d':105,'121-180d':150,'181-365d':270,'365+d':400}
tot_aged  = sum(bkt.values()) or 1
avg_days  = sum(bkt.get(b,0)*d for b,d in midpoints.items()) / tot_aged


# ════════════════════════════════════════════════════════════════════════════
# ROW 1 — KPI CARDS
# ════════════════════════════════════════════════════════════════════════════
k1,k2,k3,k4,k5,k6 = st.columns(6, gap="small")

def kpi_card(color, label, value, sub, bar_pct):
    bar_pct = min(bar_pct, 100)
    return f"""<div class='kpi {color}'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{value}</div>
        <div class='kpi-sub'>{sub}</div>
        <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{bar_pct}%;background:var(--{color})'></div></div>
    </div>"""

# Dynamic color helper
def dyn(val, warn=20, crit=40, rev=False):
    if rev: val = 100 - val
    if val >= crit: return '#ef4444'
    if val >= warn: return '#f59e0b'
    return '#10b981'

with k1:
    st.markdown(f"""<div class='kpi orange'>
        <div class='kpi-label'>Total AR Portfolio</div>
        <div class='kpi-value' style='color:#f1f1f3'>{fmtk(total_ar)}</div>
        <div class='kpi-sub'>{n_total} active accounts</div>
        <div class='kpi-bar'><div class='kpi-bar-fill' style='width:100%;background:#ff6b35'></div></div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""<div class='kpi green'>
        <div class='kpi-label'>Current (On Time)</div>
        <div class='kpi-value' style='color:#10b981'>{fmtk(total_cur)}</div>
        <div class='kpi-sub'>{n_ok} accts · {pct_cur}%</div>
        <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_cur}%;background:#10b981'></div></div>
    </div>""", unsafe_allow_html=True)

with k3:
    c3 = dyn(pct_pd, 10, 20)
    st.markdown(f"""<div class='kpi red'>
        <div class='kpi-label'>Past Due Exposure</div>
        <div class='kpi-value' style='color:{c3}'>{fmtk(total_pd)}</div>
        <div class='kpi-sub'>{n_od} accts · {pct_pd}% at risk</div>
        <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_pd}%;background:{c3}'></div></div>
    </div>""", unsafe_allow_html=True)

with k4:
    c4 = dyn(pct_90p, 15, 30)
    st.markdown(f"""<div class='kpi yellow'>
        <div class='kpi-label'>90+ Days Critical</div>
        <div class='kpi-value' style='color:{c4}'>{fmtk(pd_90p)}</div>
        <div class='kpi-sub'>{pct_90p}% of overdue</div>
        <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_90p}%;background:{c4}'></div></div>
    </div>""", unsafe_allow_html=True)

with k5:
    c5 = dyn(avg_days/180*100, 25, 50)
    st.markdown(f"""<div class='kpi blue'>
        <div class='kpi-label'>Avg Days Overdue</div>
        <div class='kpi-value' style='color:{c5}'>{avg_days:.0f}d</div>
        <div class='kpi-sub'>weighted across buckets</div>
        <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{min(avg_days/180*100,100):.0f}%;background:{c5}'></div></div>
    </div>""", unsafe_allow_html=True)

with k6:
    c6 = dyn(cr_util, 70, 90)
    cu_val = f"{cr_util:.1f}%" if COL_CLIMIT else "N/A"
    st.markdown(f"""<div class='kpi purple'>
        <div class='kpi-label'>Credit Utilization</div>
        <div class='kpi-value' style='color:{c6}'>{cu_val}</div>
        <div class='kpi-sub'>AR vs Credit Limit</div>
        <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{min(cr_util,100):.0f}%;background:{c6}'></div></div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📈  Aging Analysis",
    "👤  Collector View",
    "⚠️  Risk & Credit",
    "📋  Action List",
])


# ── TAB 1: AGING ─────────────────────────────────────────────────────────────
with tab1:
    st.markdown("""<div class='sec-hdr'>
        <span class='sec-title'>Aging Distribution</span>
        <span class='sec-badge'>BUCKET BREAKDOWN</span>
    </div>""", unsafe_allow_html=True)

    bnames   = list(bkt.keys())
    bamounts = list(bkt.values())
    colors   = BUCKET_COLORS[:len(bnames)]

    ca, cb, cc = st.columns([4, 2, 2], gap="small")

    with ca:
        fig = go.Figure(go.Bar(
            x=bnames, y=bamounts,
            marker=dict(color=colors, line=dict(width=0)),
            text=[fmtk(v) for v in bamounts], textposition='outside',
            textfont=dict(family='JetBrains Mono', size=9, color='#8b8fa8'),
        ))
        fig.update_layout(**THEME,
            title=dict(text="Overdue by aging bucket", font=dict(size=11,color='#8b8fa8'), x=0),
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10,color='#8b8fa8')),
            yaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=9)),
            bargap=0.35)
        st.plotly_chart(fig, use_container_width=True)

    with cb:
        fig2 = go.Figure(go.Pie(
            labels=['Current','Past Due'], values=[max(total_cur,0), max(total_pd,0)],
            hole=0.7, marker=dict(colors=['#10b981','#ef4444'], line=dict(width=0)),
            textinfo='percent', textfont=dict(family='Inter',size=11,color='#f1f1f3'),
            pull=[0, 0.04],
        ))
        fig2.update_layout(**THEME,
            title=dict(text="Portfolio health", font=dict(size=11,color='#8b8fa8'), x=0),
            showlegend=True,
            legend=dict(orientation='h', x=0.0, y=-0.18,
                        font=dict(size=10,color='#8b8fa8'), bgcolor='rgba(0,0,0,0)'),
            annotations=[dict(
                text=f"<b>{pct_pd:.0f}%</b><br>overdue",
                x=0.5, y=0.5, showarrow=False,
                font=dict(family='Inter',size=13,color='#ef4444'))])
        st.plotly_chart(fig2, use_container_width=True)

    with cc:
        all_l = ['Current'] + bnames
        all_v = [total_cur] + bamounts
        all_c = ['#10b981'] + colors
        fig3 = go.Figure(go.Bar(
            x=all_v, y=all_l, orientation='h',
            marker=dict(color=all_c, line=dict(width=0)),
            text=[fmtk(v) for v in all_v], textposition='outside',
            textfont=dict(family='JetBrains Mono', size=8, color='#8b8fa8'),
        ))
        fig3.update_layout(**THEME,
            title=dict(text="Balance by tier", font=dict(size=11,color='#8b8fa8'), x=0),
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=8)),
            yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9,color='#8b8fa8')))
        st.plotly_chart(fig3, use_container_width=True)

    # Detail cards per bucket
    if bkt:
        st.markdown("""<div class='sec-hdr' style='margin-top:.8rem'>
            <span class='sec-title'>Aging Composition</span>
            <span class='sec-badge'>% MIX</span>
        </div>""", unsafe_allow_html=True)
        comp_cols = st.columns(len(bkt), gap="small")
        for i, (bname, bval) in enumerate(bkt.items()):
            bp = pct(bval, total_pd)
            bc = BUCKET_COLORS[i] if i < len(BUCKET_COLORS) else '#ef4444'
            with comp_cols[i]:
                st.markdown(f"""<div class='kpi' style='padding:14px 16px;text-align:center'>
                    <div class='kpi-label'>{bname}</div>
                    <div style='font-size:1.3rem;font-weight:900;color:{bc}'>{fmtk(bval)}</div>
                    <div style='font-size:0.6rem;color:#8b8fa8;margin-top:4px'>{bp}% of overdue</div>
                    <div class='kpi-bar' style='margin-top:8px'>
                        <div class='kpi-bar-fill' style='width:{bp}%;background:{bc}'></div>
                    </div>
                </div>""", unsafe_allow_html=True)


# ── TAB 2: COLLECTOR ─────────────────────────────────────────────────────────
with tab2:
    st.markdown("""<div class='sec-hdr'>
        <span class='sec-title'>Collector Performance</span>
        <span class='sec-badge'>SLA MANAGEMENT</span>
    </div>""", unsafe_allow_html=True)

    if COL_COLL:
        cg = dff.groupby(COL_COLL).agg(
            Total_AR=   (COL_TOTAL,'sum'),
            Total_PD=   ('_PD','sum'),
            Accounts=   (COL_TOTAL,'count'),
            OD_Accts=   ('_PD', lambda x: (x>0.01).sum()),
        ).reset_index()
        cg['Pct_PD'] = cg.apply(lambda r: pct(r['Total_PD'],r['Total_AR']), axis=1)
        cg['Avg_OD'] = cg.apply(lambda r: r['Total_PD']/r['OD_Accts'] if r['OD_Accts'] else 0, axis=1)
        cg = cg.sort_values('Total_PD', ascending=False)

        cc1, cc2 = st.columns([3,2], gap="small")

        with cc1:
            fc = go.Figure()
            fc.add_trace(go.Bar(name='Current', x=cg[COL_COLL],
                y=cg['Total_AR']-cg['Total_PD'],
                marker_color='#10b981', marker_line_width=0))
            fc.add_trace(go.Bar(name='Past Due', x=cg[COL_COLL],
                y=cg['Total_PD'],
                marker_color='#ef4444', marker_line_width=0))
            fc.update_layout(**THEME, barmode='stack',
                title=dict(text="AR by collector (stacked)", font=dict(size=11,color='#8b8fa8'), x=0),
                legend=dict(orientation='h', x=0, y=1.14,
                            font=dict(size=10,color='#8b8fa8'), bgcolor='rgba(0,0,0,0)'),
                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9,color='#8b8fa8')),
                yaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False,
                           tickprefix='$', tickformat=',.0f', tickfont=dict(size=9)),
                bargap=0.3)
            st.plotly_chart(fc, use_container_width=True)

        with cc2:
            bsizes = cg['Total_PD'].apply(
                lambda v: max(12, min(40, v/total_pd*80)) if total_pd else 12)
            sc_colors = safe_color_list(cg['Pct_PD'].tolist(), '#10b981','#f59e0b','#ef4444')
            fs = go.Figure(go.Scatter(
                x=cg['Accounts'], y=cg['Pct_PD'],
                mode='markers+text',
                marker=dict(size=bsizes, color=sc_colors, line=dict(width=0)),
                text=cg[COL_COLL].str[:12],
                textposition='top center',
                textfont=dict(size=8, color='#8b8fa8'),
            ))
            fs.update_layout(**THEME,
                title=dict(text="Accounts vs % Past Due", font=dict(size=11,color='#8b8fa8'), x=0),
                xaxis=dict(title=dict(text="# Accounts", font=dict(size=9)),
                           showgrid=True, gridcolor='#22242e', zeroline=False, tickfont=dict(size=9)),
                yaxis=dict(title=dict(text="% Past Due", font=dict(size=9)),
                           showgrid=True, gridcolor='#22242e', zeroline=False,
                           tickfont=dict(size=9), ticksuffix='%'))
            st.plotly_chart(fs, use_container_width=True)

        st.markdown("""<div class='sec-hdr' style='margin-top:.4rem'>
            <span class='sec-title'>Collector Summary</span>
            <span class='sec-badge'>DETAIL</span>
        </div>""", unsafe_allow_html=True)
        disp = cg.copy()
        disp['Total AR']   = disp['Total_AR'].apply(fmt)
        disp['Past Due']   = disp['Total_PD'].apply(fmt)
        disp['Avg OD']     = disp['Avg_OD'].apply(fmt)
        disp['% Past Due'] = disp['Pct_PD'].apply(lambda x: f"{x:.1f}%")
        disp = disp.rename(columns={COL_COLL:'Collector','Accounts':'# Accts','OD_Accts':'# OD'})
        st.dataframe(disp[['Collector','# Accts','# OD','Total AR','Past Due','% Past Due','Avg OD']],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No Collector column found in this file.")

    if COL_REG:
        st.markdown("""<div class='sec-hdr'>
            <span class='sec-title'>Regional Breakdown</span>
            <span class='sec-badge'>GEOGRAPHY</span>
        </div>""", unsafe_allow_html=True)
        rg = dff.groupby(COL_REG).agg(
            Past_Due=('_PD','sum'), Accounts=(COL_TOTAL,'count')
        ).reset_index().sort_values('Past_Due', ascending=True)
        reg_colors = safe_color_list(rg['Past_Due'].tolist(), '#3b82f6','#f59e0b','#ef4444')
        fr = go.Figure(go.Bar(
            y=rg[COL_REG], x=rg['Past_Due'], orientation='h',
            marker=dict(color=reg_colors, line=dict(width=0)),
            text=rg['Past_Due'].apply(fmtk), textposition='outside',
            textfont=dict(family='JetBrains Mono', size=8, color='#8b8fa8'),
        ))
        fr.update_layout(**THEME,
            title=dict(text="Past Due by Region", font=dict(size=11,color='#8b8fa8'), x=0),
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=8)),
            yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9,color='#9ca3af')))
        st.plotly_chart(fr, use_container_width=True)


# ── TAB 3: RISK & CREDIT ─────────────────────────────────────────────────────
with tab3:
    st.markdown("""<div class='sec-hdr'>
        <span class='sec-title'>Risk Exposure Analysis</span>
        <span class='sec-badge'>CREDIT RISK</span>
    </div>""", unsafe_allow_html=True)

    if COL_RISK:
        rkg = dff.groupby(COL_RISK).agg(
            Total_AR=(COL_TOTAL,'sum'), Past_Due=('_PD','sum'), Accounts=(COL_TOTAL,'count')
        ).reset_index().sort_values('Past_Due', ascending=False)

        def rcol(label):
            s = str(label).upper()
            if 'HIGH' in s or '/H' in s: return '#ef4444'
            if 'MED'  in s or '/M' in s: return '#f59e0b'
            return '#10b981'
        rc = [rcol(r) for r in rkg[COL_RISK]]

        rr1, rr2 = st.columns([2,3], gap="small")
        with rr1:
            fp = go.Figure(go.Pie(
                labels=rkg[COL_RISK], values=rkg['Past_Due'],
                hole=0.6, marker=dict(colors=rc, line=dict(width=0)),
                textinfo='percent+label', textfont=dict(family='Inter',size=9,color='#f1f1f3'),
            ))
            fp.update_layout(**THEME,
                title=dict(text="Past Due by Risk Category", font=dict(size=11,color='#8b8fa8'), x=0),
                showlegend=False)
            st.plotly_chart(fp, use_container_width=True)

        with rr2:
            fb = go.Figure(go.Bar(
                x=rkg[COL_RISK], y=rkg['Past_Due'],
                marker=dict(color=rc, line=dict(width=0)),
                text=rkg['Past_Due'].apply(fmtk), textposition='outside',
                textfont=dict(family='JetBrains Mono',size=9,color='#8b8fa8'),
                customdata=rkg[['Total_AR','Accounts']].values,
                hovertemplate="<b>%{x}</b><br>Past Due: %{y:$,.0f}<br>Total AR: %{customdata[0]:$,.0f}<br>Accounts: %{customdata[1]}<extra></extra>",
            ))
            fb.update_layout(**THEME,
                title=dict(text="Past Due by Risk Tier", font=dict(size=11,color='#8b8fa8'), x=0),
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10,color='#9ca3af')),
                yaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False,
                           tickprefix='$', tickformat=',.0f', tickfont=dict(size=9)),
                bargap=0.35)
            st.plotly_chart(fb, use_container_width=True)

        high_pd = rkg[rkg[COL_RISK].apply(lambda x:'HIGH' in str(x).upper() or '/H' in str(x).upper())]['Past_Due'].sum()
        med_pd  = rkg[rkg[COL_RISK].apply(lambda x:'MED'  in str(x).upper() or '/M' in str(x).upper())]['Past_Due'].sum()
        low_pd  = total_pd - high_pd - med_pd

        rk1, rk2, rk3 = st.columns(3, gap="small")
        with rk1:
            st.markdown(f"""<div class='kpi red'>
                <div class='kpi-label'>High Risk Exposure</div>
                <div class='kpi-value' style='color:#ef4444'>{fmtk(high_pd)}</div>
                <div class='kpi-sub'>{pct(high_pd,total_pd):.1f}% of overdue</div>
            </div>""", unsafe_allow_html=True)
        with rk2:
            st.markdown(f"""<div class='kpi yellow'>
                <div class='kpi-label'>Medium Risk Exposure</div>
                <div class='kpi-value' style='color:#f59e0b'>{fmtk(med_pd)}</div>
                <div class='kpi-sub'>{pct(med_pd,total_pd):.1f}% of overdue</div>
            </div>""", unsafe_allow_html=True)
        with rk3:
            st.markdown(f"""<div class='kpi green'>
                <div class='kpi-label'>Low Risk Exposure</div>
                <div class='kpi-value' style='color:#10b981'>{fmtk(low_pd)}</div>
                <div class='kpi-sub'>{pct(low_pd,total_pd):.1f}% of overdue</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No Risk Category column detected in this file.")

    if COL_CLIMIT:
        st.markdown("""<div class='sec-hdr' style='margin-top:1.5rem'>
            <span class='sec-title'>Credit Limit Utilization</span>
            <span class='sec-badge'>CREDIT MGMT</span>
        </div>""", unsafe_allow_html=True)
        dff_cl = dff[dff[COL_CLIMIT]>0].copy()
        dff_cl['_Util']  = (dff_cl[COL_TOTAL]/dff_cl[COL_CLIMIT]*100).round(1)
        dff_cl['_Avail'] = (dff_cl[COL_CLIMIT]-dff_cl[COL_TOTAL]).clip(lower=0)
        over_l = dff_cl[dff_cl['_Util']>100]
        near_l = dff_cl[(dff_cl['_Util']>=80)&(dff_cl['_Util']<=100)]

        cl1, cl2, cl3 = st.columns(3, gap="small")
        with cl1:
            st.markdown(f"""<div class='kpi orange'>
                <div class='kpi-label'>Total Credit Limit</div>
                <div class='kpi-value' style='color:#ff6b35'>{fmtk(dff_cl[COL_CLIMIT].sum())}</div>
                <div class='kpi-sub'>{cr_util:.1f}% utilized overall</div>
            </div>""", unsafe_allow_html=True)
        with cl2:
            st.markdown(f"""<div class='kpi red'>
                <div class='kpi-label'>Over Credit Limit</div>
                <div class='kpi-value' style='color:#ef4444'>{len(over_l)}</div>
                <div class='kpi-sub'>accounts exceeding limit</div>
            </div>""", unsafe_allow_html=True)
        with cl3:
            st.markdown(f"""<div class='kpi yellow'>
                <div class='kpi-label'>Near Limit (80-100%)</div>
                <div class='kpi-value' style='color:#f59e0b'>{len(near_l)}</div>
                <div class='kpi-sub'>accounts approaching limit</div>
            </div>""", unsafe_allow_html=True)

        top_util = dff_cl.nlargest(10,'_Util')[[COL_PAYER,COL_CLIMIT,COL_TOTAL,'_Util','_PD']].copy()
        top_util.columns = ['Customer','Credit Limit','Total AR','Utilization %','Past Due']
        top_util['Credit Limit']  = top_util['Credit Limit'].apply(fmt)
        top_util['Total AR']      = top_util['Total AR'].apply(fmt)
        top_util['Past Due']      = top_util['Past Due'].apply(fmt)
        top_util['Utilization %'] = top_util['Utilization %'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(top_util, use_container_width=True, hide_index=True, height=280)


# ── TAB 4: ACTION LIST ───────────────────────────────────────────────────────
with tab4:
    st.markdown(f"""<div class='sec-hdr'>
        <span class='sec-title'>Priority Action List</span>
        <span class='sec-badge'>SLA TOUCH GOAL · {n_od} ACCOUNTS</span>
    </div>""", unsafe_allow_html=True)

    a1,a2,a3,a4 = st.columns(4, gap="small")
    with a1:
        st.markdown(f"""<div class='kpi yellow'>
            <div class='kpi-label'>Accounts to Contact</div>
            <div class='kpi-value' style='color:#f59e0b'>{n_od}</div>
            <div class='kpi-sub'>overdue this cycle</div>
        </div>""", unsafe_allow_html=True)
    with a2:
        st.markdown(f"""<div class='kpi red'>
            <div class='kpi-label'>Total Exposure</div>
            <div class='kpi-value' style='color:#ef4444'>{fmtk(total_pd)}</div>
            <div class='kpi-sub'>{pct_pd}% of portfolio</div>
        </div>""", unsafe_allow_html=True)
    with a3:
        st.markdown(f"""<div class='kpi orange'>
            <div class='kpi-label'>Avg per Account</div>
            <div class='kpi-value' style='color:#ff6b35'>{fmtk(avg_od)}</div>
            <div class='kpi-sub'>average overdue balance</div>
        </div>""", unsafe_allow_html=True)
    with a4:
        st.markdown(f"""<div class='kpi blue'>
            <div class='kpi-label'>Top 5 Concentration</div>
            <div class='kpi-value' style='color:#3b82f6'>{pct_top5:.1f}%</div>
            <div class='kpi-sub'>{fmtk(top5)} in top 5 accts</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if df_sla.empty:
        st.success("🎉 **All accounts are current!** No overdue balances in this portfolio.")
    else:
        top_n  = min(15, len(df_sla))
        top_df = df_sla.head(top_n)
        customers = (top_df[COL_PAYER].astype(str).str[:24].tolist()
                     if COL_PAYER in top_df.columns else [f"#{i+1}" for i in range(top_n)])
        amounts = top_df['_PD'].tolist()
        bar_colors = safe_color_list(amounts[::-1], '#f59e0b','#ff6b35','#ef4444')

        ft = go.Figure(go.Bar(
            y=customers[::-1], x=amounts[::-1], orientation='h',
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[fmtk(v) for v in amounts[::-1]], textposition='outside',
            textfont=dict(family='JetBrains Mono', size=8, color='#8b8fa8'),
        ))
        ft.update_layout(**THEME,
            title=dict(text=f"Top {top_n} accounts by past due balance",
                       font=dict(size=11,color='#8b8fa8'), x=0),
            showlegend=False,
            margin=dict(l=8,r=60,t=36,b=8),
            xaxis=dict(showgrid=True, gridcolor='#22242e', zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=8)),
            yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9,color='#9ca3af')))
        st.plotly_chart(ft, use_container_width=True)

        st.markdown("""<div class='sec-hdr' style='margin-top:0'>
            <span class='sec-title'>Full Collection List</span>
            <span class='sec-badge'>DOWNLOAD READY</span>
        </div>""", unsafe_allow_html=True)

        show_cols = [c for c in [
            COL_PAYER, COL_COLL, COL_LOC, COL_REG,
            COL_TERMS, COL_RISK, COL_TOTAL, '_PD',
        ] + [f'_B_{b}' for b in BUCKETS] if c and c in df_sla.columns]

        action_df = df_sla[show_cols].copy()
        export_df = action_df.copy()

        rmap = {
            '_PD':'Past Due', COL_TOTAL:'Total AR', COL_PAYER:'Customer',
            COL_COLL:'Collector', COL_LOC:'Location', COL_REG:'Region',
            COL_TERMS:'Payment Terms', COL_RISK:'Risk Category',
        }
        rmap.update({f'_B_{b}': b for b in BUCKETS})
        rmap = {k:v for k,v in rmap.items() if k}

        action_df = action_df.rename(columns=rmap)
        export_df = export_df.rename(columns=rmap)

        for mc in ['Total AR','Past Due'] + list(BUCKETS.keys()):
            if mc in action_df.columns:
                action_df[mc] = action_df[mc].apply(fmt)

        btn_col, _ = st.columns([2,5])
        with btn_col:
            st.download_button(
                label="📥 Download Collection List",
                data=to_excel_bytes(export_df),
                file_name=f"Collections_{pd.Timestamp.now().strftime('%Y-%m-%d')}.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

        st.dataframe(action_df, use_container_width=True, hide_index=True, height=420)
        st.info(
            f"💡 **{n_od} accounts** to action · "
            f"Total overdue: **{fmt(total_pd)}** ({pct_pd}% of portfolio) · "
            f"Avg per account: **{fmt(avg_od)}** · "
            f"90+ day critical: **{fmtk(pd_90p)}** ({pct_90p}%)"
        )
