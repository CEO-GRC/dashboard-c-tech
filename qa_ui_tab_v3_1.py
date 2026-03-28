"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QA Tab v3.1 — Dual matching + Shows match method
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from qa_module_v3_1 import (
    clean_activities_file,
    merge_aging_with_activities,
    get_multi_agent_portfolio,
    export_qa_report
)

# Colores
AMZ_MIDNIGHT = "#011E6A"
AMZ_SKY = "#00A7E1"
AMZ_ROYAL = "#0047AB"
S_GREEN = "#059669"
S_RED = "#DC2626"
S_AMBER = "#D97706"
S_GRAY = "#6B7280"

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
    
    st.markdown(f"""
    <div style='text-align:center;padding:2.5rem;
                background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                border-radius:16px;margin:2rem auto;max-width:500px;
                box-shadow:0 10px 40px rgba(1,30,106,0.3)'>
        <div style='font-size:3rem;margin-bottom:1rem'>🔐</div>
        <h2 style='color:white;margin-bottom:0.5rem;font-weight:700'>Management Access</h2>
        <p style='color:{AMZ_SKY};font-size:0.95rem;margin:0'>
            Ingrese password de gerencia
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    pwd_input = st.text_input("Password:", type="password", key="mgmt_pwd_input")
    
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
    """Renderiza el Tab 4 - Management & QA v3.1."""
    
    if not check_mgmt_password():
        return
    
    # Header
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
                    Análisis dinámico con dual matching (Customer # + Company)
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if df_aging is None or len(df_aging) == 0:
        st.warning("⚠️ No hay datos de Aging. Cargue el Aging en Tab 1 primero.")
        return
    
    # Upload
    st.markdown("### 📤 Cargar Archivo de Actividades")
    
    uploaded_file = st.file_uploader(
        "Excel o CSV con: User, Date, Company y/o Customer Number",
        type=['xlsx', 'xls', 'csv'],
        label_visibility="collapsed"
    )
    
    if uploaded_file is None:
        st.info("👆 Suba el archivo de actividades para comenzar")
        return
    
    # Procesar
    try:
        with st.spinner("📊 Procesando..."):
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)
            
            df_activities = clean_activities_file(df_raw)
            df_merged = merge_aging_with_activities(df_aging, df_activities)
        
        # Mostrar método de matching usado
        match_method = df_merged['_match_method'].iloc[0] if '_match_method' in df_merged.columns else 'Unknown'
        
        if match_method == 'Customer Number':
            st.success(f"""
            ✅ **Procesado exitosamente** | {len(df_activities):,} actividades | 
            {df_activities['agent'].nunique()} agentes | 
            🔗 **Matching:** Customer Number (recomendado)
            """)
        else:
            st.success(f"""
            ✅ **Procesado exitosamente** | {len(df_activities):,} actividades | 
            {df_activities['agent'].nunique()} agentes | 
            🔗 **Matching:** Company Name (fallback)
            """)
            st.info("💡 Para mejor precisión, asegúrese que ambos archivos tengan Customer Number con el mismo formato")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("Verifique que el archivo tenga: User, Date, y Company o Customer Number")
        return
    
    st.session_state.qa_activities = df_activities
    st.session_state.qa_merged = df_merged
    
    st.markdown("---")
    
    # ========================================================================
    # FILTROS
    # ========================================================================
    
    st.markdown("### 🔍 Filtros de Análisis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        all_agents = sorted(df_activities['agent'].unique().tolist())
        
        st.markdown("**👥 Agentes:**")
        select_all = st.checkbox("✓ Seleccionar todos", value=True, key="select_all_agents")
        
        if select_all:
            selected_agents = ['📊 Todos los agentes']
        else:
            selected_agents = st.multiselect(
                "Seleccione agentes:",
                all_agents,
                default=[],
                label_visibility="collapsed"
            )
            
            if not selected_agents:
                selected_agents = ['📊 Todos los agentes']
    
    with col2:
        top_n = st.selectbox(
            "🔝 Mostrar Top:",
            [5, 10, 20, 50, 100, 200],
            index=0
        )
    
    with col3:
        status_filter = st.selectbox(
            "📊 Estado:",
            ['Todas', 'Solo con actividad', 'Solo sin actividad']
        )
    
    # Filtrar
    if '📊 Todos los agentes' not in selected_agents and selected_agents:
        df_view = get_multi_agent_portfolio(df_merged, df_activities, selected_agents)
        st.info(f"👥 **{len(selected_agents)} agente(s) seleccionado(s):** {', '.join(selected_agents)}")
    else:
        df_view = df_merged.copy()
    
    if status_filter == 'Solo con actividad':
        df_view = df_view[df_view['was_touched'] == True]
    elif status_filter == 'Solo sin actividad':
        df_view = df_view[df_view['was_touched'] == False]
    
    if 'balance' in df_view.columns:
        df_view = df_view.sort_values('balance', ascending=False).head(top_n)
    else:
        df_view = df_view.head(top_n)
    
    if len(df_view) == 0:
        st.warning("⚠️ No hay datos con estos filtros")
        return
    
    st.markdown("---")
    
    # ========================================================================
    # TABLA PRINCIPAL
    # ========================================================================
    
    st.markdown(f"### 💰 Top {len(df_view)} Cuentas por Balance")
    
    table_data = []
    for idx, row in df_view.iterrows():
        collector = row.get('collector', 'No asignado')
        customer = row.get('customer_number', 'N/A')
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
    
    df_table = pd.DataFrame(table_data)
    
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
        height=min(400, len(df_table) * 35 + 38)
    )
    
    st.markdown("---")
    
    # ========================================================================
    # DETALLE POR CUENTA
    # ========================================================================
    
    st.markdown("### 📋 Detalle por Cuenta")
    
    if 'qa_comments' not in st.session_state:
        st.session_state.qa_comments = {}
    
    # Determinar match key para buscar actividades
    match_key = None
    if 'customer_clean' in df_view.columns and 'customer_clean' in df_activities.columns:
        match_key = 'customer_clean'
        match_label = 'customer_number'
    elif 'company_clean' in df_view.columns and 'company_clean' in df_activities.columns:
        match_key = 'company_clean'
        match_label = 'company'
    
    for idx, row in df_view.iterrows():
        company = row.get('company', 'N/A')
        collector = row.get('collector', 'No asignado')
        customer = row.get('customer_number', 'N/A')
        balance = row.get('balance', 0)
        days_od = row.get('days_overdue', 'N/A')
        
        icon = "✅" if row['was_touched'] else "⚠️"
        
        with st.expander(
            f"{icon} **{company}** • Cust# {customer} • {format_currency(balance)}",
            expanded=False
        ):
            # Info básica
            st.markdown(f"""
            <div style='background:rgba(0,167,225,0.05);padding:1.5rem;border-radius:12px;
                        border:1px solid rgba(100,116,139,0.2);margin-bottom:1.5rem'>
                <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1.5rem'>
                    <div>
                        <div style='font-size:0.75rem;color:{S_GRAY};text-transform:uppercase;
                                    letter-spacing:0.05em;margin-bottom:0.25rem'>Company</div>
                        <div style='font-size:1.1rem;font-weight:600'>{company}</div>
                    </div>
                    <div>
                        <div style='font-size:0.75rem;color:{S_GRAY};text-transform:uppercase;
                                    letter-spacing:0.05em;margin-bottom:0.25rem'>Customer Number</div>
                        <div style='font-size:1.1rem;font-weight:600;color:{AMZ_SKY}'>{customer}</div>
                    </div>
                    <div>
                        <div style='font-size:0.75rem;color:{S_GRAY};text-transform:uppercase;
                                    letter-spacing:0.05em;margin-bottom:0.25rem'>Collector</div>
                        <div style='font-size:1.1rem;font-weight:600'>{collector}</div>
                    </div>
                    <div>
                        <div style='font-size:0.75rem;color:{S_GRAY};text-transform:uppercase;
                                    letter-spacing:0.05em;margin-bottom:0.25rem'>Balance</div>
                        <div style='font-size:1.1rem;font-weight:600;color:{S_RED}'>
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
            
            # Métricas
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
                    agent_count = agents.count(',') + 1 if ',' in str(agents) else 1
                    st.metric("Agentes", agent_count)
                else:
                    st.metric("Agentes", "0")
            
            # Historial completo
            if row['was_touched'] and match_key:
                st.markdown("**📝 Historial Completo:**")
                
                match_value = row.get(match_key)
                
                account_acts = df_activities[
                    df_activities[match_key] == match_value
                ].sort_values('date', ascending=False)
                
                if len(account_acts) == 0:
                    st.warning("No se encontraron actividades")
                else:
                    for act_idx, act in account_acts.iterrows():
                        date_str = act['date'].strftime('%Y-%m-%d')
                        agent = act['agent']
                        history = act.get('history', 'N/A')
                        
                        if len(history) > 500:
                            history = history[:500] + "..."
                        
                        st.markdown(f"""
                        <div style='background:rgba(0,167,225,0.05);padding:1rem;
                                    border-radius:8px;margin:0.5rem 0;
                                    border-left:3px solid {AMZ_SKY}'>
                            <div style='display:flex;justify-content:space-between;margin-bottom:0.5rem'>
                                <span style='font-size:0.85rem;color:{S_GRAY};font-weight:600'>
                                    📅 {date_str}
                                </span>
                                <span style='font-size:0.85rem;color:{AMZ_ROYAL};font-weight:600'>
                                    👤 {agent}
                                </span>
                            </div>
                            <div style='font-size:0.95rem;line-height:1.5'>{history}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("🚨 **Sin actividad registrada**")
            
            # Comentarios
            st.markdown("---")
            st.markdown("**✍️ Comentario de QA:**")
            
            comment_key = f"qa_{customer}_{idx}"
            comment_id = customer if customer != 'N/A' else company
            existing_comment = st.session_state.qa_comments.get(comment_id, '')
            
            new_comment = st.text_area(
                "Tu análisis:",
                value=existing_comment,
                height=120,
                key=comment_key,
                placeholder="Ej: Cuenta prioritaria sin gestión. Escalar a supervisor.",
                label_visibility="collapsed"
            )
            
            if new_comment != existing_comment:
                st.session_state.qa_comments[comment_id] = new_comment
    
    # ========================================================================
    # KPIs
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 📊 KPIs del Análisis")
    
    total_accounts = len(df_view)
    touched = df_view['was_touched'].sum()
    not_touched = total_accounts - touched
    total_balance = df_view.get('balance', pd.Series([0])).sum()
    touched_balance = df_view[df_view['was_touched'] == True].get('balance', pd.Series([0])).sum()
    not_touched_balance = total_balance - touched_balance
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cuentas", total_accounts)
    
    with col2:
        pct_touched = (touched / total_accounts * 100) if total_accounts > 0 else 0
        st.metric("Cuentas Gestionadas", touched, delta=f"{pct_touched:.1f}%")
    
    with col3:
        st.metric("Balance Total", format_currency(total_balance))
    
    with col4:
        st.metric(
            "Balance Sin Gestionar",
            format_currency(not_touched_balance),
            delta="⚠️ Riesgo",
            delta_color="inverse"
        )
    
    # Top agentes
    if len(df_activities) > 0:
        st.markdown("---")
        st.markdown("**👥 Top Agentes por Actividades:**")
        
        agent_stats = df_activities.groupby('agent').size().sort_values(ascending=False).head(5)
        
        cols = st.columns(5)
        for i, (agent, count) in enumerate(agent_stats.items()):
            with cols[i]:
                st.metric(agent, f"{count} acts")
    
    # ========================================================================
    # EXPORT
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 📥 Exportar Reporte")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("📊 Generar Excel", use_container_width=True, type="primary"):
            try:
                with st.spinner("Generando..."):
                    excel_file = export_qa_report(df_view, st.session_state.qa_comments, "QA_Report")
                
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel_file,
                    file_name=f"QA_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.success("✅ Reporte generado")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        total_comments = len([c for c in st.session_state.qa_comments.values() if c.strip()])
        st.info(f"✍️ **Comentarios:** {total_comments}/{total_accounts}")
