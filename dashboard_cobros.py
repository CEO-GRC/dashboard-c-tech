import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(
    page_title="AR Collections Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg0:#0e0f11; --bg1:#16181c; --bg2:#1c1e24; --bg3:#23262e;
    --border:#2a2d37;
    --orange:#ff6b35; --yellow:#ffc300; --green:#22c55e; --red:#ef4444;
    --t1:#f0f0f0; --t2:#9ca3af; --t3:#4b5563;
}

/* ── Full dark override — no system theme interference ── */
html, body { background:#0e0f11 !important; color:#f0f0f0 !important; }
.stApp, [class*="css"] { background:#0e0f11 !important; font-family:'Inter',sans-serif !important; color:#f0f0f0 !important; }
.block-container { padding:0 !important; max-width:100% !important; }
#MainMenu, footer, header, [data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar{width:4px;height:4px} ::-webkit-scrollbar-track{background:#0e0f11} ::-webkit-scrollbar-thumb{background:#2a2d37;border-radius:4px}

/* ── Top bar ── */
.topbar {
    display:flex; align-items:center; justify-content:space-between;
    padding:14px 28px;
    background:#16181c;
    border-bottom:1px solid #2a2d37;
    position:sticky; top:0; z-index:100;
}
.logo { font-size:1.1rem; font-weight:900; color:#f0f0f0; letter-spacing:-.02em; }
.logo span { color:#ff6b35; }
.logo-sub { font-size:0.55rem; font-weight:600; color:#4b5563; text-transform:uppercase; letter-spacing:.12em; margin-top:2px; }
.ts-chip { font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#6b7280; background:#1c1e24; border:1px solid #2a2d37; border-radius:6px; padding:5px 12px; }

/* ── Main content wrapper ── */
.main-wrap { padding:20px 28px 40px; }

/* ── Upload panel ── */
.upload-panel {
    background:#16181c;
    border:1px solid #2a2d37;
    border-radius:12px;
    margin-bottom:20px;
    overflow:hidden;
}
.upload-header {
    display:flex; align-items:center; justify-content:space-between;
    padding:14px 20px;
    cursor:pointer;
    user-select:none;
}
.upload-header-left { display:flex; align-items:center; gap:10px; }
.upload-dot { width:8px; height:8px; border-radius:50%; background:#ff6b35; box-shadow:0 0 6px rgba(255,107,53,.5); }
.upload-title { font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:#f0f0f0; }
.upload-badge { font-size:0.57rem; font-weight:700; background:rgba(255,107,53,.12); color:#ff6b35; border:1px solid rgba(255,107,53,.3); border-radius:4px; padding:2px 8px; letter-spacing:.06em; text-transform:uppercase; }
.upload-chevron { font-size:0.8rem; color:#4b5563; transition:transform .2s; }
.upload-body { padding:0 20px 18px; border-top:1px solid #2a2d37; }

/* ── Force uploader dark ── */
[data-testid="stFileUploadDropzone"] {
    background:#1c1e24 !important;
    border:1.5px dashed rgba(255,107,53,.5) !important;
    border-radius:10px !important;
    margin-top:14px !important;
}
[data-testid="stFileUploadDropzone"] section { background:transparent !important; }
[data-testid="stFileUploadDropzone"] * { color:#9ca3af !important; background:transparent !important; }
[data-testid="stFileUploadDropzone"] button {
    background:#23262e !important; color:#f0f0f0 !important;
    border:1px solid #2a2d37 !important; border-radius:6px !important;
}
[data-testid="stFileUploadDropzone"] svg { fill:#4b5563 !important; }

/* ── Section header ── */
.sec-hdr { display:flex; align-items:center; gap:10px; margin:22px 0 12px; padding-bottom:8px; border-bottom:1px solid #2a2d37; }
.sec-title { font-size:0.68rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#f0f0f0; }
.sec-badge { font-size:0.55rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase; background:rgba(255,107,53,.12); color:#ff6b35; border:1px solid rgba(255,107,53,.3); border-radius:4px; padding:2px 8px; }

/* ── KPI card ── */
.kpi { background:#16181c; border:1px solid #2a2d37; border-radius:10px; padding:18px 20px; height:100%; }
.kpi-label { font-size:0.58rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:#4b5563; margin-bottom:8px; }
.kpi-value { font-size:1.9rem; font-weight:900; line-height:1; letter-spacing:-.03em; }
.kpi-sub { font-size:0.64rem; color:#9ca3af; margin-top:7px; font-weight:500; }
.kpi-bar { margin-top:12px; height:2px; border-radius:2px; background:#23262e; overflow:hidden; }
.kpi-bar-fill { height:100%; border-radius:2px; }

/* ── Download button ── */
.stDownloadButton > button {
    background:linear-gradient(135deg,#ff6b35,#d95a25) !important;
    color:#fff !important; border:none !important; border-radius:8px !important;
    font-size:0.75rem !important; font-weight:700 !important;
    letter-spacing:.04em !important; padding:.5rem 1.4rem !important;
}
.stDownloadButton > button:hover { opacity:.85 !important; }

/* ── Table ── */
[data-testid="stDataFrame"] { border-radius:10px !important; border:1px solid #2a2d37 !important; overflow:hidden !important; }
[data-testid="stDataFrame"] thead th { background:#1c1e24 !important; color:#4b5563 !important; font-size:0.58rem !important; letter-spacing:.1em !important; text-transform:uppercase !important; font-family:'JetBrains Mono',monospace !important; font-weight:700 !important; }
[data-testid="stDataFrame"] tbody td { font-family:'JetBrains Mono',monospace !important; font-size:0.78rem !important; color:#f0f0f0 !important; }
[data-testid="stDataFrame"] tbody tr:hover td { background:#1c1e24 !important; }

/* ── Alert ── */
.stAlert { background:rgba(255,107,53,.07) !important; border:1px solid rgba(255,107,53,.2) !important; border-radius:8px !important; color:#f0f0f0 !important; }

/* ── st.progress bar colors ── */
[data-testid="stProgressBar"] > div { background:#23262e !important; border-radius:3px; }
[data-testid="stProgressBar"] > div > div { background:#ff6b35 !important; border-radius:3px; }

/* ── misc ── */
.stMarkdown p { color:#9ca3af !important; font-size:0.75rem; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def limpiar_dinero(s):
    return pd.to_numeric(s.astype(str).str.replace('$','').str.replace(',','').str.strip(), errors='coerce').fillna(0)

def to_excel(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Collection_List')
    return out.getvalue()

def fmt(v):   return f"${v:,.2f}"
def pct(p,t): return round(p/t*100,1) if t else 0

THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter,sans-serif', color='#6b7280', size=10),
    margin=dict(l=8,r=8,t=30,b=8),
)
B_COLORS = ['#22c55e','#ffc300','#f97316','#ff6b35','#ef4444']


# ── TOP BAR ───────────────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%d %b %Y  ·  %H:%M")
st.markdown(f"""
<div class='topbar'>
    <div>
        <div class='logo'>⚡ Collections <span>Dashboard</span></div>
        <div class='logo-sub'>AR Analytics Platform</div>
    </div>
    <div class='ts-chip'>🕐 {now_str}</div>
</div>
<div class='main-wrap'>
""", unsafe_allow_html=True)


# ── COLLAPSIBLE UPLOAD PANEL ──────────────────────────────────────────────────
# Use st.expander — fully native, no sidebar conflicts, dark-mode safe
with st.expander("📂  Upload Aging Report  —  click to expand / collapse", expanded=True):
    st.markdown("""
    <div style='display:flex;gap:24px;align-items:flex-start;padding:4px 0 8px'>
        <div style='flex:1'>
    """, unsafe_allow_html=True)

    col_up, col_info = st.columns([2, 3], gap="large")
    with col_up:
        uploaded_file = st.file_uploader(
            "Drop your Excel Aging report here",
            type=["xlsx"],
            help="Supports .xlsx files. The system auto-detects Total AR, Current, Terms and Customer columns."
        )
    with col_info:
        st.markdown("""
        <div style='padding-top:8px'>
            <div style='font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#4b5563;margin-bottom:10px'>Expected Columns</div>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px'>
                <div style='background:#1c1e24;border:1px solid #2a2d37;border-radius:7px;padding:8px 12px'>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:#ff6b35;font-weight:700'>Total AR</div>
                    <div style='font-size:0.62rem;color:#6b7280;margin-top:2px'>Total receivables</div>
                </div>
                <div style='background:#1c1e24;border:1px solid #2a2d37;border-radius:7px;padding:8px 12px'>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:#22c55e;font-weight:700'>Current</div>
                    <div style='font-size:0.62rem;color:#6b7280;margin-top:2px'>On-time balance</div>
                </div>
                <div style='background:#1c1e24;border:1px solid #2a2d37;border-radius:7px;padding:8px 12px'>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:#9ca3af;font-weight:700'>Customer</div>
                    <div style='font-size:0.62rem;color:#6b7280;margin-top:2px'>Account name</div>
                </div>
                <div style='background:#1c1e24;border:1px solid #2a2d37;border-radius:7px;padding:8px 12px'>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:#9ca3af;font-weight:700'>Terms</div>
                    <div style='font-size:0.62rem;color:#6b7280;margin-top:2px'>Payment terms</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


# ── EMPTY STATE ───────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown("""
    <div style='margin:3rem auto;max-width:440px;background:#16181c;border:1px solid #2a2d37;border-radius:14px;padding:3rem 2rem;text-align:center'>
        <div style='font-size:2.2rem;margin-bottom:1rem'>📊</div>
        <div style='font-size:1rem;font-weight:800;color:#f0f0f0;margin-bottom:8px'>No data loaded</div>
        <div style='font-size:0.76rem;color:#6b7280;line-height:1.65'>Upload your Aging report using the panel above to start the portfolio analysis.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
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

    total_ar       = df[col_total].sum()
    total_current  = df[col_current].sum()
    total_pd       = total_ar - total_current
    pct_pd         = pct(total_pd, total_ar)
    pct_cur        = pct(total_current, total_ar)

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
    st.markdown("""
    <div class='sec-hdr'>
        <span class='sec-title'>Portfolio Overview</span>
        <span class='sec-badge'>LIVE</span>
    </div>""", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4, gap="small")
    with c1:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>Total Portfolio (AR)</div>
            <div class='kpi-value' style='color:#f0f0f0'>{fmt(total_ar)}</div>
            <div class='kpi-sub'>{n_total} active accounts</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:100%;background:#ff6b35'></div></div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>Current (On Time)</div>
            <div class='kpi-value' style='color:#22c55e'>{fmt(total_current)}</div>
            <div class='kpi-sub'>{n_current} accounts · {pct_cur}% of total</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_cur}%;background:#22c55e'></div></div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>Past Due (Overdue)</div>
            <div class='kpi-value' style='color:#ef4444'>{fmt(total_pd)}</div>
            <div class='kpi-sub'>{n_overdue} accounts · {pct_pd}% of total</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{pct_pd}%;background:#ef4444'></div></div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>Top 5 Debtors</div>
            <div class='kpi-value' style='color:#ffc300'>{fmt(top5_total)}</div>
            <div class='kpi-sub'>{pct_top5}% of total overdue</div>
            <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{min(pct_top5,100)}%;background:#ffc300'></div></div>
        </div>""", unsafe_allow_html=True)


    # ── CHARTS ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class='sec-hdr'>
        <span class='sec-title'>Aging Distribution</span>
        <span class='sec-badge'>ANALYSIS</span>
    </div>""", unsafe_allow_html=True)

    ch1, ch2, ch3 = st.columns([3,2,2], gap="small")

    with ch1:
        bnames  = list(bucket_vals.keys())
        bamount = list(bucket_vals.values())
        fig_bar = go.Figure(go.Bar(
            x=bnames, y=bamount,
            marker=dict(color=B_COLORS, line=dict(width=0)),
            text=[f"${v/1000:.1f}K" if v>=1000 else f"${v:.0f}" for v in bamount],
            textposition='outside',
            textfont=dict(family='JetBrains Mono',size=9,color='#6b7280'),
        ))
        fig_bar.update_layout(
            **THEME,
            title=dict(text="Overdue by time bucket",font=dict(size=11,color='#6b7280'),x=0),
            showlegend=False,
            xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=10,color='#6b7280')),
            yaxis=dict(showgrid=True,gridcolor='#23262e',zeroline=False,tickprefix='$',tickformat=',.0f',tickfont=dict(size=9)),
            bargap=0.38,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with ch2:
        fig_d = go.Figure(go.Pie(
            labels=['Current','Past Due'], values=[total_current,total_pd],
            hole=0.68, marker=dict(colors=['#22c55e','#ef4444'],line=dict(width=0)),
            textinfo='percent', textfont=dict(family='Inter',size=10,color='#f0f0f0'),
        ))
        fig_d.update_layout(
            **THEME,
            title=dict(text="Portfolio health",font=dict(size=11,color='#6b7280'),x=0),
            showlegend=True,
            legend=dict(orientation='h',x=0.05,y=-0.12,font=dict(size=10,color='#9ca3af'),bgcolor='rgba(0,0,0,0)'),
            annotations=[dict(text=f"<b>{pct_pd:.0f}%</b><br>overdue",x=0.5,y=0.5,showarrow=False,font=dict(family='Inter',size=14,color='#ef4444'))],
        )
        st.plotly_chart(fig_d, use_container_width=True)

    with ch3:
        top_n  = min(8, len(df_sla))
        top_df = df_sla.head(top_n)
        custs  = top_df[col_customer].astype(str).str[:16].tolist() if col_customer in top_df.columns else [f"#{i}" for i in range(top_n)]
        amts   = top_df['Past_Due'].tolist()
        fig_h  = go.Figure(go.Bar(
            y=custs[::-1], x=amts[::-1], orientation='h',
            marker=dict(color=amts[::-1],colorscale=[[0,'#ffc300'],[0.5,'#ff6b35'],[1,'#ef4444']],line=dict(width=0)),
            text=[f"${v:,.0f}" for v in amts[::-1]], textposition='outside',
            textfont=dict(family='JetBrains Mono',size=8,color='#6b7280'),
        ))
        fig_h.update_layout(
            **THEME,
            title=dict(text=f"Top {top_n} debtors",font=dict(size=11,color='#6b7280'),x=0),
            showlegend=False,
            xaxis=dict(showgrid=True,gridcolor='#23262e',zeroline=False,tickprefix='$',tickformat=',.0f',tickfont=dict(size=8)),
            yaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=9,color='#9ca3af')),
        )
        st.plotly_chart(fig_h, use_container_width=True)


    # ── BREAKDOWN ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div class='sec-hdr'>
        <span class='sec-title'>Portfolio Breakdown</span>
        <span class='sec-badge'>COMPOSITION</span>
    </div>""", unsafe_allow_html=True)

    bk1, bk2, bk3 = st.columns(3, gap="small")

    with bk1:
        st.markdown("<div class='kpi'><div class='kpi-label'>Aging Composition</div></div>", unsafe_allow_html=True)
        total_b = sum(bucket_vals.values()) or 1
        b_color_list = ['#22c55e','#ffc300','#f97316','#ff6b35','#ef4444']
        for (name, val), color in zip(bucket_vals.items(), b_color_list):
            p = int(pct(val, total_b))
            r1, r2 = st.columns([3,1])
            with r1:
                st.markdown(f"<span style='font-size:0.68rem;color:#9ca3af'>{name}</span>", unsafe_allow_html=True)
                st.progress(p)
            with r2:
                st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;font-weight:700;color:{color};padding-top:6px;text-align:right'>${val/1000:.1f}K</div>", unsafe_allow_html=True)

    with bk2:
        pct_ov = int(pct(n_overdue, n_total))
        st.markdown("<div class='kpi'><div class='kpi-label'>Account Status</div></div>", unsafe_allow_html=True)
        r1, r2 = st.columns([3,1])
        with r1:
            st.markdown("<span style='font-size:0.68rem;color:#9ca3af'>Current</span>", unsafe_allow_html=True)
            st.progress(100 - pct_ov)
        with r2:
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;font-weight:700;color:#22c55e;padding-top:6px;text-align:right'>{n_current}</div>", unsafe_allow_html=True)
        r3, r4 = st.columns([3,1])
        with r3:
            st.markdown("<span style='font-size:0.68rem;color:#9ca3af'>Overdue</span>", unsafe_allow_html=True)
            st.progress(pct_ov)
        with r4:
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;font-weight:700;color:#ef4444;padding-top:6px;text-align:right'>{n_overdue}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"<div style='font-size:0.58rem;color:#4b5563;text-transform:uppercase;letter-spacing:.08em'>Avg overdue</div><div style='font-family:JetBrains Mono,monospace;font-size:0.85rem;font-weight:700;color:#ff6b35;margin-top:2px'>{fmt(avg_pd)}</div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div style='font-size:0.58rem;color:#4b5563;text-transform:uppercase;letter-spacing:.08em'>Max single</div><div style='font-family:JetBrains Mono,monospace;font-size:0.85rem;font-weight:700;color:#ef4444;margin-top:2px'>{fmt(max_pd)}</div>", unsafe_allow_html=True)

    with bk3:
        st.markdown(f"""<div class='kpi'>
            <div class='kpi-label'>SLA Touch Goal</div>
            <div class='kpi-value' style='color:#ffc300;font-size:2.3rem'>{n_overdue}</div>
            <div class='kpi-sub'>accounts to contact this week</div>
            <div style='margin-top:14px;padding:10px;background:#0e0f11;border-radius:7px;display:flex;justify-content:space-between;align-items:center'>
                <span style='font-size:0.64rem;color:#6b7280'>Total exposure</span>
                <span style='font-family:JetBrains Mono,monospace;font-size:0.78rem;font-weight:700;color:#ff6b35'>{fmt(total_pd)}</span>
            </div>
            <div style='margin-top:6px;padding:10px;background:#0e0f11;border-radius:7px;display:flex;justify-content:space-between;align-items:center'>
                <span style='font-size:0.64rem;color:#6b7280'>% portfolio at risk</span>
                <span style='font-family:JetBrains Mono,monospace;font-size:0.78rem;font-weight:700;color:#ef4444'>{pct_pd}%</span>
            </div>
        </div>""", unsafe_allow_html=True)


    # ── PRIORITY ACTION LIST ───────────────────────────────────────────────────
    st.markdown(f"""
    <div class='sec-hdr'>
        <span class='sec-title'>Priority Action List</span>
        <span class='sec-badge'>100% TOUCH GOAL · {n_overdue} ACCOUNTS</span>
    </div>""", unsafe_allow_html=True)

    cols_show = [c for c in [col_customer,'Past_Due',col_terms,col_total] if c in df_sla.columns]
    reporte   = df_sla[cols_show].copy()

    btn_col, _ = st.columns([2,5])
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
    disp.rename(columns={'Past_Due':'Past Due', col_total:'Total AR'}, inplace=True)
    st.dataframe(disp, use_container_width=True, hide_index=True, height=380)
    st.info(f"💡 **{n_overdue} accounts** need action this week · Total overdue: **{fmt(total_pd)}** ({pct_pd}% of portfolio) · Avg per account: **{fmt(avg_pd)}**")

except Exception as e:
    st.error(f"❌ Error processing file: {e}")
    st.exception(e)

# close main-wrap div
st.markdown("</div>", unsafe_allow_html=True)
