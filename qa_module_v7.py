"""
QA Module v7.0 - FIXED: Merge Pipeline & Productivity Metrics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REEMPLAZA: qa_module_v6.py

Correcciones v7.0:
- Limpieza EXTREMA de llaves primarias (Payer/Customer)
- Normalización robusta: strip, upper, remove leading zeros, special chars
- Detección automática mejorada de columnas
- Nueva función: calculate_productivity_metrics()
"""
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re
import string


def normalize_key(value):
    """
    Normalización EXTREMA de llaves para matching.
    
    Proceso:
    1. Convertir a string
    2. Strip espacios
    3. Remover ceros a la izquierda
    4. Remover caracteres especiales
    5. Upper case
    6. Remover espacios internos
    """
    if pd.isna(value) or value == '' or str(value).lower() in ['nan', 'none', 'null']:
        return 'MISSING_KEY'
    
    # Convertir a string y limpiar
    s = str(value).strip()
    
    # Remover ceros a la izquierda SOLO si es numérico
    if s.isdigit():
        s = str(int(s))
    
    # Remover caracteres especiales pero mantener alfanuméricos
    s = re.sub(r'[^A-Za-z0-9]', '', s)
    
    # Upper y sin espacios
    s = s.upper().replace(' ', '')
    
    return s if s else 'MISSING_KEY'


def clean_activities_file(df_raw):
    """
    Limpia el archivo de actividades detectando headers y fechas.
    Retorna: DataFrame con columnas: agent, date, customer_number, history
    """
    # Buscar la fila de headers
    header_row = 0
    for idx in range(min(15, len(df_raw))):
        row_str = ' '.join([str(v) for v in df_raw.iloc[idx].values if pd.notna(v)]).lower()
        if 'user' in row_str or 'date' in row_str or 'agent' in row_str or 'customer' in row_str:
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
        elif 'customer' in c or 'cuenta' in c or 'client' in c or 'numero' in c or 'number' in c:
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
        for col in reversed(df.columns):
            if df[col].dtype == 'object':
                df['history'] = df[col]
                break
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
    
    # NORMALIZAR LLAVES CON FUNCIÓN EXTREMA
    if 'customer_number' in df.columns:
        df['_match_customer'] = df['customer_number'].apply(normalize_key)
    
    if 'company_name' in df.columns:
        df['_match_company'] = df['company_name'].apply(normalize_key)
    
    # Fallback: usar primera columna
    if '_match_customer' not in df.columns and '_match_company' not in df.columns:
        for col in df.columns:
            if col not in ['agent', 'date', 'history']:
                df['_match_customer'] = df[col].apply(normalize_key)
                break
    
    df['history'] = df['history'].fillna('Sin comentarios').astype(str)
    
    return df.sort_values('date', ascending=False).reset_index(drop=True)


