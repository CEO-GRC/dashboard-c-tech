"""
QA Module v5.0 - LA VAINA QUE SÍ FUNCIONA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Correcciones:
- Mapeo CORRECTO de columnas del dashboard
- Eliminación TOTAL de N/A
- Balance y días reales
- Matching por customer_number O company
"""
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re


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
        # Usar la primera columna como identificador
        df['customer_number'] = df.iloc[:, 0]
    
    if 'history' not in df.columns:
        df['history'] = 'N/A'
    
    # Convertir fechas
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
    else:
        df['date'] = pd.Timestamp.now()
    
    # LIMPIAR AGENTES - CERO N/A
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
    
    # VALIDACIÓN CRÍTICA: Asegurar que exista AL MENOS UNA columna de matching
    if '_match_customer' not in df.columns and '_match_company' not in df.columns:
        # Buscar la primera columna que parezca un identificador
        for col in df.columns:
            if col not in ['agent', 'date', 'history']:
                df['_match_customer'] = df[col].astype(str).str.strip().str.upper()
                break
    
    df['history'] = df['history'].fillna('Sin comentarios').astype(str)
    
    return df.sort_values('date', ascending=False).reset_index(drop=True)


def merge_aging_with_activities(df_aging, df_activities, col_payer=None, col_name=None):
    """
    Merge INTELIGENTE usando las columnas REALES del dashboard.
    
    Args:
        df_aging: DataFrame del aging report
        df_activities: DataFrame de actividades limpio
        col_payer: Nombre de la columna customer_number en aging
        col_name: Nombre de la columna company name en aging
    """
    aging = df_aging.copy()
    acts = df_activities.copy()
    
    # IDENTIFICAR COLUMNAS REALES DEL AGING
    if col_payer is None:
        # Buscar columna que parezca customer number
        for col in aging.columns:
            col_lower = str(col).lower()
            if 'payer' in col_lower or 'customer' in col_lower or 'cuenta' in col_lower or 'numero' in col_lower:
                col_payer = col
                break
    
    if col_name is None:
        # Buscar columna que parezca company name
        for col in aging.columns:
            col_lower = str(col).lower()
            if 'name' in col_lower or 'company' in col_lower or 'nombre' in col_lower or 'razon' in col_lower:
                col_name = col
                break
    
    # CREAR CAMPOS DE MATCHING
    match_key = None
    match_method = 'Unknown'
    
    # Opción 1: Match por customer_number
    if col_payer and col_payer in aging.columns and '_match_customer' in acts.columns:
        aging['_match_key'] = aging[col_payer].astype(str).str.strip().str.upper()
        acts_grouped = acts.groupby('_match_customer')
        match_key = '_match_key'
        match_method = f'Customer Number ({col_payer})'
    
    # Opción 2: Match por company name
    elif col_name and col_name in aging.columns and '_match_company' in acts.columns:
        aging['_match_key'] = aging[col_name].astype(str).str.strip().str.upper()
        acts_grouped = acts.groupby('_match_company')
        match_key = '_match_key'
        match_method = f'Company Name ({col_name})'
    
    # Opción 3: Intentar match automático por contenido
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
            acts_grouped = acts.groupby(best_match['acts_col'])
            match_key = '_match_key'
            match_method = f"Auto ({best_match['aging_col']} vs {best_match['acts_col']}) - {best_match['score']} matches"
        else:
            raise ValueError("No se encontraron columnas compatibles para el cruce. Verifique que los archivos tengan customer_number o company_name en común.")
    
    # AGREGAR ACTIVIDADES
    agg_dict = {
        'agent': lambda x: ', '.join(sorted(set([a for a in x if a != 'Sin Agente']))),
        'date': ['max', 'count'],
        'history': lambda x: ' || '.join([str(h)[:200] for h in list(x)[:5] if str(h) != 'Sin comentarios'])
    }
    
    agg = acts.groupby(acts[match_key.replace('_match_key', '_match_customer') if '_match_customer' in acts.columns else '_match_company']).agg(agg_dict).reset_index()
    agg.columns = ['_match_key', 'agents_assigned', 'last_activity_date', 'total_activities', 'recent_history']
    
    # MERGE
    merged = aging.merge(agg, on='_match_key', how='left')
    
    # CALCULAR MÉTRICAS
    today = pd.Timestamp.now()
    merged['days_since_activity'] = merged['last_activity_date'].apply(
        lambda x: (today - x).days if pd.notna(x) else 9999
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


ef get_multi_agent_portfolio(df_merged, df_activities, agent_names):
    """
    Filtra cartera por agentes seleccionados.
    ARREGLADO: Ahora incluye tanto las cuentas donde el agente tiene actividad,
    como las cuentas que tiene asignadas originalmente en el Aging.
    """
    if not agent_names or ' Todos los agentes' in agent_names:
        return df_merged.copy()
    
    # 1. Obtener llaves de los clientes que el agente SÍ tocó en actividades
    agent_acts = df_activities[df_activities['agent'].isin(agent_names)].copy()
    match_col = '_match_customer' if '_match_customer' in agent_acts.columns else '_match_company'
    
    keys_touched = []
    if match_col in agent_acts.columns and '_match_key' in df_merged.columns:
        keys_touched = agent_acts[match_col].unique().tolist()
        
    # 2. Identificar la columna de Collector en el Aging de forma dinámica
    collector_col = None
    for col in df_merged.columns:
        if 'collector' in str(col).lower() or 'cobrador' in str(col).lower():
            collector_col = col
            break

    # 3. Evaluar fila por fila (si cumple cualquiera de las 3, es del agente)
    def row_belongs_to_agent(row):
        # A) ¿El agente tocó esta cuenta? (Match por llave directa de actividad)
        if '_match_key' in row.index and row['_match_key'] in keys_touched:
            return True
            
        # B) ¿El agente tocó esta cuenta? (Match por campo concatenado agents_assigned)
        if 'agents_assigned' in row.index:
            agents_str = str(row['agents_assigned'])
            if pd.notna(agents_str) and agents_str not in ['', 'Sin Asignar', 'nan']:
                row_agents = [a.strip() for a in agents_str.split(',') if a.strip()]
                if any(ag in row_agents for ag in agent_names):
                    return True
                    
        # C) ¿La cuenta está asignada al agente en el archivo Aging original?
        if collector_col and collector_col in row.index:
            val = str(row[collector_col]).strip()
            if pd.notna(row[collector_col]) and val in agent_names:
                return True
                
        return False

    # Aplicamos el filtro completo
    filtered = df_merged[df_merged.apply(row_belongs_to_agent, axis=1)].copy()
    return filtered
    
    # MÉTODO 2: Si no hay matches, intentar por agents_assigned (campo concatenado)
    # Esto maneja casos donde agents_assigned = "Diego Gomez, Juan Perez"
    def row_has_agent(row):
        if 'agents_assigned' not in row.index:
            return False
        
        agents_str = str(row['agents_assigned'])
        if pd.isna(agents_str) or agents_str in ['', 'Sin Asignar', 'nan']:
            return False
        
        # Split por coma y limpiar
        row_agents = [a.strip() for a in agents_str.split(',') if a.strip()]
        
        # Verificar si alguno de los agentes seleccionados está en esta fila
        return any(ag in row_agents for ag in agent_names)
    
    filtered = df_merged[df_merged.apply(row_has_agent, axis=1)].copy()
    return filtered


def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA"):
    """
    Exporta reporte QA a Excel limpio.
    """
    output = BytesIO()
    df_export = df_data.copy()
    
    # Limpiar nombres de columnas
    df_export.columns = [
        re.sub(r'[^a-zA-Z0-9_ ]', '', str(c))[:100] 
        for c in df_export.columns
    ]
    
    # Agregar comentarios QA
    if '_match_key' in df_export.columns:
        df_export['QA_Comment'] = df_export['_match_key'].map(qa_comments_dict).fillna('')
    else:
        df_export['QA_Comment'] = ''
    
    # Reordenar columnas importantes al inicio
    priority_cols = []
    for col in ['customer_number', 'company', 'balance', 'days_overdue', 
                'collector', 'activity_status', 'total_activities', 
                'agents_assigned', 'days_since_activity', 'QA_Comment']:
        matching = [c for c in df_export.columns if col.lower() in c.lower()]
        priority_cols.extend(matching)
    
    other_cols = [c for c in df_export.columns if c not in priority_cols]
    final_cols = priority_cols + other_cols
    df_export = df_export[[c for c in final_cols if c in df_export.columns]]
    
    # Exportar
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='QA Report', index=False)
        
        # Autoajustar columnas
        worksheet = writer.sheets['QA Report']
        for idx, col in enumerate(df_export.columns):
            max_length = max(
                df_export[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    
    output.seek(0)
    return output
