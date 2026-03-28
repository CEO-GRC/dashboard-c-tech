"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QA Module v3.1 — Dual Matching (Customer # + Company fallback)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Intenta Customer Number primero, si no matchea usa Company Name
"""

import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re


def normalize_text(text):
    """Normaliza texto para matching (nombres de empresa o customer numbers)."""
    if pd.isna(text):
        return ''
    
    text = str(text).strip().lower()
    text = re.sub(r'[.,\-_&()]', ' ', text)
    
    # Remover sufijos corporativos
    common_words = ['inc', 'llc', 'ltd', 'corp', 'corporation', 'company', 'co', 
                    'sa', 'sas', 'ltda', 'limitada']
    for word in common_words:
        text = re.sub(r'\b' + word + r'\b', '', text)
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def clean_activities_file(df_raw):
    """Limpia archivo de actividades - ROBUSTO."""
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
    
    # Renombrar columnas
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
    
    # Verificar que tenga al menos company O customer_number
    has_company = 'company' in df.columns
    has_customer = 'customer_number' in df.columns
    
    if not has_company and not has_customer:
        raise ValueError("Archivo debe tener columna 'Company' o 'Customer Number'")
    
    # Verificar otras requeridas
    required = ['agent', 'date']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas: {missing}")
    
    # Normalizar company si existe
    if has_company:
        df = df.dropna(subset=['company'])
        df['company_clean'] = df['company'].apply(normalize_text)
    
    # Normalizar customer_number si existe
    if has_customer:
        df['customer_clean'] = df['customer_number'].astype(str).str.strip().str.lower()
    
    # Parser de fechas
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
        raise ValueError("No hay fechas válidas en el archivo")
    
    # History
    if 'history' not in df.columns:
        df['history'] = 'N/A'
    
    df['history'] = df['history'].fillna('N/A').astype(str)
    df['history'] = df['history'].str.replace('\n', ' | ', regex=False)
    df['history'] = df['history'].str.replace('  ', ' ', regex=True)
    
    df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    return df


def merge_aging_with_activities(df_aging, df_activities):
    """
    Cruza Aging con Activities usando DUAL MATCHING:
    1. Intenta Customer Number primero
    2. Si no matchea, usa Company Name
    """
    aging = df_aging.copy()
    
    # ========================================================================
    # AUTO-DETECTAR COLUMNAS DEL AGING
    # ========================================================================
    
    # Company
    company_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'company' in col_lower or 'empresa' in col_lower or 'name' in col_lower:
            company_col = col
            break
    
    # Customer Number
    customer_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'customer' in col_lower or 'client' in col_lower or 'account' in col_lower:
            customer_col = col
            break
    
    # Balance
    balance_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'balance' in col_lower or 'total' in col_lower or 'past' in col_lower:
            balance_col = col
            break
    if balance_col is None:
        numeric_cols = aging.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            balance_col = numeric_cols[0]
    
    # Collector
    collector_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'collector' in col_lower or 'cobrador' in col_lower or 'agent' in col_lower:
            collector_col = col
            break
    
    # Days
    days_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'days' in col_lower or 'días' in col_lower or 'mora' in col_lower:
            days_col = col
            break
    
    # ========================================================================
    # RENOMBRAR
    # ========================================================================
    
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
    # DUAL MATCHING: Customer Number primero, Company fallback
    # ========================================================================
    
    # Preparar aggregates de actividades
    activities_agg = None
    match_key = None
    
    # Estrategia 1: Customer Number (si ambos lo tienen)
    if 'customer_clean' in aging.columns and 'customer_clean' in df_activities.columns:
        # Intentar merge por customer number
        activities_agg = df_activities.groupby('customer_clean').agg({
            'agent': lambda x: ', '.join(sorted(set(x))),
            'date': ['max', 'count'],
            'history': lambda x: ' || '.join([str(h)[:150] for h in x.head(5)])
        }).reset_index()
        
        activities_agg.columns = [
            'customer_clean',
            'agents_assigned',
            'last_activity_date',
            'total_activities',
            'recent_history'
        ]
        
        match_key = 'customer_clean'
        match_method = 'Customer Number'
    
    # Estrategia 2: Company Name (si customer no matchea o no existe)
    if activities_agg is None and 'company_clean' in aging.columns and 'company_clean' in df_activities.columns:
        activities_agg = df_activities.groupby('company_clean').agg({
            'agent': lambda x: ', '.join(sorted(set(x))),
            'date': ['max', 'count'],
            'history': lambda x: ' || '.join([str(h)[:150] for h in x.head(5)])
        }).reset_index()
        
        activities_agg.columns = [
            'company_clean',
            'agents_assigned',
            'last_activity_date',
            'total_activities',
            'recent_history'
        ]
        
        match_key = 'company_clean'
        match_method = 'Company Name'
    
    if activities_agg is None:
        raise ValueError("No se pudo hacer matching. Verifique que archivos tengan Customer Number o Company")
    
    # ========================================================================
    # MERGE
    # ========================================================================
    
    merged = aging.merge(activities_agg, on=match_key, how='left')
    
    # Calcular días desde última actividad
    today = pd.Timestamp.now()
    merged['days_since_activity'] = merged['last_activity_date'].apply(
        lambda x: (today - x).days if pd.notna(x) else 999
    )
    
    merged['was_touched'] = merged['total_activities'].notna()
    merged['total_activities'] = merged['total_activities'].fillna(0).astype(int)
    merged['activity_status'] = merged['was_touched'].apply(
        lambda x: '✅ Con Actividad' if x else '⚠️ Sin Actividad'
    )
    
    # Agregar metadata de matching
    merged['_match_method'] = match_method
    
    return merged


def get_multi_agent_portfolio(df_merged, df_activities, agent_names):
    """Obtiene portfolio de múltiples agentes."""
    if not agent_names or '📊 Todos los agentes' in agent_names:
        return df_merged.copy()
    
    agent_acts = df_activities[df_activities['agent'].isin(agent_names)].copy()
    
    # Determinar key de matching
    if 'customer_clean' in agent_acts.columns and 'customer_clean' in df_merged.columns:
        match_key = 'customer_clean'
        touched_keys = agent_acts['customer_clean'].unique()
    elif 'company_clean' in agent_acts.columns and 'company_clean' in df_merged.columns:
        match_key = 'company_clean'
        touched_keys = agent_acts['company_clean'].unique()
    else:
        return df_merged.head(0)  # No match possible
    
    portfolio = df_merged[df_merged[match_key].isin(touched_keys)].copy()
    
    return portfolio


def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA_Report"):
    """Exporta reporte de QA."""
    output = BytesIO()
    df_export = df_data.copy()
    
    # Limpiar nombres de columnas
    def clean_column_name(col_name):
        col_str = str(col_name)
        col_str = re.sub(r'[\[\]\'\"<>]', '', col_str)
        col_str = re.sub(r'\s+', ' ', col_str)
        col_str = col_str[:255]
        if not col_str.strip():
            col_str = 'Column'
        return col_str.strip()
    
    df_export.columns = [clean_column_name(col) for col in df_export.columns]
    
    # Agregar comentarios (usar company como key si existe, sino customer_number)
    if 'company' in df_export.columns:
        df_export['QA_Comment'] = df_export['company'].map(qa_comments_dict)
    elif 'customer_number' in df_export.columns:
        df_export['QA_Comment'] = df_export['customer_number'].map(qa_comments_dict)
    else:
        df_export['QA_Comment'] = ''
    
    df_export['QA_Comment'] = df_export['QA_Comment'].fillna('')
    
    # Limpiar datos
    for col in df_export.columns:
        if df_export[col].dtype == 'object':
            df_export[col] = df_export[col].astype(str).str[:32000]
    
    # Remover columnas internas
    cols_to_remove = [c for c in df_export.columns if c.startswith('_') or 'clean' in c.lower()]
    df_export = df_export.drop(columns=cols_to_remove, errors='ignore')
    
    # Crear Excel
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='QA Report', index=False)
            
            worksheet = writer.sheets['QA Report']
            for idx, col in enumerate(df_export.columns, 1):
                max_length = max(
                    df_export[col].astype(str).apply(len).max(),
                    len(str(col))
                )
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
