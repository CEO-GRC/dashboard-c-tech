import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Collections Intelligence | AR Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;400;600;700&display=swap');

/* ── Root palette ── */
:root {
    --bg-primary:    #090e1a;
    --bg-secondary:  #0f1729;
    --bg-card:       #131c30;
    --bg-card-hover: #19253d;
    --accent-teal:   #00f5c4;
    --accent-blue:   #3b82f6;
    --accent-red:    #f43f5e;
    --accent-amber:  #f59e0b;
    --text-primary:  #e2e8f0;
    --text-muted:    #64748b;
    --border:        #1e2d47;
    --border-accent: rgba(0,245,196,0.25);
}

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

.stApp { background-color: var(--bg-primary); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stFileUploadDropzone"] {
    background: var(--bg-card) !important;
    border: 1.5px dashed var(--border-accent) !important;
    border-radius: 12px !important;
}

/* ── Hide default streamlit cruft ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 3rem 2rem; }

/* ── KPI Cards ── */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 26px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease, transform 0.15s ease;
}
.kpi-card:hover {
    border-color: var(--border-accent);
    transform: translateY(-2px);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.kpi-card.green::before  { background: linear-gradient(90deg, var(--accent-teal), transparent); }
.kpi-card.blue::before   { background: linear-gradient(90deg, var(--accent-blue), transparent); }
.kpi-card.red::before    { background: linear-gradient(90deg, var(--accent-red), transparent); }
.kpi-card.amber::before  { background: linear-gradient(90deg, var(--accent-amber), transparent); }

.kpi-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 8px;
}
.kpi-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1;
}
.kpi-sub {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 8px;
}
.kpi-sub .up   { color: var(--accent-teal); }
.kpi-sub .down { color: var(--accent-red); }

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 2rem 0 1rem 0;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}
.section-header h2 {
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-primary);
    margin: 0;
}
.section-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    background: rgba(0,245,196,0.1);
    color: var(--accent-teal);
    border: 1px solid rgba(0,245,196,0.3);
    border-radius: 20px;
    padding: 2px 10px;
}

/* ── Data table ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    overflow: hidden;
}
[data-testid="stDataFrame"] th {
    background: var(--bg-secondary) !important;
    color: var(--text-muted) !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
[data-testid="stDataFrame"] td {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, rgba(0,245,196,0.12), rgba(59,130,246,0.08)) !important;
    color: var(--accent-teal) !important;
    border: 1px solid rgba(0,245,196,0.3) !important;
    border-radius: 8px !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    letter-spacing: 0.04em;
    transition: all 0.2s ease;
}
.stDownloadButton > button:hover {
    background: rgba(0,245,196,0.2) !important;
    border-color: var(--accent-teal) !important;
    box-shadow: 0 0 18px rgba(0,245,196,0.2) !important;
}

/* ── Info box ── */
.stAlert {
    background: rgba(59,130,246,0.08) !important;
    border: 1px solid rgba(59,130,246,0.25) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}

/* ── Logo header ── */
.dash-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.25rem;
}
.dash-title {
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
}
.dash-title span { color: var(--accent-teal); }
.dash-subtitle {
    font-size: 0.75rem;
    color: var(--text-muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 2px;
}
.dash-timestamp {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-muted);
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 5px 12px;
}
.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1rem 0 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def limpiar_dinero(serie):
    return pd.to_numeric(
        serie.astype(str).str.replace('$', '').str.replace(',', '').str.strip(),
        errors='coerce'
    ).fillna(0)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Lista_de_Cobro')
    return output.getvalue()

def fmt_money(val):
    return f"${val:,.2f}"

def pct(part, total):
    return (part / total * 100) if total else 0

