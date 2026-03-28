"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QA Tab v3.2 FIXED — Clean, functional, no BS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from qa_module_v3_2 import (
    clean_activities_file,
    merge_aging_with_activities,
    get_multi_agent_portfolio,
    export_qa_report
)

AMZ_MIDNIGHT = "#011E6A"
AMZ_SKY = "#00A7E1"
AMZ_ROYAL = "#0047AB"
S_GREEN = "#059669"
S_RED = "#DC2626"
S_AMBER = "#D97706"
S_GRAY = "#6B7280"

DEFAULT_MGMT_PASSWORD = "MGMT2024"


def check_mgmt_password():
    """Password gate - simple y funcional."""
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
                border-radius:16px;margin:2rem auto;max-width:500px'>
        <div style='font-size:3rem;margin-bottom:1rem'>🔐</div>
        <h2 style='color:white;margin:0;font-weight:700'>Management Access</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Form para permitir Enter
    with st.form(key="mgmt_login_form"):
        pwd_input = st.text_input("Ingrese contraseña:", type="password", key="mgmt_pwd")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit = st.form_submit_button("Acceder", use_container_width=True, type="primary")
        
        if submit:
            if pwd_input.strip() == correct_pwd:
                st.session_state.mgmt_authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    
    return False


def format_currency(value):
    try:
        return f"${float(value):,.2f}"
    except:
        return "$0.00"


