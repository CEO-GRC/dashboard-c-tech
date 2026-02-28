"""
AR Collections Intelligence Dashboard — v6.0
- 3 tabs: Aging Analysis · Collector View · Action List
- Risk & Credit tab removed
- Credit Utilization KPI removed
- Risk column removed from Action List table and Excel export
- Session-based memory management: data cleared after 30 min of inactivity
- All file I/O via BytesIO only — no disk writes
"""

import re
import time
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
if "lang"    not in st.session_state: st.session_state.lang    = "EN"
if "theme"   not in st.session_state: st.session_state.theme   = "light"
if "upload_ts" not in st.session_state: st.session_state.upload_ts = None

LANG = st.session_state.lang
DARK = st.session_state.theme == "dark"

# ── SESSION TIMEOUT: 30 minutes ───────────────────────────────────────────────
SESSION_TIMEOUT_SEC = 30 * 60   # 30 minutes

def _session_expired() -> bool:
    ts = st.session_state.get("upload_ts")
    return ts is not None and (time.time() - ts) > SESSION_TIMEOUT_SEC

def _clear_session_data():
    """Remove all cached file data from session state and st.cache_data."""
    for key in ["upload_ts"]:
        if key in st.session_state:
            del st.session_state[key]
    load_data.clear()   # wipe st.cache_data for this function

# ── TRANSLATIONS ──────────────────────────────────────────────────────────────
T = {
    "EN": {
        "title": "Collections", "title_acc": "Dashboard",
        "sub": "AR Performance · Aging Exposure · Collector SLA",
        "upload_label": "📂 Aging Report (.xlsx)",
        "filters": "🔍 Filters",
        "filter_coll": "Collector", "filter_reg": "Region",
        "all_coll": "All collectors", "all_reg": "All regions",
        "instructions": "Upload the SAP Aging Report in .xlsx format.",
        "security_note": "🔒 Security: Data is processed in volatile memory and is not stored on external servers.",
        "session_expired": "⏱️ Session expired (30 min). Please re-upload your file.",
        "no_data": "No data loaded",
        "no_data_sub": "Upload your SAP Aging Report from the left panel to start.",
        "err_cols": "Could not find Total / Current columns. Check the file format.",
        "no_filter_results": "⚠️ No accounts match the current filters. Adjust your selection.",
        "kpi_total": "Total AR Portfolio", "kpi_current": "Current (On Time)",
        "kpi_pd": "Past Due Exposure", "kpi_90": "90+ Days Critical",
        "kpi_days": "Avg Days Overdue",
        "active_accts": "active accounts", "accts": "accts", "at_risk": "at risk",
        "of_overdue": "of overdue", "weighted": "weighted avg",
        "tab1": "📈  Aging Analysis", "tab2": "👤  Collector View", "tab3": "📋  Action List",
        "aging_dist": "Aging Distribution", "bucket_breakdown": "BUCKET BREAKDOWN",
        "overdue_by_bucket": "Overdue by aging bucket",
        "portfolio_health": "Portfolio health", "overdue": "overdue",
        "balance_by_tier": "Balance by tier",
        "aging_comp": "Aging Composition", "pct_mix": "% MIX", "of_overd": "of overdue",
        "coll_perf": "Collector Performance", "sla_mgmt": "SLA MANAGEMENT",
        "ar_by_coll": "AR by collector (stacked)", "current": "Current", "past_due": "Past Due",
        "accts_vs_pct": "Accounts vs % Past Due", "num_accounts": "# Accounts",
        "coll_summary": "Collector Summary", "detail": "DETAIL",
        "collector": "Collector", "num_accts": "# Accts", "num_od": "# OD",
        "total_ar": "Total AR", "avg_od": "Avg OD", "pct_pd": "% Past Due",
        "regional": "Regional Breakdown", "geography": "GEOGRAPHY",
        "pd_by_region": "Past Due by Region",
        "no_collector": "No Collector column found in this file.",
        "sla_goal": "SLA TOUCH GOAL",
        "to_contact": "Accounts to Contact", "overd_cycle": "overdue this cycle",
        "total_exp": "Total Exposure", "of_portfolio": "of portfolio",
        "avg_acct": "Avg per Account", "avg_bal": "average overdue balance",
        "top5_conc": "Top 5 Concentration", "in_top5": "in top 5 accts",
        "all_current": "🎉 All accounts are current! No overdue balances.",
        "top_accts": "Top {n} accounts by past due balance",
        "full_list": "Collection Action List", "dl_ready": "DOWNLOAD READY",
        "download": "📥 Download Action List",
        "customer": "Name", "payer_id": "Payer ID",
        "region": "Region", "location": "Location",
        "info_footer": "{n} accounts · Overdue: {total} ({pct}%) · Avg: {avg} · 90+d: {crit} ({pct90}%)",
        # ── DSO Analysis ──
        "tab4": "📊  DSO Analysis",
        "dso_title": "DSO Analysis", "dso_badge": "COLLECTION VELOCITY",
        "dso_avg": "Avg DSO", "dso_days": "days",
        "dso_sub_good": "Collecting on time ✓", "dso_sub_warn": "Monitor closely ⚠️",
        "dso_sub_crit": "Urgent action needed 🔴",
        "dso_gauge_title": "Collection Speed · Days Sales Outstanding",
        "dso_by_coll": "DSO by Collector", "dso_coll_badge": "WHO COLLECTS FASTEST",
        "dso_by_reg": "DSO by Region",   "dso_reg_badge": "GEOGRAPHIC BEHAVIOR",
        "dso_best": "Fastest Collector", "dso_worst": "Slowest Collector",
        "dso_method": "Method: weighted-average of aging bucket midpoints × balance share",
        "dso_kpi_pd_ar": "Past Due / AR", "dso_kpi_cur": "Current %",
        "dso_kpi_crit": "Critical 90+d",
        "dso_no_data": "Not enough data to compute DSO for this selection.",
        "days": "days",
    },
    "ES": {
        "title": "Collections", "title_acc": "Dashboard",
        "sub": "Rendimiento AR · Exposición de Antigüedad · SLA de Cobrador",
        "upload_label": "📂 Reporte de Antigüedad (.xlsx)",
        "filters": "🔍 Filtros",
        "filter_coll": "Cobrador", "filter_reg": "Región",
        "all_coll": "Todos los cobradores", "all_reg": "Todas las regiones",
        "instructions": "Sube el Reporte de Antigüedad SAP en formato .xlsx.",
        "security_note": "🔒 Seguridad: Los datos se procesan en memoria volátil y no son almacenados en servidores externos.",
        "session_expired": "⏱️ Sesión expirada (30 min). Vuelve a subir tu archivo.",
        "no_data": "Sin datos cargados",
        "no_data_sub": "Sube tu Reporte SAP desde el panel izquierdo para comenzar.",
        "err_cols": "No se encontraron columnas Total / Current. Verifica el formato.",
        "no_filter_results": "⚠️ Ninguna cuenta coincide con los filtros. Ajusta tu selección.",
        "kpi_total": "Portafolio AR Total", "kpi_current": "Al Día (A Tiempo)",
        "kpi_pd": "Exposición Vencida", "kpi_90": "Crítico 90+ Días",
        "kpi_days": "Días Prom. Vencido",
        "active_accts": "cuentas activas", "accts": "ctas", "at_risk": "en riesgo",
        "of_overdue": "del vencido", "weighted": "prom. ponderado",
        "tab1": "📈  Análisis de Antigüedad", "tab2": "👤  Vista Cobrador", "tab3": "📋  Lista de Acción",
        "aging_dist": "Distribución de Antigüedad", "bucket_breakdown": "DESGLOSE POR BUCKET",
        "overdue_by_bucket": "Vencido por bucket de antigüedad",
        "portfolio_health": "Salud del portafolio", "overdue": "vencido",
        "balance_by_tier": "Saldo por nivel",
        "aging_comp": "Composición de Antigüedad", "pct_mix": "% MIX", "of_overd": "del vencido",
        "coll_perf": "Rendimiento del Cobrador", "sla_mgmt": "GESTIÓN SLA",
        "ar_by_coll": "AR por cobrador (apilado)", "current": "Al día", "past_due": "Vencido",
        "accts_vs_pct": "Cuentas vs % Vencido", "num_accounts": "# Cuentas",
        "coll_summary": "Resumen de Cobrador", "detail": "DETALLE",
        "collector": "Cobrador", "num_accts": "# Ctas", "num_od": "# Venc",
        "total_ar": "AR Total", "avg_od": "Prom. Vencido", "pct_pd": "% Vencido",
        "regional": "Desglose Regional", "geography": "GEOGRAFÍA",
        "pd_by_region": "Vencido por Región",
        "no_collector": "No se encontró columna de Cobrador en este archivo.",
        "sla_goal": "META SLA",
        "to_contact": "Cuentas a Contactar", "overd_cycle": "vencidas este ciclo",
        "total_exp": "Exposición Total", "of_portfolio": "del portafolio",
        "avg_acct": "Promedio por Cuenta", "avg_bal": "saldo promedio vencido",
        "top5_conc": "Concentración Top 5", "in_top5": "en top 5 ctas",
        "all_current": "🎉 ¡Todas las cuentas están al día! Sin saldos vencidos.",
        "top_accts": "Top {n} cuentas por saldo vencido",
        "full_list": "Lista de Acción de Cobros", "dl_ready": "LISTA PARA DESCARGA",
        "download": "📥 Descargar Lista de Acción",
        "customer": "Nombre", "payer_id": "ID Pagador",
        "region": "Región", "location": "Ubicación",
        "info_footer": "{n} cuentas · Vencido: {total} ({pct}%) · Prom: {avg} · 90+d: {crit} ({pct90}%)",
        # ── DSO Analysis ──
        "tab4": "📊  Análisis DSO",
        "dso_title": "Análisis DSO", "dso_badge": "VELOCIDAD DE RECAUDO",
        "dso_avg": "DSO Promedio", "dso_days": "días",
        "dso_sub_good": "Cobrando a tiempo ✓", "dso_sub_warn": "Monitorear de cerca ⚠️",
        "dso_sub_crit": "Acción urgente requerida 🔴",
        "dso_gauge_title": "Velocidad de Recaudo · Días de Venta Pendiente",
        "dso_by_coll": "DSO por Cobrador",  "dso_coll_badge": "QUIÉN COBRA MÁS RÁPIDO",
        "dso_by_reg": "DSO por Región",     "dso_reg_badge": "COMPORTAMIENTO GEOGRÁFICO",
        "dso_best": "Cobrador Más Rápido",  "dso_worst": "Cobrador Más Lento",
        "dso_method": "Método: promedio ponderado de puntos medios de buckets × participación de saldo",
        "dso_kpi_pd_ar": "Vencido / AR", "dso_kpi_cur": "% Al Día",
        "dso_kpi_crit": "Crítico 90+d",
        "dso_no_data": "Datos insuficientes para calcular DSO con esta selección.",
        "days": "días",
    },
}
t = T[LANG]