PLOTLY_THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Sora, sans-serif', color='#94a3b8', size=11),
    margin=dict(l=10, r=10, t=30, b=10),
)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='margin-bottom:1.5rem'>
            <div style='font-size:1.1rem;font-weight:700;color:#e2e8f0;letter-spacing:-0.01em'>⚡ Collections<br><span style='color:#00f5c4'>Intelligence</span></div>
            <div style='font-size:0.65rem;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px'>AR Analytics Platform</div>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📂 Reporte de Aging (Excel)", type=["xlsx"])

    st.markdown("<hr style='border-color:#1e2d47;margin:1.5rem 0'>", unsafe_allow_html=True)
    st.markdown("""
        <div style='font-size:0.65rem;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>Instrucciones</div>
        <div style='font-size:0.72rem;color:#64748b;line-height:1.6'>
        Sube tu archivo de Aging en formato <strong style='color:#94a3b8'>.xlsx</strong>.<br><br>
        El sistema detecta automáticamente columnas de <em>Total AR, Current, Terms y Customer</em>.
        </div>
    """, unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────
now_str = pd.Timestamp.now().strftime("%d %b %Y · %H:%M")
st.markdown(f"""
<div class='dash-header'>
    <div>
        <div class='dash-title'>AR <span>Dashboard</span></div>
        <div class='dash-subtitle'>Collections Performance &amp; SLA Management</div>
    </div>
    <div class='dash-timestamp'>🕐 {now_str}</div>
</div>
<hr class='divider'>
""", unsafe_allow_html=True)

# ─── MAIN LOGIC ──────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown("""
    <div style='
        margin: 4rem auto;
        max-width: 480px;
        background: #131c30;
        border: 1px dashed #1e2d47;
        border-radius: 16px;
        padding: 3rem 2rem;
        text-align: center;
    '>
        <div style='font-size:2.5rem;margin-bottom:1rem'>📊</div>
        <div style='font-size:1rem;font-weight:600;color:#e2e8f0;margin-bottom:0.5rem'>Sin datos cargados</div>
        <div style='font-size:0.8rem;color:#475569;line-height:1.6'>
            Sube tu reporte de Aging desde el panel lateral para comenzar el análisis de cartera.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─── DATA PROCESSING ─────────────────────────────────────────────────────────
df = pd.read_excel(uploaded_file)
df.columns = [str(c).strip() for c in df.columns]

col_total    = next((c for c in df.columns if "Total AR" in c), None)
col_customer = 'Customer'
col_terms    = 'Terms'
col_current  = 'Current'

if not col_total or col_current not in df.columns:
    st.error("⚠️ No se encontraron las columnas necesarias (Total AR, Current). Revisa el formato del archivo.")
    st.stop()

try:
    df[col_total]   = limpiar_dinero(df[col_total])
    df[col_current] = limpiar_dinero(df[col_current])
    df['Past_Due_Total'] = df[col_total] - df[col_current]

    total_cartera  = df[col_total].sum()
    total_corriente = df[col_current].sum()
    total_vencido  = total_cartera - total_corriente
    pct_vencido    = pct(total_vencido, total_cartera)
    pct_corriente  = pct(total_corriente, total_cartera)

    df_sla = df[df['Past_Due_Total'] > 0.01].copy()
    df_sla = df_sla.sort_values(by='Past_Due_Total', ascending=False)
    cuenta_vencidas = len(df_sla)
    cuenta_total    = len(df)

    # ─── KPI CARDS ───────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class='kpi-card green'>
            <div class='kpi-label'>📦 Total Cartera (AR)</div>
            <div class='kpi-value'>{fmt_money(total_cartera)}</div>
            <div class='kpi-sub'>{cuenta_total} cuentas activas</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='kpi-card blue'>
            <div class='kpi-label'>✅ Corriente (Current)</div>
            <div class='kpi-value'>{fmt_money(total_corriente)}</div>
            <div class='kpi-sub'><span class='up'>▲ {pct_corriente:.1f}%</span> del total</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='kpi-card red'>
            <div class='kpi-label'>🔴 Vencido (Past Due)</div>
            <div class='kpi-value'>{fmt_money(total_vencido)}</div>
            <div class='kpi-sub'><span class='down'>▼ {pct_vencido:.1f}%</span> del total</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='kpi-card amber'>
            <div class='kpi-label'>🎯 SLA Touch Goal</div>
            <div class='kpi-value'>{cuenta_vencidas}</div>
            <div class='kpi-sub'>cuentas para gestionar</div>
        </div>""", unsafe_allow_html=True)

    # ─── CHARTS ROW ──────────────────────────────────────────────────────────
    st.markdown("""
    <div class='section-header'>
        <h2>📊 Distribución de Mora</h2>
        <span class='section-badge'>AGING BUCKETS</span>
    </div>""", unsafe_allow_html=True)

    # Build buckets
    buckets_map = {
        '1-30 Days':   next((c for c in df.columns if "1-30"  in c), None),
        '31-60 Days':  next((c for c in df.columns if "31-60" in c), None),
        '61-90 Days':  next((c for c in df.columns if "61-90" in c), None),
        '91-120 Days': next((c for c in df.columns if "91-120" in c), None),
        '121+ Days':   [c for c in df.columns if any(x in c for x in ["121","181","> 365"])],
    }
    data_buckets = []
    for nombre, col in buckets_map.items():
        if isinstance(col, list):
            valor = sum([limpiar_dinero(df[c]).sum() for c in col])
        elif col:
            valor = limpiar_dinero(df[col]).sum()
        else:
            valor = 0
        data_buckets.append({'Rango': nombre, 'Monto': valor})
    df_buckets = pd.DataFrame(data_buckets)

    colors_buckets = ['#00f5c4', '#3b82f6', '#f59e0b', '#f97316', '#f43f5e']

    ch1, ch2 = st.columns([3, 2])

    with ch1:
        fig_bar = go.Figure(go.Bar(
            x=df_buckets['Rango'],
            y=df_buckets['Monto'],
            marker=dict(
                color=colors_buckets,
                line=dict(width=0),
            ),
            text=[f"${v:,.0f}" for v in df_buckets['Monto']],
            textposition='outside',
            textfont=dict(family='IBM Plex Mono', size=10, color='#94a3b8'),
        ))
        fig_bar.update_layout(
            **PLOTLY_THEME,
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor='#1e2d47', zeroline=False,
                       tickprefix='$', tickformat=',.0f', tickfont=dict(size=9)),
            bargap=0.35,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with ch2:
        fig_pie = go.Figure(go.Pie(
            labels=['Corriente', 'Vencido'],
            values=[total_corriente, total_vencido],
            hole=0.65,
            marker=dict(colors=['#00f5c4', '#f43f5e'], line=dict(width=0)),
            textinfo='label+percent',
            textfont=dict(family='Sora', size=11),
        ))
        fig_pie.update_layout(
            **PLOTLY_THEME,
            showlegend=False,
            annotations=[dict(
                text=f"<b>{pct_vencido:.0f}%</b><br>mora",
                x=0.5, y=0.5, showarrow=False,
                font=dict(family='IBM Plex Mono', size=16, color='#f43f5e')
            )],
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ─── SLA TABLE ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='section-header'>
        <h2>🎯 Priority Action List</h2>
        <span class='section-badge'>100% TOUCH GOAL · {cuenta_vencidas} ACCOUNTS</span>
    </div>""", unsafe_allow_html=True)

    cols_disponibles = [c for c in [col_customer, 'Past_Due_Total', col_terms, col_total] if c in df_sla.columns]
    reporte_agente = df_sla[cols_disponibles].copy()

    # Format display copy
    display_df = reporte_agente.copy()
    if 'Past_Due_Total' in display_df.columns:
        display_df['Past_Due_Total'] = display_df['Past_Due_Total'].apply(lambda x: f"${x:,.2f}")
    if col_total in display_df.columns:
        display_df[col_total] = display_df[col_total].apply(lambda x: f"${x:,.2f}")
    display_df.columns = [c.replace('Past_Due_Total','Past Due').replace(col_total,'Total AR') for c in display_df.columns]

    btn_col, _ = st.columns([2, 5])
    with btn_col:
        st.download_button(
            label="📥 Descargar Lista de Cobro (Excel)",
            data=to_excel(reporte_agente),
            file_name=f'SLA_Cobros_{pd.Timestamp.now().strftime("%Y-%m-%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

    st.info(f"💡 **{cuenta_vencidas} cuentas** requieren gestión esta semana · Vencido total: **{fmt_money(total_vencido)}** ({pct_vencido:.1f}% de la cartera)")

except Exception as e:
    st.error(f"❌ Error procesando el archivo: {e}")
