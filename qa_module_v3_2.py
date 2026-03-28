"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QA Module v3.2 FIXED — Dual matching real (no errors)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re


def normalize_text(text):
    """Normaliza texto para matching."""
    if pd.isna(text):
        return ''
    text = str(text).strip().lower()
    text = re.sub(r'[.,\-_&()]', ' ', text)
    common_words = ['inc', 'llc', 'ltd', 'corp', 'corporation', 'company', 'co', 
                    'sa', 'sas', 'ltda', 'limitada']
    for word in common_words:
        text = re.sub(r'\b' + word + r'\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_activities_file(df_raw):
    """Limpia archivo de actividades."""
    # Detectar header
    header_row = None
    for idx, row in df_raw.iterrows():
        row_str = ' '.join([str(v) for v in row.values if pd.notna(v)]).lower()
        if 'user' in row_str and 'date' in row_str:
            header_row = idx
            break
    
    if header_row is None:
        header_row = 0
    
    df = df_raw.iloc[header_row:].copy()
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)
    
    # Renombrar
    column_mapping = {}
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if 'user' in col_lower and 'customer' not in col_lower:
            column_mapping[col] = 'agent'
        elif 'date' in col_lower:
            column_mapping[col] = 'date'
        elif 'company' in col_lower or 'empresa' in col_lower:
            column_mapping[col] = 'company'
        elif 'customer' in col_lower and 'number' in col_lower:
            column_mapping[col] = 'customer_number'
        elif 'history' in col_lower:
            column_mapping[col] = 'history'
    
    df = df.rename(columns=column_mapping)
    
    # Verificar requeridas
    required = ['agent', 'date']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas: {missing}")
    
    # Normalizar company si existe
    if 'company' in df.columns:
        df['company_clean'] = df['company'].apply(normalize_text)
    
    # Normalizar customer si existe
    if 'customer_number' in df.columns:
        df['customer_clean'] = df['customer_number'].astype(str).str.strip().str.lower()
    
    # Fechas
    def parse_date_safe(date_val):
        if pd.isna(date_val):
            return None
        if isinstance(date_val, (pd.Timestamp, datetime)):
            return pd.Timestamp(date_val)
        try:
            return pd.to_datetime(str(date_val).strip(), errors='coerce')
        except:
            return None
    
    df['date'] = df['date'].apply(parse_date_safe)
    df = df.dropna(subset=['date'])
    
    if len(df) == 0:
        raise ValueError("No hay fechas válidas")
    
    # History
    if 'history' not in df.columns:
        df['history'] = 'N/A'
    df['history'] = df['history'].fillna('N/A').astype(str)
    df['history'] = df['history'].str.replace('\n', ' | ', regex=False)
    
    df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    return df


