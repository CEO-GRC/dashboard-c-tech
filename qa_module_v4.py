"""QA Module v4.0 - QUE SÍ FUNCIONA"""

import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re


def clean_activities_file(df_raw):
    """Limpia archivo - FUNCIONA DE VERDAD."""
    
    # Buscar fila con "User", "Date", etc
    header_row = None
    for idx in range(min(10, len(df_raw))):
        row_str = ' '.join([str(v) for v in df_raw.iloc[idx].values if pd.notna(v)]).lower()
        if 'user' in row_str and 'date' in row_str:
            header_row = idx
            break
    
    if header_row is None:
        raise ValueError("No se encontró header con User y Date")
    
    # Usar esa fila como header
    df = df_raw.iloc[header_row + 1:].copy()
    df.columns = df_raw.iloc[header_row]
    df = df.reset_index(drop=True)
    
    # Renombrar
    new_cols = {}
    for col in df.columns:
        c = str(col).lower().strip()
        if 'user' in c:
            new_cols[col] = 'agent'
        elif 'date' in c:
            new_cols[col] = 'date'
        elif 'customer' in c and 'number' in c:
            new_cols[col] = 'customer_number'
        elif 'company' in c:
            new_cols[col] = 'company'
        elif 'history' in c:
            new_cols[col] = 'history'
    
    df = df.rename(columns=new_cols)
    
    # Verificar
    if 'agent' not in df.columns or 'date' not in df.columns:
        raise ValueError("Falta User o Date")
    
    # Fechas
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    
    # Company
    if 'company' in df.columns:
        df['company'] = df['company'].astype(str).str.strip()
        df['company_clean'] = df['company'].str.lower().str.replace(r'[^a-z0-9\s]', '', regex=True).str.strip()
    
    # Customer
    if 'customer_number' in df.columns:
        df['customer_number'] = df['customer_number'].astype(str).str.strip()
        df['customer_clean'] = df['customer_number'].str.lower()
    
    # History
    if 'history' not in df.columns:
        df['history'] = 'N/A'
    df['history'] = df['history'].fillna('N/A').astype(str)
    
    df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    return df


def merge_aging_with_activities(df_aging, df_activities):
    """Merge - FUNCIONA."""
    
    aging = df_aging.copy()
    
    # Buscar columnas en aging
    company_col = None
    customer_col = None
    balance_col = None
    
    for col in aging.columns:
        c = str(col).lower()
        if not company_col and ('company' in c or 'name' in c):
            company_col = col
        if not customer_col and ('customer' in c or 'account' in c):
            customer_col = col
        if not balance_col and ('balance' in c or 'total' in c):
            balance_col = col
    
    # Renombrar aging
    renames = {}
    if company_col:
        renames[company_col] = 'company'
    if customer_col:
        renames[customer_col] = 'customer_number'
    if balance_col:
        renames[balance_col] = 'balance'
    
    # Buscar collector
    for col in aging.columns:
        if 'collector' in str(col).lower() or 'cobrador' in str(col).lower():
            renames[col] = 'collector'
            break
    
    # Buscar days
    for col in aging.columns:
        if 'days' in str(col).lower() or 'días' in str(col).lower():
            renames[col] = 'days_overdue'
            break
    
    aging = aging.rename(columns=renames)
    
    # Normalizar aging
    if 'company' in aging.columns:
        aging['company_clean'] = aging['company'].astype(str).str.lower().str.replace(r'[^a-z0-9\s]', '', regex=True).str.strip()
    
    if 'customer_number' in aging.columns:
        aging['customer_clean'] = aging['customer_number'].astype(str).str.strip().str.lower()
    
    if 'balance' in aging.columns:
        aging['balance'] = pd.to_numeric(aging['balance'], errors='coerce').fillna(0)
    
    # Decidir match key
    match_key = None
    match_name = None
    
    # Probar customer primero
    if 'customer_clean' in aging.columns and 'customer_clean' in df_activities.columns:
        # Verificar que haya matches
        common = set(aging['customer_clean'].dropna()) & set(df_activities['customer_clean'].dropna())
        if len(common) > 0:
            match_key = 'customer_clean'
            match_name = 'Customer Number'
    
    # Si no, probar company
    if not match_key and 'company_clean' in aging.columns and 'company_clean' in df_activities.columns:
        common = set(aging['company_clean'].dropna()) & set(df_activities['company_clean'].dropna())
        if len(common) > 0:
            match_key = 'company_clean'
            match_name = 'Company'
    
    if not match_key:
        raise ValueError("No se encontraron matches entre archivos")
    
    # Aggregate activities
    agg = df_activities.groupby(match_key).agg({
        'agent': lambda x: ', '.join(sorted(set(x))),
        'date': ['max', 'count'],
        'history': lambda x: ' || '.join([str(h)[:200] for h in list(x)[:5]])
    }).reset_index()
    
    agg.columns = [match_key, 'agents_assigned', 'last_activity_date', 'total_activities', 'recent_history']
    
    # Merge
    merged = aging.merge(agg, on=match_key, how='left')
    
    # Calcular
    today = pd.Timestamp.now()
    merged['days_since_activity'] = merged['last_activity_date'].apply(
        lambda x: (today - x).days if pd.notna(x) else 999
    )
    
    merged['was_touched'] = merged['total_activities'].notna()
    merged['total_activities'] = merged['total_activities'].fillna(0).astype(int)
    merged['activity_status'] = merged['was_touched'].apply(
        lambda x: '✅ Con Actividad' if x else '⚠️ Sin Actividad'
    )
    
    merged['_match_key'] = match_key
    merged['_match_method'] = match_name
    
    return merged


def get_multi_agent_portfolio(df_merged, df_activities, agent_names):
    """Filtrar por agentes."""
    
    if not agent_names or '📊 Todos los agentes' in agent_names:
        return df_merged.copy()
    
    agent_acts = df_activities[df_activities['agent'].isin(agent_names)].copy()
    
    match_key = df_merged['_match_key'].iloc[0] if '_match_key' in df_merged.columns else None
    if not match_key:
        return df_merged.copy()
    
    keys = agent_acts[match_key].unique()
    return df_merged[df_merged[match_key].isin(keys)].copy()


def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA"):
    """Export."""
    
    output = BytesIO()
    df_export = df_data.copy()
    
    # Limpiar nombres
    df_export.columns = [re.sub(r'[^a-zA-Z0-9_ ]', '', str(c))[:100] for c in df_export.columns]
    
    # Comentarios
    if 'company' in df_export.columns:
        df_export['QA_Comment'] = df_export['company'].map(qa_comments_dict)
    elif 'customer_number' in df_export.columns:
        df_export['QA_Comment'] = df_export['customer_number'].map(qa_comments_dict)
    else:
        df_export['QA_Comment'] = ''
    
    df_export['QA_Comment'] = df_export['QA_Comment'].fillna('')
    
    # Limpiar
    for col in df_export.columns:
        if df_export[col].dtype == 'object':
            df_export[col] = df_export[col].astype(str).str[:30000]
    
    # Remover cols internas
    df_export = df_export[[c for c in df_export.columns if not c.startswith('_') and 'clean' not in c.lower()]]
    
    # Excel
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='QA Report', index=False)
    except:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, sheet_name='QA Report', index=False)
    
    output.seek(0)
    return output
