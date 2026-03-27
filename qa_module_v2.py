"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QA Module v2.1 — Fixed & Robust
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re


def clean_activities_file(df_raw):
    """
    Limpia el archivo de actividades detectando headers automáticamente.
    ROBUSTO: Maneja múltiples formatos de fecha y errores.
    """
    # Detectar fila de headers
    header_row = None
    for idx, row in df_raw.iterrows():
        row_str = ' '.join([str(v) for v in row.values if pd.notna(v)]).lower()
        if 'user' in row_str and 'date' in row_str and 'customer' in row_str:
            header_row = idx
            break
    
    if header_row is None:
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
    
    # ========================================================================
    # FIXED: Convertir fecha ROBUSTAMENTE
    # ========================================================================
    def parse_date_safe(date_val):
        """Parse date handling multiple formats and errors."""
        if pd.isna(date_val):
            return None
        
        # Si ya es datetime, retornar
        if isinstance(date_val, (pd.Timestamp, datetime)):
            return pd.Timestamp(date_val)
        
        # Convertir a string y limpiar
        date_str = str(date_val).strip()
        
        # Intentar parsear con pandas (maneja la mayoría de formatos)
        try:
            return pd.to_datetime(date_str, errors='coerce')
        except:
            pass
        
        # Intentar formatos específicos
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%b %d, %Y',
            '%B %d, %Y',
        ]
        
        for fmt in date_formats:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except:
                continue
        
        # Si nada funciona, retornar None
        return None
    
    df['date'] = df['date'].apply(parse_date_safe)
    
    # Eliminar filas sin fecha válida
    df = df.dropna(subset=['date'])
    
    if len(df) == 0:
        raise ValueError("No se pudieron parsear fechas válidas en el archivo")
    
    # ========================================================================
    # FIXED: Limpiar customer_number ROBUSTAMENTE
    # ========================================================================
    df['customer_number'] = df['customer_number'].astype(str).str.strip()
    
    # Eliminar valores inválidos
    df = df[df['customer_number'] != '']
    df = df[df['customer_number'] != 'nan']
    df = df[df['customer_number'] != 'None']
    
    # Agregar history si no existe
    if 'history' not in df.columns:
        df['history'] = 'N/A'
    
    # Limpiar history (quitar saltos de línea excesivos)
    df['history'] = df['history'].fillna('N/A').astype(str)
    df['history'] = df['history'].str.replace('\n', ' | ', regex=False)
    df['history'] = df['history'].str.replace('  ', ' ', regex=True)
    
    # Ordenar por fecha descendente
    df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    return df


