"""
QA Module v7.0 - FIXED FOR REAL DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARREGLOS:
✓ Detecta Payer.1 como Customer Number (no Payer)
✓ Convierte fechas seriales de Excel
✓ Maneja User sin necesidad de renombrar
✓ Normalización extrema de llaves
"""
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re
import string


class MergeEngine:
    """Motor de cruce inteligente y robusto."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.match_method = None
        self.match_stats = {}
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[MergeEngine] {message}")
    
    def _detect_aging_columns(self, df: pd.DataFrame) -> dict:
        """Detecta columnas clave del Aging - FIXED para Payer.1"""
        cols = {}
        
        # BUSCAR CUSTOMER NUMBER - Puede ser Payer.1, Payer Number, Customer, etc.
        for col in df.columns:
            col_str = str(col).lower()
            
            # Buscar columnas que contengan número de customer
            if 'payer.1' in col_str or 'customer' in col_str or 'account' in col_str:
                # Verificar que la columna tenga datos numéricos
                if pd.api.types.is_numeric_dtype(df[col]) or df[col].astype(str).str.isnumeric().any():
                    cols['payer_number'] = col
                    self._log(f"  ✓ Customer Number: {col}")
                    break
        
        # Si no encontró, buscar segunda columna numérica
        if 'payer_number' not in cols:
            for i, col in enumerate(df.columns):
                if i > 0 and (pd.api.types.is_numeric_dtype(df[col]) or df[col].astype(str).str.isnumeric().any()):
                    cols['payer_number'] = col
                    self._log(f"  ✓ Customer Number (por posición): {col}")
                    break
        
        # BUSCAR COMPANY NAME - Generalmente la primera columna
        for col in df.columns:
            col_str = str(col).lower()
            if 'payer' in col_str and '.1' not in col_str:  # Payer sin .1
                cols['name'] = col
                self._log(f"  ✓ Company Name: {col}")
                break
            elif 'company' in col_str or 'name' in col_str:
                cols['name'] = col
                self._log(f"  ✓ Company Name: {col}")
                break
        
        # Si no encontró, usar primera columna
        if 'name' not in cols and len(df.columns) > 0:
            cols['name'] = df.columns[0]
            self._log(f"  ✓ Company Name (por posición): {cols['name']}")
        
        # COLLECTOR
        for col in df.columns:
            if 'collector' in str(col).lower() or 'cobrador' in str(col).lower():
                cols['collector'] = col
                self._log(f"  ✓ Collector: {col}")
                break
        
        # TOTAL AR
        for col in df.columns:
            col_str = str(col).lower()
            if 'total' in col_str and ('ar' in col_str or col == 'Total'):
                cols['total_ar'] = col
                self._log(f"  ✓ Total AR: {col}")
                break
        
        return cols
    
    def _detect_activities_columns(self, df: pd.DataFrame) -> dict:
        """Detecta columnas clave de Actividades - FIXED para User y fechas Excel."""
        cols = {}
        
        # AGENT/USER
        for col in df.columns:
            col_str = str(col).lower()
            if col_str in ['user', 'agent', 'agente', 'usuario']:
                cols['agent'] = col
                self._log(f"  ✓ Agent: {col}")
                break
        
        # DATE
        for col in df.columns:
            col_str = str(col).lower()
            if 'date' in col_str or 'fecha' in col_str:
                cols['date'] = col
                self._log(f"  ✓ Date: {col}")
                break
        
        # CUSTOMER NUMBER
        for col in df.columns:
            col_str = str(col).lower()
            if 'customer' in col_str and 'number' in col_str:
                cols['customer_number'] = col
                self._log(f"  ✓ Customer Number: {col}")
                break
        
        # COMPANY NAME
        for col in df.columns:
            col_str = str(col).lower()
            if 'company' in col_str or 'nombre' in col_str:
                if col != cols.get('customer_number'):
                    cols['company_name'] = col
                    self._log(f"  ✓ Company Name: {col}")
                    break
        
        # HISTORY
        for col in df.columns:
            col_str = str(col).lower()
            if 'history' in col_str or 'comment' in col_str or 'note' in col_str:
                cols['history'] = col
                self._log(f"  ✓ History: {col}")
                break
        
        return cols
    
    def _clean_match_key(self, series: pd.Series) -> pd.Series:
        """Limpieza EXTREMA de llave de matching."""
        cleaned = (
            series
            .astype(str)
            .str.strip()
            .str.lstrip('0')  # Quitar ceros a la izquierda
            .str.upper()
            .str.replace(r'[^\w]', '', regex=True)  # Quitar caracteres especiales
            .replace({'NAN': np.nan, 'NONE': np.nan, '': np.nan})
        )
        return cleaned
    
    def _try_match_customer_number(self, df_aging, df_activities, aging_cols, acts_cols):
        """Intenta matching por Customer Number."""
        aging_key = aging_cols.get('payer_number')
        acts_key = acts_cols.get('customer_number')
        
        if not aging_key or not acts_key:
            self._log("  ✗ No hay columnas de Customer Number en ambos archivos")
            return None
        
        aging = df_aging.copy()
        acts = df_activities.copy()
        
        # Limpiar llaves
        aging['_match_key'] = self._clean_match_key(aging[aging_key])
        acts['_match_key'] = self._clean_match_key(acts[acts_key])
        
        # Validar matches
        set_aging = set(aging['_match_key'].dropna())
        set_acts = set(acts['_match_key'].dropna())
        matches = len(set_aging.intersection(set_acts))
        
        if matches > 0:
            self._log(f"  ✓ Customer Number match: {matches} coincidencias")
            self._log(f"    - Aging key: {aging_key}")
            self._log(f"    - Activities key: {acts_key}")
            return aging, acts, f"Customer Number ({aging_key} ↔ {acts_key})"
        else:
            self._log(f"  ✗ Customer Number: 0 coincidencias")
            # Debug
            self._log(f"    - Ejemplos Aging: {list(set_aging)[:5]}")
            self._log(f"    - Ejemplos Activities: {list(set_acts)[:5]}")
        
        return None
    
    def _try_match_company_name(self, df_aging, df_activities, aging_cols, acts_cols):
        """Intenta matching por Company Name."""
        aging_key = aging_cols.get('name')
        acts_key = acts_cols.get('company_name')
        
        if not aging_key or not acts_key:
            self._log("  ✗ No hay columnas de Company Name en ambos archivos")
            return None
        
        aging = df_aging.copy()
        acts = df_activities.copy()
        
        aging['_match_key'] = self._clean_match_key(aging[aging_key])
        acts['_match_key'] = self._clean_match_key(acts[acts_key])
        
        set_aging = set(aging['_match_key'].dropna())
        set_acts = set(acts['_match_key'].dropna())
        matches = len(set_aging.intersection(set_acts))
        
        if matches > 0:
            self._log(f"  ✓ Company Name match: {matches} coincidencias")
            return aging, acts, f"Company Name ({aging_key} ↔ {acts_key})"
        else:
            self._log(f"  ✗ Company Name: 0 coincidencias")
        
        return None
    
    def _try_match_auto(self, df_aging, df_activities):
        """Búsqueda automática de columnas compatibles."""
        best_match = {'aging_col': None, 'acts_col': None, 'score': 0, 'aging': None, 'acts': None}
        
        self._log("  Intentando auto-match...")
        
        for col_aging in df_aging.columns:
            aging_temp = df_aging.copy()
            aging_temp['_match_key'] = self._clean_match_key(aging_temp[col_aging])
            set_aging = set(aging_temp['_match_key'].dropna())
            
            for col_acts in df_activities.columns:
                acts_temp = df_activities.copy()
                acts_temp['_match_key'] = self._clean_match_key(acts_temp[col_acts])
                set_acts = set(acts_temp['_match_key'].dropna())
                
                matches = len(set_aging.intersection(set_acts))
                
                if matches > best_match['score']:
                    best_match = {
                        'aging_col': col_aging,
                        'acts_col': col_acts,
                        'score': matches,
                        'aging': aging_temp,
                        'acts': acts_temp
                    }
        
        if best_match['score'] > 0:
            self._log(f"  ✓ Auto-match: {best_match['aging_col']} ↔ {best_match['acts_col']} "
                     f"({best_match['score']} coincidencias)")
            return (
                best_match['aging'], 
                best_match['acts'], 
                f"Auto ({best_match['aging_col']} ↔ {best_match['acts_col']})"
            )
        
        self._log("  ✗ Auto-match: No encontró coincidencias")
        return None
    
    def _aggregate_activities(self, df_activities, acts_cols):
        """Agrupa actividades por _match_key."""
        acts = df_activities.copy()
        
        # Limpiar agentes
        agent_col = acts_cols.get('agent')
        if agent_col:
            acts['agent'] = acts[agent_col].astype(str).str.strip()
            acts['agent'] = acts['agent'].replace({
                'nan': 'Sin Agente',
                'NaN': 'Sin Agente',
                'None': 'Sin Agente',
                '': 'Sin Agente'
            })
        else:
            acts['agent'] = 'Sin Agente'
        
        # Convertir fechas - MANEJAR FECHAS SERIALES DE EXCEL
        date_col = acts_cols.get('date')
        if date_col:
            # Primero intentar conversión directa
            acts['date'] = pd.to_datetime(acts[date_col], errors='coerce')
            
            # Si hay NaT, intentar como fecha serial de Excel
            if acts['date'].isna().any():
                def convert_excel_date(val):
                    try:
                        if pd.isna(val):
                            return pd.NaT
                        # Si es numérico, asumrir que es fecha serial de Excel
                        if isinstance(val, (int, float)):
                            # Excel epoch: 1899-12-30
                            return pd.Timestamp('1899-12-30') + pd.Timedelta(days=val)
                        return pd.to_datetime(val, errors='coerce')
                    except:
                        return pd.NaT
                
                acts['date'] = acts[date_col].apply(convert_excel_date)
        else:
            acts['date'] = pd.Timestamp.now()
        
        # History
        history_col = acts_cols.get('history')
        if history_col:
            acts['history'] = acts[history_col].fillna('Sin comentarios').astype(str)
        else:
            acts['history'] = 'Sin comentarios'
        
        # Agrupar
        agg_dict = {
            'agent': lambda x: ', '.join(sorted(set([a for a in x if a != 'Sin Agente']))),
            'date': ['max', 'count'],
            'history': lambda x: ' || '.join([str(h)[:200] for h in list(x)[:5]])
        }
        
        grouped = acts.groupby('_match_key').agg(agg_dict).reset_index()
        grouped.columns = [
            '_match_key',
            'agents_assigned',
            'last_activity_date',
            'total_activities',
            'recent_history'
        ]
        
        grouped['agents_assigned'] = grouped['agents_assigned'].replace({
            '': 'Sin Asignar',
            'nan': 'Sin Asignar'
        })
        
        return grouped
    
    def _consolidate_agents(self, df_merged, aging_cols):
        """Consolida Collector (asignado) + Users (que tocaron)."""
        merged = df_merged.copy()
        collector_col = aging_cols.get('collector')
        
        def consolidate_row(row):
            agents = set()
            
            if collector_col and collector_col in row.index:
                val = str(row[collector_col]).strip()
                if val and val not in ['nan', 'NaN', 'None', '']:
                    agents.add(val)
            
            if 'agents_assigned' in row.index:
                val = str(row['agents_assigned']).strip()
                if val and val not in ['Sin Asignar', 'nan', 'NaN', 'None', '']:
                    for agent in val.split(','):
                        agent = agent.strip()
                        if agent:
                            agents.add(agent)
            
            if agents:
                return ', '.join(sorted(agents))
            return 'Sin Asignar'
        
        merged['agentes_consolidados'] = merged.apply(consolidate_row, axis=1)
        return merged
    
    def _calculate_metrics(self, df_merged):
        """Calcula todas las métricas finales."""
        merged = df_merged.copy()
        today = pd.Timestamp.now()
        
        merged['total_activities'] = merged['total_activities'].fillna(0).astype(int)
        merged['was_touched'] = merged['total_activities'] > 0
        merged['estado'] = merged['was_touched'].apply(
            lambda x: '✅ Gestionada' if x else '⚠️ Sin Actividad'
        )
        
        merged['days_since_activity'] = merged['last_activity_date'].apply(
            lambda x: (today - x).days if pd.notna(x) else 9999
        )
        
        merged['last_activity_date_formatted'] = merged['last_activity_date'].apply(
            lambda x: x.strftime('%b %d, %Y') if pd.notna(x) else 'Never'
        )
        
        merged['activity_status'] = merged.apply(
            lambda row: '✅ Con Actividad' if row['was_touched'] else '⚠️ Sin Actividad',
            axis=1
        )
        
        merged['recent_history'] = merged['recent_history'].fillna('Sin actividad registrada')
        
        return merged
    
    def merge(self, df_aging, df_activities, force_method=None):
        """Ejecuta el merge completo."""
        self._log("=" * 70)
        self._log("🚀 Merge Engine v7.0 - FIXED")
        self._log("=" * 70)
        
        self._log("\n📋 DETECTANDO COLUMNAS...")
        aging_cols = self._detect_aging_columns(df_aging)
        acts_cols = self._detect_activities_columns(df_activities)
        
        self._log("\n🔍 INTENTANDO MATCHING...")
        result = None
        
        if force_method == 'customer' or force_method is None:
            result = self._try_match_customer_number(df_aging, df_activities, aging_cols, acts_cols)
            if result:
                aging_keyed, acts_keyed, method = result
                self.match_method = method
        
        if result is None and (force_method == 'company' or force_method is None):
            result = self._try_match_company_name(df_aging, df_activities, aging_cols, acts_cols)
            if result:
                aging_keyed, acts_keyed, method = result
                self.match_method = method
        
        if result is None and (force_method == 'auto' or force_method is None):
            result = self._try_match_auto(df_aging, df_activities)
            if result:
                aging_keyed, acts_keyed, method = result
                self.match_method = method
        
        if result is None:
            raise ValueError(
                "❌ No se pudo encontrar una columna compatible para cruzar.\n"
                f"Aging cols: {aging_cols}\n"
                f"Activities cols: {acts_cols}"
            )
        
        self._log("\n⚙️ PROCESANDO...")
        self._log("  • Agregando actividades...")
        acts_aggregated = self._aggregate_activities(acts_keyed, acts_cols)
        
        self._log("  • Ejecutando LEFT JOIN...")
        df_merged = aging_keyed.merge(acts_aggregated, on='_match_key', how='left')
        
        self._log("  • Consolidando agentes...")
        df_merged = self._consolidate_agents(df_merged, aging_cols)
        
        self._log("  • Calculando métricas...")
        df_merged = self._calculate_metrics(df_merged)
        
        df_merged['_merge_method'] = self.match_method
        df_merged['_merge_timestamp'] = pd.Timestamp.now()
        
        total_accounts = len(df_merged)
        touched_accounts = df_merged['was_touched'].sum()
        pct_touched = (touched_accounts / total_accounts * 100) if total_accounts > 0 else 0
        
        self.match_stats = {
            'method': self.match_method,
            'total_accounts': total_accounts,
            'touched_accounts': int(touched_accounts),
            'untouched_accounts': int(total_accounts - touched_accounts),
            'pct_touched': pct_touched,
            'total_activities': int(df_merged['total_activities'].sum()),
            'unique_agents': len(df_merged['agentes_consolidados'].str.split(',').explode().unique())
        }
        
        self._log("\n" + "=" * 70)
        self._log(f"✅ MERGE COMPLETADO")
        self._log(f"   Método: {self.match_method}")
        self._log(f"   Cuentas: {total_accounts:,}")
        self._log(f"   Gestionadas: {touched_accounts:,} ({pct_touched:.1f}%)")
        self._log(f"   Actividades: {self.match_stats['total_activities']:,}")
        self._log(f"   Agentes únicos: {self.match_stats['unique_agents']}")
        self._log("=" * 70)
        
        return df_merged
    
    def get_stats(self):
        return self.match_stats.copy()
    
    def filter_by_agents(self, df_merged, agent_names):
        if not agent_names or '📊 Todos los agentes' in agent_names:
            return df_merged.copy()
        
        def row_has_agent(row):
            agents_str = str(row.get('agentes_consolidados', '')).strip()
            if not agents_str or agents_str in ['Sin Asignar', 'nan', 'NaN']:
                return False
            
            row_agents = [a.strip() for a in agents_str.split(',')]
            return any(agent in row_agents for agent in agent_names)
        
        filtered = df_merged[df_merged.apply(row_has_agent, axis=1)].copy()
        
        if self.verbose:
            self._log(f"Filtrado: {len(filtered):,} de {len(df_merged):,} cuentas")
        
        return filtered


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNCIONES PRINCIPALES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def clean_activities_file(df_raw):
    """Limpia el archivo de actividades - SIN CAMBIOS, ya funciona bien."""
    # Ya no busca headers porque el archivo viene con headers correctos
    df = df_raw.copy()
    
    # NO renombrar columnas, usar las que vienen
    # El motor las detecta automáticamente
    
    # Limpiar valores
    for col in df.columns:
        col_lower = str(col).lower()
        if 'user' in col_lower or 'agent' in col_lower:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({
                'nan': 'Sin Agente',
                'NaN': 'Sin Agente',
                'None': 'Sin Agente',
                '': 'Sin Agente'
            })
    
    return df


def merge_aging_with_activities(df_aging, df_activities, col_payer=None, col_name=None, verbose=False):
    """Merge usando MergeEngine v7.0 FIXED."""
    engine = MergeEngine(verbose=verbose)
    return engine.merge(df_aging, df_activities)


def get_multi_agent_portfolio(df_merged, df_activities, agent_names, col_collector=None, verbose=False):
    """Filtra por agentes."""
    engine = MergeEngine(verbose=verbose)
    return engine.filter_by_agents(df_merged, agent_names)


def calculate_productivity_metrics(df_merged, df_payments, col_collector=None, col_total=None):
    """Calcula métricas de productividad."""
    if col_collector is None:
        for col in df_merged.columns:
            if 'collector' in str(col).lower():
                col_collector = col
                break
    
    if col_total is None:
        for col in df_merged.columns:
            if 'total' in str(col).lower():
                col_total = col
                break
    
    # Agrupar por collector
    prod = df_merged.groupby('agentes_consolidados').agg({
        '_match_key': 'count',
        'was_touched': 'sum',
        'total_activities': 'sum',
        col_total: 'sum' if col_total else lambda x: 0
    }).reset_index()
    
    prod.columns = ['collector', 'cuentas_asignadas', 'cuentas_gestionadas', 'total_actividades', 'saldo_total']
    
    # Merge con pagos
    if df_payments is not None and len(df_payments) > 0:
        payments_agg = df_payments.groupby('collector')['amount'].sum().reset_index()
        payments_agg.columns = ['collector', 'monto_cobrado']
        prod = prod.merge(payments_agg, on='collector', how='left')
    else:
        prod['monto_cobrado'] = 0
    
    prod['monto_cobrado'] = prod['monto_cobrado'].fillna(0)
    
    # Calcular métricas
    prod['penetracion_pct'] = (prod['cuentas_gestionadas'] / prod['cuentas_asignadas'] * 100).fillna(0)
    prod['efectividad'] = (prod['monto_cobrado'] / prod['total_actividades']).fillna(0)
    
    # Ranking
    prod = prod.sort_values('monto_cobrado', ascending=False).reset_index(drop=True)
    prod['rank'] = range(1, len(prod) + 1)
    
    return prod


def export_productivity_report(df_prod):
    """Exporta reporte de productividad."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_prod.to_excel(writer, sheet_name='Productivity', index=False)
    output.seek(0)
    return output


def export_qa_report(df_data, qa_comments_dict, filename_prefix="QA"):
    """Exporta reporte QA."""
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
