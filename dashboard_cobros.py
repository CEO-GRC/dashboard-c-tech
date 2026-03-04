"""
AR Collections Intelligence Dashboard — v9.0  |  Amrize Brand Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
New in v9:
  • Full Amrize brand palette  (#011E6A Midnight Blue primary)
  • Executive-grade typography hierarchy — board-presentation ready
  • Bucket 1-30d colour corrected to amber-gold (past-due, not healthy)
  • Tab 5 · Trend History — manual monthly input, editable snapshots,
    trend lines for % Past Due, $ Past Due and # Overdue Accounts
  • All v8 security hardening preserved (session-scoped cache, proactive
    RAM purge via threading.Timer, zero disk writes, zero external HTTP)
"""

import re, time, threading
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(
    page_title="Amrize · AR Collections Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── SESSION STATE INIT ────────────────────────────────────────────────────────
if "lang"      not in st.session_state: st.session_state.lang      = "EN"
if "upload_ts" not in st.session_state: st.session_state.upload_ts = None
if "hist_data" not in st.session_state: st.session_state.hist_data = []

LANG = st.session_state.lang

# ── SESSION MEMORY MANAGEMENT ────────────────────────────────────────────────
SESSION_TIMEOUT_SEC = 30 * 60

def _clear_session_data():
    for key in ["upload_ts", "_df_raw", "_df_hash", "_purge_timer"]:
        try:
            if key in st.session_state: del st.session_state[key]
        except Exception: pass

def _schedule_purge():
    existing = st.session_state.get("_purge_timer")
    if existing is not None:
        try: existing.cancel()
        except Exception: pass
    timer = threading.Timer(SESSION_TIMEOUT_SEC, _clear_session_data)
    timer.daemon = True
    timer.start()
    st.session_state["_purge_timer"] = timer

def _session_expired() -> bool:
    ts = st.session_state.get("upload_ts")
    return ts is not None and (time.time() - ts) > SESSION_TIMEOUT_SEC

def _parse_excel(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(BytesIO(file_bytes))
    df.columns = [str(c).replace("\n", " ").replace("  ", " ").strip() for c in df.columns]
    return df

def _get_df(file_bytes: bytes) -> pd.DataFrame:
    file_hash = hash(file_bytes)
    if st.session_state.get("_df_hash") != file_hash or "_df_raw" not in st.session_state:
        st.session_state["_df_raw"]  = _parse_excel(file_bytes)
        st.session_state["_df_hash"] = file_hash
    return st.session_state["_df_raw"]

# ── TRANSLATIONS ──────────────────────────────────────────────────────────────
T = {
  "EN": {
    "title": "AR Collections", "title_acc": "Intelligence",
    "sub": "Accounts Receivable · Aging · SLA · DSO · Trend Analysis",
    "upload_label": "📂 Aging Report (.xlsx)",
    "filters": "Filters", "filter_coll": "Collector", "filter_reg": "Region",
    "all_coll": "All collectors", "all_reg": "All regions",
    "security_note": "🔒 Data processed in volatile memory only. Not stored on external servers.",
    "session_expired": "⏱️ Session expired (30 min). Please re-upload your file.",
    "no_data": "No data loaded",
    "no_data_sub": "Upload your SAP Aging Report from the left panel to begin.",
    "err_cols": "Could not find Total / Current columns. Check file format.",
    "no_filter_results": "No accounts match the current filters.",
    "kpi_total": "Total AR Portfolio", "kpi_current": "Current (On Time)",
    "kpi_pd": "Past Due Exposure", "kpi_90": "90+ Days Critical", "kpi_days": "Avg Days Overdue",
    "active_accts": "active accounts", "accts": "accts", "at_risk": "at risk",
    "of_overdue": "of overdue", "weighted": "weighted avg",
    "tab1": "Aging Analysis", "tab2": "Collector View", "tab3": "Action List",
    "tab4": "DSO Analysis",   "tab5": "Trend History",
    "aging_dist": "Aging Distribution", "bucket_breakdown": "BUCKET BREAKDOWN",
    "overdue_by_bucket": "Overdue by Aging Bucket",
    "portfolio_health": "Portfolio Health", "overdue": "overdue",
    "balance_by_tier": "Balance by Tier",
    "aging_comp": "Aging Composition", "pct_mix": "% MIX", "of_overd": "of overdue",
    "coll_perf": "Collector Performance", "sla_mgmt": "SLA MANAGEMENT",
    "ar_by_coll": "AR by Collector (stacked)", "current": "Current", "past_due": "Past Due",
    "accts_vs_pct": "Accounts vs % Past Due", "num_accounts": "# Accounts",
    "coll_summary": "Collector Summary", "detail": "DETAIL",
    "collector": "Collector", "num_accts": "# Accts", "num_od": "# OD",
    "total_ar": "Total AR", "avg_od": "Avg OD", "pct_pd": "% Past Due",
    "regional": "Regional Breakdown", "geography": "GEOGRAPHY",
    "pd_by_region": "Past Due by Region",
    "no_collector": "No Collector column found in this file.",
    "sla_goal": "SLA TOUCH GOAL", "to_contact": "Accounts to Contact",
    "overd_cycle": "overdue this cycle", "total_exp": "Total Exposure",
    "of_portfolio": "of portfolio", "avg_acct": "Avg per Account",
    "avg_bal": "average overdue balance", "top5_conc": "Top 5 Concentration",
    "in_top5": "in top 5 accounts", "all_current": "🎉 All accounts are current!",
    "top_accts": "Top {n} Accounts by Past Due Balance",
    "full_list": "Collection Action List", "dl_ready": "DOWNLOAD READY",
    "download": "📥 Download Action List", "customer": "Name", "payer_id": "Payer ID",
    "region": "Region", "location": "Location",
    "info_footer": "{n} accounts · Overdue: {total} ({pct}%) · Avg: {avg} · 90+d: {crit} ({pct90}%)",
    "dso_title": "DSO Analysis", "dso_badge": "COLLECTION VELOCITY",
    "dso_avg": "Avg DSO", "dso_days": "days",
    "dso_sub_good": "Collecting on time ✓", "dso_sub_warn": "Monitor closely ⚠️",
    "dso_sub_crit": "Urgent action needed 🔴",
    "dso_gauge_title": "Collection Speed · Days Sales Outstanding",
    "dso_by_coll": "DSO by Collector", "dso_coll_badge": "WHO COLLECTS FASTEST",
    "dso_by_reg": "DSO by Region", "dso_reg_badge": "GEOGRAPHIC BEHAVIOR",
    "dso_best": "Fastest Collector", "dso_worst": "Slowest Collector",
    "dso_method": "Method: weighted average of aging bucket midpoints × balance share",
    "dso_kpi_pd_ar": "Past Due / AR", "dso_kpi_cur": "Current %",
    "dso_kpi_crit": "Critical 90+d", "dso_no_data": "Not enough data to compute DSO.", "days": "days",
    "hist_title": "Monthly Trend Tracker", "hist_badge": "HISTORICAL PERFORMANCE",
    "hist_add": "Add Monthly Snapshot",
    "hist_month": "Month", "hist_pct_pd": "% Past Due",
    "hist_amt_pd": "Past Due ($)", "hist_n_od": "# Overdue Accounts",
    "hist_save": "💾  Save Snapshot", "hist_saved": "Snapshot saved.",
    "hist_del": "Clear History",
    "hist_empty": "No historical data yet. Save your first snapshot above.",
    "hist_trend_pct": "% Past Due Trend", "hist_trend_amt": "Past Due Exposure Trend",
    "hist_trend_n": "Overdue Accounts Trend",
    "hist_table": "Historical Data", "hist_dl": "📥 Export History",
    "hist_note": "Values are pre-filled from the current file. Review and click Save Snapshot.",
  },
  "ES": {
    "title": "Cobros AR", "title_acc": "Intelligence",
    "sub": "Cuentas por Cobrar · Antigüedad · SLA · DSO · Análisis de Tendencia",
    "upload_label": "📂 Reporte de Antigüedad (.xlsx)",
    "filters": "Filtros", "filter_coll": "Cobrador", "filter_reg": "Región",
    "all_coll": "Todos los cobradores", "all_reg": "Todas las regiones",
    "security_note": "🔒 Datos procesados en memoria volátil. No se almacenan en servidores externos.",
    "session_expired": "⏱️ Sesión expirada (30 min). Vuelve a subir tu archivo.",
    "no_data": "Sin datos cargados",
    "no_data_sub": "Sube tu Reporte SAP desde el panel izquierdo para comenzar.",
    "err_cols": "No se encontraron columnas Total / Current. Verifica el formato.",
    "no_filter_results": "Ninguna cuenta coincide con los filtros.",
    "kpi_total": "Portafolio AR Total", "kpi_current": "Al Día (A Tiempo)",
    "kpi_pd": "Exposición Vencida", "kpi_90": "Crítico 90+ Días", "kpi_days": "Días Prom. Vencido",
    "active_accts": "cuentas activas", "accts": "ctas", "at_risk": "en riesgo",
    "of_overdue": "del vencido", "weighted": "prom. ponderado",
    "tab1": "Antigüedad", "tab2": "Vista Cobrador", "tab3": "Lista de Acción",
    "tab4": "Análisis DSO", "tab5": "Historial",
    "aging_dist": "Distribución de Antigüedad", "bucket_breakdown": "DESGLOSE POR BUCKET",
    "overdue_by_bucket": "Vencido por Bucket de Antigüedad",
    "portfolio_health": "Salud del Portafolio", "overdue": "vencido",
    "balance_by_tier": "Saldo por Nivel",
    "aging_comp": "Composición de Antigüedad", "pct_mix": "% MIX", "of_overd": "del vencido",
    "coll_perf": "Rendimiento del Cobrador", "sla_mgmt": "GESTIÓN SLA",
    "ar_by_coll": "AR por Cobrador (apilado)", "current": "Al día", "past_due": "Vencido",
    "accts_vs_pct": "Cuentas vs % Vencido", "num_accounts": "# Cuentas",
    "coll_summary": "Resumen de Cobrador", "detail": "DETALLE",
    "collector": "Cobrador", "num_accts": "# Ctas", "num_od": "# Venc",
    "total_ar": "AR Total", "avg_od": "Prom. Vencido", "pct_pd": "% Vencido",
    "regional": "Desglose Regional", "geography": "GEOGRAFÍA",
    "pd_by_region": "Vencido por Región",
    "no_collector": "No se encontró columna de Cobrador.",
    "sla_goal": "META SLA", "to_contact": "Cuentas a Contactar",
    "overd_cycle": "vencidas este ciclo", "total_exp": "Exposición Total",
    "of_portfolio": "del portafolio", "avg_acct": "Promedio por Cuenta",
    "avg_bal": "saldo promedio vencido", "top5_conc": "Concentración Top 5",
    "in_top5": "en top 5 ctas", "all_current": "🎉 ¡Todas las cuentas están al día!",
    "top_accts": "Top {n} Cuentas por Saldo Vencido",
    "full_list": "Lista de Acción de Cobros", "dl_ready": "LISTA PARA DESCARGA",
    "download": "📥 Descargar Lista de Acción", "customer": "Nombre", "payer_id": "ID Pagador",
    "region": "Región", "location": "Ubicación",
    "info_footer": "{n} cuentas · Vencido: {total} ({pct}%) · Prom: {avg} · 90+d: {crit} ({pct90}%)",
    "dso_title": "Análisis DSO", "dso_badge": "VELOCIDAD DE RECAUDO",
    "dso_avg": "DSO Promedio", "dso_days": "días",
    "dso_sub_good": "Cobrando a tiempo ✓", "dso_sub_warn": "Monitorear de cerca ⚠️",
    "dso_sub_crit": "Acción urgente requerida 🔴",
    "dso_gauge_title": "Velocidad de Recaudo · Días de Venta Pendiente",
    "dso_by_coll": "DSO por Cobrador", "dso_coll_badge": "QUIÉN COBRA MÁS RÁPIDO",
    "dso_by_reg": "DSO por Región", "dso_reg_badge": "COMPORTAMIENTO GEOGRÁFICO",
    "dso_best": "Cobrador Más Rápido", "dso_worst": "Cobrador Más Lento",
    "dso_method": "Método: promedio ponderado de puntos medios de buckets × participación de saldo",
    "dso_kpi_pd_ar": "Vencido / AR", "dso_kpi_cur": "% Al Día",
    "dso_kpi_crit": "Crítico 90+d", "dso_no_data": "Datos insuficientes para calcular DSO.", "days": "días",
    "hist_title": "Seguimiento Mensual", "hist_badge": "DESEMPEÑO HISTÓRICO",
    "hist_add": "Agregar Snapshot Mensual",
    "hist_month": "Mes", "hist_pct_pd": "% Vencido",
    "hist_amt_pd": "Vencido ($)", "hist_n_od": "# Cuentas Vencidas",
    "hist_save": "💾  Guardar Snapshot", "hist_saved": "Snapshot guardado.",
    "hist_del": "Limpiar Historial",
    "hist_empty": "Sin datos históricos. Guarda tu primer snapshot arriba.",
    "hist_trend_pct": "Tendencia % Vencido", "hist_trend_amt": "Tendencia Exposición Vencida",
    "hist_trend_n": "Tendencia Cuentas Vencidas",
    "hist_table": "Datos Históricos", "hist_dl": "📥 Exportar Historial",
    "hist_note": "Valores pre-cargados del archivo actual. Revisa y guarda el snapshot.",
  },
}
t = T[LANG]

# ══════════════════════════════════════════════════════════════════════════════
# AMRIZE BRAND PALETTE
# ══════════════════════════════════════════════════════════════════════════════
AMZ_MIDNIGHT = "#011E6A"
AMZ_NAVY     = "#0A3A8C"
AMZ_ROYAL    = "#1B5EBF"
AMZ_SKY      = "#4A90D9"
AMZ_MIST     = "#D6E4F7"
AMZ_PALE     = "#EBF2FB"

S_GREEN  = "#0D9E6E"
S_AMBER  = "#C8860A"
S_YELLOW = "#D4A017"
S_RED    = "#C8373A"

BG0    = "#F2F6FB"
BG1    = "#FFFFFF"
BG2    = "#EBF2FB"
BG3    = "#D6E4F7"
BORDER = "#BDD0EE"
T1     = "#061340"
T2     = "#3D5480"
T3     = "#7A96C2"

CHART_GRID = "#DDE8F5"
CHART_FONT = T2
FONT_SANS  = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
FONT_MONO  = "'Fira Code', 'Cascadia Code', 'Courier New', ui-monospace, monospace"

GREEN  = S_GREEN; YELLOW = S_YELLOW; RED = S_RED; ORANGE = AMZ_ROYAL; BLUE = AMZ_SKY
BUCKET_COLORS = [S_AMBER, S_YELLOW, "#D4620A", S_RED, "#A32030", "#7B1525", "#52091A"]

THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(family=FONT_SANS, color=CHART_FONT, size=11),
)
MARGIN_STD  = dict(l=10, r=10, t=48, b=14)
MARGIN_WIDE = dict(l=10, r=75, t=48, b=14)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""<style>
:root{{
  --font-sans:{FONT_SANS};--font-mono:{FONT_MONO};
  --brand:{AMZ_MIDNIGHT};--brand2:{AMZ_NAVY};--accent:{AMZ_ROYAL};
  --sky:{AMZ_SKY};--mist:{AMZ_MIST};--pale:{AMZ_PALE};
  --bg0:{BG0};--bg1:{BG1};--bg2:{BG2};--bg3:{BG3};--border:{BORDER};
  --t1:{T1};--t2:{T2};--t3:{T3};--green:{S_GREEN};--amber:{S_AMBER};--red:{S_RED};
}}
html,body,[class*="css"],.stApp{{font-family:var(--font-sans)!important;background:var(--bg0)!important;color:var(--t1)!important}}
.block-container{{padding:1.8rem 2.6rem 4rem!important;max-width:100%!important}}
#MainMenu{{visibility:hidden}}footer{{visibility:hidden}}.stDeployButton{{display:none}}

[data-testid="stSidebar"]{{background:var(--brand)!important;border-right:none!important;box-shadow:4px 0 20px rgba(1,30,106,.18)!important}}
[data-testid="stSidebar"] section{{padding:1.6rem 1.4rem!important}}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] div,[data-testid="stSidebar"] small{{color:rgba(255,255,255,.72)!important}}
[data-testid="collapsedControl"]{{background:var(--brand2)!important;border:1px solid rgba(255,255,255,.15)!important;color:#fff!important}}
[data-testid="stFileUploadDropzone"]{{background:rgba(255,255,255,.07)!important;border:1.5px dashed rgba(255,255,255,.3)!important;border-radius:10px!important}}
[data-testid="stFileUploadDropzone"] *{{color:rgba(255,255,255,.65)!important}}
[data-testid="stFileUploadDropzone"] button{{background:rgba(255,255,255,.14)!important;color:#fff!important;border:1px solid rgba(255,255,255,.28)!important;border-radius:6px!important}}
[data-testid="stSidebar"] .stButton>button{{background:rgba(255,255,255,.11)!important;color:#fff!important;border:1px solid rgba(255,255,255,.22)!important;border-radius:7px!important;font-size:.7rem!important;font-weight:600!important}}
[data-testid="stSidebar"] .stButton>button:hover{{background:rgba(255,255,255,.2)!important}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"]>div{{background:rgba(255,255,255,.09)!important;border:1px solid rgba(255,255,255,.22)!important;border-radius:8px!important}}

::-webkit-scrollbar{{width:5px;height:5px}}
::-webkit-scrollbar-track{{background:var(--bg0)}}
::-webkit-scrollbar-thumb{{background:var(--mist);border-radius:4px}}

.kpi{{background:var(--bg1);border:1px solid var(--border);border-radius:14px;padding:22px 24px;position:relative;overflow:hidden;box-shadow:0 2px 8px rgba(1,30,106,.06);transition:box-shadow .2s ease}}
.kpi:hover{{box-shadow:0 4px 16px rgba(1,30,106,.12)}}
.kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px}}
.kpi.brand::before {{background:linear-gradient(90deg,{AMZ_MIDNIGHT} 0%,{AMZ_ROYAL} 60%,transparent 100%)}}
.kpi.accent::before{{background:linear-gradient(90deg,{AMZ_ROYAL},transparent)}}
.kpi.green::before {{background:linear-gradient(90deg,{S_GREEN},transparent)}}
.kpi.amber::before {{background:linear-gradient(90deg,{S_AMBER},transparent)}}
.kpi.red::before   {{background:linear-gradient(90deg,{S_RED},transparent)}}
.kpi.yellow::before{{background:linear-gradient(90deg,{S_YELLOW},transparent)}}
.kpi.sky::before   {{background:linear-gradient(90deg,{AMZ_SKY},transparent)}}
.kpi-label{{font-size:.57rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:var(--t3);margin-bottom:10px}}
.kpi-value{{font-size:1.95rem;font-weight:800;line-height:1;letter-spacing:-.03em}}
.kpi-sub{{font-size:.64rem;color:var(--t2);margin-top:9px;font-weight:500}}
.kpi-bar{{margin-top:14px;height:3px;border-radius:2px;background:var(--bg3);overflow:hidden}}
.kpi-bar-fill{{height:100%;border-radius:2px}}

.sec-hdr{{display:flex;align-items:center;gap:12px;margin:2rem 0 1.1rem;padding-bottom:12px;border-bottom:2px solid var(--mist)}}
.sec-title{{font-size:.68rem;font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:var(--brand)}}
.sec-badge{{font-size:.54rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;background:{AMZ_MIST};color:{AMZ_NAVY};border:1px solid {AMZ_SKY}66;border-radius:4px;padding:3px 10px}}

.main-title{{font-size:1.7rem;font-weight:800;letter-spacing:-.04em;color:var(--brand);line-height:1.1}}
.main-title .acc{{color:var(--accent)}}
.main-sub{{font-size:.58rem;font-weight:600;color:var(--t3);text-transform:uppercase;letter-spacing:.15em;margin-top:7px}}
.ts-chip{{font-family:var(--font-mono);font-size:.62rem;color:var(--t2);background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:5px 13px;white-space:nowrap}}
.brand-strip{{display:flex;align-items:center;gap:14px;margin-bottom:.6rem}}
.brand-icon{{width:40px;height:40px;background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;box-shadow:0 3px 10px rgba(1,30,106,.28)}}
.empty-state{{margin:5rem auto;max-width:440px;background:var(--bg1);border:1px solid var(--border);border-radius:18px;padding:3.5rem 2.5rem;text-align:center;box-shadow:0 6px 24px rgba(1,30,106,.08)}}
.security-note{{font-size:.52rem;color:rgba(255,255,255,.4);line-height:1.75;margin-top:1.1rem;padding-top:.9rem;border-top:1px solid rgba(255,255,255,.13)}}
.snap-box{{background:{AMZ_PALE};border:1px solid {AMZ_MIST};border-radius:12px;padding:18px 20px;margin-bottom:1.2rem}}

[data-testid="stDataFrame"]{{border-radius:10px!important;border:1px solid var(--border)!important;overflow:hidden!important;box-shadow:0 1px 5px rgba(1,30,106,.05)!important}}
[data-testid="stDataFrame"] thead th{{background:{AMZ_PALE}!important;color:{AMZ_NAVY}!important;font-size:.58rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;font-family:var(--font-mono)!important;font-weight:700!important}}
[data-testid="stDataFrame"] tbody td{{font-family:var(--font-mono)!important;font-size:.79rem!important;color:var(--t1)!important;background:var(--bg1)!important}}

.stDownloadButton>button{{background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_NAVY})!important;color:#fff!important;border:none!important;border-radius:8px!important;font-size:.72rem!important;font-weight:700!important;letter-spacing:.06em!important;padding:.54rem 1.5rem!important;box-shadow:0 2px 8px rgba(1,30,106,.22)!important}}
.stDownloadButton>button:hover{{opacity:.85!important}}
.stButton>button{{background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_NAVY})!important;color:#fff!important;border:none!important;border-radius:8px!important;font-size:.72rem!important;font-weight:700!important;letter-spacing:.05em!important;padding:.52rem 1.4rem!important}}
.stButton>button:hover{{opacity:.85!important}}
.stAlert{{background:{AMZ_PALE}!important;border:1px solid {AMZ_SKY}88!important;border-radius:8px!important;color:var(--t1)!important}}

[data-testid="stTabs"] [data-baseweb="tab-list"]{{background:var(--bg1);border-radius:10px;border:1px solid var(--border);padding:5px;gap:3px;box-shadow:0 1px 5px rgba(1,30,106,.06)}}
[data-testid="stTabs"] [data-baseweb="tab"]{{background:transparent!important;color:var(--t2)!important;border-radius:7px!important;font-size:.68rem!important;font-weight:700!important;letter-spacing:.07em!important;text-transform:uppercase!important;padding:7px 18px!important;transition:all .15s ease!important}}
[data-testid="stTabs"] [aria-selected="true"]{{background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_NAVY})!important;color:#fff!important;box-shadow:0 2px 8px rgba(1,30,106,.28)!important}}

[data-testid="stNumberInput"]>div{{background:var(--bg2)!important;border:1px solid var(--border)!important;border-radius:8px!important}}
[data-testid="stTextInput"]>div>div{{background:var(--bg2)!important;border:1px solid var(--border)!important;border-radius:8px!important}}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def to_num(val) -> float:
    try:
        if pd.isna(val): return 0.0
    except Exception: pass
    try: return float(val)
    except (TypeError, ValueError): pass
    cleaned = re.sub(r"[^\d.-]", "", str(val))
    if not cleaned or cleaned in (".", "-", ""): return 0.0
    try: return float(cleaned)
    except ValueError: return 0.0

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Collections")
    return buf.getvalue()

def fmt(v) -> str:  return f"${to_num(v):,.2f}"

def human_format(num) -> str:
    v = to_num(num); a = abs(v); s = "-" if v < 0 else ""
    if a >= 1_000_000: return f"{s}${a/1_000_000:,.2f}M"
    if a >= 1_000:     return f"{s}${a/1_000:,.1f}K"
    return f"{s}${a:,.2f}"

fmtk = human_format

def pct(p, total) -> float:
    return round(to_num(p) / to_num(total) * 100, 1) if to_num(total) else 0.0

def safe_colors(values, lo=S_GREEN, mid=S_YELLOW, hi=S_RED):
    values = [to_num(v) for v in values]
    if not values: return []
    mn, mx = min(values), max(values)
    if mn == mx: return [mid] * len(values)
    return [lo if (v-mn)/(mx-mn) < .33 else mid if (v-mn)/(mx-mn) < .66 else hi for v in values]

def dyn(val, warn=20, crit=40):
    v = to_num(val)
    return S_RED if v >= crit else S_YELLOW if v >= warn else S_GREEN

def _calc_dso(total_ar_val, cur_val, bkt_vals, mp) -> float:
    if total_ar_val <= 0: return 0.0
    return round(sum(bkt_vals.get(lbl, 0) * d for lbl, d in mp.items()) / total_ar_val, 1)

def _trend_line(months, y_vals, color):
    if len(y_vals) < 2: return None
    x = list(range(len(y_vals)))
    xm = sum(x)/len(x); ym = sum(y_vals)/len(y_vals)
    num = sum((xi-xm)*(yi-ym) for xi, yi in zip(x, y_vals))
    den = sum((xi-xm)**2 for xi in x) or 1
    m = num/den; b = ym - m*xm
    return go.Scatter(x=months, y=[m*xi+b for xi in x], mode="lines",
                      line=dict(color=color, width=1.5, dash="dot"),
                      opacity=0.55, showlegend=False, hoverinfo="skip")

def safe_bar_chart(x_vals, y_vals, orientation="v", colors=None, title="", is_currency=True):
    y_vals = [to_num(v) for v in y_vals]; x_vals = list(x_vals)
    if not x_vals or not y_vals or all(v == 0 for v in y_vals):
        fig = go.Figure()
        fig.update_layout(**THEME, margin=MARGIN_STD,
            title=dict(text=title, font=dict(size=12, color=T1, weight="bold"), x=0),
            annotations=[dict(text="No data available", x=0.5, y=0.5, showarrow=False,
                              font=dict(color=T3, size=12))])
        return fig
    colors = colors or safe_colors(y_vals)
    kw = dict(marker=dict(color=colors, line=dict(width=0)),
              text=[human_format(v) for v in y_vals],
              textfont=dict(family=FONT_MONO, size=10, color=CHART_FONT))
    if orientation == "v":
        fig = go.Figure(go.Bar(x=x_vals, y=y_vals, textposition="outside", **kw))
        fig.update_layout(**THEME, margin=MARGIN_STD, showlegend=False, bargap=0.38,
            title=dict(text=title, font=dict(size=12, color=T1, weight="bold"), x=0),
            xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10, color=CHART_FONT)),
            yaxis=dict(showgrid=True, gridcolor=CHART_GRID, zeroline=False,
                       tickprefix="$" if is_currency else "", tickformat=",.0f" if is_currency else "",
                       tickfont=dict(size=9, color=CHART_FONT)))
    else:
        fig = go.Figure(go.Bar(y=x_vals, x=y_vals, orientation="h", textposition="outside", **kw))
        fig.update_layout(**THEME, margin=MARGIN_WIDE, showlegend=False,
            title=dict(text=title, font=dict(size=12, color=T1, weight="bold"), x=0),
            xaxis=dict(showgrid=True, gridcolor=CHART_GRID, zeroline=False,
                       tickprefix="$" if is_currency else "", tickformat=",.0f" if is_currency else "",
                       tickfont=dict(size=9, color=CHART_FONT)),
            yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10, color=CHART_FONT)))
    return fig

def kpi_card(cls, label, value_html, sub, bar_w, bar_color=None):
    cm = {"brand": AMZ_MIDNIGHT, "accent": AMZ_ROYAL, "green": S_GREEN,
          "red": S_RED, "yellow": S_YELLOW, "amber": S_AMBER, "sky": AMZ_SKY}
    bc = cm.get(bar_color or cls, AMZ_MIDNIGHT)
    return (f"<div class='kpi {cls}'>"
            f"<div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value'>{value_html}</div>"
            f"<div class='kpi-sub'>{sub}</div>"
            f"<div class='kpi-bar'><div class='kpi-bar-fill' "
            f"style='width:{min(bar_w,100):.0f}%;background:{bc}'></div></div></div>")


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='margin-bottom:1.4rem;padding-bottom:1.2rem;border-bottom:1px solid rgba(255,255,255,.14)'>
      <div style='display:flex;align-items:center;gap:11px;margin-bottom:6px'>
        <div class='brand-icon'>⭐</div>
        <div>
          <div style='font-size:1.1rem;font-weight:800;color:#fff;letter-spacing:-.02em;line-height:1.1'>Amrize</div>
          <div style='font-size:.49rem;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.17em'>AR Intelligence · v9.0</div>
        </div>
      </div>
    </div>
    <div style='font-size:.53rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
                color:rgba(255,255,255,.45);margin-bottom:8px'>{t["upload_label"]}</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("file", type=["xlsx"], label_visibility="collapsed")
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    if st.button("🌐 ES" if LANG == "EN" else "🌐 EN", use_container_width=True):
        st.session_state.lang = "ES" if LANG == "EN" else "EN"; st.rerun()

    st.markdown(f"""
    <div style='margin-top:1rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,.13)'>
      <div style='font-size:.53rem;font-weight:700;letter-spacing:.11em;text-transform:uppercase;
                  color:rgba(255,255,255,.45);margin-bottom:8px'>{t["filters"]}</div>
    </div>""", unsafe_allow_html=True)

    col_ph = st.empty(); reg_ph = st.empty()
    st.markdown(f"<div class='security-note'>{t['security_note']}</div>", unsafe_allow_html=True)


# ── HEADER ────────────────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%d %b %Y  ·  %H:%M")
hc1, hc2 = st.columns([7, 1])
with hc1:
    st.markdown(f"""<div class='brand-strip'>
      <div class='brand-icon'>⭐</div>
      <div>
        <div class='main-title'>{t["title"]} <span class='acc'>{t["title_acc"]}</span></div>
        <div class='main-sub'>{t["sub"]}</div>
      </div>
    </div>""", unsafe_allow_html=True)
with hc2:
    st.markdown(f"<div class='ts-chip' style='text-align:right;margin-top:8px'>🕐 {now_str}</div>", unsafe_allow_html=True)
st.markdown(f"<hr style='border:none;border-top:2px solid {AMZ_MIST};margin:.4rem 0 1.8rem'>", unsafe_allow_html=True)

# ── SESSION / EMPTY STATE ─────────────────────────────────────────────────────
if _session_expired():
    _clear_session_data(); st.warning(t["session_expired"]); st.stop()

if not uploaded_file:
    st.markdown(f"""<div class='empty-state'>
      <div style='font-size:3rem;margin-bottom:1rem'>📊</div>
      <div style='font-size:1.1rem;font-weight:800;color:{AMZ_MIDNIGHT};margin-bottom:10px'>{t["no_data"]}</div>
      <div style='font-size:.76rem;color:{T2};line-height:1.85'>{t["no_data_sub"]}</div>
      <div style='margin-top:1.8rem;font-size:.58rem;color:{T3};text-transform:uppercase;letter-spacing:.1em'>
        Powered by Amrize · AR Intelligence</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── LOAD ──────────────────────────────────────────────────────────────────────
file_bytes = uploaded_file.read()
if st.session_state.upload_ts is None:
    st.session_state.upload_ts = time.time(); _schedule_purge()
try:
    df_raw = _get_df(file_bytes)
except Exception as e:
    st.error(f"❌ Error loading file: {e}"); st.stop()

# ── COLUMN MAPPING ────────────────────────────────────────────────────────────
def _resolve(df, exact, fallbacks):
    if exact in df.columns: return exact
    low = {c: c.lower() for c in df.columns}
    for fb in fallbacks:
        for col, col_low in low.items():
            if fb.lower() in col_low: return col
    return None

COL_NAME  = _resolve(df_raw,"Payer",        ["name 1","name1","name","customer","client","payer"])
COL_PAYER = _resolve(df_raw,"Payer.1",       ["payer.1","payer id","payerid"])
COL_TOTAL = _resolve(df_raw,"Total",         ["total"])
COL_CURR  = _resolve(df_raw,"Current",       ["current"])
COL_COLL  = _resolve(df_raw,"Collector",     ["collector"])
COL_REG   = _resolve(df_raw,"Region",        ["region"])
COL_LOC   = _resolve(df_raw,"Location",      ["location"])
COL_TERMS = _resolve(df_raw,"Payment terms", ["payment terms","terms"])

BUCKET_LABELS = ["1-30d","31-60d","61-90d","91-120d","121-180d","181-365d","365+d"]
BUCKET_EXACT  = ["1 - 30 days","31 - 60 days","61 - 90 days","91 - 120 days",
                 "121 - 180 days","181 - 365 days","> 365 days"]
BUCKETS: dict[str,str] = {}
for lbl, ex in zip(BUCKET_LABELS, BUCKET_EXACT):
    r = _resolve(df_raw, ex, [ex.split(" days")[0]])
    if r: BUCKETS[lbl] = r

if not COL_TOTAL or not COL_CURR:
    st.error(f"⚠️ {t['err_cols']}")
    st.code(", ".join(df_raw.columns.tolist())); st.dataframe(df_raw.head(3)); st.stop()

# ── NUMERIC ───────────────────────────────────────────────────────────────────
df = df_raw.copy()
df[COL_TOTAL] = df[COL_TOTAL].apply(to_num)
df[COL_CURR]  = df[COL_CURR].apply(to_num)
for lbl, bcol in BUCKETS.items(): df[bcol] = df[bcol].apply(to_num)
df["_PD"] = df[list(BUCKETS.values())].clip(lower=0).sum(axis=1) if BUCKETS else (df[COL_TOTAL]-df[COL_CURR]).clip(lower=0)
for lbl, bcol in BUCKETS.items(): df[f"_B_{lbl}"] = df[bcol].clip(lower=0)

# ── FILTERS ───────────────────────────────────────────────────────────────────
cols_list = sorted(df[COL_COLL].dropna().unique().tolist()) if COL_COLL and COL_COLL in df.columns else []
regs_list = sorted(df[COL_REG].dropna().unique().tolist())  if COL_REG  and COL_REG  in df.columns else []
with col_ph: sel_coll = st.multiselect(t["filter_coll"], cols_list, placeholder=t["all_coll"])
with reg_ph: sel_reg  = st.multiselect(t["filter_reg"],  regs_list, placeholder=t["all_reg"])
dff = df.copy()
if sel_coll and COL_COLL: dff = dff[dff[COL_COLL].isin(sel_coll)]
if sel_reg  and COL_REG:  dff = dff[dff[COL_REG].isin(sel_reg)]
if dff.empty: st.warning(t["no_filter_results"]); st.stop()

# ── METRICS ───────────────────────────────────────────────────────────────────
total_ar  = float(dff[COL_TOTAL].sum())
total_cur = float(dff[COL_CURR].sum())
total_pd  = float(dff["_PD"].sum())
pct_pd    = pct(total_pd, total_ar)
pct_cur   = pct(total_cur, total_ar)
n_total   = len(dff)
df_sla    = dff[dff["_PD"] > 0.01].copy().sort_values("_PD", ascending=False)
n_od      = len(df_sla)
avg_od    = total_pd / n_od if n_od else 0.0
top5_val  = float(df_sla.head(5)["_PD"].sum()) if not df_sla.empty else 0.0
pct_top5  = pct(top5_val, total_pd)
bkt       = {lbl: float(dff[f"_B_{lbl}"].sum()) for lbl in BUCKETS}
pd_90p    = sum(v for k,v in bkt.items() if any(x in k for x in ["91","121","181","365+"]))
pct_90p   = pct(pd_90p, total_pd)
MIDPOINTS = {"1-30d":15,"31-60d":45,"61-90d":75,"91-120d":105,"121-180d":150,"181-365d":270,"365+d":400}
tot_aged  = sum(bkt.values()) or 1.0
avg_days  = sum(bkt.get(b,0)*d for b,d in MIDPOINTS.items()) / tot_aged
dso_portfolio = _calc_dso(total_ar, total_cur, bkt, MIDPOINTS)
dso_by_coll: dict[str,float] = {}
if COL_COLL and COL_COLL in dff.columns:
    for cn, grp in dff.groupby(COL_COLL):
        g_bkt = {lbl: float(grp[f"_B_{lbl}"].sum()) for lbl in BUCKETS}
        dso_by_coll[str(cn)] = _calc_dso(float(grp[COL_TOTAL].sum()), float(grp[COL_CURR].sum()), g_bkt, MIDPOINTS)
dso_by_reg: dict[str,float] = {}
if COL_REG and COL_REG in dff.columns:
    for rn, grp in dff.groupby(COL_REG):
        g_bkt = {lbl: float(grp[f"_B_{lbl}"].sum()) for lbl in BUCKETS}
        dso_by_reg[str(rn)] = _calc_dso(float(grp[COL_TOTAL].sum()), float(grp[COL_CURR].sum()), g_bkt, MIDPOINTS)

# ══════════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ══════════════════════════════════════════════════════════════════════════════
k1,k2,k3,k4,k5 = st.columns(5, gap="small")
with k1: st.markdown(kpi_card("brand", t["kpi_total"],
    f"<span style='color:{AMZ_MIDNIGHT}'>{human_format(total_ar)}</span>",
    f"{n_total} {t['active_accts']}", 100, "brand"), unsafe_allow_html=True)
with k2: st.markdown(kpi_card("green", t["kpi_current"],
    f"<span style='color:{S_GREEN}'>{human_format(total_cur)}</span>",
    f"{pct_cur:.1f}% · {n_total-n_od} {t['accts']}", pct_cur, "green"), unsafe_allow_html=True)
with k3:
    c3 = dyn(pct_pd, 10, 20)
    st.markdown(kpi_card("red", t["kpi_pd"],
        f"<span style='color:{c3}'>{human_format(total_pd)}</span>",
        f"{n_od} {t['accts']} · {pct_pd:.1f}% {t['at_risk']}", pct_pd, "red"), unsafe_allow_html=True)
with k4:
    c4 = dyn(pct_90p, 15, 30)
    st.markdown(kpi_card("amber", t["kpi_90"],
        f"<span style='color:{c4}'>{human_format(pd_90p)}</span>",
        f"{pct_90p:.1f}% {t['of_overdue']}", pct_90p, "amber"), unsafe_allow_html=True)
with k5:
    c5 = dyn(avg_days/180*100, 25, 50)
    st.markdown(kpi_card("sky", t["kpi_days"],
        f"<span style='color:{c5}'>{avg_days:.0f}<span style='font-size:1rem;margin-left:3px'>d</span></span>",
        t["weighted"], min(avg_days/180*100, 100), "sky"), unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([t["tab1"], t["tab2"], t["tab3"], t["tab4"], t["tab5"]])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 · AGING ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    try:
        st.markdown(f"<div class='sec-hdr'><span class='sec-title'>{t['aging_dist']}</span>"
                    f"<span class='sec-badge'>{t['bucket_breakdown']}</span></div>", unsafe_allow_html=True)
        bnames = list(bkt.keys()); bamounts = [float(v) for v in bkt.values()]
        colors = BUCKET_COLORS[:len(bnames)]
        ca, cb, cc = st.columns([4,2,2], gap="small")
        with ca:
            st.plotly_chart(safe_bar_chart(bnames, bamounts, colors=colors,
                title=t["overdue_by_bucket"]), use_container_width=True)
        with cb:
            pie_c = max(float(total_cur), 0); pie_p = max(float(total_pd), 0)
            if pie_c + pie_p > 0:
                fig2 = go.Figure(go.Pie(labels=[t["current"],t["past_due"]], values=[pie_c,pie_p],
                    hole=0.68, marker=dict(colors=[AMZ_SKY, S_RED], line=dict(width=0)),
                    textinfo="percent", textfont=dict(family=FONT_SANS,size=11,color=T1), pull=[0,.04]))
                fig2.update_layout(**THEME, margin=MARGIN_STD, showlegend=True,
                    title=dict(text=t["portfolio_health"], font=dict(size=12,color=T1,weight="bold"), x=0),
                    legend=dict(orientation="h",x=0,y=-0.18,font=dict(size=10,color=CHART_FONT),bgcolor="rgba(0,0,0,0)"),
                    annotations=[dict(text=f"<b>{pct_pd:.0f}%</b><br>{t['overdue']}",x=0.5,y=0.5,
                                      showarrow=False, font=dict(family=FONT_SANS,size=15,color=S_RED))])
            else:
                fig2 = go.Figure(); fig2.update_layout(**THEME, margin=MARGIN_STD,
                    title=dict(text=t["portfolio_health"], font=dict(size=12,color=T1), x=0))
            st.plotly_chart(fig2, use_container_width=True)
        with cc:
            st.plotly_chart(safe_bar_chart([t["current"]]+bnames, [float(total_cur)]+bamounts,
                orientation="h", colors=[AMZ_SKY]+colors, title=t["balance_by_tier"]),
                use_container_width=True)
        if bkt:
            st.markdown(f"<div class='sec-hdr' style='margin-top:.8rem'><span class='sec-title'>"
                        f"{t['aging_comp']}</span><span class='sec-badge'>{t['pct_mix']}</span></div>",
                        unsafe_allow_html=True)
            comp_cols = st.columns(len(bkt), gap="small")
            for i,(bname,bval) in enumerate(bkt.items()):
                bp = pct(float(bval), total_pd); bc = BUCKET_COLORS[i] if i<len(BUCKET_COLORS) else S_RED
                with comp_cols[i]:
                    st.markdown(f"""<div class='kpi' style='padding:15px 16px;text-align:center'>
                      <div class='kpi-label'>{bname}</div>
                      <div style='font-size:1.25rem;font-weight:800;color:{bc}'>{human_format(float(bval))}</div>
                      <div style='font-size:.6rem;color:{T2};margin-top:4px'>{bp:.1f}% {t["of_overd"]}</div>
                      <div class='kpi-bar' style='margin-top:9px'>
                        <div class='kpi-bar-fill' style='width:{bp}%;background:{bc}'></div>
                      </div>
                    </div>""", unsafe_allow_html=True)
    except Exception as e: st.error(f"⚠️ Error rendering Aging tab: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 · COLLECTOR VIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    try:
        st.markdown(f"<div class='sec-hdr'><span class='sec-title'>{t['coll_perf']}</span>"
                    f"<span class='sec-badge'>{t['sla_mgmt']}</span></div>", unsafe_allow_html=True)
        if not COL_COLL or COL_COLL not in dff.columns:
            st.info(t["no_collector"])
        else:
            cg = dff.groupby(COL_COLL).agg(
                Total_AR=(COL_TOTAL,"sum"), Total_PD=("_PD","sum"),
                Accounts=(COL_TOTAL,"count"), OD_Accts=("_PD", lambda x:(x>0.01).sum()),
            ).reset_index()
            cg["Pct_PD"] = cg.apply(lambda r: pct(r["Total_PD"],r["Total_AR"]), axis=1)
            cg["Avg_OD"] = cg.apply(lambda r: r["Total_PD"]/r["OD_Accts"] if r["OD_Accts"] else 0, axis=1)
            cg = cg.sort_values("Total_PD", ascending=False)
            cc1, cc2 = st.columns([3,2], gap="small")
            with cc1:
                fc = go.Figure()
                fc.add_trace(go.Bar(name=t["current"], x=cg[COL_COLL],
                    y=(cg["Total_AR"]-cg["Total_PD"]).clip(lower=0), marker_color=AMZ_SKY, marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>Current: $%{y:,.2f}<extra></extra>"))
                fc.add_trace(go.Bar(name=t["past_due"], x=cg[COL_COLL], y=cg["Total_PD"],
                    marker_color=S_RED, marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>Past Due: $%{y:,.2f}<extra></extra>"))
                fc.update_layout(**THEME, margin=MARGIN_STD, barmode="stack", bargap=0.3,
                    title=dict(text=t["ar_by_coll"], font=dict(size=12,color=T1,weight="bold"), x=0),
                    legend=dict(orientation="h",x=0,y=1.14,font=dict(size=10,color=CHART_FONT),bgcolor="rgba(0,0,0,0)"),
                    xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=10,color=CHART_FONT)),
                    yaxis=dict(showgrid=True,gridcolor=CHART_GRID,zeroline=False,tickprefix="$",
                               tickformat=",.0f",tickfont=dict(size=9,color=CHART_FONT)))
                st.plotly_chart(fc, use_container_width=True)
            with cc2:
                bsizes = cg["Total_PD"].apply(
                    lambda v: max(12,min(40,to_num(v)/total_pd*80)) if total_pd else 12).tolist()
                fs = go.Figure(go.Scatter(x=cg["Accounts"].tolist(), y=cg["Pct_PD"].tolist(),
                    mode="markers+text",
                    marker=dict(size=bsizes, color=safe_colors(cg["Pct_PD"].tolist(),AMZ_SKY,S_YELLOW,S_RED),
                                line=dict(width=2,color=BG1)),
                    text=cg[COL_COLL].astype(str).str[:12].tolist(), textposition="top center",
                    textfont=dict(size=9,color=CHART_FONT)))
                fs.update_layout(**THEME, margin=MARGIN_STD,
                    title=dict(text=t["accts_vs_pct"], font=dict(size=12,color=T1,weight="bold"), x=0),
                    xaxis=dict(title=dict(text=t["num_accounts"],font=dict(size=10)),showgrid=True,
                               gridcolor=CHART_GRID,zeroline=False,tickfont=dict(size=9)),
                    yaxis=dict(title=dict(text=t["pct_pd"],font=dict(size=10)),showgrid=True,
                               gridcolor=CHART_GRID,zeroline=False,tickfont=dict(size=9),ticksuffix="%"))
                st.plotly_chart(fs, use_container_width=True)

            st.markdown(f"<div class='sec-hdr' style='margin-top:.4rem'><span class='sec-title'>"
                        f"{t['coll_summary']}</span><span class='sec-badge'>{t['detail']}</span></div>",
                        unsafe_allow_html=True)
            disp = cg.copy()
            disp[t["total_ar"]] = disp["Total_AR"].apply(fmt)
            disp[t["past_due"]] = disp["Total_PD"].apply(fmt)
            disp[t["avg_od"]]   = disp["Avg_OD"].apply(fmt)
            disp[t["pct_pd"]]   = disp["Pct_PD"].apply(lambda x: f"{x:.1f}%")
            disp = disp.rename(columns={COL_COLL:t["collector"],"Accounts":t["num_accts"],"OD_Accts":t["num_od"]})
            st.dataframe(disp[[t["collector"],t["num_accts"],t["num_od"],
                                t["total_ar"],t["past_due"],t["pct_pd"],t["avg_od"]]],
                         use_container_width=True, hide_index=True)

        if COL_REG and COL_REG in dff.columns:
            st.markdown(f"<div class='sec-hdr'><span class='sec-title'>{t['regional']}</span>"
                        f"<span class='sec-badge'>{t['geography']}</span></div>", unsafe_allow_html=True)
            rg = (dff.groupby(COL_REG).agg(Past_Due=("_PD","sum"),Accounts=(COL_TOTAL,"count"))
                     .reset_index().sort_values("Past_Due", ascending=True))
            if not rg.empty:
                st.plotly_chart(safe_bar_chart(rg[COL_REG].tolist(),
                    [float(v) for v in rg["Past_Due"].tolist()], orientation="h",
                    colors=safe_colors(rg["Past_Due"].tolist(),AMZ_SKY,S_YELLOW,S_RED),
                    title=t["pd_by_region"]), use_container_width=True)
    except Exception as e: st.error(f"⚠️ Error rendering Collector tab: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 · ACTION LIST
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    try:
        st.markdown(f"<div class='sec-hdr'><span class='sec-title'>{t['full_list']}</span>"
                    f"<span class='sec-badge'>{t['sla_goal']} · {n_od} {t['to_contact'].upper()}</span></div>",
                    unsafe_allow_html=True)
        a1,a2,a3,a4 = st.columns(4, gap="small")
        with a1: st.markdown(kpi_card("amber",t["to_contact"],
            f"<span style='color:{S_AMBER}'>{n_od}</span>",t["overd_cycle"],
            min(n_od/n_total*100,100) if n_total else 0,"amber"), unsafe_allow_html=True)
        with a2: st.markdown(kpi_card("red",t["total_exp"],
            f"<span style='color:{S_RED}'>{human_format(total_pd)}</span>",
            f"{pct_pd:.1f}% {t['of_portfolio']}",pct_pd,"red"), unsafe_allow_html=True)
        with a3: st.markdown(kpi_card("accent",t["avg_acct"],
            f"<span style='color:{AMZ_ROYAL}'>{human_format(avg_od)}</span>",
            t["avg_bal"],min(avg_od/total_ar*100,100) if total_ar else 0,"accent"), unsafe_allow_html=True)
        with a4: st.markdown(kpi_card("sky",t["top5_conc"],
            f"<span style='color:{AMZ_SKY}'>{pct_top5:.1f}%</span>",
            f"{human_format(top5_val)} {t['in_top5']}",pct_top5,"sky"), unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if df_sla.empty:
            st.success(t["all_current"])
        else:
            top_n = min(15,len(df_sla)); top_df = df_sla.head(top_n).copy()
            lbl_list = (top_df[COL_NAME].astype(str).str[:28].tolist() if COL_NAME and COL_NAME in top_df.columns
                        else top_df[COL_PAYER].astype(str).str[:28].tolist() if COL_PAYER and COL_PAYER in top_df.columns
                        else [f"#{i+1}" for i in range(top_n)])
            amt_list = [float(v) for v in top_df["_PD"].tolist()]
            st.plotly_chart(safe_bar_chart(lbl_list[::-1], amt_list[::-1], orientation="h",
                colors=safe_colors(amt_list[::-1],S_AMBER,S_YELLOW,S_RED),
                title=t["top_accts"].format(n=top_n)), use_container_width=True)
            st.markdown(f"<div class='sec-hdr' style='margin-top:0'><span class='sec-title'>"
                        f"{t['full_list']}</span><span class='sec-badge'>{t['dl_ready']}</span></div>",
                        unsafe_allow_html=True)
            FIXED_COLS=[COL_PAYER,COL_NAME,COL_COLL,COL_REG,COL_TOTAL,"_PD"]
            BCOLS=[f"_B_{lbl}" for lbl in BUCKETS]
            action_df=df_sla.copy()
            for col in FIXED_COLS+BCOLS:
                if col and col not in action_df.columns: action_df[col]=0
            select_cols=[c for c in FIXED_COLS+BCOLS if c and c in action_df.columns]
            action_df=action_df[select_cols].copy(); export_df=action_df.copy()
            cn:dict[str,str]={}
            if COL_PAYER and COL_PAYER in action_df.columns: cn[COL_PAYER]=t["payer_id"]
            if COL_NAME  and COL_NAME  in action_df.columns: cn[COL_NAME] =t["customer"]
            if COL_COLL  and COL_COLL  in action_df.columns: cn[COL_COLL] =t["collector"]
            if COL_REG   and COL_REG   in action_df.columns: cn[COL_REG]  =t["region"]
            if COL_TOTAL and COL_TOTAL in action_df.columns: cn[COL_TOTAL]=t["total_ar"]
            if "_PD" in action_df.columns: cn["_PD"]=t["past_due"]
            for lbl in BUCKETS:
                bc=f"_B_{lbl}"
                if bc in action_df.columns: cn[bc]=lbl
            action_disp=action_df.rename(columns=cn); export_disp=export_df.rename(columns=cn)
            for mc in [t["total_ar"],t["past_due"]]+list(BUCKETS.keys()):
                if mc in action_disp.columns: action_disp[mc]=action_disp[mc].apply(fmt)
            bc2,_=st.columns([2,5])
            with bc2:
                st.download_button(label=t["download"],data=to_excel_bytes(export_disp),
                    file_name=f"Collections_{pd.Timestamp.now().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.dataframe(action_disp, use_container_width=True, hide_index=True, height=430)
            st.info(t["info_footer"].format(n=n_od,total=fmt(total_pd),pct=pct_pd,
                avg=fmt(avg_od),crit=human_format(pd_90p),pct90=pct_90p))
    except Exception as e: st.error(f"⚠️ Error rendering Action List tab: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 · DSO ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    try:
        st.markdown(f"<div class='sec-hdr'><span class='sec-title'>{t['dso_title']}</span>"
                    f"<span class='sec-badge'>{t['dso_badge']}</span></div>", unsafe_allow_html=True)
        if total_ar <= 0 or not BUCKETS:
            st.info(t["dso_no_data"])
        else:
            def dso_color(d): return S_GREEN if d<=30 else S_YELLOW if d<=45 else S_RED
            dc = dso_color(dso_portfolio)
            dso_sub = t["dso_sub_good"] if dso_portfolio<=30 else t["dso_sub_warn"] if dso_portfolio<=45 else t["dso_sub_crit"]
            kpi_cls = "green" if dso_portfolio<=30 else "yellow" if dso_portfolio<=45 else "red"
            d1,d2,d3,d4 = st.columns(4, gap="small")
            with d1:
                st.markdown(f"""<div class='kpi {kpi_cls}'>
                  <div class='kpi-label'>{t["dso_avg"]}</div>
                  <div class='kpi-value' style='color:{dc}'>{dso_portfolio:.1f}
                    <span style='font-size:.95rem;font-weight:600;margin-left:4px'>{t["days"]}</span></div>
                  <div class='kpi-sub'>{dso_sub}</div>
                  <div class='kpi-bar'><div class='kpi-bar-fill'
                    style='width:{min(dso_portfolio/90*100,100):.0f}%;background:{dc}'></div></div>
                </div>""", unsafe_allow_html=True)
            with d2: st.markdown(kpi_card("red",t["dso_kpi_pd_ar"],
                f"<span style='color:{dyn(pct_pd,10,20)}'>{pct_pd:.1f}%</span>",
                human_format(total_pd),pct_pd,"red"), unsafe_allow_html=True)
            with d3: st.markdown(kpi_card("green",t["dso_kpi_cur"],
                f"<span style='color:{S_GREEN}'>{pct_cur:.1f}%</span>",
                human_format(total_cur),pct_cur,"green"), unsafe_allow_html=True)
            with d4: st.markdown(kpi_card("amber",t["dso_kpi_crit"],
                f"<span style='color:{dyn(pct_90p,15,30)}'>{pct_90p:.1f}%</span>",
                human_format(pd_90p),pct_90p,"amber"), unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            g1,g2 = st.columns([2,3], gap="small")
            with g1:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta", value=dso_portfolio,
                    number=dict(suffix=f" {t['days']}",font=dict(family=FONT_SANS,size=40,color=dc)),
                    delta=dict(reference=30,increasing=dict(color=S_RED),decreasing=dict(color=S_GREEN),
                               font=dict(size=13)),
                    gauge=dict(
                        axis=dict(range=[0,120],tickwidth=1,tickcolor=CHART_FONT,
                                  tickfont=dict(size=9,color=CHART_FONT),tickvals=[0,15,30,45,60,90,120]),
                        bar=dict(color=dc,thickness=0.28), bgcolor="rgba(0,0,0,0)", borderwidth=0,
                        steps=[dict(range=[0,30],  color=f"{S_GREEN}1E"),
                               dict(range=[30,45], color=f"{S_YELLOW}1E"),
                               dict(range=[45,120],color=f"{S_RED}15")],
                        threshold=dict(line=dict(color=S_RED,width=2),thickness=0.75,value=45)),
                    title=dict(text=t["dso_gauge_title"],font=dict(size=11,color=CHART_FONT,family=FONT_SANS))))
                fig_gauge.update_layout(**THEME, margin=dict(l=20,r=20,t=62,b=12), height=290)
                st.plotly_chart(fig_gauge, use_container_width=True)
            with g2:
                if dso_by_coll:
                    sc = sorted(dso_by_coll.items(), key=lambda x:x[1])
                    c_names=[c for c,_ in sc]; c_vals=[v for _,v in sc]
                    fig_coll = go.Figure(go.Bar(y=c_names,x=c_vals,orientation="h",
                        marker=dict(color=[dso_color(v) for v in c_vals],line=dict(width=0)),
                        text=[f"{v:.1f}d" for v in c_vals],textposition="outside",
                        textfont=dict(family=FONT_MONO,size=10,color=CHART_FONT),
                        hovertemplate="<b>%{y}</b><br>DSO: %{x:.1f} days<extra></extra>"))
                    fig_coll.update_layout(**THEME,margin=MARGIN_WIDE,showlegend=False,
                        title=dict(text=t["dso_by_coll"],font=dict(size=12,color=T1,weight="bold"),x=0),
                        xaxis=dict(showgrid=True,gridcolor=CHART_GRID,zeroline=False,ticksuffix="d",
                                   tickfont=dict(size=9),range=[0,max(c_vals)*1.32]),
                        yaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=10,color=CHART_FONT)),
                        shapes=[dict(type="line",x0=30,x1=30,y0=-.5,y1=len(c_names)-.5,
                                     line=dict(color=S_GREEN,width=1.5,dash="dot")),
                                dict(type="line",x0=45,x1=45,y0=-.5,y1=len(c_names)-.5,
                                     line=dict(color=S_RED,width=1.5,dash="dot"))],
                        annotations=[dict(x=30,y=len(c_names)-.5,text="30d",showarrow=False,
                                          font=dict(size=8,color=S_GREEN),xanchor="left",yanchor="bottom"),
                                     dict(x=45,y=len(c_names)-.5,text="45d limit",showarrow=False,
                                          font=dict(size=8,color=S_RED),xanchor="left",yanchor="bottom")])
                    st.plotly_chart(fig_coll, use_container_width=True)
                else: st.info(t["no_collector"])
            if dso_by_reg:
                st.markdown(f"<div class='sec-hdr'><span class='sec-title'>{t['dso_by_reg']}</span>"
                            f"<span class='sec-badge'>{t['dso_reg_badge']}</span></div>", unsafe_allow_html=True)
                sr=sorted(dso_by_reg.items(),key=lambda x:x[1],reverse=True)
                r_names=[r for r,_ in sr]; r_vals=[v for _,v in sr]
                fig_reg=go.Figure(go.Bar(x=r_names,y=r_vals,
                    marker=dict(color=[dso_color(v) for v in r_vals],line=dict(width=0)),
                    text=[f"{v:.1f}d" for v in r_vals],textposition="outside",
                    textfont=dict(family=FONT_MONO,size=10,color=CHART_FONT),
                    hovertemplate="<b>%{x}</b><br>DSO: %{y:.1f} days<extra></extra>"))
                fig_reg.update_layout(**THEME,margin=MARGIN_STD,showlegend=False,bargap=0.38,
                    title=dict(text=t["dso_by_reg"],font=dict(size=12,color=T1,weight="bold"),x=0),
                    xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=10,color=CHART_FONT)),
                    yaxis=dict(showgrid=True,gridcolor=CHART_GRID,zeroline=False,ticksuffix="d",
                               tickfont=dict(size=9),range=[0,max(r_vals)*1.32]),
                    shapes=[dict(type="line",x0=-.5,x1=len(r_names)-.5,y0=30,y1=30,
                                 line=dict(color=S_GREEN,width=1.5,dash="dot")),
                            dict(type="line",x0=-.5,x1=len(r_names)-.5,y0=45,y1=45,
                                 line=dict(color=S_RED,width=1.5,dash="dot"))],
                    annotations=[dict(x=len(r_names)-.5,y=30,text="30d",showarrow=False,
                                      font=dict(size=8,color=S_GREEN),xanchor="right",yanchor="bottom"),
                                 dict(x=len(r_names)-.5,y=45,text="45d",showarrow=False,
                                      font=dict(size=8,color=S_RED),xanchor="right",yanchor="bottom")])
                st.plotly_chart(fig_reg, use_container_width=True)
            if len(dso_by_coll)>=2:
                best=min(dso_by_coll,key=dso_by_coll.get); worst=max(dso_by_coll,key=dso_by_coll.get)
                hh1,hh2=st.columns(2,gap="small")
                with hh1: st.markdown(f"""<div class='kpi green'>
                  <div class='kpi-label'>{t["dso_best"]}</div>
                  <div class='kpi-value' style='color:{S_GREEN}'>{dso_by_coll[best]:.1f}
                    <span style='font-size:.9rem;margin-left:4px'>{t["days"]}</span></div>
                  <div class='kpi-sub'>{best}</div></div>""", unsafe_allow_html=True)
                with hh2: st.markdown(f"""<div class='kpi red'>
                  <div class='kpi-label'>{t["dso_worst"]}</div>
                  <div class='kpi-value' style='color:{S_RED}'>{dso_by_coll[worst]:.1f}
                    <span style='font-size:.9rem;margin-left:4px'>{t["days"]}</span></div>
                  <div class='kpi-sub'>{worst}</div></div>""", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:.55rem;color:{T3};margin-top:1.2rem;font-style:italic'>"
                        f"ℹ️ {t['dso_method']}</div>", unsafe_allow_html=True)
    except Exception as e: st.error(f"⚠️ Error rendering DSO tab: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 · TREND HISTORY
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    try:
        st.markdown(f"<div class='sec-hdr'><span class='sec-title'>{t['hist_title']}</span>"
                    f"<span class='sec-badge'>{t['hist_badge']}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:.68rem;color:{T2};margin-bottom:.8rem'>"
                    f"ℹ️ {t['hist_note']}</div>", unsafe_allow_html=True)

        # ── Snapshot input ─────────────────────────────────────────────────
        st.markdown(f"<div class='snap-box'>"
                    f"<div style='font-size:.6rem;font-weight:700;letter-spacing:.12em;"
                    f"text-transform:uppercase;color:{AMZ_NAVY};margin-bottom:10px'>"
                    f"{t['hist_add']}</div>", unsafe_allow_html=True)
        f1,f2,f3,f4,f5 = st.columns([2,1.5,2,1.5,1.2], gap="small")
        with f1: month_val = st.text_input(t["hist_month"],
                    value=pd.Timestamp.now().strftime("%b %Y"), key="h_month")
        with f2: pct_val   = st.number_input(t["hist_pct_pd"], min_value=0.0, max_value=100.0,
                    value=float(pct_pd), step=0.1, format="%.1f", key="h_pct")
        with f3: amt_val   = st.number_input(t["hist_amt_pd"], min_value=0.0,
                    value=float(total_pd), step=1000.0, format="%.2f", key="h_amt")
        with f4: nod_val   = st.number_input(t["hist_n_od"], min_value=0,
                    value=int(n_od), step=1, key="h_nod")
        with f5:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button(t["hist_save"], use_container_width=True, key="btn_save_hist"):
                if month_val.strip():
                    st.session_state.hist_data.append({
                        "month": month_val.strip(),
                        "pct_pd": round(float(pct_val), 2),
                        "amt_pd": round(float(amt_val), 2),
                        "n_od":   int(nod_val),
                    })
                    st.success(t["hist_saved"]); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        hist = st.session_state.hist_data
        if not hist:
            st.markdown(f"""<div style='text-align:center;padding:3.5rem;
              background:{BG1};border:1.5px dashed {BORDER};border-radius:14px;
              color:{T3};font-size:.82rem;margin-top:.5rem'>{t["hist_empty"]}</div>""",
              unsafe_allow_html=True)
        else:
            hdf    = pd.DataFrame(hist)
            months = hdf["month"].tolist()
            LOPT   = dict(**THEME, showlegend=False,
                          xaxis=dict(showgrid=False, zeroline=False,
                                     tickfont=dict(size=10, color=CHART_FONT), tickangle=-30),
                          margin=dict(l=10, r=10, t=52, b=55))

            # % Past Due trend (wide, full-width)
            st.markdown(f"<div class='sec-hdr' style='margin-top:.5rem'>"
                        f"<span class='sec-title'>{t['hist_trend_pct']}</span>"
                        f"<span class='sec-badge'>% PAST DUE</span></div>", unsafe_allow_html=True)
            fig_pct = go.Figure()
            fig_pct.add_trace(go.Scatter(x=months, y=hdf["pct_pd"].tolist(),
                mode="lines+markers+text",
                line=dict(color=AMZ_ROYAL, width=3),
                marker=dict(size=9, color=AMZ_ROYAL, line=dict(width=2.5, color=BG1)),
                text=[f"{v:.1f}%" for v in hdf["pct_pd"].tolist()],
                textposition="top center", textfont=dict(family=FONT_MONO, size=10, color=AMZ_MIDNIGHT),
                fill="tozeroy", fillcolor=f"{AMZ_SKY}18",
                hovertemplate="%{x}<br><b>%{y:.1f}%</b><extra></extra>"))
            tl = _trend_line(months, hdf["pct_pd"].tolist(), S_RED)
            if tl: fig_pct.add_trace(tl)
            fig_pct.update_layout(**LOPT,
                title=dict(text=t["hist_trend_pct"],font=dict(size=12,color=T1,weight="bold"),x=0),
                yaxis=dict(showgrid=True,gridcolor=CHART_GRID,zeroline=False,
                           ticksuffix="%",tickfont=dict(size=10,color=CHART_FONT),
                           range=[0, max(hdf["pct_pd"].tolist())*1.38 or 10]))
            st.plotly_chart(fig_pct, use_container_width=True)

            # $ Exposure + # Accounts side by side
            c_amt, c_nod = st.columns(2, gap="small")
            with c_amt:
                st.markdown(f"<div class='sec-hdr' style='margin-top:.3rem'>"
                            f"<span class='sec-title'>{t['hist_trend_amt']}</span>"
                            f"<span class='sec-badge'>EXPOSURE $</span></div>", unsafe_allow_html=True)
                avg_amt = hdf["amt_pd"].mean()
                bar_cl  = [AMZ_SKY if v<=avg_amt else S_AMBER if v<=avg_amt*1.3 else S_RED
                           for v in hdf["amt_pd"].tolist()]
                fig_amt = go.Figure()
                fig_amt.add_trace(go.Bar(x=months, y=hdf["amt_pd"].tolist(),
                    marker=dict(color=bar_cl, line=dict(width=0)),
                    text=[human_format(v) for v in hdf["amt_pd"].tolist()],
                    textposition="outside", textfont=dict(family=FONT_MONO,size=9,color=CHART_FONT),
                    hovertemplate="%{x}<br><b>%{text}</b><extra></extra>"))
                tl2 = _trend_line(months, hdf["amt_pd"].tolist(), S_RED)
                if tl2: fig_amt.add_trace(tl2)
                fig_amt.update_layout(**LOPT, bargap=0.38,
                    title=dict(text=t["hist_trend_amt"],font=dict(size=12,color=T1,weight="bold"),x=0),
                    yaxis=dict(showgrid=True,gridcolor=CHART_GRID,zeroline=False,
                               tickprefix="$",tickformat=",.0f",tickfont=dict(size=9,color=CHART_FONT)))
                st.plotly_chart(fig_amt, use_container_width=True)

            with c_nod:
                st.markdown(f"<div class='sec-hdr' style='margin-top:.3rem'>"
                            f"<span class='sec-title'>{t['hist_trend_n']}</span>"
                            f"<span class='sec-badge'># ACCOUNTS</span></div>", unsafe_allow_html=True)
                nod_vals = hdf["n_od"].tolist()
                fig_nod  = go.Figure()
                fig_nod.add_trace(go.Scatter(x=months, y=nod_vals, mode="lines+markers+text",
                    line=dict(color=S_AMBER, width=3),
                    marker=dict(size=9, color=safe_colors(nod_vals,AMZ_SKY,S_YELLOW,S_RED),
                                line=dict(width=2.5, color=BG1)),
                    text=[str(v) for v in nod_vals], textposition="top center",
                    textfont=dict(family=FONT_MONO,size=10,color=AMZ_MIDNIGHT),
                    fill="tozeroy", fillcolor=f"{S_AMBER}14",
                    hovertemplate="%{x}<br><b>%{y} accounts</b><extra></extra>"))
                tl3 = _trend_line(months, [float(v) for v in nod_vals], S_RED)
                if tl3: fig_nod.add_trace(tl3)
                fig_nod.update_layout(**LOPT,
                    title=dict(text=t["hist_trend_n"],font=dict(size=12,color=T1,weight="bold"),x=0),
                    yaxis=dict(showgrid=True,gridcolor=CHART_GRID,zeroline=False,
                               tickfont=dict(size=10,color=CHART_FONT),
                               range=[0, max(float(v) for v in nod_vals)*1.38 or 10]))
                st.plotly_chart(fig_nod, use_container_width=True)

            # Delta KPIs from history (only if ≥2 months)
            if len(hdf) >= 2:
                first_pct=hdf["pct_pd"].iloc[0]; last_pct=hdf["pct_pd"].iloc[-1]; dpct=last_pct-first_pct
                first_amt=hdf["amt_pd"].iloc[0]; last_amt=hdf["amt_pd"].iloc[-1]; damt=last_amt-first_amt
                sk1,sk2,sk3 = st.columns(3, gap="small")
                with sk1: st.markdown(kpi_card("green" if dpct<0 else "red",
                    "Δ % Past Due",
                    f"<span style='color:{S_GREEN if dpct<0 else S_RED}'>{dpct:+.1f}%</span>",
                    f"{first_pct:.1f}% → {last_pct:.1f}%", abs(dpct), "green" if dpct<0 else "red"),
                    unsafe_allow_html=True)
                with sk2: st.markdown(kpi_card("green" if damt<0 else "red",
                    "Δ Exposure",
                    f"<span style='color:{S_GREEN if damt<0 else S_RED}'>{human_format(damt)}</span>",
                    f"{human_format(first_amt)} → {human_format(last_amt)}",
                    min(abs(damt)/first_amt*100,100) if first_amt else 0, "green" if damt<0 else "red"),
                    unsafe_allow_html=True)
                with sk3:
                    avg_h = hdf["pct_pd"].mean(); best_h = hdf["pct_pd"].min()
                    st.markdown(kpi_card("sky","Avg % Past Due (period)",
                        f"<span style='color:{AMZ_ROYAL}'>{avg_h:.1f}%</span>",
                        f"Best month: {best_h:.1f}%", avg_h, "sky"), unsafe_allow_html=True)

            # Table + export
            st.markdown(f"<div class='sec-hdr'><span class='sec-title'>{t['hist_table']}</span>"
                        f"<span class='sec-badge'>{t['dl_ready']}</span></div>", unsafe_allow_html=True)
            disp_h = hdf.copy()
            disp_h.columns = [t["hist_month"], t["hist_pct_pd"], t["hist_amt_pd"], t["hist_n_od"]]
            disp_h[t["hist_pct_pd"]] = disp_h[t["hist_pct_pd"]].apply(lambda v: f"{v:.2f}%")
            disp_h[t["hist_amt_pd"]] = disp_h[t["hist_amt_pd"]].apply(fmt)
            hb1, hb2, _ = st.columns([1.5,1.5,4], gap="small")
            with hb1:
                st.download_button(label=t["hist_dl"], data=to_excel_bytes(hdf),
                    file_name=f"PD_History_{pd.Timestamp.now().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_hist")
            with hb2:
                if st.button(t["hist_del"], key="btn_del_hist"):
                    st.session_state.hist_data = []; st.rerun()
            st.dataframe(disp_h, use_container_width=True, hide_index=True)

    except Exception as e: st.error(f"⚠️ Error rendering Trend History tab: {e}")