def merge_aging_with_activities(df_aging, df_activities, customer_col=None, balance_col=None, collector_col=None):
    """
    Cruza Aging con Activities de forma ROBUSTA.
    
    Args:
        df_aging: DataFrame del Aging
        df_activities: DataFrame de actividades
        customer_col: Nombre de columna de customer en Aging (auto-detecta si None)
        balance_col: Nombre de columna de balance en Aging (auto-detecta si None)
        collector_col: Nombre de columna de collector en Aging (auto-detecta si None)
    """
    aging = df_aging.copy()
    
    # ========================================================================
    # Auto-detectar columnas del Aging
    # ========================================================================
    
    # Customer Number
    if customer_col is None:
        for col in aging.columns:
            col_lower = str(col).lower()
            if 'customer' in col_lower or 'client' in col_lower or 'account' in col_lower:
                customer_col = col
                break
        if customer_col is None:
            customer_col = aging.columns[0]  # Asumir primera columna
    
    # Balance / Past Due
    if balance_col is None:
        for col in aging.columns:
            col_lower = str(col).lower()
            if 'balance' in col_lower or 'total' in col_lower or 'amount' in col_lower:
                balance_col = col
                break
        if balance_col is None:
            # Buscar columnas numéricas
            numeric_cols = aging.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                balance_col = numeric_cols[0]
            else:
                balance_col = aging.columns[1]
    
    # Collector
    if collector_col is None:
        for col in aging.columns:
            col_lower = str(col).lower()
            if 'collector' in col_lower or 'cobrador' in col_lower or 'agent' in col_lower:
                collector_col = col
                break
    
    # Company
    company_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'company' in col_lower or 'empresa' in col_lower or 'name' in col_lower:
            company_col = col
            break
    
    # Days Overdue
    days_col = None
    for col in aging.columns:
        col_lower = str(col).lower()
        if 'days' in col_lower or 'días' in col_lower or 'mora' in col_lower:
            days_col = col
            break
    
    # ========================================================================
    # Preparar Aging con nombres estándar
    # ========================================================================
    
    rename_dict = {
        customer_col: 'customer_number',
        balance_col: 'balance'
    }
    
    if collector_col:
        rename_dict[collector_col] = 'collector'
    if company_col:
        rename_dict[company_col] = 'company'
    if days_col:
        rename_dict[days_col] = 'days_overdue'
    
    aging = aging.rename(columns=rename_dict)
    
    # Limpiar customer_number
    aging['customer_number'] = aging['customer_number'].astype(str).str.strip()
    
    # Asegurar que balance sea numérico
    if 'balance' in aging.columns:
        aging['balance'] = pd.to_numeric(aging['balance'], errors='coerce').fillna(0)
    
    # ========================================================================
    # Agregar info de actividades
    # ========================================================================
    
    activities_summary = df_activities.groupby('customer_number').agg({
        'agent': lambda x: ', '.join(sorted(set(x))),  # Agentes únicos
        'date': ['max', 'count'],  # Última actividad y total
        'history': lambda x: ' || '.join([str(h)[:150] for h in x.head(5)])  # Primeras 5
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
    
    # Agregar columna de status texto
    merged['activity_status'] = merged['was_touched'].apply(
        lambda x: '✅ Con Actividad' if x else '⚠️ Sin Actividad'
    )
    
    return merged


def get_agent_portfolio(df_merged, df_activities, agent_name):
    """
    Obtiene el portfolio de un agente específico.
    """
    # Filtrar actividades de ese agente
    agent_acts = df_activities[df_activities['agent'] == agent_name].copy()
    
    # Obtener customer numbers únicos
    agent_customers = agent_acts['customer_number'].unique()
    
    # Filtrar merged
    portfolio = df_merged[df_merged['customer_number'].isin(agent_customers)].copy()
    
    # Agregar detalle de actividades de este agente
    agent_detail = agent_acts.groupby('customer_number').agg({
        'date': ['max', 'count'],
        'history': lambda x: '\n\n'.join([
            f"📅 {pd.to_datetime(d).strftime('%Y-%m-%d')} | {h}" 
            for d, h in zip(x.index.map(agent_acts.set_index(agent_acts.index)['date']), x)
        ])
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
    FIXED: Maneja nombres de columnas problemáticos.
    """
    output = BytesIO()
    
    # Copiar datos
    df_export = df_data.copy()
    
    # ========================================================================
    # FIXED: Limpiar nombres de columnas para Excel
    # ========================================================================
    def clean_column_name(col_name):
        """Limpia nombres de columnas para que sean válidos en Excel."""
        col_str = str(col_name)
        # Remover caracteres problemáticos
        col_str = re.sub(r'[\[\]\'\"<>]', '', col_str)
        # Reemplazar espacios múltiples
        col_str = re.sub(r'\s+', ' ', col_str)
        # Limitar longitud (Excel max = 255)
        col_str = col_str[:255]
        # Si está vacío, usar default
        if not col_str.strip():
            col_str = 'Column'
        return col_str.strip()
    
    # Limpiar nombres de columnas
    df_export.columns = [clean_column_name(col) for col in df_export.columns]
    
    # Agregar comentarios al DataFrame
    df_export['QA_Comment'] = df_export['customer_number'].map(qa_comments_dict)
    df_export['QA_Comment'] = df_export['QA_Comment'].fillna('')
    
    # ========================================================================
    # FIXED: Manejar valores problemáticos en celdas
    # ========================================================================
    
    # Convertir objetos complejos a strings
    for col in df_export.columns:
        if df_export[col].dtype == 'object':
            df_export[col] = df_export[col].astype(str)
            # Truncar strings muy largos
            df_export[col] = df_export[col].str[:32000]  # Límite Excel por celda
    
    # Crear Excel
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='QA Report', index=False)
            
            # Ajustar anchos de columnas
            worksheet = writer.sheets['QA Report']
            for idx, col in enumerate(df_export.columns, 1):
                # Calcular ancho basado en contenido
                max_length = max(
                    df_export[col].astype(str).apply(len).max(),
                    len(str(col))
                )
                # Limitar ancho máximo
                col_width = min(max_length + 2, 100)
                
                # Convertir índice a letra de columna
                col_letter = ''
                num = idx
                while num > 0:
                    num -= 1
                    col_letter = chr(65 + (num % 26)) + col_letter
                    num //= 26
                
                worksheet.column_dimensions[col_letter].width = col_width
    
    except Exception as e:
        # Si falla openpyxl, intentar con xlsxwriter
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, sheet_name='QA Report', index=False)
        except:
            raise Exception(f"Error creando Excel: {str(e)}")
    
    output.seek(0)
    return output
