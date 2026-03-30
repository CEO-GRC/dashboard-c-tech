"""QA Tab v5.0 - REALMENTE FUNCIONA SIN N/A"""

import streamlit as st
import pandas as pd
from datetime import datetime
from qa_module_v5 import (
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
    """Formatear moneda SIN N/A."""
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
    """
    Tab Management QA - VERSION QUE SÍ FUNCIONA.
    
    Args:
        df_aging: DataFrame del aging report
        col_payer: Nombre de columna customer_number
        col_name: Nombre de columna company name
        col_collector: Nombre de columna collector
        col_total: Nombre de columna total AR
    """
    if not check_mgmt_password():
        return
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                padding:2rem;border-radius:12px;margin-bottom:2rem'>
        <h1 style='color:white;margin:0;font-size:1.8rem'>💼 Management & QA</h1>
        <p style='color:{AMZ_SKY};margin:0.5rem 0 0'>Análisis de gestión de cartera</p>
    </div>
    """, unsafe_allow_html=True)
    
    if df_aging is None or len(df_aging) == 0:
        st.warning("⚠️ No hay datos de Aging. Cargue un archivo en la pestaña Overview.")
        return
    
    # Detectar columnas automáticamente si no se proporcionan
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
            if 'collector' in str(col).lower() or 'cobrador' in str(col).lower():
                col_collector = col
                break
    
    if col_total is None:
        for col in df_aging.columns:
            if 'total' in str(col).lower() and 'ar' in str(col).lower():
                col_total = col
                break
    
    # Buscar columna de días
    col_days = None
    for col in df_aging.columns:
        if 'days' in str(col).lower() or 'dias' in str(col).lower():
            col_days = col
            break
    
    st.markdown("### 📤 Cargar Actividades")
    
    file = st.file_uploader(
        "Excel o CSV con actividades de gestión",
        type=['xlsx', 'xls', 'csv'],
        help="Debe contener: User/Agent, Date, Customer/Company, History/Comments"
    )
    
    if not file:
        st.info("👆 Suba un archivo de actividades para comenzar el análisis")
        return
    
    # PROCESAR ARCHIVO
    try:
        with st.spinner("🔄 Procesando actividades..."):
            if file.name.endswith('.csv'):
                raw = pd.read_csv(file)
            else:
                raw = pd.read_excel(file)
            
            # Limpiar actividades
            acts = clean_activities_file(raw)
            
            # Merge con aging
            merged = merge_aging_with_activities(df_aging, acts, col_payer, col_name)
        
        method = merged['_match_method'].iloc[0] if '_match_method' in merged.columns else 'Desconocido'
        st.success(f"✅ **{len(acts)} actividades** | **{acts['agent'].nunique()} agentes** | Matching: {method}")
        
    except Exception as e:
        st.error(f"❌ Error procesando archivo: {str(e)}")
        st.info("""
        **Verifique que el archivo tenga:**
        - Columna de User/Agent/Agente
        - Columna de Date/Fecha
        - Columna de Customer/Company/Cliente
        - Columna de History/Comments/Comentarios
        """)
        return
    
    # Guardar en session state
    st.session_state.qa_activities = acts
    st.session_state.qa_merged = merged
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # FILTROS
    # ═══════════════════════════════════════════════════════════════
    
    st.markdown("### 🎯 Filtros")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        agents = sorted(acts['agent'].unique().tolist())
        st.markdown("**Agentes:**")
        all_sel = st.checkbox("Seleccionar todos", value=True, key="all_agents_qa")
        
        if all_sel:
            sel_agents = ['📊 Todos los agentes']
        else:
            sel_agents = st.multiselect(
                "Seleccionar agentes:",
                agents,
                default=[],
                label_visibility="collapsed"
            )
            if not sel_agents:
                sel_agents = ['📊 Todos los agentes']
    
    with c2:
        top = st.selectbox("Top clientes:", [5, 10, 20, 50, 100], index=1, key="top_qa")
    
    with c3:
        status = st.selectbox(
            "Estado de gestión:",
            ['Todas', 'Con actividad', 'Sin actividad'],
            key="status_qa"
        )
    
    # Aplicar filtros
    if '📊 Todos los agentes' not in sel_agents and sel_agents:
        df_view = get_multi_agent_portfolio(merged, acts, sel_agents)
        
        # DEBUG INFO
        total_antes = len(merged)
        total_despues = len(df_view)
        st.info(f"🔍 Filtrando por: **{', '.join(sel_agents)}** | {total_despues} de {total_antes} cuentas")
        
        # Mostrar sample de actividades del agente
        agent_sample = acts[acts['agent'].isin(sel_agents)].head(3)
        if len(agent_sample) > 0:
            with st.expander("📋 Ver sample de actividades detectadas", expanded=False):
                st.dataframe(agent_sample[['agent', 'date', 'customer_number', 'company_name', 'history']], use_container_width=True)
    else:
        df_view = merged.copy()
    
    if status == 'Con actividad':
        df_view = df_view[df_view['was_touched'] == True]
    elif status == 'Sin actividad':
        df_view = df_view[df_view['was_touched'] == False]
    
    # Ordenar por balance y limitar
    if col_total and col_total in df_view.columns:
        df_view = df_view.sort_values(col_total, ascending=False).head(top)
    else:
        df_view = df_view.head(top)
    
    if len(df_view) == 0:
        st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados")
        
        # DEBUG: Mostrar info útil
        st.info(f"""
        **Debug Info:**
        - Total actividades cargadas: {len(acts)}
        - Agentes únicos en actividades: {acts['agent'].nunique()}
        - Agentes seleccionados: {', '.join(sel_agents) if sel_agents else 'Ninguno'}
        - Total cuentas en aging: {len(merged)}
        - Método de matching: {merged['_match_method'].iloc[0] if '_match_method' in merged.columns else 'N/A'}
        """)
        
        # Mostrar agentes disponibles
        with st.expander("👥 Ver todos los agentes disponibles"):
            st.write(sorted(acts['agent'].unique().tolist()))
        
        return
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # TABLA TOP
    # ═══════════════════════════════════════════════════════════════
    
    st.markdown(f"### 📊 Top {len(df_view)} Clientes")
    
    tbl = []
    for _, r in df_view.iterrows():
        # Obtener valores de forma segura
        collector = safe_get(r, col_collector, 'Sin asignar') if col_collector else 'N/A'
        customer = safe_get(r, col_payer, 'N/A') if col_payer else 'N/A'
        company = safe_get(r, col_name, 'N/A') if col_name else 'N/A'
        balance = safe_get(r, col_total, 0) if col_total else 0
        days = safe_get(r, col_days, 0) if col_days else 0
        
        tbl.append({
            'Collector': collector,
            'Customer #': customer,
            'Company': company,
            'Balance': fmt(balance),
            'Days': days,
            'Status': r.get('activity_status', '⚠️ Sin Actividad'),
            'Activities': int(r.get('total_activities', 0))
        })
    
    df_table = pd.DataFrame(tbl)
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
        height=min(500, len(tbl) * 35 + 38)
    )
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # DETALLE POR CLIENTE
    # ═══════════════════════════════════════════════════════════════
    
    st.markdown("### 🔍 Detalle por Cliente")
    
    if 'qa_comments' not in st.session_state:
        st.session_state.qa_comments = {}
    
    for idx, row in df_view.iterrows():
        # Obtener datos
        company = safe_get(row, col_name, 'N/A') if col_name else 'N/A'
        customer = safe_get(row, col_payer, 'N/A') if col_payer else 'N/A'
        collector = safe_get(row, col_collector, 'Sin asignar') if col_collector else 'N/A'
        balance = safe_get(row, col_total, 0) if col_total else 0
        days = safe_get(row, col_days, 0) if col_days else 0
        
        was_touched = row.get('was_touched', False)
        total_acts = int(row.get('total_activities', 0))
        
        icon = "✅" if was_touched else "⚠️"
        
        with st.expander(f"{icon} **{company}** • {customer} • {fmt(balance)}", expanded=False):
            
            # Header con datos principales
            st.markdown(f"""
            <div style='background:#f0f8ff;padding:1rem;border-radius:8px;margin-bottom:1rem;
                        border-left:4px solid {AMZ_SKY}'>
                <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1rem'>
                    <div>
                        <small style='color:#666;font-weight:500'>Company</small><br>
                        <b style='color:{AMZ_MIDNIGHT}'>{company}</b>
                    </div>
                    <div>
                        <small style='color:#666;font-weight:500'>Customer #</small><br>
                        <b style='color:{AMZ_SKY}'>{customer}</b>
                    </div>
                    <div>
                        <small style='color:#666;font-weight:500'>Collector</small><br>
                        <b style='color:{AMZ_ROYAL}'>{collector}</b>
                    </div>
                    <div>
                        <small style='color:#666;font-weight:500'>Balance</small><br>
                        <b style='color:{S_RED};font-size:1.1em'>{fmt(balance)}</b>
                    </div>
                    <div>
                        <small style='color:#666;font-weight:500'>Days Overdue</small><br>
                        <b style='color:{S_AMBER};font-size:1.1em'>{days}</b>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Métricas de actividad
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("📞 Actividades", total_acts if total_acts > 0 else "0")
            
            with c2:
                if was_touched:
                    days_ago = int(row.get('days_since_activity', 9999))
                    if days_ago < 9999:
                        st.metric("⏱️ Última gestión", f"{days_ago} días")
                    else:
                        st.metric("⏱️ Última gestión", "Desconocida")
                else:
                    st.metric("⏱️ Última gestión", "Nunca", delta="⚠️", delta_color="inverse")
            
            with c3:
                if was_touched:
                    agents_str = row.get('agents_assigned', 'Sin Asignar')
                    if agents_str and agents_str != 'Sin Asignar':
                        cnt = len([a.strip() for a in str(agents_str).split(',') if a.strip()])
                        st.metric("👥 Agentes", cnt)
                    else:
                        st.metric("👥 Agentes", "0")
                else:
                    st.metric("👥 Agentes", "0")
            
            # Historial de actividades
            st.markdown("---")
            
            if was_touched:
                st.markdown("**📋 Historial de Actividades:**")
                
                # Buscar actividades de este cliente
                match_key = row.get('_match_key')
                if match_key and pd.notna(match_key):
                    # Determinar columna de matching en activities
                    match_col = '_match_customer' if '_match_customer' in acts.columns else '_match_company'
                    history_acts = acts[acts[match_col] == match_key].sort_values('date', ascending=False).head(10)
                    
                    if len(history_acts) > 0:
                        for _, act in history_acts.iterrows():
                            date = act['date'].strftime('%Y-%m-%d %H:%M') if pd.notna(act.get('date')) else 'Sin fecha'
                            agent = act.get('agent', 'Sin agente')
                            hist = str(act.get('history', 'Sin comentarios'))
                            
                            # Truncar comentario largo
                            if len(hist) > 500:
                                hist = hist[:500] + "..."
                            
                            st.markdown(f"""
                            <div style='background:#f8fafc;padding:0.9rem;border-radius:6px;
                                        margin:0.5rem 0;border-left:3px solid {AMZ_SKY}'>
                                <div style='display:flex;justify-content:space-between;margin-bottom:0.5rem'>
                                    <small style='color:#666;font-weight:600'>📅 {date}</small>
                                    <small style='color:{AMZ_ROYAL};font-weight:600'>👤 {agent}</small>
                                </div>
                                <div style='color:#334155;line-height:1.5'>{hist}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No se encontraron actividades en el historial")
                else:
                    st.info("No se pudo cargar el historial")
            else:
                st.warning("⚠️ **Este cliente NO tiene actividades registradas**")
            
            # Comentario QA
            st.markdown("---")
            st.markdown("**✍️ Comentario QA:**")
            
            # ID único para el comentario
            comment_id = f"{customer}_{company}".replace(' ', '_')
            existing = st.session_state.qa_comments.get(comment_id, '')
            
            new_comment = st.text_area(
                "Análisis QA:",
                value=existing,
                height=120,
                key=f"qa_comment_{comment_id}_{idx}",
                placeholder="Escriba su análisis de calidad aquí...",
                label_visibility="collapsed"
            )
            
            if new_comment != existing:
                st.session_state.qa_comments[comment_id] = new_comment
    
    # ═══════════════════════════════════════════════════════════════
    # RESUMEN Y KPIs
    # ═══════════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("### 📈 Resumen General")
    
    total = len(df_view)
    touched = df_view['was_touched'].sum()
    
    if col_total and col_total in df_view.columns:
        total_bal = df_view[col_total].sum()
        untouched_bal = df_view[df_view['was_touched'] == False][col_total].sum()
    else:
        total_bal = 0
        untouched_bal = 0
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("📊 Total Clientes", total)
    
    with c2:
        pct = (touched / total * 100) if total > 0 else 0
        st.metric("✅ Gestionados", touched, delta=f"{pct:.1f}%")
    
    with c3:
        st.metric("💰 Balance Total", fmt(total_bal))
    
    with c4:
        pct_untouched = (untouched_bal / total_bal * 100) if total_bal > 0 else 0
        st.metric(
            "⚠️ Sin Gestionar",
            fmt(untouched_bal),
            delta=f"{pct_untouched:.1f}%",
            delta_color="inverse"
        )
    
    # Top agentes
    if len(acts) > 0:
        st.markdown("---")
        st.markdown("**🏆 Top 5 Agentes por Actividades:**")
        
        top_ag = acts.groupby('agent').size().sort_values(ascending=False).head(5)
        cols = st.columns(min(5, len(top_ag)))
        
        for i, (ag, cnt) in enumerate(top_ag.items()):
            if i < len(cols):
                with cols[i]:
                    st.metric(ag, f"{cnt} acts")
    
    # ═══════════════════════════════════════════════════════════════
    # EXPORTAR
    # ═══════════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("### 📥 Exportar Reporte")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        if st.button("📄 Generar Reporte Excel", use_container_width=True, type="primary"):
            try:
                with st.spinner("Generando reporte..."):
                    excel = export_qa_report(df_view, st.session_state.qa_comments, "QA")
                
                st.download_button(
                    "⬇️ Descargar Reporte",
                    data=excel,
                    file_name=f"QA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ Reporte generado exitosamente")
            except Exception as e:
                st.error(f"❌ Error generando reporte: {str(e)}")
    
    with c2:
        comments_count = len([c for c in st.session_state.qa_comments.values() if c.strip()])
        st.info(f"💬 Comentarios QA:\n**{comments_count}** / {total}")