def merge_aging_with_activities(df_aging, df_activities, col_payer=None, col_name=None):
    """
    Merge ROBUSTO usando normalización extrema de llaves.
    NUEVO v7.0: Limpieza agresiva y diagnóstico detallado
    """
    aging = df_aging.copy()
    acts = df_activities.copy()
    
    # IDENTIFICAR COLUMNAS DE AGING
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
                if col != col_payer and 'payer' not in col_lower:
                    col_name = col
                    break
    
    # CREAR MATCH KEY CON NORMALIZACIÓN EXTREMA
    match_key = None
    match_method = 'Unknown'
    acts_match_col = None
    
    # PRIORIDAD 1: Customer Number (Payer)
    if col_payer and col_payer in aging.columns and '_match_customer' in acts.columns:
        aging['_match_key'] = aging[col_payer].apply(normalize_key)
        acts_match_col = '_match_customer'
        match_key = '_match_key'
        match_method = f'Customer Number ({col_payer})'
    
    # PRIORIDAD 2: Company Name
    elif col_name and col_name in aging.columns and '_match_company' in acts.columns:
        aging['_match_key'] = aging[col_name].apply(normalize_key)
        acts_match_col = '_match_company'
        match_key = '_match_key'
        match_method = f'Company Name ({col_name})'
    
    # PRIORIDAD 3: Auto-detect mejor match
    else:
        best_match = {'aging_col': None, 'acts_col': None, 'score': 0}
        
        for c_age in aging.columns:
            if aging[c_age].dtype == 'object' or pd.api.types.is_numeric_dtype(aging[c_age]):
                set_age = set(aging[c_age].dropna().apply(normalize_key))
                
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
            aging['_match_key'] = aging[best_match['aging_col']].apply(normalize_key)
            acts_match_col = best_match['acts_col']
            match_key = '_match_key'
            match_method = f"Auto ({best_match['aging_col']}) - {best_match['score']} matches"
        else:
            raise ValueError("❌ ERROR: No se encontraron columnas compatibles para el cruce.")
    
    # AGREGAR ACTIVIDADES POR LLAVE
    agg_dict = {
        'agent': lambda x: ', '.join(sorted(set([a for a in x if a != 'Sin Agente']))),
        'date': ['max', 'count'],
        'history': lambda x: ' || '.join([str(h)[:200] for h in list(x)[:5] if str(h) != 'Sin comentarios'])
    }
    
    agg = acts.groupby(acts_match_col).agg(agg_dict).reset_index()
    agg.columns = ['_match_key', 'agents_assigned', 'last_activity_date', 'total_activities', 'recent_history']
    
    # MERGE
    merged = aging.merge(agg, on='_match_key', how='left')
    
    # CALCULAR MÉTRICAS
    today = pd.Timestamp.now()
    
    merged['days_since_activity'] = merged['last_activity_date'].apply(
        lambda x: (today - x).days if pd.notna(x) else 9999
    )
    
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
    VERSIÓN 7.0: Normalización de nombres de agentes
    """
    if not agent_names or '📊 Todos los agentes' in agent_names:
        return df_merged.copy()
    
    # Normalizar nombres de agentes para matching
    agent_names_normalized = [name.strip().upper() for name in agent_names]
    
    # 1. Obtener llaves de clientes que el agente tocó
    agent_acts = df_activities[
        df_activities['agent'].str.strip().str.upper().isin(agent_names_normalized)
    ].copy()
    
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
        # A) ¿El agente tocó esta cuenta?
        if '_match_key' in row.index and row['_match_key'] in keys_touched:
            return True
        
        # B) ¿Está en agents_assigned?
        if 'agents_assigned' in row.index:
            agents_str = str(row['agents_assigned']).strip().upper()
            if pd.notna(agents_str) and agents_str not in ['', 'SIN ASIGNAR', 'NAN']:
                row_agents = [a.strip().upper() for a in agents_str.split(',') if a.strip()]
                if any(ag in row_agents for ag in agent_names_normalized):
                    return True
        
        # C) ¿Está asignada en el Aging original?
        if col_collector and col_collector in row.index:
            val = str(row[col_collector]).strip().upper()
            if pd.notna(row[col_collector]) and val in agent_names_normalized:
                return True
        
        return False
    
    filtered = df_merged[df_merged.apply(row_belongs_to_agent, axis=1)].copy()
    
    return filtered


def calculate_productivity_metrics(df_merged, df_payments, col_collector=None, col_total=None):
    """
    NUEVA FUNCIÓN v7.0: Calcula métricas de productividad por agente/collector.
    
    Args:
        df_merged: DataFrame resultado del merge aging + activities
        df_payments: DataFrame con columnas ['collector', 'amount']
        col_collector: Nombre de columna Collector en aging
        col_total: Nombre de columna Total AR en aging
    
    Returns:
        DataFrame con métricas de productividad
    """
    # Detectar columna de collector si no se provee
    if col_collector is None:
        for col in df_merged.columns:
            if 'collector' in str(col).lower() or 'cobrador' in str(col).lower():
                col_collector = col
                break
    
    if col_collector is None:
        raise ValueError("❌ No se encontró columna de Collector en el aging")
    
    # Detectar columna de total AR
    if col_total is None:
        for col in df_merged.columns:
            col_lower = str(col).lower()
            if 'total' in col_lower and ('ar' in col_lower or 'balance' in col_lower):
                col_total = col
                break
    
    if col_total is None:
        for col in df_merged.columns:
            if pd.api.types.is_numeric_dtype(df_merged[col]):
                col_total = col
                break
    
    # PASO 1: Agrupar por collector en aging
    aging_agg = df_merged.groupby(col_collector, as_index=False).agg({
        'was_touched': 'sum',
        'total_activities': 'sum',
        col_total: 'sum'
    })
    
    counts = df_merged.groupby(col_collector).size().reset_index(name='cuentas_asignadas')
    aging_agg = aging_agg.merge(counts, on=col_collector, how='left')
    
    aging_agg = aging_agg.rename(columns={
        col_collector: 'collector',
        'was_touched': 'cuentas_gestionadas',
        'total_activities': 'total_actividades',
        col_total: 'balance_asignado'
    })
    
    # Calcular penetración
    aging_agg['penetracion_pct'] = (
        aging_agg['cuentas_gestionadas'] / aging_agg['cuentas_asignadas'] * 100
    ).fillna(0).round(2)
    
    # PASO 2: Merge con payments
    if df_payments is not None and len(df_payments) > 0:
        payments_norm = df_payments.copy()
        payments_norm['collector_clean'] = payments_norm['collector'].str.strip().str.upper()
        
        aging_agg['collector_clean'] = aging_agg['collector'].str.strip().str.upper()
        
        productivity = aging_agg.merge(
            payments_norm[['collector_clean', 'amount']],
            on='collector_clean',
            how='left'
        )
        
        productivity = productivity.rename(columns={'amount': 'monto_cobrado'})
        productivity['monto_cobrado'] = productivity['monto_cobrado'].fillna(0)
    else:
        productivity = aging_agg.copy()
        productivity['monto_cobrado'] = 0
        productivity['collector_clean'] = productivity['collector'].str.strip().str.upper()
    
    # PASO 3: Calcular efectividad
    productivity['efectividad'] = (
        productivity['monto_cobrado'] / productivity['total_actividades']
    ).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    
    # Ordenar por monto cobrado
    productivity = productivity.sort_values('monto_cobrado', ascending=False).reset_index(drop=True)
    
    # Añadir ranking
    productivity['rank'] = range(1, len(productivity) + 1)
    
    # Limpiar columnas temporales
    productivity = productivity.drop(columns=['collector_clean'], errors='ignore')
    
    return productivity


def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA"):
    """Exporta reporte QA a Excel."""
    output = BytesIO()
    df_export = df_data.copy()
    
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
    
    match_key_col = None
    for col in df_export.columns:
        if 'match' in col.lower() and 'key' in col.lower():
            match_key_col = col
            break
    
    if match_key_col:
        df_export['QA_Comment'] = df_export[match_key_col].map(qa_comments_dict).fillna('')
    else:
        df_export['QA_Comment'] = ''
    
    priority_keywords = ['customer', 'company', 'balance', 'last_activity', 
                        'collector', 'activity', 'total', 'agents', 'QA']
    priority_cols = []
    for keyword in priority_keywords:
        matching = [c for c in df_export.columns if keyword.lower() in c.lower()]
        priority_cols.extend(matching)
    
    other_cols = [c for c in df_export.columns if c not in priority_cols]
    final_order = priority_cols + other_cols
    df_export = df_export[[c for c in final_order if c in df_export.columns]]
    
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


def export_productivity_report(df_productivity, filename="Productivity_Report.xlsx"):
    """Exporta reporte de productividad a Excel."""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export = df_productivity.copy()
        
        df_export['penetracion_display'] = df_export['penetracion_pct'].apply(lambda x: f"{x:.1f}%")
        df_export['monto_display'] = df_export['monto_cobrado'].apply(lambda x: f"${x:,.2f}")
        df_export['efectividad_display'] = df_export['efectividad'].apply(lambda x: f"${x:,.2f}")
        df_export['balance_display'] = df_export['balance_asignado'].apply(lambda x: f"${x:,.2f}")
        
        columns_order = [
            'rank', 'collector', 'cuentas_asignadas', 'cuentas_gestionadas',
            'penetracion_display', 'total_actividades', 'monto_display',
            'efectividad_display', 'balance_display'
        ]
        
        df_export_final = df_export[[c for c in columns_order if c in df_export.columns]].copy()
        df_export_final.columns = [
            'Rank', 'Collector', 'Cuentas Asignadas', 'Cuentas Gestionadas',
            'Penetración %', 'Total Actividades', 'Monto Cobrado',
            'Efectividad ($/Act)', 'Balance Asignado'
        ]
        
        df_export_final.to_excel(writer, sheet_name='Productividad', index=False)
        
        summary_data = {
            'Métrica': [
                'Total Collectors', 'Total Cuentas Asignadas', 'Total Cuentas Gestionadas',
                'Penetración Promedio', 'Total Actividades', 'Total Cobrado', 'Efectividad Promedio'
            ],
            'Valor': [
                len(df_productivity),
                f"{df_productivity['cuentas_asignadas'].sum():.0f}",
                f"{df_productivity['cuentas_gestionadas'].sum():.0f}",
                f"{df_productivity['penetracion_pct'].mean():.1f}%",
                f"{df_productivity['total_actividades'].sum():.0f}",
                f"${df_productivity['monto_cobrado'].sum():,.2f}",
                f"${df_productivity['efectividad'].mean():,.2f}"
            ]
        }
        
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Resumen', index=False)
    
    output.seek(0)
    return output
