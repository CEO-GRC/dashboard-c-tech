"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QA Tab v2.0 — Management View
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Simple, dinámico, útil. No automatizaciones genéricas.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from qa_module_v2 import (
    clean_activities_file,
    merge_aging_with_activities,
    get_agent_portfolio,
    export_qa_report
)

# Colores Amrize
AMZ_MIDNIGHT = "#011E6A"
AMZ_SKY = "#00A7E1"
AMZ_ROYAL = "#0047AB"
S_GREEN = "#10B981"
S_RED = "#EF4444"
S_AMBER = "#F59E0B"

# Password de Management
DEFAULT_MGMT_PASSWORD = "MGMT2024"


def check_mgmt_password():
    """Verifica password de Management."""
    # Intentar desde secrets primero
    try:
        correct_pwd = st.secrets.get("MGMT_PASSWORD", DEFAULT_MGMT_PASSWORD)
    except:
        correct_pwd = DEFAULT_MGMT_PASSWORD
    
    if 'mgmt_authenticated' not in st.session_state:
        st.session_state.mgmt_authenticated = False
    
    if st.session_state.mgmt_authenticated:
        return True
    
    # Mostrar login
    st.markdown(f"""
    <div style='text-align:center;padding:2rem;background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                border-radius:12px;margin:2rem 0'>
        <h2 style='color:white;margin-bottom:0.5rem'>🔐 Management Access</h2>
        <p style='color:{AMZ_SKY};font-size:0.9rem'>Ingrese password de gerencia para continuar</p>
    </div>
    """, unsafe_allow_html=True)
    
    pwd_input = st.text_input("Password de Management:", type="password", key="mgmt_pwd_input")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔓 Acceder", use_container_width=True):
            if pwd_input.strip() == correct_pwd:
                st.session_state.mgmt_authenticated = True
                st.rerun()
            else:
                st.error("❌ Password incorrecto")
    
    return False