def merge_aging_with_activities(df_aging, df_activities):
    """Cruza Aging con Activities - DUAL MATCHING."""
    aging = df_aging.copy()
    
    # Auto-detectar columnas
    company_col = None
    for col in aging.columns:
        if 'company' in str(col).lower() or 'empresa' in str(col).lower():
            company_col = col
            break
    
    customer_col = None
    for col in aging.columns:
        if 'customer' in str(col).lower() or 'client' in str(col).lower():
            customer_col = col
            break
    
    balance_col = None
    for col in aging.columns:
        if 'balance' in str(col).lower() or 'total' in str(col).lower():
            balance_col = col
            break
    if not balance_col:
        numeric_cols = aging.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            balance_col = numeric_cols[0]
    
    collector_col = None
    for col in aging.columns:
        if 'collector' in str(col).lower() or 'cobrador' in str(col).lower():
            collector_col = col
            break
    
    days_col = None
    for col in aging.columns:
        if 'days' in str(col).lower() or 'días' in str(col).lower():
            days_col = col
            break
    
    # Renombrar
    rename_dict = {}
    if company_col:
        rename_dict[company_col] = 'company'
    if customer_col:
        rename_dict[customer_col] = 'customer_number'
    if balance_col:
        rename_dict[balance_col] = 'balance'
    if collector_col:
        rename_dict[collector_col] = 'collector'
    if days_col:
        rename_dict[days_col] = 'days_overdue'
    
    aging = aging.rename(columns=rename_dict)
    
    # Normalizar
    if 'company' in aging.columns:
        aging['company_clean'] = aging['company'].apply(normalize_text)
    if 'customer_number' in aging.columns:
        aging['customer_clean'] = aging['customer_number'].astype(str).str.strip().str.lower()
    if 'balance' in aging.columns:
        aging['balance'] = pd.to_numeric(aging['balance'], errors='coerce').fillna(0)
    
    # ========================================================================
    # DUAL MATCHING INTELIGENTE
    # ========================================================================
    
    # Determinar qué keys están disponibles en AMBOS archivos
    aging_has_customer = 'customer_clean' in aging.columns and len(aging['customer_clean'].dropna()) > 0
    aging_has_company = 'company_clean' in aging.columns and len(aging['company_clean'].dropna()) > 0
    
    acts_has_customer = 'customer_clean' in df_activities.columns and len(df_activities['customer_clean'].dropna()) > 0
    acts_has_company = 'company_clean' in df_activities.columns and len(df_activities['company_clean'].dropna()) > 0
    
    # Estrategia de matching
    match_key = None
    match_method = None
    
    # Prioridad 1: Customer Number (si ambos lo tienen)
    if aging_has_customer and acts_has_customer:
        match_key = 'customer_clean'
        match_method = 'Customer Number'
    
    # Prioridad 2: Company Name (si ambos lo tienen)
    elif aging_has_company and acts_has_company:
        match_key = 'company_clean'
        match_method = 'Company Name'
    
    # Si ninguno funciona
    else:
        # Intentar lo que sea
        if aging_has_company or acts_has_company:
            if 'company_clean' not in aging.columns and 'company' in aging.columns:
                aging['company_clean'] = aging['company'].apply(normalize_text)
            if 'company_clean' not in df_activities.columns and 'company' in df_activities.columns:
                df_activities['company_clean'] = df_activities['company'].apply(normalize_text)
            match_key = 'company_clean'
            match_method = 'Company Name'
        else:
            raise ValueError("No se pudo encontrar columna común (Customer Number o Company)")
    
    # Aggregate actividades
    activities_agg = df_activities.groupby(match_key).agg({
        'agent': lambda x: ', '.join(sorted(set(x))),
        'date': ['max', 'count'],
        'history': lambda x: ' || '.join([str(h)[:150] for h in x.head(5)])
    }).reset_index()
    
    activities_agg.columns = [
        match_key,
        'agents_assigned',
        'last_activity_date',
        'total_activities',
        'recent_history'
    ]
    
    # Merge
    merged = aging.merge(activities_agg, on=match_key, how='left')
    
    # Calcular días
    today = pd.Timestamp.now()
    merged['days_since_activity'] = merged['last_activity_date'].apply(
        lambda x: (today - x).days if pd.notna(x) else 999
    )
    
    merged['was_touched'] = merged['total_activities'].notna()
    merged['total_activities'] = merged['total_activities'].fillna(0).astype(int)
    merged['activity_status'] = merged['was_touched'].apply(
        lambda x: '✅ Con Actividad' if x else '⚠️ Sin Actividad'
    )
    
    merged['_match_method'] = match_method
    merged['_match_key'] = match_key
    
    return merged


def get_multi_agent_portfolio(df_merged, df_activities, agent_names):
    """Portfolio de múltiples agentes."""
    if not agent_names or '📊 Todos los agentes' in agent_names:
        return df_merged.copy()
    
    agent_acts = df_activities[df_activities['agent'].isin(agent_names)].copy()
    
    # Usar el match_key que se usó en el merge
    match_key = df_merged['_match_key'].iloc[0] if '_match_key' in df_merged.columns else None
    
    if not match_key:
        # Fallback
        if 'customer_clean' in df_merged.columns and 'customer_clean' in agent_acts.columns:
            match_key = 'customer_clean'
        elif 'company_clean' in df_merged.columns and 'company_clean' in agent_acts.columns:
            match_key = 'company_clean'
        else:
            return df_merged.head(0)
    
    touched_keys = agent_acts[match_key].unique()
    portfolio = df_merged[df_merged[match_key].isin(touched_keys)].copy()
    
    return portfolio


def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA_Report"):
    """Exporta reporte."""
    output = BytesIO()
    df_export = df_data.copy()
    
    def clean_column_name(col_name):
        col_str = str(col_name)
        col_str = re.sub(r'[\[\]\'\"<>]', '', col_str)
        col_str = re.sub(r'\s+', ' ', col_str)
        col_str = col_str[:255]
        if not col_str.strip():
            col_str = 'Column'
        return col_str.strip()
    
    df_export.columns = [clean_column_name(col) for col in df_export.columns]
    
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
            df_export[col] = df_export[col].astype(str).str[:32000]
    
    # Remover columnas internas
    cols_to_remove = [c for c in df_export.columns if c.startswith('_') or 'clean' in c.lower()]
    df_export = df_export.drop(columns=cols_to_remove, errors='ignore')
    
    # Excel
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='QA Report', index=False)
            worksheet = writer.sheets['QA Report']
            for idx, col in enumerate(df_export.columns, 1):
                max_length = max(df_export[col].astype(str).apply(len).max(), len(str(col)))
                col_width = min(max_length + 2, 100)
                col_letter = ''
                num = idx
                while num > 0:
                    num -= 1
                    col_letter = chr(65 + (num % 26)) + col_letter
                    num //= 26
                worksheet.column_dimensions[col_letter].width = col_width
    except:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, sheet_name='QA Report', index=False)
    
    output.seek(0)
    return output
