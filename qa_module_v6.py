"""
QA Module v6.0 - FIXED: Fechas y Filtros
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Correcciones v6.0:
- Columna "Days" ahora muestra FECHA de última actividad (Feb 15, 2026)
- Filtro por collector COMPLETO: asignadas + gestionadas
- Nuevo filtro de estado: Todas / Solo Gestionadas / Solo NO Gestionadas
"""
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re
import string


def clean_activities_file(df_raw):
    """
    Limpia el archivo de actividades detectando headers y fechas.
    Retorna: DataFrame con columnas: agent, date, customer_number, history
    """
    # Buscar la fila de headers
    header_row = 0
    for idx in range(min(15, len(df_raw))):
        row_str = ' '.join([str(v) for v in df_raw.iloc[idx].values if pd.notna(v)]).lower()
        if 'user' in row_str or 'date' in row_str or 'agent' in row_str:
            header_row = idx
            break
    
    df = df_raw.iloc[header_row + 1:].copy()
    df.columns = df_raw.iloc[header_row]
    df = df.reset_index(drop=True)
    
    # Mapeo inteligente de columnas
    new_cols = {}
    for col in df.columns:
        c = str(col).lower().strip()
        if 'user' in c or 'agent' in c or 'agente' in c:
            new_cols[col] = 'agent'
        elif 'date' in c or 'fecha' in c:
            new_cols[col] = 'date'
        elif 'customer' in c or 'cuenta' in c or 'client' in c or 'numero' in c:
            new_cols[col] = 'customer_number'
        elif 'company' in c or 'nombre' in c or 'razon' in c or 'name' in c:
            new_cols[col] = 'company_name'
        elif 'history' in c or 'comentario' in c or 'comment' in c or 'note' in c:
            new_cols[col] = 'history'
    
    df = df.rename(columns=new_cols)
    
    # Asegurar columnas mínimas
    if 'agent' not in df.columns:
        df['agent'] = 'Sin Agente'
    
    if 'customer_number' not in df.columns and 'company_name' not in df.columns:
        df['customer_number'] = df.iloc[:, 0]
    
    if 'history' not in df.columns:
        df['history'] = 'N/A'
    
    # Convertir fechas
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
    else:
        df['date'] = pd.Timestamp.now()
    
    # LIMPIAR AGENTES
    df['agent'] = df['agent'].astype(str).str.strip()
    df['agent'] = df['agent'].replace({
        r'(?i)^nan$': 'Sin Agente',
        r'(?i)^n/?a$': 'Sin Agente',
        r'^None$': 'Sin Agente',
        r'^\s*$': 'Sin Agente'
    }, regex=True)
    
    # Crear campos limpios para matching
    if 'customer_number' in df.columns:
        df['_match_customer'] = df['customer_number'].astype(str).str.strip().str.upper()
    
    if 'company_name' in df.columns:
        df['_match_company'] = df['company_name'].astype(str).str.strip().str.upper()
    
    if '_match_customer' not in df.columns and '_match_company' not in df.columns:
        for col in df.columns:
            if col not in ['agent', 'date', 'history']:
                df['_match_customer'] = df[col].astype(str).str.strip().str.upper()
                break
    
    df['history'] = df['history'].fillna('Sin comentarios').astype(str)
    
    return df.sort_values('date', ascending=False).reset_index(drop=True)


