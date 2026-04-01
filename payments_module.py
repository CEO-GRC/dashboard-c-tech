"""
Payments Module v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Procesa la Sheet 3 de pagos del archivo Aging y genera análisis.
"""
import pandas as pd
import numpy as np
from io import BytesIO


def load_payments_from_aging(file_bytes, sheet_name='Sheet3'):
    """
    Carga la sheet de pagos del archivo Aging.
    
    Args:
        file_bytes: Bytes del archivo Excel
        sheet_name: Nombre de la sheet (default: 'Sheet3')
    
    Returns:
        DataFrame con columnas: collector, amount
    """
    try:
        # Intentar leer Sheet3
        df_raw = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)
        
        # Buscar las columnas correctas
        # Esperamos: "Row Labels" y "Sum of Amount in local currency"
        
        # Mapeo de columnas
        col_collector = None
        col_amount = None
        
        for col in df_raw.columns:
            col_lower = str(col).lower()
            if 'row' in col_lower and 'label' in col_lower:
                col_collector = col
            elif 'sum' in col_lower and 'amount' in col_lower:
                col_amount = col
            elif 'amount' in col_lower and col_amount is None:
                col_amount = col
        
        # Si no encontramos las columnas exactas, usar las primeras dos
        if col_collector is None:
            col_collector = df_raw.columns[0]
        if col_amount is None:
            col_amount = df_raw.columns[1] if len(df_raw.columns) > 1 else df_raw.columns[0]
        
        # Limpiar DataFrame
        df = df_raw[[col_collector, col_amount]].copy()
        df.columns = ['collector', 'amount']
        
        # Remover filas vacías y totales
        df = df.dropna(subset=['collector'])
        df = df[~df['collector'].astype(str).str.lower().str.contains('total|grand', na=False)]
        
        # Limpiar nombres de collectors
        df['collector'] = df['collector'].astype(str).str.strip()
        
        # Convertir amounts a numérico
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
        
        # Remover collectors sin monto
        df = df[df['amount'] > 0].reset_index(drop=True)
        
        return df
        
    except Exception as e:
        raise ValueError(f"Error leyendo pagos de {sheet_name}: {str(e)}")


def calculate_payment_metrics(df_payments, total_ar):
    """
    Calcula métricas de pagos.
    
    Args:
        df_payments: DataFrame con columnas collector, amount
        total_ar: Total AR del portfolio
    
    Returns:
        dict con métricas
    """
    total_collected = df_payments['amount'].sum()
    pct_collected = (total_collected / total_ar * 100) if total_ar > 0 else 0
    
    # Calcular por collector
    df_metrics = df_payments.copy()
    df_metrics['pct_of_total'] = (df_metrics['amount'] / total_collected * 100) if total_collected > 0 else 0
    df_metrics['pct_of_ar'] = (df_metrics['amount'] / total_ar * 100) if total_ar > 0 else 0
    
    # Ordenar por monto
    df_metrics = df_metrics.sort_values('amount', ascending=False).reset_index(drop=True)
    
    # Añadir ranking
    df_metrics['rank'] = range(1, len(df_metrics) + 1)
    
    return {
        'total_collected': total_collected,
        'pct_of_ar': pct_collected,
        'num_collectors': len(df_metrics),
        'avg_per_collector': total_collected / len(df_metrics) if len(df_metrics) > 0 else 0,
        'df_ranking': df_metrics
    }


def export_payments_report(df_ranking, metrics):
    """
    Exporta reporte de pagos a Excel.
    
    Args:
        df_ranking: DataFrame con ranking de collectors
        metrics: dict con métricas generales
    
    Returns:
        BytesIO con archivo Excel
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Ranking
        df_export = df_ranking.copy()
        df_export.columns = ['Collector', 'Amount Collected', '% of Total Collected', '% of AR', 'Rank']
        df_export.to_excel(writer, sheet_name='Ranking', index=False)
        
        # Sheet 2: Summary
        summary_data = {
            'Metric': [
                'Total Collected',
                'Number of Collectors',
                'Average per Collector',
                '% of Total AR Collected'
            ],
            'Value': [
                f"${metrics['total_collected']:,.2f}",
                metrics['num_collectors'],
                f"${metrics['avg_per_collector']:,.2f}",
                f"{metrics['pct_of_ar']:.2f}%"
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    return output
