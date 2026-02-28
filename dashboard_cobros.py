import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(
    page_title="AR Collections Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── LANGUAGE & THEME STATE ────────────────────────────────────────────────────
if 'lang'  not in st.session_state: st.session_state.lang  = 'EN'
if 'theme' not in st.session_state: st.session_state.theme = 'light'

LANG = st.session_state.lang
DARK = (st.session_state.theme == 'dark')

# ── TRANSLATIONS ──────────────────────────────────────────────────────────────
T = {
    'EN': {
        'title':'Collections', 'title_acc':'Dashboard',
        'sub':'AR Performance · Risk Exposure · Collector SLA',
        'upload_label':'📂 Aging Report (.xlsx)',
        'filters':'🔍 Filters',
        'filter_coll':'Collector', 'filter_reg':'Region', 'filter_risk':'Risk Category',
        'all_coll':'All collectors', 'all_reg':'All regions', 'all_risk':'All categories',
        'instructions':'Upload the SAP Aging Report in .xlsx format. Buckets, collectors, risk tiers and credit limits are auto-detected.',
        'no_data':'No data loaded',
        'no_data_sub':'Upload your SAP Aging Report from the left panel to start the portfolio analysis.',
        'err_cols':'Could not find Total / Current columns. Check the file format.',
        'kpi_total':'Total AR Portfolio', 'kpi_current':'Current (On Time)',
        'kpi_pd':'Past Due Exposure', 'kpi_90':'90+ Days Critical',
        'kpi_days':'Avg Days Overdue', 'kpi_cu':'Credit Utilization',
        'active_accts':'active accounts', 'accts':'accts', 'at_risk':'at risk',
        'of_overdue':'of overdue', 'weighted':'weighted avg',
        'tab1':'📈  Aging Analysis', 'tab2':'👤  Collector View',
        'tab3':'⚠️  Risk & Credit', 'tab4':'📋  Action List',
        'aging_dist':'Aging Distribution', 'bucket_breakdown':'BUCKET BREAKDOWN',
        'overdue_by_bucket':'Overdue by aging bucket',
        'portfolio_health':'Portfolio health', 'overdue':'overdue',
        'balance_by_tier':'Balance by tier',
        'aging_comp':'Aging Composition', 'pct_mix':'% MIX',
        'of_overd':'of overdue',
        'coll_perf':'Collector Performance', 'sla_mgmt':'SLA MANAGEMENT',
        'ar_by_coll':'AR by collector (stacked)', 'current':'Current', 'past_due':'Past Due',
        'accts_vs_pct':'Accounts vs % Past Due', 'num_accounts':'# Accounts',
        'coll_summary':'Collector Summary', 'detail':'DETAIL',
        'collector':'Collector', 'num_accts':'# Accts', 'num_od':'# OD',
        'total_ar':'Total AR', 'avg_od':'Avg OD', 'pct_pd':'% Past Due',
        'regional':'Regional Breakdown', 'geography':'GEOGRAPHY',
        'pd_by_region':'Past Due by Region',
        'no_collector':'No Collector column found in this file.',
        'risk_exp':'Risk Exposure Analysis', 'credit_risk':'CREDIT RISK',
        'pd_by_risk':'Past Due by Risk Category',
        'pd_by_tier':'Past Due by Risk Tier',
        'high_risk':'High Risk Exposure', 'med_risk':'Medium Risk Exposure',
        'low_risk':'Low Risk Exposure',
        'no_risk':'No Risk Category column detected.',
        'risk_table':'Risk & Payer Detail', 'risk_table_badge':'DOWNLOAD READY',
        'download_risk':'📥 Download Risk Table',
        'customer':'Customer', 'payer_id':'Payer ID', 'risk_cat':'Risk Category',
        'location':'Location', 'region':'Region', 'payment_terms':'Payment Terms',
        'sla_goal':'SLA TOUCH GOAL',
        'to_contact':'Accounts to Contact', 'overd_cycle':'overdue this cycle',
        'total_exp':'Total Exposure', 'of_portfolio':'of portfolio',
        'avg_acct':'Avg per Account', 'avg_bal':'average overdue balance',
        'top5_conc':'Top 5 Concentration', 'in_top5':'in top 5 accts',
        'all_current':'🎉 All accounts are current! No overdue balances in this portfolio.',
        'top_accts':'Top {n} accounts by past due balance',
        'full_list':'Full Collection List', 'dl_ready':'DOWNLOAD READY',
        'download':'📥 Download Collection List',
        'info_footer':'{n} accounts to action · Total overdue: {total} ({pct}% of portfolio) · Avg per account: {avg} · 90+ day critical: {crit} ({pct90}%)',
        'ar_perf':'AR Performance', 'risk_exp_short':'Risk Exposure', 'coll_sla':'Collector SLA',
    },
    'ES': {
        'title':'Collections', 'title_acc':'Dashboard',
        'sub':'Rendimiento AR · Exposición de Riesgo · SLA de Cobrador',
        'upload_label':'📂 Reporte de Antigüedad (.xlsx)',
        'filters':'🔍 Filtros',
        'filter_coll':'Cobrador', 'filter_reg':'Región', 'filter_risk':'Categoría de Riesgo',
        'all_coll':'Todos los cobradores', 'all_reg':'Todas las regiones', 'all_risk':'Todas las categorías',
        'instructions':'Sube el Reporte de Antigüedad SAP en formato .xlsx. Se detectan automáticamente los buckets, cobradores, niveles de riesgo y límites de crédito.',
        'no_data':'Sin datos cargados',
        'no_data_sub':'Sube tu Reporte de Antigüedad SAP desde el panel izquierdo para comenzar el análisis.',
        'err_cols':'No se encontraron las columnas Total / Current. Verifica el formato del archivo.',
        'kpi_total':'Portafolio AR Total', 'kpi_current':'Al Día (A Tiempo)',
        'kpi_pd':'Exposición Vencida', 'kpi_90':'Crítico 90+ Días',
        'kpi_days':'Días Prom. Vencido', 'kpi_cu':'Utilización de Crédito',
        'active_accts':'cuentas activas', 'accts':'ctas', 'at_risk':'en riesgo',
        'of_overdue':'del vencido', 'weighted':'prom. ponderado',
        'tab1':'📈  Análisis de Antigüedad', 'tab2':'👤  Vista Cobrador',
        'tab3':'⚠️  Riesgo y Crédito', 'tab4':'📋  Lista de Acción',
        'aging_dist':'Distribución de Antigüedad', 'bucket_breakdown':'DESGLOSE POR BUCKET',
        'overdue_by_bucket':'Vencido por bucket de antigüedad',
        'portfolio_health':'Salud del portafolio', 'overdue':'vencido',
        'balance_by_tier':'Saldo por nivel',
        'aging_comp':'Composición de Antigüedad', 'pct_mix':'% MIX',
        'of_overd':'del vencido',
        'coll_perf':'Rendimiento del Cobrador', 'sla_mgmt':'GESTIÓN SLA',
        'ar_by_coll':'AR por cobrador (apilado)', 'current':'Al día', 'past_due':'Vencido',
        'accts_vs_pct':'Cuentas vs % Vencido', 'num_accounts':'# Cuentas',
        'coll_summary':'Resumen de Cobrador', 'detail':'DETALLE',
        'collector':'Cobrador', 'num_accts':'# Ctas', 'num_od':'# Venc',
        'total_ar':'AR Total', 'avg_od':'Prom. Vencido', 'pct_pd':'% Vencido',
        'regional':'Desglose Regional', 'geography':'GEOGRAFÍA',
        'pd_by_region':'Vencido por Región',
        'no_collector':'No se encontró columna de Cobrador en este archivo.',
        'risk_exp':'Análisis de Exposición de Riesgo', 'credit_risk':'RIESGO CREDITICIO',
        'pd_by_risk':'Vencido por Categoría de Riesgo',
        'pd_by_tier':'Vencido por Nivel de Riesgo',
        'high_risk':'Exposición Alto Riesgo', 'med_risk':'Exposición Riesgo Medio',
        'low_risk':'Exposición Bajo Riesgo',
        'no_risk':'No se detectó columna de Categoría de Riesgo.',
        'risk_table':'Detalle Riesgo y Pagador', 'risk_table_badge':'LISTO PARA DESCARGA',
        'download_risk':'📥 Descargar Tabla de Riesgo',
        'customer':'Cliente', 'payer_id':'ID Pagador', 'risk_cat':'Categoría Riesgo',
        'location':'Ubicación', 'region':'Región', 'payment_terms':'Términos de Pago',
        'sla_goal':'META SLA',
        'to_contact':'Cuentas a Contactar', 'overd_cycle':'vencidas este ciclo',
        'total_exp':'Exposición Total', 'of_portfolio':'del portafolio',
        'avg_acct':'Promedio por Cuenta', 'avg_bal':'saldo promedio vencido',
        'top5_conc':'Concentración Top 5', 'in_top5':'en top 5 ctas',
        'all_current':'🎉 ¡Todas las cuentas están al día! Sin saldos vencidos en este portafolio.',
        'top_accts':'Top {n} cuentas por saldo vencido',
        'full_list':'Lista Completa de Cobros', 'dl_ready':'LISTA PARA DESCARGA',
        'download':'📥 Descargar Lista de Cobros',
        'info_footer':'{n} cuentas a gestionar · Total vencido: {total} ({pct}% del portafolio) · Prom. por cuenta: {avg} · Crítico 90+d: {crit} ({pct90}%)',
        'ar_perf':'Rendimiento AR', 'risk_exp_short':'Exposición Riesgo', 'coll_sla':'SLA Cobrador',
    }
}
t = T[LANG]

# ── COLORS ────────────────────────────────────────────────────────────────────
if DARK:
    BG0='#0d0e11'; BG1='#13141a'; BG2='#1a1c24'; BG3='#22242e'
    BORDER='#2a2d3a'; T1='#f1f1f3'; T2='#8b8fa8'; T3='#404460'
    CHART_GRID='#22242e'; CHART_FONT='#8b8fa8'
else:
    BG0='#f4f6f9'; BG1='#ffffff'; BG2='#f0f2f5'; BG3='#e5e7eb'
    BORDER='#d1d5db'; T1='#111827'; T2='#6b7280'; T3='#9ca3af'
    CHART_GRID='#e5e7eb'; CHART_FONT='#6b7280'

ORANGE='#ff6b35'; YELLOW='#f59e0b'; GREEN='#10b981'
RED='#ef4444'; BLUE='#3b82f6'; PURPLE='#8b5cf6'
BUCKET_COLORS = ['#10b981','#f59e0b','#f97316','#ff6b35','#ef4444','#dc2626','#991b1b']

THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color=CHART_FONT, size=10),
    margin=dict(l=8, r=8, t=36, b=8),
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');
html,body,[class*="css"],.stApp {{
    font-family:'Inter',sans-serif !important;
    background:{BG0} !important;
    color:{T1} !important;
}}
.block-container {{ padding:1.4rem 2rem 3rem !important; max-width:100% !important; }}
#MainMenu {{ visibility:hidden; }}
footer {{ visibility:hidden; }}
.stDeployButton {{ display:none; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background:{BG1} !important;
    border-right:1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] section {{ padding:1.4rem 1.2rem !important; }}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] small {{ color:{T2} !important; }}