def merge_aging_with_activities(df_aging, df_activities, col_payer=None, col_name=None):
    """
    Merge INTELIGENTE usando las columnas REALES del dashboard.
    NUEVO: Calcula fecha de última actividad correctamente
    """
    aging = df_aging.copy()
    acts = df_activities.copy()
    
    # IDENTIFICAR COLUMNAS
    if col_payer is None:
        for col in aging.columns:
            col_lower = str(col).lower()
            if 'payer' in col_lower or 'customer' in col_lower or 'cuenta' in col_lower:
                col_payer = col
                break
    
    if col_name is None:
        for col in aging.columns:
            col_lower = str(col).lower()
            if 'name' in col_lower or 'company' in col_lower or 'nombre' in col_lower:
                col_name = col
                break
    
    # CREAR MATCH KEY
    match_key = None
    match_method = 'Unknown'
    acts_match_col = None
    
    if col_payer and col_payer in aging.columns and '_match_customer' in acts.columns:
        aging['_match_key'] = aging[col_payer].astype(str).str.strip().str.upper()
        acts_match_col = '_match_customer'
        match_key = '_match_key'
        match_method = f'Customer Number ({col_payer})'
    elif col_name and col_name in aging.columns and '_match_company' in acts.columns:
        aging['_match_key'] = aging[col_name].astype(str).str.strip().str.upper()
        acts_match_col = '_match_company'
        match_key = '_match_key'
        match_method = f'Company Name ({col_name})'
    else:
        best_match = {'aging_col': None, 'acts_col': None, 'score': 0}
        
        for c_age in aging.columns:
            if aging[c_age].dtype == 'object':
                set_age = set(aging[c_age].dropna().astype(str).str.strip().str.upper())
                
                for c_acts in ['_match_customer', '_match_company']:
                    if c_acts in acts.columns:
                        set_acts = set(acts[c_acts].dropna())
                        matches = len(set_age.intersection(set_acts))
                        if matches > best_match['score']:
                            best_match = {
                                'aging_col': c_age,
                                'acts_col': c_acts,
                                'score': matches
                            }
        
        if best_match['score'] > 0:
            aging['_match_key'] = aging[best_match['aging_col']].astype(str).str.strip().str.upper()
            acts_match_col = best_match['acts_col']
            match_key = '_match_key'
            match_method = f"Auto ({best_match['aging_col']}) - {best_match['score']} matches"
        else:
            raise ValueError("No se encontraron columnas compatibles para el cruce.")
    
    # AGREGAR ACTIVIDADES
    agg_dict = {
        'agent': lambda x: ', '.join(sorted(set([a for a in x if a != 'Sin Agente']))),
        'date': ['max', 'count'],
        'history': lambda x: ' || '.join([str(h)[:200] for h in list(x)[:5] if str(h) != 'Sin comentarios'])
    }
    
    agg = acts.groupby(acts_match_col).agg(agg_dict).reset_index()
    agg.columns = ['_match_key', 'agents_assigned', 'last_activity_date', 'total_activities', 'recent_history']
    
    # MERGE
    merged = aging.merge(agg, on='_match_key', how='left')
    
    # CALCULAR MÉTRICAS - INCLUYENDO FECHA
    today = pd.Timestamp.now()
    
    # Días desde última actividad
    merged['days_since_activity'] = merged['last_activity_date'].apply(
        lambda x: (today - x).days if pd.notna(x) else 9999
    )
    
    # NUEVA COLUMNA: Fecha de última actividad formateada
    merged['last_activity_date_formatted'] = merged['last_activity_date'].apply(
        lambda x: x.strftime('%b %d, %Y') if pd.notna(x) else 'Never'
    )
    
    merged['total_activities'] = merged['total_activities'].fillna(0).astype(int)
    merged['was_touched'] = merged['total_activities'] > 0
    
    merged['activity_status'] = merged['was_touched'].apply(
        lambda x: '✅ Con Actividad' if x else '⚠️ Sin Actividad'
    )
    
    # LIMPIAR CAMPOS VACÍOS
    merged['agents_assigned'] = merged['agents_assigned'].fillna('Sin Asignar')
    merged['agents_assigned'] = merged['agents_assigned'].replace({'': 'Sin Asignar', 'nan': 'Sin Asignar'})
    merged['recent_history'] = merged['recent_history'].fillna('Sin actividad registrada')
    
    # METADATA
    merged['_match_method'] = match_method
    merged['_source_match_key'] = match_key
    
    return merged


