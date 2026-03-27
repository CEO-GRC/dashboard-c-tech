"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QA Module v3.0 FINAL — Company-based matching
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cruce por COMPANY NAME (no por Customer Number)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re


def normalize_company_name(name):
    """
    Normaliza nombres de empresas para matching robusto.
    Elimina puntuación, espacios extra, convierte a lowercase.
    """
    if pd.isna(name):
        return ''
    
    name = str(name).strip().lower()
    
    # Remover puntuación común
    name = re.sub(r'[.,\-_&()]', ' ', name)
    
    # Remover palabras comunes que pueden variar
    common_words = ['inc', 'llc', 'ltd', 'corp', 'corporation', 'company', 'co', 
                    'sa', 'sas', 'ltda', 'limitada']
    for word in common_words:
        name = re.sub(r'\b' + word + r'\b', '', name)
    
    # Remover espacios múltiples
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def clean_activities_file(df_raw):
    """Limpia archivo de actividades - ROBUSTO."""
    # Detectar header
    header_row = None
    for idx, row in df_raw.iterrows():
        row_str = ' '.join([str(v) for v in row.values if pd.notna(v)]).lower()
        if 'user' in row_str and 'date' in row_str and 'company' in row_str:
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
        elif 'history' in col_lower:
            column_mapping[col] = 'history'
        elif 'customer' in col_lower and 'number' in col_lower:
            column_mapping[col] = 'customer_number'
    
    df = df.rename(columns=column_mapping)
    
    # Verificar columnas requeridas
    required = ['agent', 'date', 'company']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}. Necesita: User, Date, Company")
    
    # Limpiar company names
    df = df.dropna(subset=['company'])
    df['company_clean'] = df['company'].apply(normalize_company_name)
    df = df[df['company_clean'] != '']
    
    # Parser de fechas robusto
    def parse_date_safe(date_val):
        if pd.isna(date_val):
            return None
        if isinstance(date_val, (pd.Timestamp, datetime)):
            return pd.Timestamp(date_val)
        
        date_str = str(date_val).strip()
        try:
            return pd.to_datetime(date_str, errors='coerce')
        except:
            return None
    
    df['date'] = df['date'].apply(parse_date_safe)
    df = df.dropna(subset=['date'])
    
    if len(df) == 0:
        raise ValueError("No se pudieron parsear fechas válidas")
    
    # Agregar history si no existe
    if 'history' not in df.columns:
        df['history'] = 'N/A'
    
    df['history'] = df['history'].fillna('N/A').astype(str)
    df['history'] = df['history'].str.replace('\n', ' | ', regex=False)
    df['history'] = df['history'].str.replace('  ', ' ', regex=True)
    
    # Ordenar por fecha
    df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    return df


def merge_aging_with_activities(df_aging, df_activities):
    """
    Cruza Aging con Activities usando COMPANY NAME.
    """
    aging = df_aging.copy()
    
    # Auto-detectar columnas del Aging
    company_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'company' in col_lower or 'empresa' in col_lower or 'name' in col_lower:
            company_col = col
            break
    
    if company_col is None:
        # Buscar columna que parezca nombre (muchos textos únicos)
        for col in aging.columns:
            if aging[col].dtype == 'object':
                unique_ratio = aging[col].nunique() / len(aging)
                if unique_ratio > 0.5:  # Más del 50% son únicos
                    company_col = col
                    break
    
    if company_col is None:
        raise ValueError("No se pudo detectar columna de Company en el Aging")
    
    # Detectar otras columnas
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
    
    collector_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'collector' in col_lower or 'cobrador' in col_lower or 'agent' in col_lower:
            collector_col = col
            break
    
    customer_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'customer' in col_lower or 'client' in col_lower or 'account' in col_lower:
            customer_col = col
            break
    
    days_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'days' in col_lower or 'días' in col_lower or 'mora' in col_lower:
            days_col = col
            break
    
    # Renombrar columnas
    rename_dict = {company_col: 'company'}
    
    if balance_col:
        rename_dict[balance_col] = 'balance'
    if collector_col:
        rename_dict[collector_col] = 'collector'
    if customer_col:
        rename_dict[customer_col] = 'customer_number'
    if days_col:
        rename_dict[days_col] = 'days_overdue'
    
    aging = aging.rename(columns=rename_dict)
    
    # Normalizar company names en Aging
    aging['company_clean'] = aging['company'].apply(normalize_company_name)
    
    # Asegurar balance numérico
    if 'balance' in aging.columns:
        aging['balance'] = pd.to_numeric(aging['balance'], errors='coerce').fillna(0)
    
    # Agregar info de actividades
    activities_by_company = df_activities.groupby('company_clean').agg({
        'agent': lambda x: ', '.join(sorted(set(x))),
        'date': ['max', 'count'],
        'history': lambda x: ' || '.join([str(h)[:150] for h in x.head(5)])
    }).reset_index()
    
    activities_by_company.columns = [
        'company_clean',
        'agents_assigned',
        'last_activity_date',
        'total_activities',
        'recent_history'
    ]
    
    # MERGE POR COMPANY
    merged = aging.merge(activities_by_company, on='company_clean', how='left')
    
    # Calcular días desde última actividad
    today = pd.Timestamp.now()
    merged['days_since_activity'] = merged['last_activity_date'].apply(
        lambda x: (today - x).days if pd.notna(x) else 999
    )
    
    # Marcar si fue tocada
    merged['was_touched'] = merged['total_activities'].notna()
    merged['total_activities'] = merged['total_activities'].fillna(0).astype(int)
    
    # Status texto
    merged['activity_status'] = merged['was_touched'].apply(
        lambda x: '✅ Con Actividad' if x else '⚠️ Sin Actividad'
    )
    
    return merged


def get_multi_agent_portfolio(df_merged, df_activities, agent_names):
    """
    Obtiene portfolio de MÚLTIPLES agentes.
    
    Args:
        df_merged: DataFrame mergeado
        df_activities: DataFrame de actividades
        agent_names: Lista de nombres de agentes
    """
    if not agent_names or '📊 Todos los agentes' in agent_names:
        return df_merged.copy()
    
    # Filtrar actividades de estos agentes
    agent_acts = df_activities[df_activities['agent'].isin(agent_names)].copy()
    
    # Obtener companies únicas tocadas por estos agentes
    touched_companies = agent_acts['company_clean'].unique()
    
    # Filtrar merged
    portfolio = df_merged[df_merged['company_clean'].isin(touched_companies)].copy()
    
    return portfolio


def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA_Report"):
    """Exporta reporte de QA - ROBUSTO."""
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
    
    # Agregar comentarios usando company como key
    if 'company' in df_export.columns:
        df_export['QA_Comment'] = df_export['company'].map(qa_comments_dict)
    else:
        df_export['QA_Comment'] = ''
    
    df_export['QA_Comment'] = df_export['QA_Comment'].fillna('')
    
    # Convertir objetos a strings
    for col in df_export.columns:
        if df_export[col].dtype == 'object':
            df_export[col] = df_export[col].astype(str).str[:32000]
    
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