[data-testid="collapsedControl"] {{
    background:{BG2} !important;
    border:1px solid {BORDER} !important;
    color:{T1} !important;
}}

/* File uploader */
[data-testid="stFileUploadDropzone"] {{
    background:{BG2} !important;
    border:1.5px dashed rgba(255,107,53,.5) !important;
    border-radius:10px !important;
}}
[data-testid="stFileUploadDropzone"] * {{ color:{T2} !important; }}
[data-testid="stFileUploadDropzone"] button {{
    background:{BG3} !important;
    color:{T1} !important;
    border:1px solid {BORDER} !important;
    border-radius:6px !important;
}}

::-webkit-scrollbar{{width:4px;height:4px}}
::-webkit-scrollbar-track{{background:{BG0}}}
::-webkit-scrollbar-thumb{{background:{BG3};border-radius:4px}}

/* KPI cards */
.kpi {{
    background:{BG1};
    border:1px solid {BORDER};
    border-radius:12px;
    padding:18px 20px;
    position:relative;
    overflow:hidden;
}}
.kpi::before {{ content:''; position:absolute; top:0;left:0;right:0;height:2px; }}
.kpi.orange::before {{ background:linear-gradient(90deg,#ff6b35,transparent); }}
.kpi.green::before  {{ background:linear-gradient(90deg,#10b981,transparent); }}
.kpi.red::before    {{ background:linear-gradient(90deg,#ef4444,transparent); }}
.kpi.yellow::before {{ background:linear-gradient(90deg,#f59e0b,transparent); }}
.kpi.blue::before   {{ background:linear-gradient(90deg,#3b82f6,transparent); }}
.kpi.purple::before {{ background:linear-gradient(90deg,#8b5cf6,transparent); }}
.kpi-label {{ font-size:.56rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:{T3};margin-bottom:10px; }}
.kpi-value {{ font-size:1.75rem;font-weight:900;line-height:1;letter-spacing:-.04em; }}
.kpi-sub   {{ font-size:.62rem;color:{T2};margin-top:7px;font-weight:500; }}
.kpi-bar   {{ margin-top:12px;height:3px;border-radius:2px;background:{BG3};overflow:hidden; }}
.kpi-bar-fill {{ height:100%;border-radius:2px; }}

/* Section header */
.sec-hdr {{
    display:flex;align-items:center;gap:10px;
    margin:1.8rem 0 1rem;padding-bottom:10px;
    border-bottom:1px solid {BORDER};
}}
.sec-title {{ font-size:.66rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{T1}; }}
.sec-badge {{
    font-size:.54rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
    background:rgba(255,107,53,.1);color:{ORANGE};
    border:1px solid rgba(255,107,53,.25);border-radius:4px;padding:2px 8px;
}}

/* Main header */
.main-title {{ font-size:1.5rem;font-weight:900;letter-spacing:-.04em;color:{T1};line-height:1; }}
.main-title .acc {{ color:{ORANGE}; }}
.main-sub  {{ font-size:.58rem;font-weight:600;color:{T3};text-transform:uppercase;letter-spacing:.12em;margin-top:5px; }}
.ts-chip {{
    font-family:'JetBrains Mono',monospace;font-size:.62rem;
    color:{T2};background:{BG2};
    border:1px solid {BORDER};border-radius:6px;padding:5px 12px;
    white-space:nowrap;
}}

/* Empty state */
.empty-state {{
    margin:5rem auto;max-width:400px;background:{BG1};
    border:1px solid {BORDER};border-radius:16px;
    padding:3rem 2.5rem;text-align:center;
}}

/* DataFrames */
[data-testid="stDataFrame"] {{
    border-radius:10px !important;border:1px solid {BORDER} !important;overflow:hidden !important;
}}
[data-testid="stDataFrame"] thead th {{
    background:{BG2} !important;color:{T3} !important;
    font-size:.57rem !important;letter-spacing:.1em !important;
    text-transform:uppercase !important;
    font-family:'JetBrains Mono',monospace !important;font-weight:700 !important;
}}
[data-testid="stDataFrame"] tbody td {{
    font-family:'JetBrains Mono',monospace !important;
    font-size:.75rem !important;color:{T1} !important;
    background:{BG1} !important;
}}

/* Download button */
.stDownloadButton>button {{
    background:linear-gradient(135deg,#ff6b35,#d94e1f) !important;
    color:#fff !important;border:none !important;
    border-radius:8px !important;font-size:.72rem !important;
    font-weight:700 !important;letter-spacing:.05em !important;
    padding:.5rem 1.4rem !important;
}}
.stDownloadButton>button:hover {{ opacity:.82; }}

/* Alerts */
.stAlert {{
    background:rgba(255,107,53,.06) !important;
    border:1px solid rgba(255,107,53,.2) !important;
    border-radius:8px !important;color:{T1} !important;
}}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background:{BG1};border-radius:8px;
    border:1px solid {BORDER};padding:4px;gap:2px;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    background:transparent !important;color:{T2} !important;
    border-radius:6px !important;font-size:.68rem !important;
    font-weight:600 !important;letter-spacing:.06em !important;
    text-transform:uppercase !important;padding:6px 16px !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    background:{BG3} !important;color:{T1} !important;
}}

/* Progress */
.stProgress>div>div>div {{ background:{BG3} !important;border-radius:3px !important; }}
.stProgress>div>div>div>div {{ border-radius:3px !important; }}

/* Multiselect */
[data-testid="stMultiSelect"]>div {{
    background:{BG2} !important;border:1px solid {BORDER} !important;border-radius:8px !important;
}}

/* Toggle buttons */
.toggle-btn {{
    display:inline-flex;align-items:center;gap:6px;
    font-size:.65rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
    background:{BG2};color:{T2};
    border:1px solid {BORDER};border-radius:8px;
    padding:6px 12px;cursor:pointer;margin-right:6px;
}}
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def clean_money(s):
    return pd.to_numeric(
        s.astype(str).str.replace(r'[\$,\s]','',regex=True).str.strip(),
        errors='coerce'
    ).fillna(0)

def to_excel_bytes(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Data')
    return out.getvalue()

def fmt(v):    return f"${v:,.2f}"
def fmtk(v):   return f"${v/1000:,.1f}K" if abs(v)>=1000 else f"${v:,.0f}"
def pct(p,t):  return round(p/t*100,1) if t else 0

def safe_colors(values, lo=GREEN, mid=YELLOW, hi=RED):
    if not values: return []
    mn,mx = min(values), max(values)
    if mn==mx: return [mid]*len(values)
    out=[]
    for v in values:
        r=(v-mn)/(mx-mn)
        out.append(lo if r<.33 else mid if r<.66 else hi)
    return out

def dyn(val, warn=20, crit=40):
    if val>=crit: return RED
    if val>=warn: return YELLOW
    return GREEN

def find_col(df, patterns):
    for p in patterns:
        for c in df.columns:
            if p.lower() in c.lower():
                return c
    return None

@st.cache_data
def load_data(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes))
    df.columns = [str(c).strip().replace('\n',' ') for c in df.columns]
    return df

def safe_bar_chart(x_vals, y_vals, orientation='v', colors=None,
                   title='', xprefix='$', is_currency=True):
    """Build a bar chart safely — handles empty or single-value data."""
    if not x_vals or not y_vals:
        fig = go.Figure()
        fig.update_layout(**THEME,
            title=dict(text=title, font=dict(size=11,color=CHART_FONT), x=0),
            annotations=[dict(text='No data', x=0.5, y=0.5, showarrow=False,
                              font=dict(color=T2, size=12))])
        return fig
    colors = colors or safe_colors(y_vals if orientation=='v' else x_vals)
    texts  = [fmtk(v) for v in (y_vals if orientation=='v' else x_vals)]
    if orientation=='v':
        fig = go.Figure(go.Bar(x=x_vals, y=y_vals, marker=dict(color=colors,line=dict(width=0)),
                               text=texts, textposition='outside',
                               textfont=dict(family='JetBrains Mono',size=9,color=CHART_FONT)))
        fig.update_layout(**THEME, showlegend=False,
            title=dict(text=title,font=dict(size=11,color=CHART_FONT),x=0),
            xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=10,color=CHART_FONT)),
            yaxis=dict(showgrid=True,gridcolor=CHART_GRID,zeroline=False,
                       tickprefix=xprefix if is_currency else '',
                       tickformat=',.0f' if is_currency else '',tickfont=dict(size=9)),
            bargap=0.35)
    else:
        fig = go.Figure(go.Bar(y=x_vals, x=y_vals, orientation='h',
                               marker=dict(color=colors,line=dict(width=0)),
                               text=texts, textposition='outside',
                               textfont=dict(family='JetBrains Mono',size=8,color=CHART_FONT)))
        fig.update_layout(**THEME, showlegend=False,
            title=dict(text=title,font=dict(size=11,color=CHART_FONT),x=0),
            margin=dict(l=8,r=60,t=36,b=8),
            xaxis=dict(showgrid=True,gridcolor=CHART_GRID,zeroline=False,
                       tickprefix=xprefix if is_currency else '',
                       tickformat=',.0f' if is_currency else '',tickfont=dict(size=8)),
            yaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=9,color=CHART_FONT)))
    return fig


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='margin-bottom:1.2rem;padding-bottom:1rem;border-bottom:1px solid {BORDER}'>
        <div style='font-size:1rem;font-weight:900;color:{T1};letter-spacing:-.025em;line-height:1.3'>
            ⚡ Collections<br><span style='color:{ORANGE}'>Intelligence</span>
        </div>
        <div style='font-size:.52rem;color:{T3};text-transform:uppercase;letter-spacing:.14em;margin-top:5px'>
            AR Analytics · v2.1
        </div>
    </div>
    <div style='font-size:.54rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
                color:{T3};margin-bottom:8px'>{t['upload_label']}</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("file", type=["xlsx"], label_visibility="collapsed")

    # Language & theme toggles
    st.markdown(f"<div style='height:.8rem'></div>", unsafe_allow_html=True)
    tc1, tc2 = st.columns(2)
    with tc1:
        lang_label = "🌐 ES" if LANG=='EN' else "🌐 EN"
        if st.button(lang_label, use_container_width=True):
            st.session_state.lang = 'ES' if LANG=='EN' else 'EN'
            st.rerun()
    with tc2:
        theme_label = "🌙 Dark" if not DARK else "☀️ Light"
        if st.button(theme_label, use_container_width=True):
            st.session_state.theme = 'dark' if not DARK else 'light'
            st.rerun()

    st.markdown(f"""
    <div style='margin-top:1rem;padding-top:1rem;border-top:1px solid {BORDER}'>
        <div style='font-size:.54rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
                    color:{T3};margin-bottom:8px'>{t['filters']}</div>
    </div>""", unsafe_allow_html=True)

    col_ph  = st.empty()
    reg_ph  = st.empty()
    risk_ph = st.empty()

    st.markdown(f"""
    <div style='margin-top:1rem;padding-top:1rem;border-top:1px solid {BORDER};
                font-size:.6rem;color:{T2};line-height:1.8'>
        {t['instructions']}
    </div>""", unsafe_allow_html=True)


# ── HEADER ────────────────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%d %b %Y  ·  %H:%M")
hc1, hc2 = st.columns([6,1])
with hc1:
    st.markdown(f"""
    <div style='margin-bottom:.4rem'>
        <div class='main-title'>{t['title']} <span class='acc'>{t['title_acc']}</span></div>
        <div class='main-sub'>{t['sub']}</div>
    </div>""", unsafe_allow_html=True)
with hc2:
    st.markdown(f"<div class='ts-chip' style='text-align:right;margin-top:4px'>🕐 {now_str}</div>",
                unsafe_allow_html=True)
st.markdown(f"<hr style='border:none;border-top:1px solid {BORDER};margin:.6rem 0 1.4rem'>",
            unsafe_allow_html=True)


# ── EMPTY STATE ───────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown(f"""
    <div class='empty-state'>
        <div style='font-size:2.8rem;margin-bottom:1rem'>📊</div>
        <div style='font-size:1rem;font-weight:800;color:{T1};margin-bottom:8px'>{t['no_data']}</div>
        <div style='font-size:.72rem;color:{T2};line-height:1.75'>{t['no_data_sub']}</div>
    </div>""", unsafe_allow_html=True)
    st.stop()


# ── LOAD ──────────────────────────────────────────────────────────────────────
try:
    df_raw = load_data(uploaded_file.read())
except Exception as e:
    st.error(f"❌ {e}")
    st.stop()

COL_PAYER  = find_col(df_raw, ['Payer','Customer','Client'])
COL_PAYID  = find_col(df_raw, ['Payer.1','Payer ID','PayerID'])   # numeric payer ID
COL_COLL   = find_col(df_raw, ['Collector'])
COL_LOC    = find_col(df_raw, ['Location'])
COL_REG    = find_col(df_raw, ['Region'])
COL_TERMS  = find_col(df_raw, ['Payment terms','Terms'])
COL_RISK   = find_col(df_raw, ['Cr/Mgt Risk','Risk Category','Risk'])
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
    st.error(f"⚠️ {t['err_cols']}")
    st.dataframe(df_raw.head(3))
    st.stop()


# ── PROCESS ───────────────────────────────────────────────────────────────────
df = df_raw.copy()
for c in [c for c in [COL_TOTAL, COL_CURR] + list(BUCKETS.values()) if c]:
    df[c] = clean_money(df[c])

df['_PD'] = (df[COL_TOTAL] - df[COL_CURR]).clip(lower=0)
for bname, bcol in BUCKETS.items():
    df[f'_B_{bname}'] = df[bcol].clip(lower=0)


# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
cols_list = sorted(df[COL_COLL].dropna().unique().tolist())  if COL_COLL  else []
regs_list = sorted(df[COL_REG].dropna().unique().tolist())   if COL_REG   else []
risk_list = sorted(df[COL_RISK].dropna().unique().tolist())  if COL_RISK  else []

with col_ph:
    sel_coll = st.multiselect(t['filter_coll'], cols_list, placeholder=t['all_coll'])
with reg_ph:
    sel_reg  = st.multiselect(t['filter_reg'],  regs_list, placeholder=t['all_reg'])
with risk_ph:
    sel_risk = st.multiselect(t['filter_risk'], risk_list, placeholder=t['all_risk'])

dff = df.copy()
if sel_coll and COL_COLL:  dff = dff[dff[COL_COLL].isin(sel_coll)]
if sel_reg  and COL_REG:   dff = dff[dff[COL_REG].isin(sel_reg)]
if sel_risk and COL_RISK:  dff = dff[dff[COL_RISK].isin(sel_risk)]


# ── METRICS ───────────────────────────────────────────────────────────────────
total_ar  = float(dff[COL_TOTAL].sum())
total_cur = float(dff[COL_CURR].sum())
total_pd  = float(dff['_PD'].sum())
pct_pd    = pct(total_pd, total_ar)
pct_cur   = pct(total_cur, total_ar)
n_total   = len(dff)

df_sla    = dff[dff['_PD'] > 0.01].copy().sort_values('_PD', ascending=False)
n_od      = len(df_sla)
n_ok      = n_total - n_od
avg_od    = total_pd / n_od if n_od else 0.0
top5_val  = float(df_sla.head(5)['_PD'].sum()) if not df_sla.empty else 0.0
pct_top5  = pct(top5_val, total_pd)

bkt = {b: float(dff[f'_B_{b}'].sum()) for b in BUCKETS}
pd_90p    = sum(v for k,v in bkt.items() if any(x in k for x in ['91','121','181','365+']))
pct_90p   = pct(pd_90p, total_pd)

midpoints = {'1-30d':15,'31-60d':45,'61-90d':75,'91-120d':105,
             '121-180d':150,'181-365d':270,'365+d':400}
tot_aged  = sum(bkt.values()) or 1.0
avg_days  = sum(bkt.get(b,0)*d for b,d in midpoints.items()) / tot_aged


# ════════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ════════════════════════════════════════════════════════════════════════════
k1,k2,k3,k4,k5,k6 = st.columns(6, gap="small")

def kpi(color, label, value_html, sub, bar_w, bar_color=None):
    bc = bar_color or color
    color_map = {'orange':ORANGE,'green':GREEN,'red':RED,'yellow':YELLOW,'blue':BLUE,'purple':PURPLE}
    hex_c = color_map.get(bc, ORANGE)
    return f"""<div class='kpi {color}'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{value_html}</div>
        <div class='kpi-sub'>{sub}</div>
        <div class='kpi-bar'><div class='kpi-bar-fill' style='width:{min(bar_w,100):.0f}%;background:{hex_c}'></div></div>
    </div>"""

with k1: st.markdown(kpi('orange', t['kpi_total'],
    f"<span style='color:{T1}'>{fmtk(total_ar)}</span>",
    f"{n_total} {t['active_accts']}", 100), unsafe_allow_html=True)

with k2: st.markdown(kpi('green', t['kpi_current'],
    f"<span style='color:{GREEN}'>{fmtk(total_cur)}</span>",
    f"{n_ok} {t['accts']} · {pct_cur}%", pct_cur, 'green'), unsafe_allow_html=True)

with k3:
    c3 = dyn(pct_pd,10,20)
    st.markdown(kpi('red', t['kpi_pd'],
        f"<span style='color:{c3}'>{fmtk(total_pd)}</span>",
        f"{n_od} {t['accts']} · {pct_pd}% {t['at_risk']}", pct_pd, 'red'), unsafe_allow_html=True)

with k4:
    c4 = dyn(pct_90p,15,30)
    st.markdown(kpi('yellow', t['kpi_90'],
        f"<span style='color:{c4}'>{fmtk(pd_90p)}</span>",
        f"{pct_90p}% {t['of_overdue']}", pct_90p, 'yellow'), unsafe_allow_html=True)

with k5:
    c5 = dyn(avg_days/180*100,25,50)
    st.markdown(kpi('blue', t['kpi_days'],
        f"<span style='color:{c5}'>{avg_days:.0f}d</span>",
        t['weighted'], min(avg_days/180*100,100), 'blue'), unsafe_allow_html=True)

with k6: st.markdown(kpi('purple', t['kpi_cu'],
    f"<span style='color:{T2}'>N/A</span>",
    "—", 0, 'purple'), unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([t['tab1'], t['tab2'], t['tab3'], t['tab4']])


# ── TAB 1: AGING ─────────────────────────────────────────────────────────────
with tab1:
    st.markdown(f"""<div class='sec-hdr'>
        <span class='sec-title'>{t['aging_dist']}</span>
        <span class='sec-badge'>{t['bucket_breakdown']}</span>
    </div>""", unsafe_allow_html=True)

    bnames   = list(bkt.keys())
    bamounts = [float(v) for v in bkt.values()]
    colors   = BUCKET_COLORS[:len(bnames)]

    ca, cb, cc = st.columns([4,2,2], gap="small")

    with ca:
        fig = safe_bar_chart(bnames, bamounts, colors=colors, title=t['overdue_by_bucket'])
        st.plotly_chart(fig, use_container_width=True)

    with cb:
        pie_vals = [max(float(total_cur),0), max(float(total_pd),0)]
        if sum(pie_vals) > 0:
            fig2 = go.Figure(go.Pie(
                labels=[t['current'], t['past_due']], values=pie_vals,
                hole=0.7, marker=dict(colors=[GREEN, RED], line=dict(width=0)),
                textinfo='percent', textfont=dict(family='Inter',size=11,color=T1),
                pull=[0,0.04],
            ))
            fig2.update_layout(**THEME,
                title=dict(text=t['portfolio_health'],font=dict(size=11,color=CHART_FONT),x=0),
                showlegend=True,
                legend=dict(orientation='h',x=0.0,y=-0.18,
                            font=dict(size=10,color=CHART_FONT),bgcolor='rgba(0,0,0,0)'),
                annotations=[dict(text=f"<b>{pct_pd:.0f}%</b><br>{t['overdue']}",
                                  x=0.5,y=0.5,showarrow=False,
                                  font=dict(family='Inter',size=13,color=RED))])
        else:
            fig2 = go.Figure()
            fig2.update_layout(**THEME,
                title=dict(text=t['portfolio_health'],font=dict(size=11,color=CHART_FONT),x=0))
        st.plotly_chart(fig2, use_container_width=True)

    with cc:
        all_l = [t['current']] + bnames
        all_v = [float(total_cur)] + bamounts
        all_c = [GREEN] + colors
        fig3 = safe_bar_chart(all_l, all_v, orientation='h', colors=all_c, title=t['balance_by_tier'])
        st.plotly_chart(fig3, use_container_width=True)

    if bkt:
        st.markdown(f"""<div class='sec-hdr' style='margin-top:.8rem'>
            <span class='sec-title'>{t['aging_comp']}</span>
            <span class='sec-badge'>{t['pct_mix']}</span>
        </div>""", unsafe_allow_html=True)
        comp_cols = st.columns(len(bkt), gap="small")
        for i,(bname,bval) in enumerate(bkt.items()):
            bp = pct(bval, total_pd)
            bc = BUCKET_COLORS[i] if i<len(BUCKET_COLORS) else RED
            with comp_cols[i]:
                st.markdown(f"""<div class='kpi' style='padding:14px 16px;text-align:center'>
                    <div class='kpi-label'>{bname}</div>
                    <div style='font-size:1.3rem;font-weight:900;color:{bc}'>{fmtk(bval)}</div>
                    <div style='font-size:.6rem;color:{T2};margin-top:4px'>{bp}% {t['of_overd']}</div>
                    <div class='kpi-bar' style='margin-top:8px'>
                        <div class='kpi-bar-fill' style='width:{bp}%;background:{bc}'></div>
                    </div>
                </div>""", unsafe_allow_html=True)


# ── TAB 2: COLLECTOR ─────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"""<div class='sec-hdr'>
        <span class='sec-title'>{t['coll_perf']}</span>
        <span class='sec-badge'>{t['sla_mgmt']}</span>
    </div>""", unsafe_allow_html=True)

    if COL_COLL:
        cg = dff.groupby(COL_COLL).agg(
            Total_AR=(COL_TOTAL,'sum'),
            Total_PD=('_PD','sum'),
            Accounts=(COL_TOTAL,'count'),
            OD_Accts=('_PD', lambda x:(x>0.01).sum()),
        ).reset_index()
        cg['Pct_PD'] = cg.apply(lambda r: pct(r['Total_PD'],r['Total_AR']), axis=1)
        cg['Avg_OD'] = cg.apply(lambda r: r['Total_PD']/r['OD_Accts'] if r['OD_Accts'] else 0, axis=1)
        cg = cg.sort_values('Total_PD', ascending=False)

        cc1, cc2 = st.columns([3,2], gap="small")
        with cc1:
            fc = go.Figure()
            fc.add_trace(go.Bar(name=t['current'], x=cg[COL_COLL],
                y=cg['Total_AR']-cg['Total_PD'],
                marker_color=GREEN, marker_line_width=0))
            fc.add_trace(go.Bar(name=t['past_due'], x=cg[COL_COLL],
                y=cg['Total_PD'],
                marker_color=RED, marker_line_width=0))
            fc.update_layout(**THEME, barmode='stack',
                title=dict(text=t['ar_by_coll'],font=dict(size=11,color=CHART_FONT),x=0),
                legend=dict(orientation='h',x=0,y=1.14,
                            font=dict(size=10,color=CHART_FONT),bgcolor='rgba(0,0,0,0)'),
                xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=9,color=CHART_FONT)),
                yaxis=dict(showgrid=True,gridcolor=CHART_GRID,zeroline=False,
                           tickprefix='$',tickformat=',.0f',tickfont=dict(size=9)),
                bargap=0.3)
            st.plotly_chart(fc, use_container_width=True)

        with cc2:
            bsizes = cg['Total_PD'].apply(
                lambda v: max(12,min(40,v/total_pd*80)) if total_pd else 12).tolist()
            sc_colors = safe_colors(cg['Pct_PD'].tolist(), GREEN, YELLOW, RED)
            fs = go.Figure(go.Scatter(
                x=cg['Accounts'].tolist(), y=cg['Pct_PD'].tolist(),
                mode='markers+text',
                marker=dict(size=bsizes,color=sc_colors,line=dict(width=0)),
                text=cg[COL_COLL].str[:12].tolist(),
                textposition='top center',
                textfont=dict(size=8,color=CHART_FONT),
            ))
            fs.update_layout(**THEME,
                title=dict(text=t['accts_vs_pct'],font=dict(size=11,color=CHART_FONT),x=0),
                xaxis=dict(title=dict(text=t['num_accounts'],font=dict(size=9)),
                           showgrid=True,gridcolor=CHART_GRID,zeroline=False,tickfont=dict(size=9)),
                yaxis=dict(title=dict(text=t['pct_pd'],font=dict(size=9)),
                           showgrid=True,gridcolor=CHART_GRID,zeroline=False,
                           tickfont=dict(size=9),ticksuffix='%'))
            st.plotly_chart(fs, use_container_width=True)

        st.markdown(f"""<div class='sec-hdr' style='margin-top:.4rem'>
            <span class='sec-title'>{t['coll_summary']}</span>
            <span class='sec-badge'>{t['detail']}</span>
        </div>""", unsafe_allow_html=True)
        disp = cg.copy()
        disp[t['total_ar']]   = disp['Total_AR'].apply(fmt)
        disp[t['past_due']]   = disp['Total_PD'].apply(fmt)
        disp[t['avg_od']]     = disp['Avg_OD'].apply(fmt)
        disp[t['pct_pd']]     = disp['Pct_PD'].apply(lambda x:f"{x:.1f}%")
        disp = disp.rename(columns={COL_COLL:t['collector'],'Accounts':t['num_accts'],'OD_Accts':t['num_od']})
        st.dataframe(disp[[t['collector'],t['num_accts'],t['num_od'],t['total_ar'],
                           t['past_due'],t['pct_pd'],t['avg_od']]],
                     use_container_width=True, hide_index=True)
    else:
        st.info(t['no_collector'])

    if COL_REG:
        st.markdown(f"""<div class='sec-hdr'>
            <span class='sec-title'>{t['regional']}</span>
            <span class='sec-badge'>{t['geography']}</span>
        </div>""", unsafe_allow_html=True)
        rg = dff.groupby(COL_REG).agg(
            Past_Due=('_PD','sum'), Accounts=(COL_TOTAL,'count')
        ).reset_index().sort_values('Past_Due',ascending=True)
        fig_r = safe_bar_chart(
            rg[COL_REG].tolist(), rg['Past_Due'].tolist(),
            orientation='h',
            colors=safe_colors(rg['Past_Due'].tolist(), BLUE, YELLOW, RED),
            title=t['pd_by_region'])
        st.plotly_chart(fig_r, use_container_width=True)


# ── TAB 3: RISK ───────────────────────────────────────────────────────────────
with tab3:
    st.markdown(f"""<div class='sec-hdr'>
        <span class='sec-title'>{t['risk_exp']}</span>
        <span class='sec-badge'>{t['credit_risk']}</span>
    </div>""", unsafe_allow_html=True)

    if COL_RISK:
        rkg = dff.groupby(COL_RISK).agg(
            Total_AR=(COL_TOTAL,'sum'), Past_Due=('_PD','sum'), Accounts=(COL_TOTAL,'count')
        ).reset_index().sort_values('Past_Due',ascending=False)

        def rcol(label):
            s=str(label).upper()
            if 'HIGH' in s or '/H' in s or 'ALTO' in s: return RED
            if 'MED' in s or '/M' in s or 'MEDIO' in s: return YELLOW
            return GREEN
        rc=[rcol(r) for r in rkg[COL_RISK]]

        rr1, rr2 = st.columns([2,3], gap="small")
        with rr1:
            pd_vals = rkg['Past_Due'].tolist()
            if sum(pd_vals)>0:
                fp = go.Figure(go.Pie(
                    labels=rkg[COL_RISK].tolist(), values=pd_vals,
                    hole=0.6, marker=dict(colors=rc,line=dict(width=0)),
                    textinfo='percent+label', textfont=dict(family='Inter',size=9,color=T1),
                ))
                fp.update_layout(**THEME,
                    title=dict(text=t['pd_by_risk'],font=dict(size=11,color=CHART_FONT),x=0),
                    showlegend=False)
            else:
                fp = go.Figure()
                fp.update_layout(**THEME,
                    title=dict(text=t['pd_by_risk'],font=dict(size=11,color=CHART_FONT),x=0))
            st.plotly_chart(fp, use_container_width=True)

        with rr2:
            fig_rb = safe_bar_chart(
                rkg[COL_RISK].tolist(), rkg['Past_Due'].tolist(),
                colors=rc, title=t['pd_by_tier'])
            st.plotly_chart(fig_rb, use_container_width=True)

        high_pd = sum(rkg[rkg[COL_RISK].apply(lambda x:'HIGH' in str(x).upper() or '/H' in str(x).upper())]['Past_Due'].tolist())
        med_pd  = sum(rkg[rkg[COL_RISK].apply(lambda x:'MED'  in str(x).upper() or '/M' in str(x).upper())]['Past_Due'].tolist())
        low_pd  = total_pd - high_pd - med_pd

        rk1,rk2,rk3 = st.columns(3,gap="small")
        with rk1: st.markdown(f"""<div class='kpi red'>
            <div class='kpi-label'>{t['high_risk']}</div>
            <div class='kpi-value' style='color:{RED}'>{fmtk(high_pd)}</div>
            <div class='kpi-sub'>{pct(high_pd,total_pd):.1f}% {t['of_overdue']}</div>
        </div>""", unsafe_allow_html=True)
        with rk2: st.markdown(f"""<div class='kpi yellow'>
            <div class='kpi-label'>{t['med_risk']}</div>
            <div class='kpi-value' style='color:{YELLOW}'>{fmtk(med_pd)}</div>
            <div class='kpi-sub'>{pct(med_pd,total_pd):.1f}% {t['of_overdue']}</div>
        </div>""", unsafe_allow_html=True)
        with rk3: st.markdown(f"""<div class='kpi green'>
            <div class='kpi-label'>{t['low_risk']}</div>
            <div class='kpi-value' style='color:{GREEN}'>{fmtk(low_pd)}</div>
            <div class='kpi-sub'>{pct(low_pd,total_pd):.1f}% {t['of_overdue']}</div>
        </div>""", unsafe_allow_html=True)

    else:
        st.info(t['no_risk'])

    # ── Risk table with Payer ID + downloadable ────────────────────────────
    st.markdown(f"""<div class='sec-hdr' style='margin-top:1.5rem'>
        <span class='sec-title'>{t['risk_table']}</span>
        <span class='sec-badge'>{t['risk_table_badge']}</span>
    </div>""", unsafe_allow_html=True)

    # Build risk detail table — includes payer name, payer ID, risk, location, terms, past due
    risk_show = [c for c in [COL_PAYER, COL_PAYID, COL_RISK, COL_LOC, COL_REG, COL_TERMS, COL_TOTAL, '_PD']
                 if c and c in dff.columns]
    risk_df = dff[risk_show].copy().sort_values('_PD', ascending=False)

    rename_risk = {
        COL_PAYER: t['customer'], COL_PAYID: t['payer_id'],
        COL_RISK: t['risk_cat'], COL_LOC: t['location'],
        COL_REG: t['region'], COL_TERMS: t['payment_terms'],
        COL_TOTAL: t['total_ar'], '_PD': t['past_due'],
    }
    rename_risk = {k:v for k,v in rename_risk.items() if k}
    risk_df_display  = risk_df.rename(columns=rename_risk)
    risk_df_download = risk_df_display.copy()

    for mc in [t['total_ar'], t['past_due']]:
        if mc in risk_df_display.columns:
            risk_df_display[mc] = risk_df_display[mc].apply(fmt)

    btn_r, _ = st.columns([2,5])
    with btn_r:
        st.download_button(
            label=t['download_risk'],
            data=to_excel_bytes(risk_df_download),
            file_name=f"Risk_Table_{pd.Timestamp.now().strftime('%Y-%m-%d')}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    st.dataframe(risk_df_display, use_container_width=True, hide_index=True, height=350)


# ── TAB 4: ACTION LIST ────────────────────────────────────────────────────────
with tab4:
    st.markdown(f"""<div class='sec-hdr'>
        <span class='sec-title'>{t['full_list']}</span>
        <span class='sec-badge'>{t['sla_goal']} · {n_od} {t['to_contact'].upper()}</span>
    </div>""", unsafe_allow_html=True)

    a1,a2,a3,a4 = st.columns(4,gap="small")
    with a1: st.markdown(f"""<div class='kpi yellow'>
        <div class='kpi-label'>{t['to_contact']}</div>
        <div class='kpi-value' style='color:{YELLOW}'>{n_od}</div>
        <div class='kpi-sub'>{t['overd_cycle']}</div>
    </div>""", unsafe_allow_html=True)
    with a2: st.markdown(f"""<div class='kpi red'>
        <div class='kpi-label'>{t['total_exp']}</div>
        <div class='kpi-value' style='color:{RED}'>{fmtk(total_pd)}</div>
        <div class='kpi-sub'>{pct_pd}% {t['of_portfolio']}</div>
    </div>""", unsafe_allow_html=True)
    with a3: st.markdown(f"""<div class='kpi orange'>
        <div class='kpi-label'>{t['avg_acct']}</div>
        <div class='kpi-value' style='color:{ORANGE}'>{fmtk(avg_od)}</div>
        <div class='kpi-sub'>{t['avg_bal']}</div>
    </div>""", unsafe_allow_html=True)
    with a4: st.markdown(f"""<div class='kpi blue'>
        <div class='kpi-label'>{t['top5_conc']}</div>
        <div class='kpi-value' style='color:{BLUE}'>{pct_top5:.1f}%</div>
        <div class='kpi-sub'>{fmtk(top5_val)} {t['in_top5']}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if df_sla.empty:
        st.success(t['all_current'])
    else:
        # ── Top debtors chart ──────────────────────────────────────────────
        top_n  = min(15, len(df_sla))
        top_df = df_sla.head(top_n).copy()
        customers_list = (top_df[COL_PAYER].astype(str).str[:24].tolist()
                          if COL_PAYER and COL_PAYER in top_df.columns
                          else [f"#{i+1}" for i in range(top_n)])
        amounts_list = [float(v) for v in top_df['_PD'].tolist()]

        fig_top = safe_bar_chart(
            customers_list[::-1], amounts_list[::-1],
            orientation='h',
            colors=safe_colors(amounts_list[::-1], YELLOW, ORANGE, RED),
            title=t['top_accts'].format(n=top_n))
        st.plotly_chart(fig_top, use_container_width=True)

        # ── Full action table ──────────────────────────────────────────────
        st.markdown(f"""<div class='sec-hdr' style='margin-top:0'>
            <span class='sec-title'>{t['full_list']}</span>
            <span class='sec-badge'>{t['dl_ready']}</span>
        </div>""", unsafe_allow_html=True)

        show_cols = [c for c in [
            COL_PAYER, COL_PAYID, COL_COLL, COL_LOC, COL_REG,
            COL_TERMS, COL_RISK, COL_TOTAL, '_PD',
        ] + [f'_B_{b}' for b in BUCKETS] if c and c in df_sla.columns]

        action_df  = df_sla[show_cols].copy()
        export_df  = action_df.copy()

        rmap = {
            '_PD': t['past_due'], COL_TOTAL: t['total_ar'],
            COL_PAYER: t['customer'], COL_PAYID: t['payer_id'],
            COL_COLL: t['collector'], COL_LOC: t['location'],
            COL_REG: t['region'], COL_TERMS: t['payment_terms'],
            COL_RISK: t['risk_cat'],
        }
        rmap.update({f'_B_{b}': b for b in BUCKETS})
        rmap = {k:v for k,v in rmap.items() if k}

        action_df  = action_df.rename(columns=rmap)
        export_df  = export_df.rename(columns=rmap)

        for mc in [t['total_ar'], t['past_due']] + list(BUCKETS.keys()):
            if mc in action_df.columns:
                action_df[mc] = action_df[mc].apply(fmt)

        btn_col, _ = st.columns([2,5])
        with btn_col:
            st.download_button(
                label=t['download'],
                data=to_excel_bytes(export_df),
                file_name=f"Collections_{pd.Timestamp.now().strftime('%Y-%m-%d')}.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

        st.dataframe(action_df, use_container_width=True, hide_index=True, height=420)

        st.info(t['info_footer'].format(
            n=n_od, total=fmt(total_pd), pct=pct_pd,
            avg=fmt(avg_od), crit=fmtk(pd_90p), pct90=pct_90p))