def get_multi_agent_portfolio(df_merged, df_activities, agent_names, col_collector=None):
    """
    Filtra cartera por agentes seleccionados.
    VERSIÓN 6.0: Incluye AMBAS (asignadas en Aging + gestionadas en actividades)
    
    Args:
        df_merged: DataFrame merged
        df_activities: DataFrame de actividades
        agent_names: Lista de nombres de agentes
        col_collector: Nombre de la columna Collector en aging
    """
    if not agent_names or '📊 Todos los agentes' in agent_names:
        return df_merged.copy()
    
    # 1. Obtener llaves de clientes que el agente tocó
    agent_acts = df_activities[df_activities['agent'].isin(agent_names)].copy()
    match_col = '_match_customer' if '_match_customer' in agent_acts.columns else '_match_company'
    
    keys_touched = []
    if match_col in agent_acts.columns and '_match_key' in df_merged.columns:
        keys_touched = agent_acts[match_col].unique().tolist()
    
    # 2. Identificar columna de Collector
    if col_collector is None:
        for col in df_merged.columns:
            if 'collector' in str(col).lower() or 'cobrador' in str(col).lower():
                col_collector = col
                break
    
    # 3. Filtro COMPLETO: Asignadas O Gestionadas
    def row_belongs_to_agent(row):
        # A) ¿El agente tocó esta cuenta? (Match directo)
        if '_match_key' in row.index and row['_match_key'] in keys_touched:
            return True
        
        # B) ¿Está en agents_assigned?
        if 'agents_assigned' in row.index:
            agents_str = str(row['agents_assigned'])
            if pd.notna(agents_str) and agents_str not in ['', 'Sin Asignar', 'nan']:
                row_agents = [a.strip() for a in agents_str.split(',') if a.strip()]
                if any(ag in row_agents for ag in agent_names):
                    return True
        
        # C) ¿Está asignada en el Aging original?
        if col_collector and col_collector in row.index:
            val = str(row[col_collector]).strip()
            if pd.notna(row[col_collector]) and val in agent_names:
                return True
        
        return False
    
    filtered = df_merged[df_merged.apply(row_belongs_to_agent, axis=1)].copy()
    return filtered


def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA"):
    """
    Exporta reporte QA a Excel.
    """
    output = BytesIO()
    df_export = df_data.copy()
    
    # Limpiar nombres de columnas
    def clean_column_name(col_name):
        s = str(col_name)
        s = re.sub(r'[^a-zA-Z0-9_ ]', '', s)
        s = s.strip()
        if not s:
            s = 'Column'
        s = s[:31]
        return s
    
    new_cols = {}
    for col in df_export.columns:
        new_cols[col] = clean_column_name(col)
    
    # Verificar duplicados
    final_cols = []
    seen = {}
    for old_col, new_col in new_cols.items():
        if new_col in seen:
            seen[new_col] += 1
            final_cols.append(f"{new_col}_{seen[new_col]}")
        else:
            seen[new_col] = 0
            final_cols.append(new_col)
    
    df_export.columns = final_cols
    
    # Agregar comentarios QA
    match_key_col = None
    for col in df_export.columns:
        if 'match' in col.lower() and 'key' in col.lower():
            match_key_col = col
            break
    
    if match_key_col:
        df_export['QA_Comment'] = df_export[match_key_col].map(qa_comments_dict).fillna('')
    else:
        df_export['QA_Comment'] = ''
    
    # Reordenar columnas
    priority_keywords = ['customer', 'company', 'balance', 'last_activity', 
                        'collector', 'activity', 'total', 'agents', 'QA']
    priority_cols = []
    for keyword in priority_keywords:
        matching = [c for c in df_export.columns if keyword.lower() in c.lower()]
        priority_cols.extend(matching)
    
    other_cols = [c for c in df_export.columns if c not in priority_cols]
    final_order = priority_cols + other_cols
    df_export = df_export[[c for c in final_order if c in df_export.columns]]
    
    # Exportar
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='QA Report', index=False)
            
            try:
                worksheet = writer.sheets['QA Report']
                for idx, col in enumerate(df_export.columns):
                    if idx < 26:
                        col_letter = string.ascii_uppercase[idx]
                        max_len = min(len(col) + 5, 50)
                        worksheet.column_dimensions[col_letter].width = max_len
            except:
                pass
    except Exception:
        output = BytesIO()
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, sheet_name='QA Report', index=False)
        except Exception:
            output = BytesIO()
            csv_str = df_export.to_csv(index=False)
            output.write(csv_str.encode('utf-8'))
    
    output.seek(0)
    return output
