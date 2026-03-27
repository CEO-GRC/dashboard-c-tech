"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QA Tab v2.1 — Fixed, Robust & Professional
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from qa_module_v2_fixed import (
    clean_activities_file,
    merge_aging_with_activities,
    get_agent_portfolio,
    export_qa_report
)

# ========================================================================
# COLORES - Funcionan en LIGHT y DARK mode
# ========================================================================

# Amrize Brand Colors
AMZ_MIDNIGHT = "#011E6A"
AMZ_SKY = "#00A7E1"
AMZ_ROYAL = "#0047AB"

# Status Colors (más saturados para mejor contraste)
S_GREEN = "#059669"      # Verde más oscuro
S_RED = "#DC2626"        # Rojo más oscuro
S_AMBER = "#D97706"      # Ámbar más oscuro
S_GRAY = "#6B7280"       # Gris neutro

# Backgrounds adaptivos
def get_card_bg():
    """Retorna color de fondo para cards según tema."""
    # Streamlit detecta tema automáticamente
    return "rgba(255, 255, 255, 0.05)"  # Funciona en ambos modos

def get_border_color():
    """Retorna color de borde según tema."""
    return "rgba(100, 116, 139, 0.2)"

def get_text_color():
    """Retorna color de texto principal."""
    return "#1F2937"  # Gris oscuro para light, se ve bien en dark también


# Password de Management
DEFAULT_MGMT_PASSWORD = "MGMT2024"


