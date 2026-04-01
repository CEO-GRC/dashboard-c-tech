"""
Productivity Tab v1.0 - NUEVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Medición de productividad de equipo de cobros:
- Consolidación de Aging + Actividades + Pagos
- Métricas por agente/collector
- Dashboards ejecutivos
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from qa_module_v7_FIXED import (
    calculate_productivity_metrics,
    export_productivity_report
)

# Colores Amrize
AMZ_MIDNIGHT = "#011E6A"
AMZ_SKY = "#00A7E1"
AMZ_ROYAL = "#0047AB"
S_GREEN = "#059669"
S_RED = "#DC2626"
S_AMBER = "#D97706"
S_YELLOW = "#F59E0B"
S_GRAY = "#6B7280"


def fmt(v):
    """Formatear moneda."""
    try:
        num = float(v)
        if pd.isna(num) or num == 0:
            return "$0.00"
        return f"${num:,.2f}"
    except:
        return "$0.00"


def fmt_pct(v):
    """Formatear porcentaje."""
    try:
        num = float(v)
        if pd.isna(num):
            return "0.0%"
        return f"{num:.1f}%"
    except:
        return "0.0%"


def fmt_num(v):
    """Formatear número."""
    try:
        num = float(v)
        if pd.isna(num):
            return "0"
        return f"{num:,.0f}"
    except:
        return "0"


def check_mgmt_password():
    """Password con secrets y Enter."""
    try:
        correct_pwd = st.secrets["MGMT_PASSWORD"]
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
    """
    Tab de Productividad - Consolidación de datos de equipo.
    
    Args:
        df_merged: DataFrame del merge aging + activities (de session_state.qa_merged)
        df_payments: DataFrame de pagos (de session_state.payments_data)
        col_collector: Columna de Collector
        col_total: Columna de Total AR
    """
    
    if not check_mgmt_password():
        return
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                padding:2rem;border-radius:12px;margin-bottom:2rem'>
        <h1 style='color:white;margin:0;font-size:1.8rem'>📊 Team Productivity Dashboard</h1>
        <p style='color:{AMZ_SKY};margin:0.5rem 0 0'>Análisis consolidado de cartera, gestión y cobros</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Validar que tenemos los datos necesarios
    if df_merged is None:
        if 'qa_merged' in st.session_state:
            df_merged = st.session_state.qa_merged
        else:
            st.warning("⚠️ No hay datos de Aging + Actividades. Por favor procese primero en el tab 'Management & QA'.")
            return
    
    if df_payments is None:
        if 'payments_data' in st.session_state:
            df_payments = st.session_state.payments_data
        else:
            st.info("ℹ️ No hay datos de pagos cargados. Las métricas de cobro mostrarán $0.")
            df_payments = pd.DataFrame(columns=['collector', 'amount'])
    
    # Calcular métricas de productividad
    try:
        with st.spinner("🔄 Calculando métricas de productividad..."):
            productivity = calculate_productivity_metrics(
                df_merged,
                df_payments,
                col_collector,
                col_total
            )
        
        st.session_state.productivity_data = productivity
        
    except Exception as e:
        st.error(f"❌ Error calculando productividad: {str(e)}")
        import traceback
        with st.expander("🔍 Detalles del Error"):
            st.code(traceback.format_exc())
        return
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 1: KPIs EJECUTIVOS
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 🎯 KPIs Ejecutivos")
    
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    with kpi1:
        st.metric(
            "👥 Collectors",
            len(productivity)
        )
    
    with kpi2:
        st.metric(
            "📋 Cuentas Totales",
            fmt_num(productivity['cuentas_asignadas'].sum())
        )
    
    with kpi3:
        pct_gestionadas = (productivity['cuentas_gestionadas'].sum() / 
                          productivity['cuentas_asignadas'].sum() * 100) if productivity['cuentas_asignadas'].sum() > 0 else 0
        st.metric(
            "✅ Penetración",
            fmt_pct(pct_gestionadas),
            delta=f"{fmt_num(productivity['cuentas_gestionadas'].sum())} cuentas"
        )
    
    with kpi4:
        st.metric(
            "💰 Total Cobrado",
            fmt(productivity['monto_cobrado'].sum())
        )
    
    with kpi5:
        efectividad_global = (productivity['monto_cobrado'].sum() / 
                             productivity['total_actividades'].sum()) if productivity['total_actividades'].sum() > 0 else 0
        st.metric(
            "⚡ Efectividad",
            fmt(efectividad_global),
            delta="$/actividad"
        )
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 2: GRÁFICAS DE RENDIMIENTO
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📈 Análisis de Rendimiento")
    
    tab1, tab2, tab3 = st.tabs(["💰 Cobros", "📊 Penetración", "⚡ Efectividad"])
    
    # TAB 1: Cobros
    with tab1:
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # Gráfica de barras - Top 10 por cobros
            df_top10 = productivity.head(10).copy()
            
            fig_cobros = go.Figure()
            
            colors = []
            for i in range(len(df_top10)):
                if i == 0:
                    colors.append(S_GREEN)
                elif i < 3:
                    colors.append(AMZ_SKY)
                elif i < 5:
                    colors.append(AMZ_ROYAL)
                else:
                    colors.append(S_AMBER)
            
            fig_cobros.add_trace(go.Bar(
                x=df_top10['monto_cobrado'],
                y=df_top10['collector'],
                orientation='h',
                marker=dict(color=colors),
                text=[fmt(v) for v in df_top10['monto_cobrado']],
                textposition='outside',
                textfont=dict(size=10)
            ))
            
            fig_cobros.update_layout(
                title="Top 10 Collectors por Monto Cobrado",
                xaxis_title="Monto ($)",
                yaxis_title="",
                height=450,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Arial", size=11),
                margin=dict(l=150, r=50, t=50, b=50)
            )
            
            fig_cobros.update_yaxis(categoryorder='total ascending')
            
            st.plotly_chart(fig_cobros, use_container_width=True)
        
        with col_right:
            st.markdown("**🏆 Top 5 Collectors**")
            
            for idx, row in productivity.head(5).iterrows():
                st.markdown(f"""
                <div style='background:#f0f8ff;padding:0.8rem;border-radius:8px;margin:0.5rem 0'>
                    <div style='font-size:1.2rem;font-weight:bold;color:{AMZ_MIDNIGHT}'>
                        #{row['rank']} {row['collector'][:20]}
                    </div>
                    <div style='font-size:1.5rem;font-weight:bold;color:{S_GREEN};margin:0.3rem 0'>
                        {fmt(row['monto_cobrado'])}
                    </div>
                    <div style='font-size:0.85rem;color:{S_GRAY}'>
                        {fmt_num(row['total_actividades'])} actividades
                        • {fmt(row['efectividad'])}/act
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # TAB 2: Penetración
    with tab2:
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Scatter plot: Cuentas Asignadas vs Gestionadas
            fig_scatter = px.scatter(
                productivity,
                x='cuentas_asignadas',
                y='cuentas_gestionadas',
                size='monto_cobrado',
                color='penetracion_pct',
                hover_name='collector',
                hover_data={
                    'cuentas_asignadas': ':,.0f',
                    'cuentas_gestionadas': ':,.0f',
                    'penetracion_pct': ':.1f',
                    'monto_cobrado': ':$,.2f'
                },
                color_continuous_scale='RdYlGn',
                title='Penetración: Asignadas vs Gestionadas'
            )
            
            fig_scatter.update_layout(
                height=400,
                xaxis_title="Cuentas Asignadas",
                yaxis_title="Cuentas Gestionadas",
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col_right:
            # Bar chart horizontal - Penetración %
            df_penet = productivity.sort_values('penetracion_pct', ascending=False).head(10)
            
            fig_penet = go.Figure()
            
            colors_penet = []
            for pct in df_penet['penetracion_pct']:
                if pct >= 80:
                    colors_penet.append(S_GREEN)
                elif pct >= 60:
                    colors_penet.append(AMZ_SKY)
                elif pct >= 40:
                    colors_penet.append(S_AMBER)
                else:
                    colors_penet.append(S_RED)
            
            fig_penet.add_trace(go.Bar(
                x=df_penet['penetracion_pct'],
                y=df_penet['collector'],
                orientation='h',
                marker=dict(color=colors_penet),
                text=[f"{v:.1f}%" for v in df_penet['penetracion_pct']],
                textposition='outside'
            ))
            
            fig_penet.update_layout(
                title="Top 10 por % Penetración",
                xaxis_title="Penetración (%)",
                yaxis_title="",
                height=400,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=150, r=50, t=50, b=50)
            )
            
            fig_penet.update_yaxis(categoryorder='total ascending')
            
            st.plotly_chart(fig_penet, use_container_width=True)
    
    # TAB 3: Efectividad
    with tab3:
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Scatter: Actividades vs Monto Cobrado
            fig_efectividad = px.scatter(
                productivity,
                x='total_actividades',
                y='monto_cobrado',
                size='efectividad',
                color='penetracion_pct',
                hover_name='collector',
                hover_data={
                    'total_actividades': ':,.0f',
                    'monto_cobrado': ':$,.2f',
                    'efectividad': ':$,.2f',
                    'penetracion_pct': ':.1f'
                },
                color_continuous_scale='Viridis',
                title='Efectividad: Actividades vs Cobros'
            )
            
            fig_efectividad.update_layout(
                height=400,
                xaxis_title="Total Actividades",
                yaxis_title="Monto Cobrado ($)",
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig_efectividad, use_container_width=True)
        
        with col_right:
            # Top 10 por efectividad
            df_efec = productivity[productivity['efectividad'] > 0].sort_values('efectividad', ascending=False).head(10)
            
            if len(df_efec) > 0:
                fig_efec_bar = go.Figure()
                
                fig_efec_bar.add_trace(go.Bar(
                    x=df_efec['efectividad'],
                    y=df_efec['collector'],
                    orientation='h',
                    marker=dict(color=AMZ_SKY),
                    text=[fmt(v) for v in df_efec['efectividad']],
                    textposition='outside'
                ))
                
                fig_efec_bar.update_layout(
                    title="Top 10 por Efectividad ($/Act)",
                    xaxis_title="Efectividad ($)",
                    yaxis_title="",
                    height=400,
                    showlegend=False,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(l=150, r=50, t=50, b=50)
                )
                
                fig_efec_bar.update_yaxis(categoryorder='total ascending')
                
                st.plotly_chart(fig_efec_bar, use_container_width=True)
            else:
                st.info("ℹ️ No hay datos de efectividad disponibles")
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 3: TABLA DETALLADA
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📋 Tabla de Productividad Detallada")
    
    # Preparar tabla para display
    df_display = productivity.copy()
    
    df_display_formatted = pd.DataFrame({
        'Rank': df_display['rank'],
        'Collector': df_display['collector'],
        'Asignadas': df_display['cuentas_asignadas'].apply(fmt_num),
        'Gestionadas': df_display['cuentas_gestionadas'].apply(fmt_num),
        'Penetración': df_display['penetracion_pct'].apply(fmt_pct),
        'Actividades': df_display['total_actividades'].apply(fmt_num),
        'Cobrado': df_display['monto_cobrado'].apply(fmt),
        'Efectividad': df_display['efectividad'].apply(fmt),
        'Balance': df_display['balance_asignado'].apply(fmt)
    })
    
    st.dataframe(
        df_display_formatted,
        use_container_width=True,
        hide_index=True,
        height=500
    )
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 4: INSIGHTS Y ALERTAS
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 💡 Insights Automáticos")
    
    col_ins1, col_ins2 = st.columns(2)
    
    with col_ins1:
        st.markdown("**🎯 Mejores Performers**")
        
        # Top penetración
        top_penetracion = productivity.nlargest(3, 'penetracion_pct')
        st.success(f"""
        **Alta Penetración:**
        {chr(10).join([f"• {row['collector']}: {row['penetracion_pct']:.1f}%" 
                      for _, row in top_penetracion.iterrows()])}
        """)
        
        # Top efectividad
        top_efectividad = productivity[productivity['efectividad'] > 0].nlargest(3, 'efectividad')
        if len(top_efectividad) > 0:
            st.success(f"""
            **Alta Efectividad:**
            {chr(10).join([f"• {row['collector']}: {fmt(row['efectividad'])}/act" 
                          for _, row in top_efectividad.iterrows()])}
            """)
    
    with col_ins2:
        st.markdown("**⚠️ Áreas de Oportunidad**")
        
        # Baja penetración
        low_penetracion = productivity.nsmallest(3, 'penetracion_pct')
        st.warning(f"""
        **Baja Penetración:**
        {chr(10).join([f"• {row['collector']}: {row['penetracion_pct']:.1f}% ({row['cuentas_gestionadas']:.0f}/{row['cuentas_asignadas']:.0f})" 
                      for _, row in low_penetracion.iterrows()])}
        """)
        
        # Sin actividad reciente
        sin_actividad = productivity[productivity['total_actividades'] == 0]
        if len(sin_actividad) > 0:
            st.error(f"""
            **Sin Actividades:**
            {chr(10).join([f"• {row['collector']}: {row['cuentas_asignadas']:.0f} cuentas sin gestionar" 
                          for _, row in sin_actividad.head(3).iterrows()])}
            """)
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 5: EXPORTAR
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📥 Exportar Reporte")
    
    col_export1, col_export2 = st.columns([1, 3])
    
    with col_export1:
        if st.button("📊 Generar Excel", use_container_width=True, type="primary"):
            try:
                excel_data = export_productivity_report(
                    productivity,
                    filename=f"Productivity_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                )
                
                st.download_button(
                    label="⬇️ Descargar Reporte",
                    data=excel_data,
                    file_name=f"Productivity_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.success("✅ Reporte generado exitosamente")
                
            except Exception as e:
                st.error(f"❌ Error generando reporte: {str(e)}")
    
    with col_export2:
        st.info("""
        **El reporte incluye:**
        - Métricas de productividad completas por collector
        - Resumen ejecutivo con KPIs globales
        - Ranking por cobros, penetración y efectividad
        """)
