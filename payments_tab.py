"""Payments Tab v1.0 - UI Component"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from payments_module import (
    load_payments_from_aging,
    calculate_payment_metrics,
    export_payments_report
)

# Colores Amrize
AMZ_MIDNIGHT = "#011E6A"
AMZ_SKY = "#00A7E1"
AMZ_ROYAL = "#0047AB"
S_GREEN = "#059669"
S_RED = "#DC2626"
S_AMBER = "#D97706"
S_YELLOW = "#F59E0B"


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


def render_payments_tab(uploaded_file, total_ar):
    """
    Render del tab de Payments.
    
    Args:
        uploaded_file: Archivo subido (mismo que el Aging)
        total_ar: Total AR del portfolio
    """
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                padding:2rem;border-radius:12px;margin-bottom:2rem'>
        <h1 style='color:white;margin:0;font-size:1.8rem'>💰 Payments Analysis</h1>
        <p style='color:{AMZ_SKY};margin:0.5rem 0 0'>Análisis de cobros por collector</p>
    </div>
    """, unsafe_allow_html=True)
    
    if uploaded_file is None:
        st.warning("⚠️ No hay archivo cargado. Por favor suba un archivo en la pestaña Overview.")
        return
    
    # Cargar datos de pagos
    try:
        with st.spinner("🔄 Cargando datos de pagos..."):
            # Leer el archivo de nuevo para obtener Sheet3
            file_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, 'getvalue') else uploaded_file.read()
            
            df_payments = load_payments_from_aging(file_bytes, sheet_name='Sheet3')
            
        if len(df_payments) == 0:
            st.warning("⚠️ No se encontraron datos de pagos en Sheet3.")
            return
            
        # Calcular métricas
        metrics = calculate_payment_metrics(df_payments, total_ar)
        
        st.success(f"✅ **{len(df_payments)} collectors** | **{fmt(metrics['total_collected'])} cobrados**")
        
    except Exception as e:
        st.error(f"❌ Error cargando pagos: {str(e)}")
        st.info("""
        **Nota:** Asegúrese de que:
        - El archivo tenga una hoja llamada 'Sheet3'
        - Contenga columnas 'Row Labels' y 'Sum of Amount in local currency'
        """)
        return
    
    # Guardar en session_state
    st.session_state.payments_data = df_payments
    st.session_state.payments_metrics = metrics
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 1: KPIs PRINCIPALES
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📊 Resumen General")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric(
            "💵 Total Cobrado",
            fmt(metrics['total_collected'])
        )
    
    with c2:
        st.metric(
            "📈 % del AR Total",
            fmt_pct(metrics['pct_of_ar']),
            delta=f"{fmt_pct(metrics['pct_of_ar'])} del portfolio"
        )
    
    with c3:
        st.metric(
            "👥 Collectors Activos",
            metrics['num_collectors']
        )
    
    with c4:
        st.metric(
            "📊 Promedio/Collector",
            fmt(metrics['avg_per_collector'])
        )
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 2: GRÁFICAS
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📈 Visualizaciones")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Gráfica de barras - Top 10
        df_top10 = metrics['df_ranking'].head(10).copy()
        
        fig_bar = go.Figure()
        
        # Gradiente de colores basado en ranking
        colors = []
        for i, _ in enumerate(df_top10.iterrows()):
            if i == 0:
                colors.append(S_GREEN)
            elif i < 3:
                colors.append(AMZ_SKY)
            elif i < 5:
                colors.append(AMZ_ROYAL)
            else:
                colors.append(S_AMBER)
        
        fig_bar.add_trace(go.Bar(
            x=df_top10['amount'],
            y=df_top10['collector'],
            orientation='h',
            marker=dict(color=colors),
            text=[fmt(v) for v in df_top10['amount']],
            textposition='outside',
            textfont=dict(size=10)
        ))
        
        fig_bar.update_layout(
            title="Top 10 Collectors por Monto Cobrado",
            xaxis_title="Monto ($)",
            yaxis_title="",
            height=400,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=11),
            margin=dict(l=150, r=50, t=50, b=50)
        )
        
        fig_bar.update_yaxis(categoryorder='total ascending')
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_right:
        # Pie chart - Distribución % del total cobrado
        df_top5 = metrics['df_ranking'].head(5).copy()
        others_amount = metrics['df_ranking'].iloc[5:]['amount'].sum() if len(metrics['df_ranking']) > 5 else 0
        
        labels = df_top5['collector'].tolist()
        values = df_top5['amount'].tolist()
        
        if others_amount > 0:
            labels.append('Otros')
            values.append(others_amount)
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(
                colors=[S_GREEN, AMZ_SKY, AMZ_ROYAL, S_AMBER, S_YELLOW, '#9CA3AF']
            ),
            textinfo='label+percent',
            textfont=dict(size=10)
        )])
        
        fig_pie.update_layout(
            title="Distribución de Cobros (Top 5 + Otros)",
            height=400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=11)
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 3: RANKING COMPLETO
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 🏆 Ranking de Collectors")
    
    # Crear tabla formateada para display
    df_display = metrics['df_ranking'].copy()
    
    # Formatear para mostrar
    df_display['rank_display'] = df_display['rank'].apply(lambda x: f"#{x}")
    df_display['amount_display'] = df_display['amount'].apply(fmt)
    df_display['pct_total_display'] = df_display['pct_of_total'].apply(fmt_pct)
    df_display['pct_ar_display'] = df_display['pct_of_ar'].apply(fmt_pct)
    
    # Seleccionar y renombrar columnas para display
    df_show = df_display[[
        'rank_display',
        'collector',
        'amount_display',
        'pct_total_display',
        'pct_ar_display'
    ]].copy()
    
    df_show.columns = ['Rank', 'Collector', 'Monto Cobrado', '% del Total', '% del AR']
    
    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 4: EXPORTAR
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📥 Exportar Reporte")
    
    col_export1, col_export2 = st.columns([1, 3])
    
    with col_export1:
        if st.button("📄 Generar Excel", use_container_width=True, type="primary"):
            try:
                excel_data = export_payments_report(
                    metrics['df_ranking'],
                    metrics
                )
                
                st.download_button(
                    label="⬇️ Descargar Reporte",
                    data=excel_data,
                    file_name=f"Payments_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.success("✅ Reporte generado exitosamente")
                
            except Exception as e:
                st.error(f"❌ Error generando reporte: {str(e)}")
    
    with col_export2:
        st.info("""
        **El reporte incluye:**
        - Ranking completo de collectors
        - Métricas generales
        - Distribución de cobros
        """)
