"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QA Module v2.0 — Simple, Dynamic, Useful
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Diseñado para gerentes que quieren VER datos reales y hacer SU análisis.
No automatizaciones genéricas.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO


def clean_activities_file(df_raw):
    """
    Limpia el archivo de actividades detectando headers automáticamente.
    
    Args:
        df_raw: DataFrame crudo del Excel/CSV subido
        
    Returns:
        DataFrame limpio con columnas estandarizadas
    """
    # Detectar fila de headers (buscar "User", "Date", "Customer Number")
    header_row = None
    for idx, row in df_raw.iterrows():
        row_str = ' '.join([str(v) for v in row.values if pd.notna(v)]).lower()
        if 'user' in row_str and 'date' in row_str and 'customer' in row_str:
            header_row = idx
            break
    
    if header_row is None:
        # Si no encuentra header, asumir que la primera fila es header
        header_row = 0
    
    # Re-leer con el header correcto
    df = df_raw.iloc[header_row:].copy()
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)
    
    # Renombrar columnas a nombres estándar
    column_mapping = {}
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if 'user' in col_lower and 'customer' not in col_lower:
            column_mapping[col] = 'agent'
        elif 'date' in col_lower:
            column_mapping[col] = 'date'
        elif 'customer' in col_lower and 'number' in col_lower:
            column_mapping[col] = 'customer_number'
        elif 'company' in col_lower:
            column_mapping[col] = 'company'
        elif 'history' in col_lower:
            column_mapping[col] = 'history'
        elif 'follow' in col_lower:
            column_mapping[col] = 'follow_up'
        elif 'promised' in col_lower:
            column_mapping[col] = 'promised'
    
    df = df.rename(columns=column_mapping)
    
    # Verificar columnas requeridas
    required = ['agent', 'date', 'customer_number']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")
    
    # Limpiar datos
    df = df.dropna(subset=['customer_number'])
    
    # Convertir fecha
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    
    # Limpiar customer_number (quitar espacios, convertir a string)
    df['customer_number'] = df['customer_number'].astype(str).str.strip()
    
    # Ordenar por fecha descendente
    df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    return df


def merge_aging_with_activities(df_aging, df_activities):
    """
    Cruza Aging con Activities para ver qué cuentas fueron tocadas.
    
    Args:
        df_aging: DataFrame del Aging (del dashboard)
        df_activities: DataFrame de actividades (archivo subido)
        
    Returns:
        DataFrame mergeado con info de actividades
    """
    # Preparar Aging
    aging = df_aging.copy()
    
    # Detectar columna de customer ID en Aging
    customer_col = None
    for col in aging.columns:
        if 'customer' in str(col).lower():
            customer_col = col
            break
    
    if customer_col is None:
        # Asumir que la primera columna es customer
        customer_col = aging.columns[0]
    
    # Renombrar para estandarizar
    aging = aging.rename(columns={customer_col: 'customer_number'})
    aging['customer_number'] = aging['customer_number'].astype(str).str.strip()
    
    # Agregar info de actividades
    activities_summary = df_activities.groupby('customer_number').agg({
        'agent': lambda x: ', '.join(sorted(set(x))),  # Agentes únicos
        'date': ['max', 'count'],  # Última actividad y total
        'history': lambda x: ' | '.join([str(h)[:100] for h in x.head(3)])  # Primeras 3 histories
    }).reset_index()
    
    activities_summary.columns = [
        'customer_number', 
        'agents_assigned', 
        'last_activity_date', 
        'total_activities',
        'recent_history'
    ]
    
    # Merge
    merged = aging.merge(activities_summary, on='customer_number', how='left')
    
    # Calcular días desde última actividad
    today = pd.Timestamp.now()
    merged['days_since_activity'] = merged['last_activity_date'].apply(
        lambda x: (today - x).days if pd.notna(x) else 999
    )
    
    # Marcar si fue tocada
    merged['was_touched'] = merged['total_activities'].notna()
    merged['total_activities'] = merged['total_activities'].fillna(0).astype(int)
    
    return merged


def get_agent_portfolio(df_merged, df_activities, agent_name):
    """
    Obtiene el portfolio de un agente específico.
    
    Args:
        df_merged: DataFrame mergeado (Aging + Activities)
        df_activities: DataFrame de actividades completo
        agent_name: Nombre del agente
        
    Returns:
        DataFrame con las cuentas que tocó ese agente
    """
    # Filtrar actividades de ese agente
    agent_acts = df_activities[df_activities['agent'] == agent_name].copy()
    
    # Obtener customer numbers únicos
    agent_customers = agent_acts['customer_number'].unique()
    
    # Filtrar merged
    portfolio = df_merged[df_merged['customer_number'].isin(agent_customers)].copy()
    
    # Agregar detalle de actividades de este agente en estas cuentas
    agent_detail = agent_acts.groupby('customer_number').agg({
        'date': ['max', 'count'],
        'history': lambda x: '\n\n'.join([f"[{h[0]}] {h[1]}" for h in zip(
            pd.to_datetime(x).dt.strftime('%Y-%m-%d'), x
        )])
    }).reset_index()
    
    agent_detail.columns = [
        'customer_number',
        'agent_last_activity',
        'agent_activity_count',
        'agent_full_history'
    ]
    
    portfolio = portfolio.merge(agent_detail, on='customer_number', how='left')
    
    return portfolio


def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA_Report"):
    """
    Exporta reporte de QA con comentarios del gerente.
    
    Args:
        df_data: DataFrame con los datos
        qa_comments_dict: Dict con {customer_number: comment}
        filename_prefix: Prefijo para el nombre del archivo
        
    Returns:
        BytesIO con el Excel
    """
    output = BytesIO()
    
    # Agregar comentarios al DataFrame
    df_export = df_data.copy()
    df_export['qa_comment'] = df_export['customer_number'].map(qa_comments_dict)
    df_export['qa_comment'] = df_export['qa_comment'].fillna('')
    
    # Crear Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='QA Report', index=False)
        
        # Ajustar anchos de columnas
        worksheet = writer.sheets['QA Report']
        for idx, col in enumerate(df_export.columns, 1):
            max_length = max(
                df_export[col].astype(str).apply(len).max(),
                len(str(col))
            )
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
    
    output.seek(0)
    return output
