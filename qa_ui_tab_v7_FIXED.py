"""QA Tab v7.0 - FIXED: Pipeline Robusto + Diagnóstico"""

import streamlit as st
import pandas as pd
from datetime import datetime
from qa_module_v7_FIXED import (
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
    
    with st.form("login_form", clear_on_submit=False):
        pwd = st.text_input("Contraseña:", type="password")
        submitted = st.form_submit_button("Acceder", use_container_width=True, type="primary")
        
        if submitted:
            if pwd == correct_pwd:
                st.session_state.mgmt_authenticated = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    
    return False


def fmt(v):
    """Formatear moneda."""
    try:
        num = float(v)
        if pd.isna(num) or num == 0:
            return "$0.00"
        return f"${num:,.2f}"
    except:
        return "$0.00"


def safe_get(row, col, default='N/A'):
    """Obtener valor seguro de una fila."""
    if col not in row.index:
        return default
    val = row[col]
    if pd.isna(val) or val == '' or str(val).lower() == 'nan':
        return default
    return val


def render_qa_tab(df_aging, col_payer=None, col_name=None, col_collector=None, col_total=None):
    """Tab Management QA v7.0 - Pipeline robusto con diagnóstico."""
    
    if not check_mgmt_password():
        return
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                padding:2rem;border-radius:12px;margin-bottom:2rem'>
        <h1 style='color:white;margin:0;font-size:1.8rem'>💼 Management & QA v7.0</h1>
        <p style='color:{AMZ_SKY};margin:0.5rem 0 0'>Pipeline robusto con normalización extrema de llaves</p>
    </div>
    """, unsafe_allow_html=True)
    
    if df_aging is None or len(df_aging) == 0:
        st.warning("⚠️ No hay datos de Aging. Cargue un archivo en la pestaña Overview.")
        return
    
    # Detectar columnas automáticamente
    if col_payer is None:
        for col in df_aging.columns:
            if 'payer' in str(col).lower() or 'customer' in str(col).lower():
                col_payer = col
                break
    
    if col_name is None:
        for col in df_aging.columns:
            if 'name' in str(col).lower() or 'company' in str(col).lower():
                if col != col_payer:  # Evitar duplicados
                    col_name = col
                    break
    
    if col_collector is None:
        for col in df_aging.columns:
            if 'collector' in str(col).lower():
                col_collector = col
                break
    
    if col_total is None:
        for col in df_aging.columns:
            if 'total' in str(col).lower() and 'ar' in str(col).lower():
                col_total = col
                break
    
    # Mostrar columnas detectadas
    with st.expander("🔍 Diagnóstico de Columnas Detectadas", expanded=False):
        st.write(f"**Columnas del Aging:** {list(df_aging.columns)}")
        st.write(f"**col_payer:** `{col_payer}`")
        st.write(f"**col_name:** `{col_name}`")
        st.write(f"**col_collector:** `{col_collector}`")
        st.write(f"**col_total:** `{col_total}`")
    
    st.markdown("### 📤 Cargar Actividades")
    
    file = st.file_uploader(
        "Excel o CSV con actividades",
        type=['xlsx', 'xls', 'csv'],
        help="Debe contener: User/Agent, Date, Customer/Company, History"
    )
    
    if not file:
        st.info("👆 Suba un archivo de actividades para comenzar")
        return
    
    # PROCESAR
    try:
        with st.spinner("🔄 Procesando..."):
            # Crear expander para logs
            log_expander = st.expander("📋 Log de Procesamiento", expanded=True)
            
            with log_expander:
                # Leer archivo
                if file.name.endswith('.csv'):
                    raw = pd.read_csv(file)
                else:
                    raw = pd.read_excel(file)
                
                st.write("**1. Limpiando actividades...**")
                acts = clean_activities_file(raw)
                
                st.write("**2. Realizando merge con aging...**")
                merged = merge_aging_with_activities(df_aging, acts, col_payer, col_name)
        
        method = merged['_match_method'].iloc[0] if '_match_method' in merged.columns else '?'
        
        touched_count = merged['was_touched'].sum()
        touched_pct = (touched_count / len(merged) * 100) if len(merged) > 0 else 0
        
        st.success(f"""
        ✅ **Procesamiento Exitoso**
        - {len(acts)} actividades de {acts['agent'].nunique()} agentes
        - {len(merged)} cuentas en cartera
        - {touched_count} cuentas gestionadas ({touched_pct:.1f}%)
        - Método de matching: {method}
        """)
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        with st.expander("🔍 Detalles del Error"):
            st.code(traceback.format_exc())
        return
    
    st.session_state.qa_activities = acts
    st.session_state.qa_merged = merged
    
    st.markdown("---")
    st.markdown("### 🎯 Filtros")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        agents = sorted(acts['agent'].unique().tolist())
        st.markdown("**Agentes:**")
        all_sel = st.checkbox("Seleccionar todos", value=True, key="qa_all_agents")
        
        if all_sel:
            sel_agents = ['📊 Todos los agentes']
        else:
            sel_agents = st.multiselect("Seleccionar:", agents, default=[], key="qa_agent_select")
            if not sel_agents:
                sel_agents = ['📊 Todos los agentes']
    
    with c2:
        top = st.selectbox("Top:", [5, 10, 20, 50, 100], index=1, key="qa_top")
    
    with c3:
        status = st.selectbox(
            "Estado:", 
            ['Todas', 'Solo Gestionadas', 'Solo NO Gestionadas'],
            key="qa_status"
        )
    
    with c4:
        st.markdown("**Info:**")
        st.info(f"🔍 {len(merged)} cuentas totales")
    
    # Filtrar por agente
    if '📊 Todos los agentes' not in sel_agents and sel_agents:
        df_view = get_multi_agent_portfolio(merged, acts, sel_agents, col_collector)
        st.info(f"🔍 Filtrando: **{', '.join(sel_agents)}**")
    else:
        df_view = merged.copy()
    
    # Filtrar por estado
    if status == 'Solo Gestionadas':
        df_view = df_view[df_view['was_touched'] == True]
        st.info(f"✅ Mostrando solo cuentas **gestionadas** ({len(df_view)} cuentas)")
    elif status == 'Solo NO Gestionadas':
        df_view = df_view[df_view['was_touched'] == False]
        st.warning(f"⚠️ Mostrando solo cuentas **SIN gestionar** ({len(df_view)} cuentas)")
    
    # Ordenar y limitar
    if col_total and col_total in df_view.columns:
        df_view = df_view.sort_values(col_total, ascending=False).head(top)
    else:
        df_view = df_view.head(top)
    
    if len(df_view) == 0:
        st.warning("⚠️ Sin datos con esos filtros")
        return
    
    st.markdown("---")
    st.markdown(f"### 📊 Top {len(df_view)}")
    
    # Tabla mejorada
    tbl = []
    for _, r in df_view.iterrows():
        collector = safe_get(r, col_collector, 'Sin asignar') if col_collector else 'N/A'
        customer = safe_get(r, col_payer, 'N/A') if col_payer else 'N/A'
        company = safe_get(r, col_name, 'N/A') if col_name else 'N/A'
        balance = safe_get(r, col_total, 0) if col_total else 0
        last_date = safe_get(r, 'last_activity_date_formatted', 'Never')
        
        tbl.append({
            'Collector': collector,
            'Customer #': customer,
            'Company': company,
            'Balance': fmt(balance),
            'Last Activity': last_date,
            'Status': r.get('activity_status', '⚠️ Sin Actividad'),
            'Activities': int(r.get('total_activities', 0))
        })
    
    st.dataframe(pd.DataFrame(tbl), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 🔍 Detalle")
    
    if 'qa_comments' not in st.session_state:
        st.session_state.qa_comments = {}
    
    for idx, row in df_view.iterrows():
        company = safe_get(row, col_name, 'N/A') if col_name else 'N/A'
        customer = safe_get(row, col_payer, 'N/A') if col_payer else 'N/A'
        collector = safe_get(row, col_collector, 'Sin asignar') if col_collector else 'N/A'
        balance = safe_get(row, col_total, 0) if col_total else 0
        
        was_touched = row.get('was_touched', False)
        total_acts = int(row.get('total_activities', 0))
        last_date = safe_get(row, 'last_activity_date_formatted', 'Never')
        
        icon = "✅" if was_touched else "⚠️"
        
        with st.expander(f"{icon} **{company}** • {customer} • {fmt(balance)}", expanded=False):
            st.markdown(f"""
            <div style='background:#f0f8ff;padding:1rem;border-radius:8px;margin-bottom:1rem'>
                <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1rem'>
                    <div><small>Company</small><br><b>{company}</b></div>
                    <div><small>Customer #</small><br><b>{customer}</b></div>
                    <div><small>Collector</small><br><b>{collector}</b></div>
                    <div><small>Balance</small><br><b style='color:{S_RED}'>{fmt(balance)}</b></div>
                    <div><small>Last Activity</small><br><b style='color:{S_AMBER}'>{last_date}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("📞 Actividades", total_acts)
            with c2:
                if was_touched:
                    days_ago = int(row.get('days_since_activity', 9999))
                    if days_ago < 9999:
                        st.metric("⏱️ Hace", f"{days_ago}d")
                    else:
                        st.metric("⏱️ Hace", "?")
                else:
                    st.metric("⏱️ Última", "Nunca")
            with c3:
                if was_touched:
                    ags = row.get('agents_assigned', '')
                    cnt = len([a.strip() for a in str(ags).split(',') if a.strip() and a.strip() != 'Sin Asignar'])
                    st.metric("👥 Agentes", cnt)
                else:
                    st.metric("👥 Agentes", "0")
            
            # Historial
            st.markdown("---")
            if was_touched:
                st.markdown("**📋 Historial:**")
                match_key = row.get('_match_key')
                if match_key and pd.notna(match_key):
                    match_col = '_match_customer' if '_match_customer' in acts.columns else '_match_company'
                    history = acts[acts[match_col] == match_key].sort_values('date', ascending=False).head(10)
                    
                    for _, act in history.iterrows():
                        date = act['date'].strftime('%Y-%m-%d') if pd.notna(act.get('date')) else '?'
                        agent = act.get('agent', '?')
                        hist = str(act.get('history', ''))[:500]
                        
                        st.markdown(f"""
                        <div style='background:#f8fafc;padding:0.8rem;border-radius:6px;margin:0.5rem 0;border-left:3px solid {AMZ_SKY}'>
                            <small>📅 {date} | 👤 {agent}</small><br>
                            <div style='margin-top:0.3rem'>{hist}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("Sin actividad")
            
            # Comentario
            st.markdown("---")
            st.markdown("**✍️ Comentario QA:**")
            cid = f"{customer}_{company}".replace(' ', '_')
            existing = st.session_state.qa_comments.get(cid, '')
            new_comment = st.text_area("", value=existing, height=100, key=f"qa_{cid}_{idx}")
            if new_comment != existing:
                st.session_state.qa_comments[cid] = new_comment
    
    # Resumen
    st.markdown("---")
    st.markdown("### 📈 Resumen")
    
    total = len(df_view)
    touched = df_view['was_touched'].sum()
    total_bal = df_view[col_total].sum() if col_total and col_total in df_view.columns else 0
    untouched_bal = df_view[df_view['was_touched'] == False][col_total].sum() if col_total and col_total in df_view.columns else 0
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("Total", total)
    with c2:
        pct = (touched/total*100) if total > 0 else 0
        st.metric("Gestionadas", touched, delta=f"{pct:.1f}%")
    with c3:
        st.metric("Balance Total", fmt(total_bal))
    with c4:
        st.metric("Sin Gestionar", fmt(untouched_bal))
    
    # Export
    st.markdown("---")
    st.markdown("### 📥 Exportar")
    
    if st.button("📄 Generar Excel", use_container_width=True, type="primary"):
        try:
            excel = export_qa_report(df_view, st.session_state.qa_comments, "QA")
            st.download_button(
                "⬇️ Descargar",
                data=excel,
                file_name=f"QA_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.success("✅ Listo")
        except Exception as e:
            st.error(f"❌ Error: {e}")
