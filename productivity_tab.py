"""
Productivity Tab v1.0 - NUEVO TAB
Añade este tab a tu dashboard para análisis de productividad
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from qa_module_v7 import calculate_productivity_metrics, export_productivity_report

AMZ_MIDNIGHT = "#011E6A"
AMZ_SKY = "#00A7E1"
AMZ_ROYAL = "#0047AB"
S_GREEN = "#059669"
S_RED = "#DC2626"
S_AMBER = "#D97706"
S_YELLOW = "#F59E0B"


def fmt(v):
    try:
        num = float(v)
        return "$0.00" if pd.isna(num) or num == 0 else f"${num:,.2f}"
    except:
        return "$0.00"


def fmt_pct(v):
    try:
        return "0.0%" if pd.isna(v) else f"{float(v):.1f}%"
    except:
        return "0.0%"


def fmt_num(v):
    try:
        return "0" if pd.isna(v) else f"{float(v):,.0f}"
    except:
        return "0"


def check_mgmt_password():
    try:
        correct_pwd = st.secrets.get("MGMT_PASSWORD", "MGMT2024")
    except:
        correct_pwd = "MGMT2024"
    
    if 'mgmt_authenticated' not in st.session_state:
        st.session_state.mgmt_authenticated = False
    
    if st.session_state.mgmt_authenticated:
        return True
    
    st.markdown(f"""
    <div style='text-align:center;padding:2.5rem;
                background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                border-radius:16px;margin:2rem auto;max-width:500px'>
        <div style='font-size:3rem;margin-bottom:1rem'>🔐</div>
        <h2 style='color:white;margin:0;font-weight:700'>Management Access</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form_prod", clear_on_submit=False):
        pwd = st.text_input("Contraseña:", type="password", key="pwd_prod")
        submitted = st.form_submit_button("Acceder", use_container_width=True, type="primary")
        
        if submitted:
            if pwd == correct_pwd:
                st.session_state.mgmt_authenticated = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    
    return False


