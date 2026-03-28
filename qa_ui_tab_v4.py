"""QA Tab v4.0 - FUNCIONA DE VERDAD"""

import streamlit as st
import pandas as pd
from datetime import datetime
from qa_module_v4 import (
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
    """Password - CON SECRETS Y ENTER."""
    
    # Intentar secrets primero
    try:
        correct_pwd = st.secrets["MGMT_PASSWORD"]
    except:
        # Fallback a default
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
        <h2 style='color:white;margin:0;font-weight:700'>Management</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # FORM para Enter
    with st.form("login_form", clear_on_submit=False):
        pwd = st.text_input("Contraseña:", type="password")
        submitted = st.form_submit_button("Acceder", use_container_width=True, type="primary")
        
        if submitted:
            if pwd == correct_pwd:
                st.session_state.mgmt_authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    
    return False


def fmt(v):
    try:
        return f"${float(v):,.2f}"
    except:
        return "$0.00"


def render_qa_tab(df_aging):
    """Tab Management."""
    
    if not check_mgmt_password():
        return
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AMZ_MIDNIGHT},{AMZ_ROYAL});
                padding:2rem;border-radius:12px;margin-bottom:2rem'>
        <h1 style='color:white;margin:0;font-size:1.8rem'>Management & QA</h1>
        <p style='color:{AMZ_SKY};margin:0.5rem 0 0'>Análisis de cartera</p>
    </div>
    """, unsafe_allow_html=True)
    
    if df_aging is None or len(df_aging) == 0:
        st.warning("No hay datos de Aging")
        return
    
    st.markdown("### Cargar Actividades")
    
    file = st.file_uploader("Excel o CSV", type=['xlsx', 'xls', 'csv'], label_visibility="collapsed")
    
    if not file:
        st.info("Suba archivo de actividades")
        return
    
    try:
        with st.spinner("Procesando..."):
            if file.name.endswith('.csv'):
                raw = pd.read_csv(file)
            else:
                raw = pd.read_excel(file)
            
            acts = clean_activities_file(raw)
            merged = merge_aging_with_activities(df_aging, acts)
        
        method = merged['_match_method'].iloc[0] if '_match_method' in merged.columns else '?'
        st.success(f"✅ {len(acts)} actividades | {acts['agent'].nunique()} agentes | Matching: {method}")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return
    
    st.session_state.qa_activities = acts
    st.session_state.qa_merged = merged
    
    st.markdown("---")
    
    # Filtros
    st.markdown("### Filtros")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        agents = sorted(acts['agent'].unique().tolist())
        st.markdown("**Agentes:**")
        all_sel = st.checkbox("Todos", value=True)
        
        if all_sel:
            sel_agents = ['📊 Todos los agentes']
        else:
            sel_agents = st.multiselect("Seleccionar:", agents, default=[], label_visibility="collapsed")
            if not sel_agents:
                sel_agents = ['📊 Todos los agentes']
    
    with c2:
        top = st.selectbox("Top:", [5, 10, 20, 50, 100], index=0)
    
    with c3:
        status = st.selectbox("Estado:", ['Todas', 'Con actividad', 'Sin actividad'])
    
    # Filtrar
    if '📊 Todos los agentes' not in sel_agents and sel_agents:
        df_view = get_multi_agent_portfolio(merged, acts, sel_agents)
        st.info(f"Filtrando: {', '.join(sel_agents)}")
    else:
        df_view = merged.copy()
    
    if status == 'Con actividad':
        df_view = df_view[df_view['was_touched'] == True]
    elif status == 'Sin actividad':
        df_view = df_view[df_view['was_touched'] == False]
    
    if 'balance' in df_view.columns:
        df_view = df_view.sort_values('balance', ascending=False).head(top)
    else:
        df_view = df_view.head(top)
    
    if len(df_view) == 0:
        st.warning("Sin datos")
        return
    
    st.markdown("---")
    
    # Tabla
    st.markdown(f"### Top {len(df_view)}")
    
    tbl = []
    for _, r in df_view.iterrows():
        tbl.append({
            'Collector': r.get('collector', 'N/A'),
            'Customer': r.get('customer_number', 'N/A'),
            'Company': r.get('company', 'N/A'),
            'Balance': fmt(r.get('balance', 0)),
            'Days': r.get('days_overdue', 'N/A'),
            'Status': r['activity_status'],
            'Acts': int(r.get('total_activities', 0))
        })
    
    st.dataframe(pd.DataFrame(tbl), use_container_width=True, hide_index=True, height=min(400, len(tbl)*35+38))
    
    st.markdown("---")
    
    # Detalle
    st.markdown("### Detalle")
    
    if 'qa_comments' not in st.session_state:
        st.session_state.qa_comments = {}
    
    match_key = merged['_match_key'].iloc[0] if '_match_key' in merged.columns else None
    
    for idx, row in df_view.iterrows():
        company = row.get('company', 'N/A')
        customer = row.get('customer_number', 'N/A')
        collector = row.get('collector', 'N/A')
        balance = row.get('balance', 0)
        days = row.get('days_overdue', 'N/A')
        
        icon = "✅" if row['was_touched'] else "⚠️"
        
        with st.expander(f"{icon} {company} • {customer} • {fmt(balance)}", expanded=False):
            
            st.markdown(f"""
            <div style='background:#f0f8ff;padding:1rem;border-radius:8px;margin-bottom:1rem'>
                <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1rem'>
                    <div><small style='color:#666'>Company</small><br><b>{company}</b></div>
                    <div><small style='color:#666'>Customer</small><br><b style='color:{AMZ_SKY}'>{customer}</b></div>
                    <div><small style='color:#666'>Collector</small><br><b>{collector}</b></div>
                    <div><small style='color:#666'>Balance</small><br><b style='color:{S_RED}'>{fmt(balance)}</b></div>
                    <div><small style='color:#666'>Days</small><br><b style='color:{S_AMBER}'>{days}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            
            total_acts = int(row.get('total_activities', 0))
            
            with c1:
                st.metric("Actividades", total_acts if total_acts > 0 else "0")
            with c2:
                if row['was_touched']:
                    st.metric("Última", f"{int(row['days_since_activity'])}d")
                else:
                    st.metric("Última", "Nunca")
            with c3:
                if row['was_touched']:
                    ag = row.get('agents_assigned', 'N/A')
                    cnt = ag.count(',') + 1 if ',' in str(ag) else 1
                    st.metric("Agentes", cnt)
                else:
                    st.metric("Agentes", "0")
            
            # Historial
            if row['was_touched'] and match_key:
                st.markdown("**Historial:**")
                
                val = row.get(match_key)
                history_acts = acts[acts[match_key] == val].sort_values('date', ascending=False)
                
                for _, act in history_acts.iterrows():
                    date = act['date'].strftime('%Y-%m-%d')
                    agent = act['agent']
                    hist = str(act.get('history', 'N/A'))
                    if len(hist) > 400:
                        hist = hist[:400] + "..."
                    
                    st.markdown(f"""
                    <div style='background:#f0f8ff;padding:0.8rem;border-radius:6px;margin:0.5rem 0;border-left:3px solid {AMZ_SKY}'>
                        <small style='color:#666'>📅 {date} | 👤 {agent}</small><br>
                        <div style='margin-top:0.3rem'>{hist}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Sin actividad")
            
            # Comentario
            st.markdown("---")
            st.markdown("**Comentario QA:**")
            
            cid = customer if customer != 'N/A' else company
            existing = st.session_state.qa_comments.get(cid, '')
            
            new_comment = st.text_area(
                "Análisis:",
                value=existing,
                height=100,
                key=f"qa_{cid}_{idx}",
                placeholder="Comentario...",
                label_visibility="collapsed"
            )
            
            if new_comment != existing:
                st.session_state.qa_comments[cid] = new_comment
    
    # KPIs
    st.markdown("---")
    st.markdown("### Resumen")
    
    total = len(df_view)
    touched = df_view['was_touched'].sum()
    total_bal = df_view.get('balance', pd.Series([0])).sum()
    untouched_bal = df_view[df_view['was_touched'] == False].get('balance', pd.Series([0])).sum()
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("Total", total)
    with c2:
        pct = (touched/total*100) if total > 0 else 0
        st.metric("Gestionadas", touched, delta=f"{pct:.1f}%")
    with c3:
        st.metric("Balance Total", fmt(total_bal))
    with c4:
        st.metric("Sin Gestionar", fmt(untouched_bal), delta="⚠️", delta_color="inverse")
    
    # Top agentes
    if len(acts) > 0:
        st.markdown("**Top Agentes:**")
        top_ag = acts.groupby('agent').size().sort_values(ascending=False).head(5)
        cols = st.columns(min(5, len(top_ag)))
        for i, (ag, cnt) in enumerate(top_ag.items()):
            if i < len(cols):
                with cols[i]:
                    st.metric(ag, cnt)
    
    # Export
    st.markdown("---")
    st.markdown("### Exportar")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
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
    
    with c2:
        comments = len([c for c in st.session_state.qa_comments.values() if c.strip()])
        st.info(f"Comentarios: {comments}/{total}")