def render_qa_tab(df_aging):
    """Management QA Tab - v3.2."""
    
    if not check_mgmt_password():
        return
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                padding:2rem 2.5rem;border-radius:16px;margin-bottom:2rem'>
        <h1 style='color:white;margin:0;font-size:2rem;font-weight:700'>
            Management & QA Review
        </h1>
        <p style='color:{AMZ_SKY};margin:0.5rem 0 0 0;font-size:1rem'>
            Análisis de cartera y actividades
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if df_aging is None or len(df_aging) == 0:
        st.warning("No hay datos de Aging. Cargue en Tab 1 primero.")
        return
    
    st.markdown("### 📤 Cargar Actividades")
    
    uploaded_file = st.file_uploader(
        "Excel o CSV",
        type=['xlsx', 'xls', 'csv'],
        label_visibility="collapsed"
    )
    
    if not uploaded_file:
        st.info("Suba el archivo de actividades")
        return
    
    try:
        with st.spinner("Procesando..."):
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)
            
            df_activities = clean_activities_file(df_raw)
            df_merged = merge_aging_with_activities(df_aging, df_activities)
        
        match_method = df_merged['_match_method'].iloc[0] if '_match_method' in df_merged.columns else 'Unknown'
        
        st.success(f"""
        ✅ Procesado: {len(df_activities):,} actividades | {df_activities['agent'].nunique()} agentes | 
        Matching: {match_method}
        """)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return
    
    st.session_state.qa_activities = df_activities
    st.session_state.qa_merged = df_merged
    
    st.markdown("---")
    
    # Filtros
    st.markdown("### 🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        all_agents = sorted(df_activities['agent'].unique().tolist())
        st.markdown("**Agentes:**")
        select_all = st.checkbox("Todos", value=True, key="sel_all")
        
        if select_all:
            selected_agents = ['📊 Todos los agentes']
        else:
            selected_agents = st.multiselect(
                "Seleccionar:",
                all_agents,
                default=[],
                label_visibility="collapsed"
            )
            if not selected_agents:
                selected_agents = ['📊 Todos los agentes']
    
    with col2:
        top_n = st.selectbox("Top:", [5, 10, 20, 50, 100, 200], index=0)
    
    with col3:
        status_filter = st.selectbox(
            "Estado:",
            ['Todas', 'Con actividad', 'Sin actividad']
        )
    
    # Filtrar data
    if '📊 Todos los agentes' not in selected_agents and selected_agents:
        df_view = get_multi_agent_portfolio(df_merged, df_activities, selected_agents)
        st.info(f"Filtrando: {', '.join(selected_agents)}")
    else:
        df_view = df_merged.copy()
    
    if status_filter == 'Con actividad':
        df_view = df_view[df_view['was_touched'] == True]
    elif status_filter == 'Sin actividad':
        df_view = df_view[df_view['was_touched'] == False]
    
    if 'balance' in df_view.columns:
        df_view = df_view.sort_values('balance', ascending=False).head(top_n)
    else:
        df_view = df_view.head(top_n)
    
    if len(df_view) == 0:
        st.warning("No hay datos con estos filtros")
        return
    
    st.markdown("---")
    
    # Tabla
    st.markdown(f"### 💰 Top {len(df_view)} Cuentas")
    
    table_data = []
    for idx, row in df_view.iterrows():
        table_data.append({
            'Collector': row.get('collector', 'N/A'),
            'Customer #': row.get('customer_number', 'N/A'),
            'Company': row.get('company', 'N/A'),
            'Past Due': format_currency(row.get('balance', 0)),
            'Days': row.get('days_overdue', 'N/A'),
            'Status': row['activity_status'],
            'Acts': int(row.get('total_activities', 0))
        })
    
    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True,
        height=min(400, len(table_data) * 35 + 38)
    )
    
    st.markdown("---")
    
    # Detalle
    st.markdown("### 📋 Detalle")
    
    if 'qa_comments' not in st.session_state:
        st.session_state.qa_comments = {}
    
    match_key = df_merged['_match_key'].iloc[0] if '_match_key' in df_merged.columns else None
    
    for idx, row in df_view.iterrows():
        company = row.get('company', 'N/A')
        customer = row.get('customer_number', 'N/A')
        collector = row.get('collector', 'N/A')
        balance = row.get('balance', 0)
        days = row.get('days_overdue', 'N/A')
        
        icon = "✅" if row['was_touched'] else "⚠️"
        
        with st.expander(f"{icon} {company} • {customer} • {format_currency(balance)}", expanded=False):
            
            st.markdown(f"""
            <div style='background:rgba(0,167,225,0.05);padding:1.5rem;border-radius:8px;margin-bottom:1rem'>
                <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem'>
                    <div>
                        <div style='font-size:0.7rem;color:{S_GRAY};text-transform:uppercase'>Company</div>
                        <div style='font-size:1rem;font-weight:600'>{company}</div>
                    </div>
                    <div>
                        <div style='font-size:0.7rem;color:{S_GRAY};text-transform:uppercase'>Customer #</div>
                        <div style='font-size:1rem;font-weight:600;color:{AMZ_SKY}'>{customer}</div>
                    </div>
                    <div>
                        <div style='font-size:0.7rem;color:{S_GRAY};text-transform:uppercase'>Collector</div>
                        <div style='font-size:1rem;font-weight:600'>{collector}</div>
                    </div>
                    <div>
                        <div style='font-size:0.7rem;color:{S_GRAY};text-transform:uppercase'>Balance</div>
                        <div style='font-size:1rem;font-weight:600;color:{S_RED}'>{format_currency(balance)}</div>
                    </div>
                    <div>
                        <div style='font-size:0.7rem;color:{S_GRAY};text-transform:uppercase'>Days OD</div>
                        <div style='font-size:1rem;font-weight:600;color:{S_AMBER}'>{days}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            
            with c1:
                total_acts = int(row.get('total_activities', 0))
                st.metric("Actividades", total_acts if total_acts > 0 else "0")
            
            with c2:
                if row['was_touched']:
                    days_ago = int(row['days_since_activity'])
                    st.metric("Última", f"{days_ago}d")
                else:
                    st.metric("Última", "Nunca")
            
            with c3:
                if row['was_touched']:
                    agents = row.get('agents_assigned', 'N/A')
                    agent_count = agents.count(',') + 1 if ',' in str(agents) else 1
                    st.metric("Agentes", agent_count)
                else:
                    st.metric("Agentes", "0")
            
            # Historial
            if row['was_touched'] and match_key:
                st.markdown("**Historial:**")
                
                match_value = row.get(match_key)
                acts = df_activities[df_activities[match_key] == match_value].sort_values('date', ascending=False)
                
                for _, act in acts.iterrows():
                    date_str = act['date'].strftime('%Y-%m-%d')
                    agent = act['agent']
                    history = str(act.get('history', 'N/A'))
                    if len(history) > 500:
                        history = history[:500] + "..."
                    
                    st.markdown(f"""
                    <div style='background:rgba(0,167,225,0.05);padding:0.8rem;border-radius:6px;margin:0.5rem 0;border-left:3px solid {AMZ_SKY}'>
                        <div style='font-size:0.8rem;color:{S_GRAY};margin-bottom:0.3rem'>
                            📅 {date_str} | 👤 {agent}
                        </div>
                        <div style='font-size:0.9rem'>{history}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Sin actividad")
            
            # Comentarios
            st.markdown("---")
            st.markdown("**Comentario QA:**")
            
            comment_key = f"qa_{customer}_{idx}"
            comment_id = customer if customer != 'N/A' else company
            existing = st.session_state.qa_comments.get(comment_id, '')
            
            new_comment = st.text_area(
                "Análisis:",
                value=existing,
                height=100,
                key=comment_key,
                placeholder="Ej: Cuenta prioritaria sin gestión.",
                label_visibility="collapsed"
            )
            
            if new_comment != existing:
                st.session_state.qa_comments[comment_id] = new_comment
    
    # KPIs
    st.markdown("---")
    st.markdown("### 📊 Resumen")
    
    total = len(df_view)
    touched = df_view['was_touched'].sum()
    total_bal = df_view.get('balance', pd.Series([0])).sum()
    untouched_bal = df_view[df_view['was_touched'] == False].get('balance', pd.Series([0])).sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cuentas", total)
    with col2:
        pct = (touched / total * 100) if total > 0 else 0
        st.metric("Gestionadas", touched, delta=f"{pct:.1f}%")
    with col3:
        st.metric("Balance Total", format_currency(total_bal))
    with col4:
        st.metric("Sin Gestionar", format_currency(untouched_bal), delta="⚠️", delta_color="inverse")
    
    # Top agentes
    if len(df_activities) > 0:
        st.markdown("**Top Agentes:**")
        stats = df_activities.groupby('agent').size().sort_values(ascending=False).head(5)
        cols = st.columns(min(5, len(stats)))
        for i, (agent, count) in enumerate(stats.items()):
            if i < len(cols):
                with cols[i]:
                    st.metric(agent, f"{count}")
    
    # Export
    st.markdown("---")
    st.markdown("### 📥 Exportar")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("Generar Excel", use_container_width=True, type="primary"):
            try:
                excel = export_qa_report(df_view, st.session_state.qa_comments, "QA")
                st.download_button(
                    "Descargar",
                    data=excel,
                    file_name=f"QA_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("Listo")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        comments = len([c for c in st.session_state.qa_comments.values() if c.strip()])
        st.info(f"Comentarios: {comments}/{total}")