# ── COLORS ────────────────────────────────────────────────────────────────────
if DARK:
    BG0 = "#0d0e11"; BG1 = "#13141a"; BG2 = "#1a1c24"; BG3 = "#22242e"
    BORDER = "#2a2d3a"; T1 = "#f1f1f3"; T2 = "#8b8fa8"; T3 = "#404460"
    CHART_GRID = "#22242e"; CHART_FONT = "#8b8fa8"
else:
    BG0 = "#f4f6f9"; BG1 = "#ffffff"; BG2 = "#f0f2f5"; BG3 = "#e5e7eb"
    BORDER = "#d1d5db"; T1 = "#111827"; T2 = "#6b7280"; T3 = "#9ca3af"
    CHART_GRID = "#e5e7eb"; CHART_FONT = "#6b7280"

ORANGE = "#ff6b35"; YELLOW = "#f59e0b"; GREEN = "#10b981"
RED = "#ef4444"; BLUE = "#3b82f6"
BUCKET_COLORS = ["#10b981", "#f59e0b", "#f97316", "#ff6b35", "#ef4444", "#dc2626", "#991b1b"]

# margin key intentionally excluded from THEME to avoid Plotly kwarg conflicts
THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=CHART_FONT, size=10),
)
MARGIN_STD  = dict(l=8, r=8,  t=36, b=8)
MARGIN_WIDE = dict(l=8, r=60, t=36, b=8)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');
html,body,[class*="css"],.stApp{{font-family:'Inter',sans-serif!important;background:{BG0}!important;color:{T1}!important}}
.block-container{{padding:1.4rem 2rem 3rem!important;max-width:100%!important}}
#MainMenu{{visibility:hidden}}footer{{visibility:hidden}}.stDeployButton{{display:none}}
[data-testid="stSidebar"]{{background:{BG1}!important;border-right:1px solid {BORDER}!important}}
[data-testid="stSidebar"] section{{padding:1.4rem 1.2rem!important}}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,[data-testid="stSidebar"] small{{color:{T2}!important}}
[data-testid="collapsedControl"]{{background:{BG2}!important;border:1px solid {BORDER}!important;color:{T1}!important}}
[data-testid="stFileUploadDropzone"]{{background:{BG2}!important;border:1.5px dashed rgba(255,107,53,.5)!important;border-radius:10px!important}}
[data-testid="stFileUploadDropzone"] *{{color:{T2}!important}}
[data-testid="stFileUploadDropzone"] button{{background:{BG3}!important;color:{T1}!important;border:1px solid {BORDER}!important;border-radius:6px!important}}
::-webkit-scrollbar{{width:4px;height:4px}}::-webkit-scrollbar-track{{background:{BG0}}}
::-webkit-scrollbar-thumb{{background:{BG3};border-radius:4px}}
.kpi{{background:{BG1};border:1px solid {BORDER};border-radius:12px;padding:18px 20px;position:relative;overflow:hidden}}
.kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px}}
.kpi.orange::before{{background:linear-gradient(90deg,#ff6b35,transparent)}}
.kpi.green::before{{background:linear-gradient(90deg,#10b981,transparent)}}
.kpi.red::before{{background:linear-gradient(90deg,#ef4444,transparent)}}
.kpi.yellow::before{{background:linear-gradient(90deg,#f59e0b,transparent)}}
.kpi.blue::before{{background:linear-gradient(90deg,#3b82f6,transparent)}}
.kpi-label{{font-size:.56rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:{T3};margin-bottom:10px}}
.kpi-value{{font-size:1.75rem;font-weight:900;line-height:1;letter-spacing:-.04em}}
.kpi-sub{{font-size:.62rem;color:{T2};margin-top:7px;font-weight:500}}
.kpi-bar{{margin-top:12px;height:3px;border-radius:2px;background:{BG3};overflow:hidden}}
.kpi-bar-fill{{height:100%;border-radius:2px}}
.sec-hdr{{display:flex;align-items:center;gap:10px;margin:1.8rem 0 1rem;padding-bottom:10px;border-bottom:1px solid {BORDER}}}
.sec-title{{font-size:.66rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{T1}}}
.sec-badge{{font-size:.54rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;background:rgba(255,107,53,.1);color:{ORANGE};border:1px solid rgba(255,107,53,.25);border-radius:4px;padding:2px 8px}}
.main-title{{font-size:1.5rem;font-weight:900;letter-spacing:-.04em;color:{T1};line-height:1}}
.main-title .acc{{color:{ORANGE}}}
.main-sub{{font-size:.58rem;font-weight:600;color:{T3};text-transform:uppercase;letter-spacing:.12em;margin-top:5px}}
.ts-chip{{font-family:'JetBrains Mono',monospace;font-size:.62rem;color:{T2};background:{BG2};border:1px solid {BORDER};border-radius:6px;padding:5px 12px;white-space:nowrap}}
.empty-state{{margin:5rem auto;max-width:420px;background:{BG1};border:1px solid {BORDER};border-radius:16px;padding:3rem 2.5rem;text-align:center}}
.security-note{{font-size:.52rem;color:{T3};line-height:1.7;margin-top:1rem;padding-top:.8rem;border-top:1px solid {BORDER}}}
[data-testid="stDataFrame"]{{border-radius:10px!important;border:1px solid {BORDER}!important;overflow:hidden!important}}
[data-testid="stDataFrame"] thead th{{background:{BG2}!important;color:{T3}!important;font-size:.57rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;font-family:'JetBrains Mono',monospace!important;font-weight:700!important}}
[data-testid="stDataFrame"] tbody td{{font-family:'JetBrains Mono',monospace!important;font-size:.75rem!important;color:{T1}!important;background:{BG1}!important}}
.stDownloadButton>button{{background:linear-gradient(135deg,#ff6b35,#d94e1f)!important;color:#fff!important;border:none!important;border-radius:8px!important;font-size:.72rem!important;font-weight:700!important;letter-spacing:.05em!important;padding:.5rem 1.4rem!important}}
.stDownloadButton>button:hover{{opacity:.82}}
.stAlert{{background:rgba(255,107,53,.06)!important;border:1px solid rgba(255,107,53,.2)!important;border-radius:8px!important;color:{T1}!important}}
[data-testid="stTabs"] [data-baseweb="tab-list"]{{background:{BG1};border-radius:8px;border:1px solid {BORDER};padding:4px;gap:2px}}
[data-testid="stTabs"] [data-baseweb="tab"]{{background:transparent!important;color:{T2}!important;border-radius:6px!important;font-size:.68rem!important;font-weight:600!important;letter-spacing:.06em!important;text-transform:uppercase!important;padding:6px 16px!important}}
[data-testid="stTabs"] [aria-selected="true"]{{background:{BG3}!important;color:{T1}!important}}
[data-testid="stMultiSelect"]>div{{background:{BG2}!important;border:1px solid {BORDER}!important;border-radius:8px!important}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def to_num(val) -> float:
    """Convert any value to float. Strips $, commas, spaces. Returns 0.0 on failure."""
    try:
        if pd.isna(val): return 0.0
    except Exception:
        pass
    try:
        return float(val)
    except (TypeError, ValueError):
        pass
    cleaned = re.sub(r"[^\d.-]", "", str(val))
    if not cleaned or cleaned in (".", "-", ""):
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def apply_to_num_col(df: pd.DataFrame, col: str) -> pd.Series:
    return df[col].apply(to_num)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize DataFrame to .xlsx bytes entirely in memory. No disk I/O."""
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Collections")
    return buf.getvalue()


def fmt(v) -> str:
    return f"${to_num(v):,.2f}"


def human_format(num) -> str:
    """
    Dynamic scale formatter:
      >= 1,000,000 → $X.XXM   (e.g. $2.50M)
      >= 1,000     → $X.XK    (e.g. $439.0K)
      < 1,000      → $X,XXX.XX
    """
    v     = to_num(num)
    abs_v = abs(v)
    sign  = "-" if v < 0 else ""
    if abs_v >= 1_000_000:
        return f"{sign}${abs_v / 1_000_000:,.2f}M"
    if abs_v >= 1_000:
        return f"{sign}${abs_v / 1_000:,.1f}K"
    return f"{sign}${abs_v:,.2f}"

fmtk = human_format   # alias — keep all existing call sites working


def pct(p, total) -> float:
    return round(to_num(p) / to_num(total) * 100, 1) if to_num(total) else 0.0


def safe_colors(values, lo=GREEN, mid=YELLOW, hi=RED):
    values = [to_num(v) for v in values]
    if not values: return []
    mn, mx = min(values), max(values)
    if mn == mx: return [mid] * len(values)
    return [lo if (v-mn)/(mx-mn) < .33 else mid if (v-mn)/(mx-mn) < .66 else hi
            for v in values]


def dyn(val, warn=20, crit=40):
    v = to_num(val)
    return RED if v >= crit else YELLOW if v >= warn else GREEN


@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes) -> pd.DataFrame:
    """
    Read Excel entirely in memory (BytesIO).
    Normalise column names: newlines and double-spaces collapsed to single space.
    No temporary files written to disk.
    """
    df = pd.read_excel(BytesIO(file_bytes))
    df.columns = [
        str(c).replace("\n", " ").replace("  ", " ").strip()
        for c in df.columns
    ]
    return df


def safe_bar_chart(x_vals, y_vals, orientation="v", colors=None, title="", is_currency=True):
    """Build a Plotly bar chart safely. Never raises on empty/bad data."""
    y_vals = [to_num(v) for v in y_vals]
    x_vals = list(x_vals)
    if not x_vals or not y_vals or all(v == 0 for v in y_vals):
        fig = go.Figure()
        fig.update_layout(**THEME, margin=MARGIN_STD,
            title=dict(text=title, font=dict(size=11, color=CHART_FONT), x=0),
            annotations=[dict(text="No data", x=0.5, y=0.5, showarrow=False,
                              font=dict(color=T2, size=12))])
        return fig
    colors = colors or safe_colors(y_vals)
    texts  = [human_format(v) for v in y_vals]
    if orientation == "v":
        fig = go.Figure(go.Bar(
            x=x_vals, y=y_vals, marker=dict(color=colors, line=dict(width=0)),
            text=texts, textposition="outside",
            textfont=dict(family="JetBrains Mono", size=9, color=CHART_FONT),
        ))
        fig.update_layout(**THEME, margin=MARGIN_STD, showlegend=False,
            title=dict(text=title, font=dict(size=11, color=CHART_FONT), x=0),
            xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10, color=CHART_FONT)),
            yaxis=dict(showgrid=True, gridcolor=CHART_GRID, zeroline=False,
                       tickprefix="$" if is_currency else "",
                       tickformat=",.0f" if is_currency else "",
                       tickfont=dict(size=9)),
            bargap=0.35)
    else:
        fig = go.Figure(go.Bar(
            y=x_vals, x=y_vals, orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=texts, textposition="outside",
            textfont=dict(family="JetBrains Mono", size=8, color=CHART_FONT),
        ))
        fig.update_layout(**THEME, margin=MARGIN_WIDE, showlegend=False,
            title=dict(text=title, font=dict(size=11, color=CHART_FONT), x=0),
            xaxis=dict(showgrid=True, gridcolor=CHART_GRID, zeroline=False,
                       tickprefix="$" if is_currency else "",
                       tickformat=",.0f" if is_currency else "",
                       tickfont=dict(size=8)),
            yaxis=dict(showgrid=False, zeroline=False,
                       tickfont=dict(size=9, color=CHART_FONT)))
    return fig


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='margin-bottom:1.2rem;padding-bottom:1rem;border-bottom:1px solid {BORDER}'>
        <div style='font-size:1rem;font-weight:900;color:{T1};letter-spacing:-.025em;line-height:1.3'>
            ⚡ Collections<br><span style='color:{ORANGE}'>Intelligence</span>
        </div>
        <div style='font-size:.52rem;color:{T3};text-transform:uppercase;letter-spacing:.14em;margin-top:5px'>
            AR Analytics · v7.0
        </div>
    </div>
    <div style='font-size:.54rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
                color:{T3};margin-bottom:8px'>{t["upload_label"]}</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("file", type=["xlsx"], label_visibility="collapsed")

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    tc1, tc2 = st.columns(2)
    with tc1:
        if st.button("🌐 ES" if LANG == "EN" else "🌐 EN", use_container_width=True):
            st.session_state.lang = "ES" if LANG == "EN" else "EN"
            st.rerun()
    with tc2:
        if st.button("🌙 Dark" if not DARK else "☀️ Light", use_container_width=True):
            st.session_state.theme = "dark" if not DARK else "light"
            st.rerun()

    st.markdown(f"""
    <div style='margin-top:1rem;padding-top:1rem;border-top:1px solid {BORDER}'>
        <div style='font-size:.54rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
                    color:{T3};margin-bottom:8px'>{t["filters"]}</div>
    </div>""", unsafe_allow_html=True)

    col_ph = st.empty()
    reg_ph = st.empty()

    # Security note — always visible
    st.markdown(
        f"<div class='security-note'>{t['security_note']}</div>",
        unsafe_allow_html=True,
    )


# ── HEADER ────────────────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%d %b %Y  ·  %H:%M")
hc1, hc2 = st.columns([6, 1])
with hc1:
    st.markdown(f"""
    <div style='margin-bottom:.4rem'>
        <div class='main-title'>{t["title"]} <span class='acc'>{t["title_acc"]}</span></div>
        <div class='main-sub'>{t["sub"]}</div>
    </div>""", unsafe_allow_html=True)
with hc2:
    st.markdown(f"<div class='ts-chip' style='text-align:right;margin-top:4px'>🕐 {now_str}</div>",
                unsafe_allow_html=True)
st.markdown(f"<hr style='border:none;border-top:1px solid {BORDER};margin:.6rem 0 1.4rem'>",
            unsafe_allow_html=True)


# ── SESSION TIMEOUT CHECK ─────────────────────────────────────────────────────
if _session_expired():
    _clear_session_data()
    st.warning(t["session_expired"])
    st.stop()


# ── EMPTY STATE ───────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown(f"""
    <div class='empty-state'>
        <div style='font-size:2.8rem;margin-bottom:1rem'>📊</div>
        <div style='font-size:1rem;font-weight:800;color:{T1};margin-bottom:8px'>{t["no_data"]}</div>
        <div style='font-size:.72rem;color:{T2};line-height:1.75'>{t["no_data_sub"]}</div>
    </div>""", unsafe_allow_html=True)
    st.stop()


# ── LOAD & TIMESTAMP ──────────────────────────────────────────────────────────
# Record first-load time so the 30-min timer can trigger on next interaction.
# The file bytes are passed to st.cache_data; nothing is written to disk.
file_bytes = uploaded_file.read()
if st.session_state.upload_ts is None:
    st.session_state.upload_ts = time.time()

try:
    df_raw = load_data(file_bytes)
except Exception as e:
    st.error(f"❌ Error loading file: {e}")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# COLUMN MAPPING
# After load_data normalisation "1 - 30\ndays" → "1 - 30 days"
# ══════════════════════════════════════════════════════════════════════════════

def _resolve(df: pd.DataFrame, exact: str, fallbacks: list) -> str | None:
    if exact in df.columns:
        return exact
    low = {c: c.lower() for c in df.columns}
    for fb in fallbacks:
        for col, col_low in low.items():
            if fb.lower() in col_low:
                return col
    return None

COL_NAME  = _resolve(df_raw, "Payer",    ["name 1", "name1", "name", "customer", "client", "payer"])
COL_PAYER = _resolve(df_raw, "Payer.1",  ["payer.1", "payer id", "payerid"])
COL_TOTAL = _resolve(df_raw, "Total",    ["total"])
COL_CURR  = _resolve(df_raw, "Current",  ["current"])
COL_COLL  = _resolve(df_raw, "Collector",["collector"])
COL_REG   = _resolve(df_raw, "Region",   ["region"])
COL_LOC   = _resolve(df_raw, "Location", ["location"])
COL_TERMS = _resolve(df_raw, "Payment terms", ["payment terms", "terms"])

BUCKET_LABELS = ["1-30d", "31-60d", "61-90d", "91-120d", "121-180d", "181-365d", "365+d"]
BUCKET_EXACT  = ["1 - 30 days", "31 - 60 days", "61 - 90 days", "91 - 120 days",
                 "121 - 180 days", "181 - 365 days", "> 365 days"]

BUCKETS: dict[str, str] = {}
for lbl, exact_col in zip(BUCKET_LABELS, BUCKET_EXACT):
    resolved = _resolve(df_raw, exact_col, [exact_col.split(" days")[0]])
    if resolved:
        BUCKETS[lbl] = resolved

if not COL_TOTAL or not COL_CURR:
    st.error(f"⚠️ {t['err_cols']}")
    st.markdown("**Columns found in file:**")
    st.code(", ".join(df_raw.columns.tolist()))
    st.dataframe(df_raw.head(3))
    st.stop()


# ── NUMERIC CONVERSION ────────────────────────────────────────────────────────
df = df_raw.copy()
df[COL_TOTAL] = apply_to_num_col(df, COL_TOTAL)
df[COL_CURR]  = apply_to_num_col(df, COL_CURR)
for lbl, bcol in BUCKETS.items():
    df[bcol] = apply_to_num_col(df, bcol)

# Past Due = sum of buckets (NaN-safe)
if BUCKETS:
    df["_PD"] = df[list(BUCKETS.values())].clip(lower=0).sum(axis=1)
else:
    df["_PD"] = (df[COL_TOTAL] - df[COL_CURR]).clip(lower=0)

for lbl, bcol in BUCKETS.items():
    df[f"_B_{lbl}"] = df[bcol].clip(lower=0)


# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
cols_list = sorted(df[COL_COLL].dropna().unique().tolist()) if COL_COLL and COL_COLL in df.columns else []
regs_list = sorted(df[COL_REG].dropna().unique().tolist())  if COL_REG  and COL_REG  in df.columns else []

with col_ph:
    sel_coll = st.multiselect(t["filter_coll"], cols_list, placeholder=t["all_coll"])
with reg_ph:
    sel_reg  = st.multiselect(t["filter_reg"],  regs_list, placeholder=t["all_reg"])

dff = df.copy()
if sel_coll and COL_COLL: dff = dff[dff[COL_COLL].isin(sel_coll)]
if sel_reg  and COL_REG:  dff = dff[dff[COL_REG].isin(sel_reg)]

if dff.empty:
    st.warning(t["no_filter_results"])
    st.stop()


# ── METRICS ───────────────────────────────────────────────────────────────────
total_ar  = float(dff[COL_TOTAL].sum())
total_cur = float(dff[COL_CURR].sum())
total_pd  = float(dff["_PD"].sum())
pct_pd    = pct(total_pd, total_ar)
pct_cur   = pct(total_cur, total_ar)
n_total   = len(dff)

df_sla   = dff[dff["_PD"] > 0.01].copy().sort_values("_PD", ascending=False)
n_od     = len(df_sla)
n_ok     = n_total - n_od
avg_od   = total_pd / n_od if n_od else 0.0
top5_val = float(df_sla.head(5)["_PD"].sum()) if not df_sla.empty else 0.0
pct_top5 = pct(top5_val, total_pd)

bkt = {lbl: float(dff[f"_B_{lbl}"].sum()) for lbl in BUCKETS}
pd_90p  = sum(v for k, v in bkt.items() if any(x in k for x in ["91", "121", "181", "365+"]))
pct_90p = pct(pd_90p, total_pd)

midpoints = {"1-30d": 15, "31-60d": 45, "61-90d": 75, "91-120d": 105,
             "121-180d": 150, "181-365d": 270, "365+d": 400}
tot_aged = sum(bkt.values()) or 1.0
avg_days = sum(bkt.get(b, 0) * d for b, d in midpoints.items()) / tot_aged


# ── DSO CALCULATIONS ──────────────────────────────────────────────────────────
# DSO = weighted average of bucket midpoints, weighted by the $ balance in each bucket.
# Current (on-time) bucket contributes 0 days.
# Formula per account group G:
#   DSO_G = Σ(balance_bucket_i × midpoint_i) / total_AR_G
#
# Portfolio DSO also incorporates the Current balance at 0 days so that a
# portfolio with mostly on-time payers correctly shows a low DSO.

_MP = {**{lbl: 0 for lbl in ["Current"]}, **midpoints}

def _calc_dso(total_ar_val: float, cur_val: float, bkt_vals: dict) -> float:
    """Weighted-average DSO. total_ar_val is the denominator (avoids divide-by-zero)."""
    if total_ar_val <= 0:
        return 0.0
    weighted = sum(bkt_vals.get(lbl, 0) * mp for lbl, mp in midpoints.items())
    # Current bucket is 0 days — cur_val * 0 = 0, so no need to add it
    return round(weighted / total_ar_val, 1)

dso_portfolio = _calc_dso(total_ar, total_cur, bkt)

# DSO by collector
dso_by_coll: dict[str, float] = {}
if COL_COLL and COL_COLL in dff.columns:
    for coll_name, grp in dff.groupby(COL_COLL):
        g_total = float(grp[COL_TOTAL].sum())
        g_cur   = float(grp[COL_CURR].sum())
        g_bkt   = {lbl: float(grp[f"_B_{lbl}"].sum()) for lbl in BUCKETS}
        dso_by_coll[str(coll_name)] = _calc_dso(g_total, g_cur, g_bkt)

# DSO by region
dso_by_reg: dict[str, float] = {}
if COL_REG and COL_REG in dff.columns:
    for reg_name, grp in dff.groupby(COL_REG):
        g_total = float(grp[COL_TOTAL].sum())
        g_cur   = float(grp[COL_CURR].sum())
        g_bkt   = {lbl: float(grp[f"_B_{lbl}"].sum()) for lbl in BUCKETS}
        dso_by_reg[str(reg_name)] = _calc_dso(g_total, g_cur, g_bkt)


# ══════════════════════════════════════════════════════════════════════════════
# KPI CARDS — 5 cards (Credit Utilization removed)
# ══════════════════════════════════════════════════════════════════════════════
k1, k2, k3, k4, k5 = st.columns(5, gap="small")

def kpi_card(color, label, value_html, sub, bar_w, bar_color=None):
    bc = bar_color or color
    cx = {"orange": ORANGE, "green": GREEN, "red": RED, "yellow": YELLOW, "blue": BLUE}
    hx = cx.get(bc, ORANGE)
    return f"""<div class='kpi {color}'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{value_html}</div>
        <div class='kpi-sub'>{sub}</div>
        <div class='kpi-bar'><div class='kpi-bar-fill'
            style='width:{min(bar_w,100):.0f}%;background:{hx}'></div></div>
    </div>"""

with k1: st.markdown(kpi_card("orange", t["kpi_total"],
    f"<span style='color:{T1}'>{human_format(total_ar)}</span>",
    f"{n_total} {t['active_accts']}", 100), unsafe_allow_html=True)

with k2: st.markdown(kpi_card("green", t["kpi_current"],
    f"<span style='color:{GREEN}'>{human_format(total_cur)}</span>",
    f"{n_ok} {t['accts']} · {pct_cur}%", pct_cur, "green"), unsafe_allow_html=True)

with k3:
    c3 = dyn(pct_pd, 10, 20)
    st.markdown(kpi_card("red", t["kpi_pd"],
        f"<span style='color:{c3}'>{human_format(total_pd)}</span>",
        f"{n_od} {t['accts']} · {pct_pd}% {t['at_risk']}", pct_pd, "red"), unsafe_allow_html=True)

with k4:
    c4 = dyn(pct_90p, 15, 30)
    st.markdown(kpi_card("yellow", t["kpi_90"],
        f"<span style='color:{c4}'>{human_format(pd_90p)}</span>",
        f"{pct_90p}% {t['of_overdue']}", pct_90p, "yellow"), unsafe_allow_html=True)

with k5:
    c5 = dyn(avg_days / 180 * 100, 25, 50)
    st.markdown(kpi_card("blue", t["kpi_days"],
        f"<span style='color:{c5}'>{avg_days:.0f}d</span>",
        t["weighted"], min(avg_days / 180 * 100, 100), "blue"), unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABS — 4 tabs: Aging · Collector · Action List · DSO Analysis
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([t["tab1"], t["tab2"], t["tab3"], t["tab4"]])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 · AGING ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    try:
        st.markdown(f"""<div class='sec-hdr'>
            <span class='sec-title'>{t["aging_dist"]}</span>
            <span class='sec-badge'>{t["bucket_breakdown"]}</span>
        </div>""", unsafe_allow_html=True)

        bnames   = list(bkt.keys())
        bamounts = [float(v) for v in bkt.values()]
        colors   = BUCKET_COLORS[:len(bnames)]

        ca, cb, cc = st.columns([4, 2, 2], gap="small")

        with ca:
            fig = safe_bar_chart(bnames, bamounts, colors=colors,
                                 title=t["overdue_by_bucket"])
            st.plotly_chart(fig, use_container_width=True)

        with cb:
            pie_cur = max(float(total_cur), 0)
            pie_pd  = max(float(total_pd),  0)
            if pie_cur + pie_pd > 0:
                fig2 = go.Figure(go.Pie(
                    labels=[t["current"], t["past_due"]],
                    values=[pie_cur, pie_pd], hole=0.7,
                    marker=dict(colors=[GREEN, RED], line=dict(width=0)),
                    textinfo="percent",
                    textfont=dict(family="Inter", size=11, color=T1),
                    pull=[0, 0.04],
                ))
                fig2.update_layout(**THEME, margin=MARGIN_STD,
                    title=dict(text=t["portfolio_health"],
                               font=dict(size=11, color=CHART_FONT), x=0),
                    showlegend=True,
                    legend=dict(orientation="h", x=0.0, y=-0.18,
                                font=dict(size=10, color=CHART_FONT),
                                bgcolor="rgba(0,0,0,0)"),
                    annotations=[dict(
                        text=f"<b>{pct_pd:.0f}%</b><br>{t['overdue']}",
                        x=0.5, y=0.5, showarrow=False,
                        font=dict(family="Inter", size=13, color=RED))])
            else:
                fig2 = go.Figure()
                fig2.update_layout(**THEME, margin=MARGIN_STD,
                    title=dict(text=t["portfolio_health"],
                               font=dict(size=11, color=CHART_FONT), x=0))
            st.plotly_chart(fig2, use_container_width=True)

        with cc:
            all_l = [t["current"]] + bnames
            all_v = [float(total_cur)] + bamounts
            all_c = [GREEN] + colors
            fig3 = safe_bar_chart(all_l, all_v, orientation="h",
                                  colors=all_c, title=t["balance_by_tier"])
            st.plotly_chart(fig3, use_container_width=True)

        if bkt:
            st.markdown(f"""<div class='sec-hdr' style='margin-top:.8rem'>
                <span class='sec-title'>{t["aging_comp"]}</span>
                <span class='sec-badge'>{t["pct_mix"]}</span>
            </div>""", unsafe_allow_html=True)
            comp_cols = st.columns(len(bkt), gap="small")
            for i, (bname, bval) in enumerate(bkt.items()):
                bp = pct(float(bval), total_pd)
                bc = BUCKET_COLORS[i] if i < len(BUCKET_COLORS) else RED
                with comp_cols[i]:
                    st.markdown(f"""<div class='kpi' style='padding:14px 16px;text-align:center'>
                        <div class='kpi-label'>{bname}</div>
                        <div style='font-size:1.3rem;font-weight:900;color:{bc}'>{human_format(float(bval))}</div>
                        <div style='font-size:.6rem;color:{T2};margin-top:4px'>{bp}% {t["of_overd"]}</div>
                        <div class='kpi-bar' style='margin-top:8px'>
                            <div class='kpi-bar-fill' style='width:{bp}%;background:{bc}'></div>
                        </div>
                    </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"⚠️ Error rendering Aging tab: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 · COLLECTOR VIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    try:
        st.markdown(f"""<div class='sec-hdr'>
            <span class='sec-title'>{t["coll_perf"]}</span>
            <span class='sec-badge'>{t["sla_mgmt"]}</span>
        </div>""", unsafe_allow_html=True)

        if not COL_COLL or COL_COLL not in dff.columns:
            st.info(t["no_collector"])
        else:
            cg = dff.groupby(COL_COLL).agg(
                Total_AR=(COL_TOTAL, "sum"),
                Total_PD=("_PD",    "sum"),
                Accounts=(COL_TOTAL, "count"),
                OD_Accts=("_PD",    lambda x: (x > 0.01).sum()),
            ).reset_index()
            cg["Pct_PD"] = cg.apply(lambda r: pct(r["Total_PD"], r["Total_AR"]), axis=1)
            cg["Avg_OD"] = cg.apply(
                lambda r: r["Total_PD"] / r["OD_Accts"] if r["OD_Accts"] else 0, axis=1)
            cg = cg.sort_values("Total_PD", ascending=False)

            cc1, cc2 = st.columns([3, 2], gap="small")
            with cc1:
                fc = go.Figure()
                fc.add_trace(go.Bar(
                    name=t["current"], x=cg[COL_COLL],
                    y=(cg["Total_AR"] - cg["Total_PD"]).clip(lower=0),
                    marker_color=GREEN, marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>Current: $%{y:,.2f}<extra></extra>"))
                fc.add_trace(go.Bar(
                    name=t["past_due"], x=cg[COL_COLL],
                    y=cg["Total_PD"],
                    marker_color=RED, marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>Past Due: $%{y:,.2f}<extra></extra>"))
                fc.update_layout(**THEME, margin=MARGIN_STD, barmode="stack",
                    title=dict(text=t["ar_by_coll"],
                               font=dict(size=11, color=CHART_FONT), x=0),
                    legend=dict(orientation="h", x=0, y=1.14,
                                font=dict(size=10, color=CHART_FONT),
                                bgcolor="rgba(0,0,0,0)"),
                    xaxis=dict(showgrid=False, zeroline=False,
                               tickfont=dict(size=9, color=CHART_FONT)),
                    yaxis=dict(showgrid=True, gridcolor=CHART_GRID, zeroline=False,
                               tickprefix="$", tickformat=",.0f",
                               tickfont=dict(size=9)),
                    bargap=0.3)
                st.plotly_chart(fc, use_container_width=True)

            with cc2:
                bsizes = cg["Total_PD"].apply(
                    lambda v: max(12, min(40, to_num(v) / total_pd * 80))
                    if total_pd else 12).tolist()
                fs = go.Figure(go.Scatter(
                    x=cg["Accounts"].tolist(), y=cg["Pct_PD"].tolist(),
                    mode="markers+text",
                    marker=dict(size=bsizes,
                                color=safe_colors(cg["Pct_PD"].tolist(), GREEN, YELLOW, RED),
                                line=dict(width=0)),
                    text=cg[COL_COLL].astype(str).str[:12].tolist(),
                    textposition="top center",
                    textfont=dict(size=8, color=CHART_FONT),
                ))
                fs.update_layout(**THEME, margin=MARGIN_STD,
                    title=dict(text=t["accts_vs_pct"],
                               font=dict(size=11, color=CHART_FONT), x=0),
                    xaxis=dict(title=dict(text=t["num_accounts"], font=dict(size=9)),
                               showgrid=True, gridcolor=CHART_GRID, zeroline=False,
                               tickfont=dict(size=9)),
                    yaxis=dict(title=dict(text=t["pct_pd"], font=dict(size=9)),
                               showgrid=True, gridcolor=CHART_GRID, zeroline=False,
                               tickfont=dict(size=9), ticksuffix="%"))
                st.plotly_chart(fs, use_container_width=True)

            # Collector summary table — exact values
            st.markdown(f"""<div class='sec-hdr' style='margin-top:.4rem'>
                <span class='sec-title'>{t["coll_summary"]}</span>
                <span class='sec-badge'>{t["detail"]}</span>
            </div>""", unsafe_allow_html=True)
            disp = cg.copy()
            disp[t["total_ar"]] = disp["Total_AR"].apply(fmt)
            disp[t["past_due"]] = disp["Total_PD"].apply(fmt)
            disp[t["avg_od"]]   = disp["Avg_OD"].apply(fmt)
            disp[t["pct_pd"]]   = disp["Pct_PD"].apply(lambda x: f"{x:.1f}%")
            disp = disp.rename(columns={
                COL_COLL: t["collector"], "Accounts": t["num_accts"], "OD_Accts": t["num_od"]})
            st.dataframe(
                disp[[t["collector"], t["num_accts"], t["num_od"],
                      t["total_ar"], t["past_due"], t["pct_pd"], t["avg_od"]]],
                use_container_width=True, hide_index=True)

        # Regional breakdown
        if COL_REG and COL_REG in dff.columns:
            st.markdown(f"""<div class='sec-hdr'>
                <span class='sec-title'>{t["regional"]}</span>
                <span class='sec-badge'>{t["geography"]}</span>
            </div>""", unsafe_allow_html=True)
            rg = (dff.groupby(COL_REG)
                     .agg(Past_Due=("_PD", "sum"), Accounts=(COL_TOTAL, "count"))
                     .reset_index()
                     .sort_values("Past_Due", ascending=True))
            if not rg.empty:
                fig_r = safe_bar_chart(
                    rg[COL_REG].tolist(),
                    [float(v) for v in rg["Past_Due"].tolist()],
                    orientation="h",
                    colors=safe_colors(rg["Past_Due"].tolist(), BLUE, YELLOW, RED),
                    title=t["pd_by_region"])
                st.plotly_chart(fig_r, use_container_width=True)
    except Exception as e:
        st.error(f"⚠️ Error rendering Collector tab: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 · ACTION LIST
# Columns: Payer ID · Name · Collector · Region · Total AR · Past Due · Buckets
# No Risk column. No index. Exact values for auditability.
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    try:
        st.markdown(f"""<div class='sec-hdr'>
            <span class='sec-title'>{t["full_list"]}</span>
            <span class='sec-badge'>{t["sla_goal"]} · {n_od} {t["to_contact"].upper()}</span>
        </div>""", unsafe_allow_html=True)

        a1, a2, a3, a4 = st.columns(4, gap="small")
        with a1: st.markdown(f"""<div class='kpi yellow'>
            <div class='kpi-label'>{t["to_contact"]}</div>
            <div class='kpi-value' style='color:{YELLOW}'>{n_od}</div>
            <div class='kpi-sub'>{t["overd_cycle"]}</div>
        </div>""", unsafe_allow_html=True)
        with a2: st.markdown(f"""<div class='kpi red'>
            <div class='kpi-label'>{t["total_exp"]}</div>
            <div class='kpi-value' style='color:{RED}'>{human_format(total_pd)}</div>
            <div class='kpi-sub'>{pct_pd}% {t["of_portfolio"]}</div>
        </div>""", unsafe_allow_html=True)
        with a3: st.markdown(f"""<div class='kpi orange'>
            <div class='kpi-label'>{t["avg_acct"]}</div>
            <div class='kpi-value' style='color:{ORANGE}'>{human_format(avg_od)}</div>
            <div class='kpi-sub'>{t["avg_bal"]}</div>
        </div>""", unsafe_allow_html=True)
        with a4: st.markdown(f"""<div class='kpi blue'>
            <div class='kpi-label'>{t["top5_conc"]}</div>
            <div class='kpi-value' style='color:{BLUE}'>{pct_top5:.1f}%</div>
            <div class='kpi-sub'>{human_format(top5_val)} {t["in_top5"]}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        if df_sla.empty:
            st.success(t["all_current"])
        else:
            # ── Top debtors chart ──────────────────────────────────────────
            top_n  = min(15, len(df_sla))
            top_df = df_sla.head(top_n).copy()

            if COL_NAME and COL_NAME in top_df.columns:
                lbl_list = top_df[COL_NAME].astype(str).str[:28].tolist()
            elif COL_PAYER and COL_PAYER in top_df.columns:
                lbl_list = top_df[COL_PAYER].astype(str).str[:28].tolist()
            else:
                lbl_list = [f"#{i+1}" for i in range(top_n)]

            amt_list = [float(v) for v in top_df["_PD"].tolist()]
            fig_top  = safe_bar_chart(
                lbl_list[::-1], amt_list[::-1], orientation="h",
                colors=safe_colors(amt_list[::-1], YELLOW, ORANGE, RED),
                title=t["top_accts"].format(n=top_n))
            st.plotly_chart(fig_top, use_container_width=True)

            # ── Action table ───────────────────────────────────────────────
            st.markdown(f"""<div class='sec-hdr' style='margin-top:0'>
                <span class='sec-title'>{t["full_list"]}</span>
                <span class='sec-badge'>{t["dl_ready"]}</span>
            </div>""", unsafe_allow_html=True)

            # Ordered operative columns — NO Risk column
            FIXED_COLS = [COL_PAYER, COL_NAME, COL_COLL, COL_REG, COL_TOTAL, "_PD"]
            BUCKET_COMPUTED = [f"_B_{lbl}" for lbl in BUCKETS]

            action_df = df_sla.copy()
            # Fill any missing column with 0 (robustness guarantee)
            for col in FIXED_COLS + BUCKET_COMPUTED:
                if col and col not in action_df.columns:
                    action_df[col] = 0

            select_cols = [c for c in FIXED_COLS + BUCKET_COMPUTED
                           if c and c in action_df.columns]
            action_df = action_df[select_cols].copy()
            export_df = action_df.copy()   # raw numbers for Excel download

            # Friendly column names
            col_names: dict[str, str] = {}
            if COL_PAYER and COL_PAYER in action_df.columns: col_names[COL_PAYER] = t["payer_id"]
            if COL_NAME  and COL_NAME  in action_df.columns: col_names[COL_NAME]  = t["customer"]
            if COL_COLL  and COL_COLL  in action_df.columns: col_names[COL_COLL]  = t["collector"]
            if COL_REG   and COL_REG   in action_df.columns: col_names[COL_REG]   = t["region"]
            if COL_TOTAL and COL_TOTAL in action_df.columns: col_names[COL_TOTAL] = t["total_ar"]
            if "_PD"     in action_df.columns:               col_names["_PD"]     = t["past_due"]
            for lbl in BUCKETS:
                bc = f"_B_{lbl}"
                if bc in action_df.columns:
                    col_names[bc] = lbl

            action_disp = action_df.rename(columns=col_names)
            export_disp = export_df.rename(columns=col_names)   # raw numbers in Excel

            # Display: exact $x,xxx.xx — no K/M abbreviation (auditable)
            money_cols = [t["total_ar"], t["past_due"]] + list(BUCKETS.keys())
            for mc in money_cols:
                if mc in action_disp.columns:
                    action_disp[mc] = action_disp[mc].apply(fmt)

            # Download button — BytesIO only, no disk write
            btn_col, _ = st.columns([2, 5])
            with btn_col:
                st.download_button(
                    label=t["download"],
                    data=to_excel_bytes(export_disp),
                    file_name=f"Collections_{pd.Timestamp.now().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            # Table — no index, clean operative view
            st.dataframe(action_disp, use_container_width=True, hide_index=True, height=430)

            st.info(t["info_footer"].format(
                n=n_od, total=fmt(total_pd), pct=pct_pd,
                avg=fmt(avg_od), crit=human_format(pd_90p), pct90=pct_90p))

    except Exception as e:
        st.error(f"⚠️ Error rendering Action List tab: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 · DSO ANALYSIS — Collection Velocity
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    try:
        st.markdown(f"""<div class='sec-hdr'>
            <span class='sec-title'>{t["dso_title"]}</span>
            <span class='sec-badge'>{t["dso_badge"]}</span>
        </div>""", unsafe_allow_html=True)

        if total_ar <= 0 or not BUCKETS:
            st.info(t["dso_no_data"])
        else:
            # ── DSO colour thresholds ─────────────────────────────────────
            #   Green:  0 – 30 d
            #   Yellow: 31 – 45 d
            #   Red:    > 45 d
            def dso_color(d: float) -> str:
                return GREEN if d <= 30 else YELLOW if d <= 45 else RED

            dso_label_color = dso_color(dso_portfolio)
            if dso_portfolio <= 30:
                dso_sub = t["dso_sub_good"]
                kpi_cls = "green"
            elif dso_portfolio <= 45:
                dso_sub = t["dso_sub_warn"]
                kpi_cls = "yellow"
            else:
                dso_sub = t["dso_sub_crit"]
                kpi_cls = "red"

            # ── Top KPI row ───────────────────────────────────────────────
            d1, d2, d3, d4 = st.columns(4, gap="small")
            with d1:
                st.markdown(f"""<div class='kpi {kpi_cls}'>
                    <div class='kpi-label'>{t["dso_avg"]}</div>
                    <div class='kpi-value' style='color:{dso_label_color}'>{dso_portfolio:.1f}<span style='font-size:.9rem;font-weight:600;margin-left:4px'>{t["days"]}</span></div>
                    <div class='kpi-sub'>{dso_sub}</div>
                    <div class='kpi-bar'><div class='kpi-bar-fill'
                        style='width:{min(dso_portfolio/90*100,100):.0f}%;background:{dso_label_color}'></div></div>
                </div>""", unsafe_allow_html=True)
            with d2:
                st.markdown(kpi_card("orange", t["dso_kpi_pd_ar"],
                    f"<span style='color:{dyn(pct_pd,10,20)}'>{pct_pd:.1f}%</span>",
                    f"{human_format(total_pd)}", pct_pd, "orange"), unsafe_allow_html=True)
            with d3:
                st.markdown(kpi_card("green", t["dso_kpi_cur"],
                    f"<span style='color:{GREEN}'>{pct_cur:.1f}%</span>",
                    f"{human_format(total_cur)}", pct_cur, "green"), unsafe_allow_html=True)
            with d4:
                st.markdown(kpi_card("yellow", t["dso_kpi_crit"],
                    f"<span style='color:{dyn(pct_90p,15,30)}'>{pct_90p:.1f}%</span>",
                    f"{human_format(pd_90p)}", pct_90p, "yellow"), unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # ── Gauge + DSO by Collector ───────────────────────────────────
            g1, g2 = st.columns([2, 3], gap="small")

            with g1:
                # Gauge chart — Collection Speed
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=dso_portfolio,
                    number=dict(
                        suffix=f" {t['days']}",
                        font=dict(family="Inter", size=36, color=dso_label_color),
                    ),
                    delta=dict(reference=30, increasing=dict(color=RED),
                               decreasing=dict(color=GREEN),
                               font=dict(size=13)),
                    gauge=dict(
                        axis=dict(
                            range=[0, 120],
                            tickwidth=1, tickcolor=CHART_FONT,
                            tickfont=dict(size=9, color=CHART_FONT),
                            tickvals=[0, 15, 30, 45, 60, 90, 120],
                        ),
                        bar=dict(color=dso_label_color, thickness=0.28),
                        bgcolor="rgba(0,0,0,0)",
                        borderwidth=0,
                        steps=[
                            dict(range=[0,  30], color="rgba(16,185,129,.15)"),
                            dict(range=[30, 45], color="rgba(245,158,11,.15)"),
                            dict(range=[45,120], color="rgba(239,68,68,.12)"),
                        ],
                        threshold=dict(
                            line=dict(color=RED, width=2),
                            thickness=0.75, value=45,
                        ),
                    ),
                    title=dict(
                        text=t["dso_gauge_title"],
                        font=dict(size=11, color=CHART_FONT),
                    ),
                ))
                fig_gauge.update_layout(
                    **THEME,
                    margin=dict(l=20, r=20, t=60, b=10),
                    height=280,
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

            with g2:
                # DSO by Collector — horizontal bar, sorted best→worst
                if dso_by_coll:
                    sorted_coll = sorted(dso_by_coll.items(), key=lambda x: x[1])
                    c_names = [c for c, _ in sorted_coll]
                    c_vals  = [v for _, v in sorted_coll]
                    c_colors = [dso_color(v) for v in c_vals]
                    c_texts  = [f"{v:.1f}d" for v in c_vals]

                    fig_coll = go.Figure(go.Bar(
                        y=c_names, x=c_vals, orientation="h",
                        marker=dict(color=c_colors, line=dict(width=0)),
                        text=c_texts, textposition="outside",
                        textfont=dict(family="JetBrains Mono", size=9, color=CHART_FONT),
                        hovertemplate="<b>%{y}</b><br>DSO: %{x:.1f} days<extra></extra>",
                    ))
                    fig_coll.update_layout(
                        **THEME,
                        margin=MARGIN_WIDE,
                        title=dict(text=t["dso_by_coll"],
                                   font=dict(size=11, color=CHART_FONT), x=0),
                        showlegend=False,
                        xaxis=dict(showgrid=True, gridcolor=CHART_GRID, zeroline=False,
                                   ticksuffix="d", tickfont=dict(size=9),
                                   range=[0, max(c_vals) * 1.25]),
                        yaxis=dict(showgrid=False, zeroline=False,
                                   tickfont=dict(size=9, color=CHART_FONT)),
                        shapes=[
                            dict(type="line", x0=30, x1=30, y0=-0.5,
                                 y1=len(c_names)-0.5,
                                 line=dict(color=GREEN, width=1.5, dash="dot")),
                            dict(type="line", x0=45, x1=45, y0=-0.5,
                                 y1=len(c_names)-0.5,
                                 line=dict(color=RED, width=1.5, dash="dot")),
                        ],
                        annotations=[
                            dict(x=30, y=len(c_names)-0.5, text="30d target",
                                 showarrow=False, font=dict(size=8, color=GREEN),
                                 xanchor="left", yanchor="bottom"),
                            dict(x=45, y=len(c_names)-0.5, text="45d limit",
                                 showarrow=False, font=dict(size=8, color=RED),
                                 xanchor="left", yanchor="bottom"),
                        ],
                    )
                    st.plotly_chart(fig_coll, use_container_width=True)
                else:
                    st.info(t["no_collector"])

            # ── DSO by Region — colour-coded bars ─────────────────────────
            if dso_by_reg:
                st.markdown(f"""<div class='sec-hdr'>
                    <span class='sec-title'>{t["dso_by_reg"]}</span>
                    <span class='sec-badge'>{t["dso_reg_badge"]}</span>
                </div>""", unsafe_allow_html=True)

                sorted_reg = sorted(dso_by_reg.items(), key=lambda x: x[1], reverse=True)
                r_names = [r for r, _ in sorted_reg]
                r_vals  = [v for _, v in sorted_reg]
                r_colors = [dso_color(v) for v in r_vals]

                fig_reg = go.Figure(go.Bar(
                    x=r_names, y=r_vals,
                    marker=dict(color=r_colors, line=dict(width=0)),
                    text=[f"{v:.1f}d" for v in r_vals],
                    textposition="outside",
                    textfont=dict(family="JetBrains Mono", size=9, color=CHART_FONT),
                    hovertemplate="<b>%{x}</b><br>DSO: %{y:.1f} days<extra></extra>",
                ))
                fig_reg.update_layout(
                    **THEME,
                    margin=MARGIN_STD,
                    title=dict(text=t["dso_by_reg"],
                               font=dict(size=11, color=CHART_FONT), x=0),
                    showlegend=False,
                    xaxis=dict(showgrid=False, zeroline=False,
                               tickfont=dict(size=10, color=CHART_FONT)),
                    yaxis=dict(showgrid=True, gridcolor=CHART_GRID, zeroline=False,
                               ticksuffix="d", tickfont=dict(size=9),
                               range=[0, max(r_vals) * 1.25]),
                    bargap=0.35,
                    shapes=[
                        dict(type="line", x0=-0.5, x1=len(r_names)-0.5, y0=30, y1=30,
                             line=dict(color=GREEN, width=1.5, dash="dot")),
                        dict(type="line", x0=-0.5, x1=len(r_names)-0.5, y0=45, y1=45,
                             line=dict(color=RED, width=1.5, dash="dot")),
                    ],
                    annotations=[
                        dict(x=len(r_names)-0.5, y=30, text="30d",
                             showarrow=False, font=dict(size=8, color=GREEN),
                             xanchor="right", yanchor="bottom"),
                        dict(x=len(r_names)-0.5, y=45, text="45d",
                             showarrow=False, font=dict(size=8, color=RED),
                             xanchor="right", yanchor="bottom"),
                    ],
                )
                st.plotly_chart(fig_reg, use_container_width=True)

            # ── Best / Worst collector highlight ─────────────────────────
            if len(dso_by_coll) >= 2:
                best_coll  = min(dso_by_coll, key=dso_by_coll.get)
                worst_coll = max(dso_by_coll, key=dso_by_coll.get)
                hc1, hc2 = st.columns(2, gap="small")
                with hc1:
                    st.markdown(f"""<div class='kpi green'>
                        <div class='kpi-label'>{t["dso_best"]}</div>
                        <div class='kpi-value' style='color:{GREEN}'>{dso_by_coll[best_coll]:.1f}<span style='font-size:.9rem;margin-left:4px'>{t["days"]}</span></div>
                        <div class='kpi-sub'>{best_coll}</div>
                    </div>""", unsafe_allow_html=True)
                with hc2:
                    st.markdown(f"""<div class='kpi red'>
                        <div class='kpi-label'>{t["dso_worst"]}</div>
                        <div class='kpi-value' style='color:{RED}'>{dso_by_coll[worst_coll]:.1f}<span style='font-size:.9rem;margin-left:4px'>{t["days"]}</span></div>
                        <div class='kpi-sub'>{worst_coll}</div>
                    </div>""", unsafe_allow_html=True)

            # ── Methodology note ─────────────────────────────────────────
            st.markdown(
                f"<div style='font-size:.55rem;color:{T3};margin-top:1.2rem;font-style:italic'>"
                f"ℹ️ {t['dso_method']}</div>",
                unsafe_allow_html=True,
            )

    except Exception as e:
        st.error(f"⚠️ Error rendering DSO Analysis tab: {e}")
