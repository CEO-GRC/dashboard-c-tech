"""QA Tab v7.0 - INTEGRADO CON MERGE ENGINE"""

import streamlit as st
import pandas as pd
from datetime import datetime
from qa_module_v7 import (
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
    """Tab Management QA v7.0 - INTEGRADO CON MERGE ENGINE."""
    
    if not check_mgmt_password():
        return
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                padding:2rem;border-radius:12px;margin-bottom:2rem'>
        <h1 style='color:white;margin:0;font-size:1.8rem'>💼 Management & QA v7.0</h1>
        <p style='color:{AMZ_SKY};margin:0.5rem 0 0'>Análisis de gestión de cartera - Motor integrado</p>
    </div>
    """, unsafe_allow_html=True)
    
    if df_aging is None or len(df_aging) == 0:
        st.warning("⚠️ No hay datos de Aging. Cargue un archivo en la pestaña Overview.")
        return
    
    # Detectar columnas automáticamente (aunque el motor lo hace, las necesitamos para display)
    if col_payer is None:
        for col in df_aging.columns:
            if 'payer' in str(col).lower() or 'customer' in str(col).lower():
                col_payer = col
                break
    
    if col_name is None:
        for col in df_aging.columns:
            if 'name' in str(col).lower() or 'company' in str(col).lower():
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
    
    st.markdown("### 📤 Cargar Actividades")
    
    file = st.file_uploader(
        "Excel o CSV con actividades",
        type=['xlsx', 'xls', 'csv'],
        help="Debe contener: User/Agent, Date, Customer/Company, History"
    )
    
    if not file:
        st.info("👆 Suba un archivo de actividades para comenzar")
        return
    
    # PROCESAR CON EL MOTOR v7.0
    try:
        with st.spinner("🔄 Procesando con Merge Engine v7.0..."):
            if file.name.endswith('.csv'):
                raw = pd.read_csv(file)
            else:
                raw = pd.read_excel(file)
            
            acts = clean_activities_file(raw)
            
            # ✅ EL MOTOR HACE TODO EL TRABAJO PESADO
            merged = merge_aging_with_activities(
                df_aging, 
                acts, 
                col_payer=col_payer,
                col_name=col_name,
                verbose=False  # No mostrar logs en producción
            )
        
        method = merged['_merge_method'].iloc[0] if '_merge_method' in merged.columns else 'Automático'
        touched = merged['was_touched'].sum()
        total = len(merged)
        pct = (touched/total*100) if total > 0 else 0
        
        st.success(f"✅ **{len(acts)} actividades** | **{acts['agent'].nunique()} agentes** | "
                  f"**{touched}/{total} gestionadas ({pct:.1f}%)** | Método: {method}")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        with st.expander("Ver detalles del error"):
            st.code(traceback.format_exc())
        return
    
    st.session_state.qa_activities = acts
    st.session_state.qa_merged = merged
    
    st.markdown("---")
    st.markdown("### 🎯 Filtros")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        # Usar agentes_consolidados para obtener la lista completa
        all_agents = merged['agentes_consolidados'].str.split(',').explode().str.strip().unique().tolist()
        all_agents = sorted([a for a in all_agents if a and a != 'Sin Asignar'])
        
        st.markdown("**Agentes:**")
        all_sel = st.checkbox("Seleccionar todos", value=True, key="qa_all_agents")
        
        if all_sel:
            sel_agents = ['📊 Todos los agentes']
        else:
            sel_agents = st.multiselect("Seleccionar:", all_agents, default=[], key="qa_agent_select")
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
    
    # Filtrar por agente usando el motor
    if '📊 Todos los agentes' not in sel_agents and sel_agents:
        df_view = get_multi_agent_portfolio(
            merged, 
            acts,  # Ya no se usa, pero mantenemos la firma
            sel_agents, 
            col_collector=col_collector
        )
        st.info(f"🔍 Filtrando: **{', '.join(sel_agents)}** ({len(df_view)} cuentas)")
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
    
    # Tabla
    tbl = []
    for _, r in df_view.iterrows():
        collector = safe_get(r, col_collector, 'Sin asignar') if col_collector else 'N/A'
        customer = safe_get(r, col_payer, 'N/A') if col_payer else 'N/A'
        company = safe_get(r, col_name, 'N/A') if col_name else 'N/A'
        balance = safe_get(r, col_total, 0) if col_total else 0
        
        # Usar las columnas del motor
        last_date = safe_get(r, 'last_activity_date_formatted', 'Never')
        agents_all = safe_get(r, 'agentes_consolidados', 'Sin Asignar')
        
        tbl.append({
            'Collector': collector,
            'Agentes (Todos)': agents_all,  # ✅ NUEVA COLUMNA
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
        agents_all = safe_get(row, 'agentes_consolidados', 'Sin Asignar')
        
        icon = "✅" if was_touched else "⚠️"
        
        with st.expander(f"{icon} **{company}** • {customer} • {fmt(balance)}", expanded=False):
            st.markdown(f"""
            <div style='background:rgba(0, 167, 225, 0.1);
                        border:1px solid rgba(0, 167, 225, 0.3);
                        padding:1rem;border-radius:8px;margin-bottom:1rem'>
                <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1rem'>
                    <div><small style='opacity:0.7'>Company</small><br><b>{company}</b></div>
                    <div><small style='opacity:0.7'>Customer #</small><br><b>{customer}</b></div>
                    <div><small style='opacity:0.7'>Collector (Asignado)</small><br><b>{collector}</b></div>
                    <div><small style='opacity:0.7'>Agentes (Todos)</small><br><b style='color:{AMZ_SKY}'>{agents_all}</b></div>
                    <div><small style='opacity:0.7'>Balance</small><br><b style='color:{S_RED}'>{fmt(balance)}</b></div>
                    <div><small style='opacity:0.7'>Last Activity</small><br><b style='color:{S_AMBER}'>{last_date}</b></div>
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
                    cnt = len([a.strip() for a in agents_all.split(',') if a.strip() and a.strip() != 'Sin Asignar'])
                    st.metric("👥 Agentes", cnt)
                else:
                    st.metric("👥 Agentes", "0")
            
            # Historial
            st.markdown("---")
            if was_touched:
                st.markdown("**📋 Historial:**")
                match_key = row.get('_match_key')
                if match_key and pd.notna(match_key):
                    # Buscar en actividades originales
                    match_col = None
                    for col in ['customer_number', 'company_name']:
                        if col in acts.columns:
                            match_col = col
                            break
                    
                    if match_col:
                        # Limpiar la llave de actividades de la misma forma que el motor
                        acts_temp = acts.copy()
                        acts_temp['_temp_key'] = acts_temp[match_col].astype(str).str.strip().str.lstrip('0').str.upper()
                        history = acts_temp[acts_temp['_temp_key'] == match_key].sort_values('date', ascending=False).head(10)
                        
                        for _, act in history.iterrows():
                            date = act['date'].strftime('%Y-%m-%d') if pd.notna(act.get('date')) else '?'
                            agent = act.get('agent', '?')
                            hist = str(act.get('history', ''))[:500]
                            
                            st.markdown(f"""
                            <div style='background:rgba(0, 167, 225, 0.05);
                                        border-left:3px solid {AMZ_SKY};
                                        padding:0.8rem;border-radius:6px;margin:0.5rem 0'>
                                <small style='opacity:0.7'>📅 {date} | 👤 {agent}</small><br>
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
                file_name=f"QA_v7_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.success("✅ Listo")
        except Exception as e:
            st.error(f"❌ Error: {e}")