def render_productivity_tab(df_merged=None, df_payments=None, col_collector=None, col_total=None):
    """Tab de Productividad con métricas consolidadas."""
    
    if not check_mgmt_password():
        return
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                padding:2rem;border-radius:12px;margin-bottom:2rem'>
        <h1 style='color:white;margin:0;font-size:1.8rem'>📊 Team Productivity</h1>
        <p style='color:{AMZ_SKY};margin:0.5rem 0 0'>Análisis consolidado de cartera, gestión y cobros</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Validar datos
    if df_merged is None:
        if 'qa_merged' in st.session_state:
            df_merged = st.session_state.qa_merged
        else:
            st.warning("⚠️ Procesa primero datos en el tab 'Management & QA'")
            return
    
    if df_payments is None:
        if 'payments_data' in st.session_state:
            df_payments = st.session_state.payments_data
        else:
            st.info("ℹ️ No hay datos de pagos. Las métricas de cobro mostrarán $0.")
            df_payments = pd.DataFrame(columns=['collector', 'amount'])
    
    # Calcular productividad
    try:
        with st.spinner("🔄 Calculando métricas..."):
            prod = calculate_productivity_metrics(df_merged, df_payments, col_collector, col_total)
        st.session_state.productivity_data = prod
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return
    
    # KPIs
    st.markdown("### 🎯 KPIs Ejecutivos")
    k1, k2, k3, k4, k5 = st.columns(5)
    
    with k1:
        st.metric("👥 Collectors", len(prod))
    with k2:
        st.metric("📋 Cuentas", fmt_num(prod['cuentas_asignadas'].sum()))
    with k3:
        pct_g = (prod['cuentas_gestionadas'].sum() / prod['cuentas_asignadas'].sum() * 100) if prod['cuentas_asignadas'].sum() > 0 else 0
        st.metric("✅ Penetración", fmt_pct(pct_g))
    with k4:
        st.metric("💰 Cobrado", fmt(prod['monto_cobrado'].sum()))
    with k5:
        efec = (prod['monto_cobrado'].sum() / prod['total_actividades'].sum()) if prod['total_actividades'].sum() > 0 else 0
        st.metric("⚡ Efectividad", fmt(efec))
    
    # Tabs de análisis
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["💰 Cobros", "📊 Penetración", "⚡ Efectividad"])
    
    with tab1:
        c1, c2 = st.columns([2, 1])
        with c1:
            top10 = prod.head(10)
            fig = go.Figure()
            colors = [S_GREEN if i == 0 else AMZ_SKY if i < 3 else AMZ_ROYAL if i < 5 else S_AMBER for i in range(len(top10))]
            fig.add_trace(go.Bar(
                x=top10['monto_cobrado'], y=top10['collector'], orientation='h',
                marker=dict(color=colors), text=[fmt(v) for v in top10['monto_cobrado']],
                textposition='outside'
            ))
            fig.update_layout(
                title="Top 10 por Cobros", height=450, showlegend=False,
                plot_bgcolor='white', yaxis=dict(categoryorder='total ascending')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.markdown("**🏆 Top 5**")
            for _, r in prod.head(5).iterrows():
                st.markdown(f"""
                <div style='background:#f0f8ff;padding:0.8rem;border-radius:8px;margin:0.5rem 0'>
                    <b>#{r['rank']} {r['collector'][:20]}</b><br>
                    <div style='font-size:1.5rem;color:{S_GREEN}'>{fmt(r['monto_cobrado'])}</div>
                    <small>{fmt_num(r['total_actividades'])} acts • {fmt(r['efectividad'])}/act</small>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.scatter(
                prod, x='cuentas_asignadas', y='cuentas_gestionadas',
                size='monto_cobrado', color='penetracion_pct', hover_name='collector',
                color_continuous_scale='RdYlGn', title='Asignadas vs Gestionadas'
            )
            fig.update_layout(height=400, plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            top_pen = prod.sort_values('penetracion_pct', ascending=False).head(10)
            fig = go.Figure()
            colors_p = [S_GREEN if p >= 80 else AMZ_SKY if p >= 60 else S_AMBER if p >= 40 else S_RED for p in top_pen['penetracion_pct']]
            fig.add_trace(go.Bar(
                x=top_pen['penetracion_pct'], y=top_pen['collector'], orientation='h',
                marker=dict(color=colors_p), text=[f"{v:.1f}%" for v in top_pen['penetracion_pct']],
                textposition='outside'
            ))
            fig.update_layout(
                title="Top 10 Penetración %", height=400, showlegend=False,
                plot_bgcolor='white', yaxis=dict(categoryorder='total ascending')
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.scatter(
                prod, x='total_actividades', y='monto_cobrado',
                size='efectividad', color='penetracion_pct', hover_name='collector',
                color_continuous_scale='Viridis', title='Actividades vs Cobros'
            )
            fig.update_layout(height=400, plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            top_ef = prod[prod['efectividad'] > 0].sort_values('efectividad', ascending=False).head(10)
            if len(top_ef) > 0:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=top_ef['efectividad'], y=top_ef['collector'], orientation='h',
                    marker=dict(color=AMZ_SKY), text=[fmt(v) for v in top_ef['efectividad']],
                    textposition='outside'
                ))
                fig.update_layout(
                    title="Top 10 Efectividad", height=400, showlegend=False,
                    plot_bgcolor='white', yaxis=dict(categoryorder='total ascending')
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Tabla
    st.markdown("---")
    st.markdown("### 📋 Tabla de Productividad")
    
    tbl = pd.DataFrame({
        'Rank': prod['rank'],
        'Collector': prod['collector'],
        'Asignadas': prod['cuentas_asignadas'].apply(fmt_num),
        'Gestionadas': prod['cuentas_gestionadas'].apply(fmt_num),
        'Penetración': prod['penetracion_pct'].apply(fmt_pct),
        'Actividades': prod['total_actividades'].apply(fmt_num),
        'Cobrado': prod['monto_cobrado'].apply(fmt),
        'Efectividad': prod['efectividad'].apply(fmt)
    })
    st.dataframe(tbl, use_container_width=True, hide_index=True, height=400)
    
    # Insights
    st.markdown("---")
    st.markdown("### 💡 Insights")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**🎯 Top Performers**")
        top_p = prod.nlargest(3, 'penetracion_pct')
        st.success("**Alta Penetración:**\n" + "\n".join([f"• {r['collector']}: {r['penetracion_pct']:.1f}%" for _, r in top_p.iterrows()]))
    
    with c2:
        st.markdown("**⚠️ Oportunidades**")
        low_p = prod.nsmallest(3, 'penetracion_pct')
        st.warning("**Baja Penetración:**\n" + "\n".join([f"• {r['collector']}: {r['penetracion_pct']:.1f}%" for _, r in low_p.iterrows()]))
    
    # Export
    st.markdown("---")
    if st.button("📊 Exportar a Excel", type="primary"):
        try:
            excel = export_productivity_report(prod)
            st.download_button(
                "⬇️ Descargar Reporte",
                data=excel,
                file_name=f"Productivity_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("✅ Listo")
        except Exception as e:
            st.error(f"❌ Error: {e}")