def render_qa_tab(df_aging):
    """
    Renderiza el Tab 6 - Management & QA.
    
    Args:
        df_aging: DataFrame del Aging (del dashboard principal)
    """
    # Verificar autenticación
    if not check_mgmt_password():
        return
    
    # Header
    st.markdown(f"""
    <div style='background:linear-gradient(90deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                padding:1.5rem;border-radius:12px;margin-bottom:2rem'>
        <h1 style='color:white;margin:0;font-size:1.8rem'>🔐 Management & QA Review</h1>
        <p style='color:{AMZ_SKY};margin:0.5rem 0 0 0'>
            Análisis dinámico de cartera y actividades de agentes
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar que haya Aging data
    if df_aging is None or len(df_aging) == 0:
        st.warning("⚠️ No hay datos de Aging cargados. Por favor cargue el Aging en Tab 1 primero.")
        return
    
    # Upload de actividades
    st.markdown("### 📤 Upload Archivo de Actividades")
    
    uploaded_file = st.file_uploader(
        "Suba su archivo de actividades (.xlsx, .csv)",
        type=['xlsx', 'xls', 'csv'],
        help="Debe contener: User (agente), Date, Customer Number, History"
    )
    
    if uploaded_file is None:
        st.info("👆 Suba el archivo de actividades para comenzar el análisis")
        return
    
    # Procesar archivo
    try:
        with st.spinner("📊 Procesando archivo..."):
            # Leer archivo
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)
            
            # Limpiar
            df_activities = clean_activities_file(df_raw)
            
            # Merge con Aging
            df_merged = merge_aging_with_activities(df_aging, df_activities)
        
        st.success(f"✅ Archivo procesado: {len(df_activities):,} actividades | {df_activities['agent'].nunique()} agentes")
        
    except Exception as e:
        st.error(f"❌ Error procesando archivo: {e}")
        st.info("Verifique que el archivo tenga las columnas: User, Date, Customer Number")
        return
    
    # Guardar en session state
    st.session_state.qa_activities = df_activities
    st.session_state.qa_merged = df_merged
    
    st.markdown("---")
    
    # ========================================================================
    # FILTROS
    # ========================================================================
    
    st.markdown("### 🔍 Filtros de Análisis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro de agente
        agents = ['📊 Todos los agentes'] + sorted(df_activities['agent'].unique().tolist())
        selected_agent = st.selectbox("Agente:", agents)
    
    with col2:
        # Filtro de top N cuentas
        top_n = st.selectbox("Mostrar Top:", [5, 10, 20, 50, 100], index=0)
    
    with col3:
        # Filtro de estado
        status_filter = st.selectbox(
            "Estado:",
            ['Todas', 'Solo con actividad', 'Solo sin actividad']
        )
    
    # ========================================================================
    # ANÁLISIS: TOP CUENTAS
    # ========================================================================
    
    st.markdown("---")
    st.markdown(f"### 💰 Top {top_n} Cuentas por Balance")
    
    # Filtrar data
    if selected_agent != '📊 Todos los agentes':
        # Obtener portfolio de ese agente
        df_view = get_agent_portfolio(df_merged, df_activities, selected_agent)
        st.info(f"👤 Mostrando portfolio de **{selected_agent}**: {len(df_view)} cuentas tocadas")
    else:
        df_view = df_merged.copy()
    
    # Aplicar filtro de estado
    if status_filter == 'Solo con actividad':
        df_view = df_view[df_view['was_touched'] == True]
    elif status_filter == 'Solo sin actividad':
        df_view = df_view[df_view['was_touched'] == False]
    
    # Ordenar por balance y tomar top N
    # Buscar columna de balance
    balance_col = None
    for col in df_view.columns:
        if 'balance' in str(col).lower() or 'total' in str(col).lower():
            balance_col = col
            break
    
    if balance_col is None:
        # Asumir que es la segunda columna (después de customer)
        balance_col = df_view.columns[1]
    
    df_view = df_view.sort_values(balance_col, ascending=False).head(top_n)
    
    # ========================================================================
    # TABLA INTERACTIVA CON DETALLES
    # ========================================================================
    
    if 'qa_comments' not in st.session_state:
        st.session_state.qa_comments = {}
    
    for idx, row in df_view.iterrows():
        customer = row['customer_number']
        company = row.get('company', row.get('Company', 'N/A'))
        balance = row[balance_col]
        
        # Indicador visual de si fue tocada
        if row['was_touched']:
            status_icon = "✅"
            status_color = S_GREEN
            status_text = "CON ACTIVIDAD"
        else:
            status_icon = "⚠️"
            status_color = S_RED
            status_text = "SIN ACTIVIDAD"
        
        # Card expandible
        with st.expander(
            f"{status_icon} **{company}** | ${balance:,.2f} | {status_text}",
            expanded=False
        ):
            # Info básica
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Customer #", customer)
            with c2:
                if row['was_touched']:
                    st.metric("Total Actividades", int(row['total_activities']))
                else:
                    st.metric("Total Actividades", "0", delta="Sin gestión", delta_color="inverse")
            with c3:
                if row['was_touched']:
                    days_ago = int(row['days_since_activity'])
                    st.metric("Última Actividad", f"Hace {days_ago}d")
                else:
                    st.metric("Última Actividad", "Nunca")
            
            # Mostrar agentes asignados
            if row['was_touched']:
                st.markdown(f"**👥 Agentes:** {row['agents_assigned']}")
            
            # Mostrar historial completo
            if row['was_touched']:
                st.markdown("**📝 Historial de Actividades:**")
                
                # Obtener todas las actividades de esta cuenta
                customer_acts = df_activities[
                    df_activities['customer_number'] == customer
                ].sort_values('date', ascending=False)
                
                for _, act in customer_acts.iterrows():
                    date_str = act['date'].strftime('%Y-%m-%d')
                    agent = act['agent']
                    history = act.get('history', 'N/A')
                    
                    st.markdown(f"""
                    <div style='background:#f8f9fa;padding:0.8rem;border-radius:6px;margin:0.5rem 0;
                                border-left:3px solid {AMZ_SKY}'>
                        <div style='font-size:0.85rem;color:#6c757d;margin-bottom:0.3rem'>
                            📅 {date_str} | 👤 {agent}
                        </div>
                        <div style='font-size:0.95rem;color:#212529'>
                            {history}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("🚨 Esta cuenta NO tiene ninguna actividad registrada")
            
            # Campo de comentarios QA (editable)
            st.markdown("---")
            st.markdown("**✍️ Tu Comentario de QA:**")
            
            comment_key = f"qa_comment_{customer}"
            existing_comment = st.session_state.qa_comments.get(customer, '')
            
            new_comment = st.text_area(
                "Escribe tu análisis/perspectiva sobre esta cuenta:",
                value=existing_comment,
                height=100,
                key=comment_key,
                placeholder="Ej: El agente ha hecho seguimiento pero falta escalamiento. Cliente no responde emails."
            )
            
            # Guardar comentario
            if new_comment != existing_comment:
                st.session_state.qa_comments[customer] = new_comment
    
    # ========================================================================
    # RESUMEN Y EXPORTACIÓN
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 📊 Resumen General")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_accounts = len(df_view)
        st.metric("Total Cuentas Analizadas", total_accounts)
    
    with col2:
        touched = df_view['was_touched'].sum()
        pct_touched = (touched / total_accounts * 100) if total_accounts > 0 else 0
        st.metric("Con Actividad", touched, delta=f"{pct_touched:.1f}%")
    
    with col3:
        not_touched = total_accounts - touched
        pct_not_touched = (not_touched / total_accounts * 100) if total_accounts > 0 else 0
        st.metric("Sin Actividad", not_touched, delta=f"{pct_not_touched:.1f}%", delta_color="inverse")
    
    with col4:
        total_balance = df_view[balance_col].sum()
        st.metric("Balance Total", f"${total_balance:,.0f}")
    
    # Gráfico simple
    if total_accounts > 0:
        st.markdown("**Distribución de Gestión:**")
        
        fig = go.Figure(data=[
            go.Bar(
                x=['Con Actividad', 'Sin Actividad'],
                y=[touched, not_touched],
                marker_color=[S_GREEN, S_RED],
                text=[f"{touched}<br>({pct_touched:.1f}%)", 
                      f"{not_touched}<br>({pct_not_touched:.1f}%)"],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis_title="# Cuentas",
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Exportar
    st.markdown("---")
    st.markdown("### 📥 Exportar Reporte QA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Descargar Excel con Comentarios", use_container_width=True):
            try:
                excel_file = export_qa_report(
                    df_view,
                    st.session_state.qa_comments,
                    "QA_Report"
                )
                
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel_file,
                    file_name=f"QA_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generando Excel: {e}")
    
    with col2:
        # Resumen de comentarios
        total_comments = len([c for c in st.session_state.qa_comments.values() if c.strip()])
        st.info(f"✍️ Has escrito **{total_comments}** comentario(s) de QA")