def check_mgmt_password():
    """Verifica password de Management."""
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
    <div style='text-align:center;padding:2.5rem;
                background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                border-radius:16px;margin:2rem auto;max-width:500px;
                box-shadow:0 10px 40px rgba(1,30,106,0.3)'>
        <div style='font-size:3rem;margin-bottom:1rem'>🔐</div>
        <h2 style='color:white;margin-bottom:0.5rem;font-weight:700'>Management Access</h2>
        <p style='color:{AMZ_SKY};font-size:0.95rem;margin:0'>
            Ingrese password de gerencia para continuar
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    pwd_input = st.text_input(
        "Password de Management:", 
        type="password", 
        key="mgmt_pwd_input",
        placeholder="Ingrese password..."
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔓 Acceder", use_container_width=True, type="primary"):
            if pwd_input.strip() == correct_pwd:
                st.session_state.mgmt_authenticated = True
                st.rerun()
            else:
                st.error("❌ Password incorrecto")
    
    return False


def format_currency(value):
    """Formatea valores monetarios."""
    try:
        return f"${float(value):,.2f}"
    except:
        return "$0.00"


def render_qa_tab(df_aging):
    """
    Renderiza el Tab 4 - Management & QA.
    FIXED & ROBUST version.
    """
    # Verificar autenticación
    if not check_mgmt_password():
        return
    
    # ========================================================================
    # HEADER
    # ========================================================================
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AMZ_MIDNIGHT} 0%,{AMZ_ROYAL} 100%);
                padding:2rem 2.5rem;border-radius:16px;margin-bottom:2rem;
                box-shadow:0 4px 20px rgba(1,30,106,0.2)'>
        <div style='display:flex;align-items:center;gap:1rem'>
            <div style='font-size:2.5rem'>🔐</div>
            <div>
                <h1 style='color:white;margin:0;font-size:2rem;font-weight:700;letter-spacing:-0.02em'>
                    Management & QA Review
                </h1>
                <p style='color:{AMZ_SKY};margin:0.5rem 0 0 0;font-size:1rem'>
                    Análisis dinámico de cartera y actividades de agentes
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar que haya Aging data
    if df_aging is None or len(df_aging) == 0:
        st.warning("⚠️ No hay datos de Aging cargados. Por favor cargue el Aging en Tab 1 primero.")
        return
    
    # ========================================================================
    # UPLOAD DE ACTIVIDADES
    # ========================================================================
    
    st.markdown("### 📤 Cargar Archivo de Actividades")
    st.markdown("""
    <div style='background:rgba(0,167,225,0.1);border-left:4px solid #00A7E1;
                padding:1rem 1.5rem;border-radius:8px;margin-bottom:1.5rem'>
        <strong>Formato requerido:</strong> Excel (.xlsx, .xls) o CSV con columnas: 
        <code>User</code>, <code>Date</code>, <code>Customer Number</code>, <code>History</code>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Seleccione archivo",
        type=['xlsx', 'xls', 'csv'],
        help="El archivo debe contener actividades de gestión de agentes",
        label_visibility="collapsed"
    )
    
    if uploaded_file is None:
        st.info("👆 Suba el archivo de actividades para comenzar el análisis")
        return
    
    # ========================================================================
    # PROCESAR ARCHIVO - ROBUSTO
    # ========================================================================
    
    try:
        with st.spinner("📊 Procesando archivo..."):
            # Leer archivo
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)
            
            # Limpiar con función ROBUSTA
            df_activities = clean_activities_file(df_raw)
            
            # Merge con Aging - auto-detecta columnas
            df_merged = merge_aging_with_activities(df_aging, df_activities)
        
        # Mostrar confirmación
        st.success(f"""
        ✅ **Archivo procesado exitosamente**  
        📊 {len(df_activities):,} actividades | 👥 {df_activities['agent'].nunique()} agentes | 
        🏢 {df_activities['customer_number'].nunique()} clientes únicos
        """)
        
    except Exception as e:
        st.error(f"❌ **Error procesando archivo:** {str(e)}")
        st.info("""
        **Verifique:**
        - El archivo tiene las columnas: `User`, `Date`, `Customer Number`
        - Las fechas están en formato válido
        - No hay filas completamente vacías
        """)
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
        agents = ['📊 Todos los agentes'] + sorted(df_activities['agent'].unique().tolist())
        selected_agent = st.selectbox(
            "👤 Agente:",
            agents,
            help="Filtrar por agente específico o ver todos"
        )
    
    with col2:
        top_n = st.selectbox(
            "🔝 Mostrar Top:",
            [5, 10, 20, 50, 100],
            index=0,
            help="Cantidad de cuentas principales a mostrar"
        )
    
    with col3:
        status_filter = st.selectbox(
            "📊 Estado:",
            ['Todas', 'Solo con actividad', 'Solo sin actividad'],
            help="Filtrar por estado de gestión"
        )
    
    # ========================================================================
    # FILTRAR DATA
    # ========================================================================
    
    if selected_agent != '📊 Todos los agentes':
        df_view = get_agent_portfolio(df_merged, df_activities, selected_agent)
        st.info(f"👤 **Portfolio de {selected_agent}:** {len(df_view)} cuentas gestionadas")
    else:
        df_view = df_merged.copy()
    
    # Aplicar filtro de estado
    if status_filter == 'Solo con actividad':
        df_view = df_view[df_view['was_touched'] == True]
    elif status_filter == 'Solo sin actividad':
        df_view = df_view[df_view['was_touched'] == False]
    
    # Ordenar por balance y tomar top N
    if 'balance' in df_view.columns:
        df_view = df_view.sort_values('balance', ascending=False).head(top_n)
    else:
        df_view = df_view.head(top_n)
    
    if len(df_view) == 0:
        st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados")
        return
    
    st.markdown("---")
    
    # ========================================================================
    # TABLA PRINCIPAL - PROFESIONAL Y CLARA
    # ========================================================================
    
    st.markdown(f"### 💰 Top {len(df_view)} Cuentas por Balance")
    
    # Preparar datos para tabla
    table_data = []
    for idx, row in df_view.iterrows():
        customer = row.get('customer_number', 'N/A')
        collector = row.get('collector', 'No asignado')
        company = row.get('company', 'N/A')
        balance = row.get('balance', 0)
        days = row.get('days_overdue', 'N/A')
        status = row['activity_status']
        total_acts = int(row.get('total_activities', 0))
        
        table_data.append({
            'Collector': collector,
            'Customer #': customer,
            'Company': company,
            'Past Due': format_currency(balance),
            'Days OD': days,
            'Status': status,
            'Activities': total_acts
        })
    
    # Crear DataFrame para tabla
    df_table = pd.DataFrame(table_data)
    
    # Mostrar tabla con estilo
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.markdown("---")
    
    # ========================================================================
    # DETALLES EXPANDIBLES
    # ========================================================================
    
    st.markdown("### 📋 Detalle por Cuenta")
    st.markdown("*Click en una cuenta para ver el historial completo y agregar comentarios de QA*")
    
    if 'qa_comments' not in st.session_state:
        st.session_state.qa_comments = {}
    
    for idx, row in df_view.iterrows():
        customer = row['customer_number']
        company = row.get('company', 'N/A')
        collector = row.get('collector', 'No asignado')
        balance = row.get('balance', 0)
        days_od = row.get('days_overdue', 'N/A')
        
        # Icon y color según estado
        if row['was_touched']:
            icon = "✅"
            color = S_GREEN
        else:
            icon = "⚠️"
            color = S_RED
        
        # Card expandible
        with st.expander(
            f"{icon} **{company}** • {customer} • {format_currency(balance)}",
            expanded=False
        ):
            # Header info
            st.markdown(f"""
            <div style='background:{get_card_bg()};padding:1.5rem;border-radius:12px;
                        border:1px solid {get_border_color()};margin-bottom:1.5rem'>
                <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.5rem'>
                    <div>
                        <div style='font-size:0.75rem;color:{S_GRAY};text-transform:uppercase;
                                    letter-spacing:0.05em;margin-bottom:0.25rem'>Collector</div>
                        <div style='font-size:1.1rem;font-weight:600'>{collector}</div>
                    </div>
                    <div>
                        <div style='font-size:0.75rem;color:{S_GRAY};text-transform:uppercase;
                                    letter-spacing:0.05em;margin-bottom:0.25rem'>Customer #</div>
                        <div style='font-size:1.1rem;font-weight:600'>{customer}</div>
                    </div>
                    <div>
                        <div style='font-size:0.75rem;color:{S_GRAY};text-transform:uppercase;
                                    letter-spacing:0.05em;margin-bottom:0.25rem'>Balance</div>
                        <div style='font-size:1.1rem;font-weight:600;color:{AMZ_SKY}'>
                            {format_currency(balance)}
                        </div>
                    </div>
                    <div>
                        <div style='font-size:0.75rem;color:{S_GRAY};text-transform:uppercase;
                                    letter-spacing:0.05em;margin-bottom:0.25rem'>Days Overdue</div>
                        <div style='font-size:1.1rem;font-weight:600;color:{S_AMBER}'>{days_od}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Métricas de actividad
            c1, c2, c3 = st.columns(3)
            with c1:
                total_acts = int(row.get('total_activities', 0))
                if row['was_touched']:
                    st.metric("Total Actividades", total_acts)
                else:
                    st.metric("Total Actividades", "0", delta="Sin gestión", delta_color="inverse")
            
            with c2:
                if row['was_touched']:
                    days_ago = int(row['days_since_activity'])
                    st.metric("Última Actividad", f"Hace {days_ago}d")
                else:
                    st.metric("Última Actividad", "Nunca")
            
            with c3:
                if row['was_touched']:
                    agents = row.get('agents_assigned', 'N/A')
                    st.metric("Agentes Asignados", agents.count(',') + 1 if ',' in agents else 1)
                else:
                    st.metric("Agentes Asignados", "0")
            
            # Historial completo
            if row['was_touched']:
                st.markdown("**📝 Historial Completo de Actividades:**")
                
                # Obtener actividades de esta cuenta
                customer_acts = df_activities[
                    df_activities['customer_number'] == customer
                ].sort_values('date', ascending=False)
                
                for act_idx, act in customer_acts.iterrows():
                    date_str = act['date'].strftime('%Y-%m-%d %H:%M')
                    agent = act['agent']
                    history = act.get('history', 'N/A')
                    
                    # Truncar historial muy largo
                    if len(history) > 500:
                        history = history[:500] + "..."
                    
                    st.markdown(f"""
                    <div style='background:rgba(0,167,225,0.05);padding:1rem;
                                border-radius:8px;margin:0.5rem 0;
                                border-left:3px solid {AMZ_SKY}'>
                        <div style='display:flex;justify-content:space-between;align-items:center;
                                    margin-bottom:0.5rem'>
                            <span style='font-size:0.85rem;color:{S_GRAY};font-weight:600'>
                                📅 {date_str}
                            </span>
                            <span style='font-size:0.85rem;color:{AMZ_ROYAL};font-weight:600'>
                                👤 {agent}
                            </span>
                        </div>
                        <div style='font-size:0.95rem;line-height:1.5;color:{get_text_color()}'>
                            {history}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("🚨 **Esta cuenta NO tiene ninguna actividad registrada**")
            
            # Campo de comentarios QA
            st.markdown("---")
            st.markdown("**✍️ Comentario de QA (Management):**")
            
            comment_key = f"qa_comment_{customer}_{idx}"
            existing_comment = st.session_state.qa_comments.get(customer, '')
            
            new_comment = st.text_area(
                "Escribe tu análisis/perspectiva:",
                value=existing_comment,
                height=120,
                key=comment_key,
                placeholder="Ejemplo: Seguimiento adecuado pero falta escalamiento. Cliente no responde emails, considerar llamada directa.",
                label_visibility="collapsed"
            )
            
            # Guardar comentario
            if new_comment != existing_comment:
                st.session_state.qa_comments[customer] = new_comment
    
    # ========================================================================
    # RESUMEN Y EXPORTACIÓN
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 📊 Resumen del Análisis")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_accounts = len(df_view)
    touched = df_view['was_touched'].sum()
    not_touched = total_accounts - touched
    total_balance = df_view.get('balance', pd.Series([0])).sum()
    
    pct_touched = (touched / total_accounts * 100) if total_accounts > 0 else 0
    pct_not_touched = (not_touched / total_accounts * 100) if total_accounts > 0 else 0
    
    with col1:
        st.metric("Total Cuentas", total_accounts)
    
    with col2:
        st.metric("Con Actividad", touched, delta=f"{pct_touched:.1f}%")
    
    with col3:
        st.metric("Sin Actividad", not_touched, delta=f"{pct_not_touched:.1f}%", delta_color="inverse")
    
    with col4:
        st.metric("Balance Total", format_currency(total_balance))
    
    # Gráfico simple de distribución
    if total_accounts > 0:
        st.markdown("**📈 Distribución de Gestión:**")
        
        fig = go.Figure(data=[
            go.Bar(
                x=['Con Actividad', 'Sin Actividad'],
                y=[touched, not_touched],
                marker_color=[S_GREEN, S_RED],
                text=[f"{touched}<br>({pct_touched:.1f}%)", 
                      f"{not_touched}<br>({pct_not_touched:.1f}%)"],
                textposition='auto',
                textfont=dict(size=14, color='white', family='Arial Black')
            )
        ])
        
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis_title="Número de Cuentas",
            xaxis_title="",
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title=dict(
                text="Distribución de Gestión por Estado",
                font=dict(size=16, color=AMZ_MIDNIGHT)
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # EXPORTACIÓN
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 📥 Exportar Reporte de QA")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("📊 Generar y Descargar Excel con Comentarios", 
                    use_container_width=True, type="primary"):
            try:
                with st.spinner("Generando reporte..."):
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
                
                st.success("✅ Reporte generado exitosamente")
                
            except Exception as e:
                st.error(f"❌ Error generando Excel: {str(e)}")
                st.info("Intente nuevamente o contacte soporte técnico")
    
    with col2:
        total_comments = len([c for c in st.session_state.qa_comments.values() if c.strip()])
        st.info(f"""
        **✍️ Comentarios escritos:**  
        {total_comments} de {total_accounts}
        """)
