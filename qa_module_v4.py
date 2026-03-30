"""
QA Module v4.2 - DEFINITIVO
Corrección de N/A en agentes y restauración de columna 'was_touched'
"""
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re

def clean_activities_file(df_raw):
    """Limpia el archivo de actividades detectando headers y fechas de forma inteligente."""
    header_row = 0
    for idx in range(min(15, len(df_raw))):
        row_str = ' '.join([str(v) for v in df_raw.iloc[idx].values if pd.notna(v)]).lower()
        if 'user' in row_str or 'date' in row_str or 'agent' in row_str:
            header_row = idx
            break
    
    df = df_raw.iloc[header_row + 1:].copy()
    df.columns = df_raw.iloc[header_row]
    df = df.reset_index(drop=True)
    
    new_cols = {}
    for col in df.columns:
        c = str(col).lower().strip()
        if 'user' in c or 'agent' in c: new_cols[col] = 'agent'
        elif 'date' in c or 'fecha' in c: new_cols[col] = 'date'
        elif 'customer' in c or 'cuenta' in c: new_cols[col] = 'customer_number'
        elif 'history' in c or 'comentario' in c: new_cols[col] = 'history'
    
    df = df.rename(columns=new_cols)
    
    if 'agent' not in df.columns: 
        df['agent'] = 'Sin Agente'
    if 'customer_number' not in df.columns: 
        df = df.rename(columns={df.columns[0]: 'customer_number'})

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    
    # === ANIKIILACIÓN DE LOS N/A EN LOS AGENTES ===
    df['agent'] = df['agent'].astype(str).str.strip()
    df['agent'] = df['agent'].replace(
        {r'(?i)^nan$': 'Sin Agente', r'(?i)^n/a$': 'Sin Agente', '^$': 'Sin Agente', 'None': 'Sin Agente'}, 
        regex=True
    )
    
    df['customer_clean'] = df['customer_number'].astype(str).str.strip().str.lower()
    df['history'] = df['history'].fillna('N/A').astype(str)
    
    return df.sort_values('date', ascending=False).reset_index(drop=True)

def merge_aging_with_activities(df_aging, df_activities):
    """Merge por CONTENIDO para que el Management funcione sin importar los títulos."""
    aging = df_aging.copy()
    acts = df_activities.copy()
    
    best_match = {'aging_col': None, 'acts_col': None, 'score': 0}
    
    for c_age in aging.columns:
        set_age = set(aging[c_age].dropna().astype(str).str.strip().str.lower())
        for c_acts in acts.columns:
            set_acts = set(acts[c_acts].dropna().astype(str).str.strip().str.lower())
            matches = len(set_age.intersection(set_acts))
            if matches > best_match['score']:
                best_match = {'aging_col': c_age, 'acts_col': c_acts, 'score': matches}
                
    if best_match['score'] == 0:
        raise ValueError("No se encontraron datos en común para cruzar los archivos.")

    # Fix Anti-Dimensional Errors
    if 'customer_clean' in aging.columns and best_match['aging_col'] != 'customer_clean':
        aging = aging.drop(columns=['customer_clean'])
    if 'customer_clean' in acts.columns and best_match['acts_col'] != 'customer_clean':
        acts = acts.drop(columns=['customer_clean'])

    aging = aging.rename(columns={best_match['aging_col']: 'customer_clean'})
    acts = acts.rename(columns={best_match['acts_col']: 'customer_clean'})
    
    aging = aging.loc[:, ~aging.columns.duplicated()].copy()
    acts = acts.loc[:, ~acts.columns.duplicated()].copy()
    
    if 'company' not in aging.columns:
        for c in aging.columns:
            if 'name' in str(c).lower() or 'nombre' in str(c).lower():
                aging = aging.rename(columns={c: 'company'})
                break

    agg = acts.groupby('customer_clean').agg({
        'agent': lambda x: ', '.join(sorted(set([a for a in x if a != 'Sin Agente']))),
        'date': ['max', 'count'],
        'history': lambda x: ' || '.join([str(h)[:200] for h in list(x)[:5]])
    }).reset_index()
    
    agg.columns = ['customer_clean', 'agents_assigned', 'last_activity_date', 'total_activities', 'recent_history']
    
    merged = aging.merge(agg, on='customer_clean', how='left')
    
    today = pd.Timestamp.now()
    merged['days_since_activity'] = merged['last_activity_date'].apply(
        lambda x: (today - x).days if pd.notna(x) else 999
    )
    
    # === RESTAURACIÓN DEL was_touched (CHAO ERROR DE RENDERIZADO) ===
    merged['total_activities'] = merged['total_activities'].fillna(0).astype(int)
    merged['was_touched'] = merged['total_activities'] > 0  
    
    merged['activity_status'] = merged['was_touched'].apply(
        lambda x: '✅ Con Actividad' if x else '⚠️ Sin Actividad'
    )
    
    # Limpiar campos vacíos del cruce
    merged['agents_assigned'] = merged['agents_assigned'].replace({'': 'Sin Asignar'})
    merged['agents_assigned'] = merged['agents_assigned'].fillna('Sin Asignar')
    
    merged['_match_key'] = 'customer_clean'
    
    return merged

def get_multi_agent_portfolio(df_merged, df_activities, agent_names):
    """Filtra por múltiples agentes."""
    if not agent_names or '📊 Todos los agentes' in agent_names:
        return df_merged.copy()
    
    agent_acts = df_activities[df_activities['agent'].isin(agent_names)].copy()
    keys = agent_acts['customer_clean'].unique()
    return df_merged[df_merged['customer_clean'].isin(keys)].copy()

def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA"):
    """Exportación a Excel sin caracteres raros."""
    output = BytesIO()
    df_export = df_data.copy()
    
    df_export.columns = [re.sub(r'[^a-zA-Z0-9_ ]', '', str(c))[:100] for c in df_export.columns]
    
    key_col = 'customer_clean' if 'customer_clean' in df_export.columns else df_export.columns[0]
    df_export['QA_Comment'] = df_export[key_col].map(qa_comments_dict).fillna('')
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='QA Report', index=False)
    
    output.seek(0)
    return output
