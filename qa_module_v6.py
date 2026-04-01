"""
QA Module v7.0 - INTEGRADO CON MERGE ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAMBIOS v7.0:
✓ Integración completa con merge_engine.py
✓ Limpieza estricta pre-merge (espacios, ceros, mayúsculas)
✓ Consolidación de agentes (Collector + Users)
✓ Filtros que FUNCIONAN
✓ Estados correctos (Gestionada/Sin Actividad)
"""
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import re
import string

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MERGE ENGINE - MOTOR DE CRUCE ROBUSTO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
        """Detecta columnas clave del Aging."""
        cols = {}
        
        for col in df.columns:
            c_lower = str(col).lower()
            if 'payer' in c_lower or 'customer' in c_lower or 'cuenta' in c_lower:
                cols['payer'] = col
                break
        
        if 'payer' not in cols and len(df.columns) > 1:
            cols['payer'] = df.columns[1]
        
        for col in df.columns:
            c_lower = str(col).lower()
            if ('name' in c_lower or 'company' in c_lower or 'nombre' in c_lower or 'razon' in c_lower):
                if col != cols.get('payer'):
                    cols['name'] = col
                    break
        
        for col in df.columns:
            c_lower = str(col).lower()
            if 'collector' in c_lower or 'cobrador' in c_lower:
                cols['collector'] = col
                break
        
        for col in df.columns:
            c_lower = str(col).lower()
            if 'total' in c_lower and 'ar' in c_lower:
                cols['total_ar'] = col
                break
        
        self._log(f"Columnas detectadas en Aging: {cols}")
        return cols
    
    def _detect_activities_columns(self, df: pd.DataFrame) -> dict:
        """Detecta columnas clave de Actividades."""
        cols = {}
        
        for col in df.columns:
            c_lower = str(col).lower()
            if 'user' in c_lower or 'agent' in c_lower or 'agente' in c_lower:
                cols['agent'] = col
                break
        
        for col in df.columns:
            c_lower = str(col).lower()
            if 'date' in c_lower or 'fecha' in c_lower:
                cols['date'] = col
                break
        
        for col in df.columns:
            c_lower = str(col).lower()
            # ✅ FIXED: Acepta "Customer", "Customer Number", "Customer #", etc.
            if 'customer' in c_lower or 'cuenta' in c_lower or 'client' in c_lower:
                cols['customer_number'] = col
                break
        
        for col in df.columns:
            c_lower = str(col).lower()
            if 'company' in c_lower or 'nombre' in c_lower or 'name' in c_lower:
                if col != cols.get('customer_number'):
                    cols['company_name'] = col
                    break
        
        for col in df.columns:
            c_lower = str(col).lower()
            if 'history' in c_lower or 'comment' in c_lower or 'note' in c_lower:
                cols['history'] = col
                break
        
        self._log(f"Columnas detectadas en Actividades: {cols}")
        return cols
    
    def _clean_match_key(self, series: pd.Series) -> pd.Series:
        """Limpieza ESTRICTA de llave de matching."""
        cleaned = (
            series
            .astype(str)
            .str.strip()
            .str.lstrip('0')
            .str.upper()
            .replace({'NAN': np.nan, 'NONE': np.nan, '': np.nan})
        )
        return cleaned
    
    def _try_match_customer_number(self, df_aging, df_activities, aging_cols, acts_cols):
        """Intenta matching por Customer Number."""
        if 'payer' not in aging_cols or 'customer_number' not in acts_cols:
            return None
        
        aging = df_aging.copy()
        acts = df_activities.copy()
        
        aging['_match_key'] = self._clean_match_key(aging[aging_cols['payer']])
        acts['_match_key'] = self._clean_match_key(acts[acts_cols['customer_number']])
        
        set_aging = set(aging['_match_key'].dropna())
        set_acts = set(acts['_match_key'].dropna())
        matches = len(set_aging.intersection(set_acts))
        
        if matches > 0:
            self._log(f"✓ Customer Number match: {matches} coincidencias")
            return aging, acts, f"Customer Number ({aging_cols['payer']})"
        
        return None
    
    def _try_match_company_name(self, df_aging, df_activities, aging_cols, acts_cols):
        """Intenta matching por Company Name."""
        if 'name' not in aging_cols or 'company_name' not in acts_cols:
            return None
        
        aging = df_aging.copy()
        acts = df_activities.copy()
        
        aging['_match_key'] = self._clean_match_key(aging[aging_cols['name']])
        acts['_match_key'] = self._clean_match_key(acts[acts_cols['company_name']])
        
        set_aging = set(aging['_match_key'].dropna())
        set_acts = set(acts['_match_key'].dropna())
        matches = len(set_aging.intersection(set_acts))
        
        if matches > 0:
            self._log(f"✓ Company Name match: {matches} coincidencias")
            return aging, acts, f"Company Name ({aging_cols['name']})"
        
        return None
    
    def _try_match_auto(self, df_aging, df_activities):
        """Búsqueda automática de columnas compatibles."""
        best_match = {'aging_col': None, 'acts_col': None, 'score': 0, 'aging': None, 'acts': None}
        
        for col_aging in df_aging.columns:
            if df_aging[col_aging].dtype != 'object':
                continue
            
            aging_temp = df_aging.copy()
            aging_temp['_match_key'] = self._clean_match_key(aging_temp[col_aging])
            set_aging = set(aging_temp['_match_key'].dropna())
            
            for col_acts in df_activities.columns:
                if df_activities[col_acts].dtype != 'object':
                    continue
                
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
            self._log(f"✓ Auto-match: {best_match['aging_col']} ↔ {best_match['acts_col']} "
                     f"({best_match['score']} coincidencias)")
            return (
                best_match['aging'], 
                best_match['acts'], 
                f"Auto ({best_match['aging_col']} ↔ {best_match['acts_col']})"
            )
        
        return None
    
    def _aggregate_activities(self, df_activities, acts_cols):
        """Agrupa actividades por _match_key."""
        acts = df_activities.copy()
        
        if 'agent' in acts_cols:
            acts['agent'] = acts[acts_cols['agent']].astype(str).str.strip()
            acts['agent'] = acts['agent'].replace({
                'nan': 'Sin Agente',
                'NaN': 'Sin Agente',
                'None': 'Sin Agente',
                '': 'Sin Agente'
            })
        else:
            acts['agent'] = 'Sin Agente'
        
        if 'date' in acts_cols:
            acts['date'] = pd.to_datetime(acts[acts_cols['date']], errors='coerce')
        else:
            acts['date'] = pd.Timestamp.now()
        
        if 'history' in acts_cols:
            acts['history'] = acts[acts_cols['history']].fillna('Sin comentarios').astype(str)
        else:
            acts['history'] = 'Sin comentarios'
        
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
        self._log("Iniciando Merge Engine v7.0")
        self._log("=" * 70)
        
        aging_cols = self._detect_aging_columns(df_aging)
        acts_cols = self._detect_activities_columns(df_activities)
        
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
                "❌ No se pudo encontrar una columna compatible para cruzar Aging y Actividades."
            )
        
        self._log("Agregando actividades por cuenta...")
        acts_aggregated = self._aggregate_activities(acts_keyed, acts_cols)
        
        self._log("Ejecutando LEFT JOIN...")
        df_merged = aging_keyed.merge(acts_aggregated, on='_match_key', how='left')
        
        self._log("Consolidando agentes (Collector + Users)...")
        df_merged = self._consolidate_agents(df_merged, aging_cols)
        
        self._log("Calculando métricas finales...")
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
        
        self._log("=" * 70)
        self._log(f"✓ Merge completado: {self.match_method}")
        self._log(f"  • {total_accounts:,} cuentas totales")
        self._log(f"  • {touched_accounts:,} gestionadas ({pct_touched:.1f}%)")
        self._log(f"  • {self.match_stats['total_activities']:,} actividades totales")
        self._log("=" * 70)
        
        return df_merged
    
    def get_stats(self):
        """Retorna estadísticas del último merge."""
        return self.match_stats.copy()
    
    def filter_by_agents(self, df_merged, agent_names):
        """Filtra el DataFrame merged por agentes."""
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
            self._log(f"Filtrado por agentes: {len(filtered):,} de {len(df_merged):,} cuentas")
        
        return filtered


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNCIONES PRINCIPALES DEL MÓDULO QA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def clean_activities_file(df_raw):
    """Limpia el archivo de actividades detectando headers y fechas."""
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
        if 'user' in c or 'agent' in c or 'agente' in c:
            new_cols[col] = 'agent'
        elif 'date' in c or 'fecha' in c:
            new_cols[col] = 'date'
        # ✅ PRIORIDAD 1: Detectar Customer Number primero
        elif ('customer' in c or 'cuenta' in c or 'client' in c) and ('number' in c or 'num' in c or '#' in c or c == 'customer'):
            new_cols[col] = 'customer_number'
        elif 'history' in c or 'comentario' in c or 'comment' in c or 'note' in c:
            new_cols[col] = 'history'
    
    # ✅ SEGUNDA PASADA: Detectar Company solo si no confunde con Customer
    for col in df.columns:
        if col in new_cols:  # Ya fue asignada
            continue
        c = str(col).lower().strip()
        if 'company' in c or 'nombre' in c or 'razon' in c or 'name' in c:
            new_cols[col] = 'company_name'
            break
    
    df = df.rename(columns=new_cols)
    
    # 🔍 DEBUG: Mostrar qué columnas detectó
    print("=" * 60)
    print("🔍 DETECCIÓN DE COLUMNAS EN ACTIVIDADES:")
    if 'agent' in df.columns:
        print(f"  ✅ Agent: OK")
    else:
        print(f"  ❌ Agent: NO DETECTADO")
    
    if 'date' in df.columns:
        print(f"  ✅ Date: OK")
    else:
        print(f"  ❌ Date: NO DETECTADO")
    
    if 'customer_number' in df.columns:
        print(f"  ✅ Customer Number: OK (valores ejemplo: {df['customer_number'].head(3).tolist()})")
    else:
        print(f"  ❌ Customer Number: NO DETECTADO")
    
    if 'company_name' in df.columns:
        print(f"  ✅ Company Name: OK")
    else:
        print(f"  ❌ Company Name: NO DETECTADO")
    
    if 'history' in df.columns:
        print(f"  ✅ History: OK")
    else:
        print(f"  ❌ History: NO DETECTADO")
    print("=" * 60)

    
    if 'agent' not in df.columns:
        df['agent'] = 'Sin Agente'
    
    if 'customer_number' not in df.columns and 'company_name' not in df.columns:
        df['customer_number'] = df.iloc[:, 0]
    
    if 'history' not in df.columns:
        df['history'] = 'N/A'
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
    else:
        df['date'] = pd.Timestamp.now()
    
    df['agent'] = df['agent'].astype(str).str.strip()
    df['agent'] = df['agent'].replace({
        r'(?i)^nan$': 'Sin Agente',
        r'(?i)^n/?a$': 'Sin Agente',
        r'^None$': 'Sin Agente',
        r'^\s*$': 'Sin Agente'
    }, regex=True)
    
    df['history'] = df['history'].fillna('Sin comentarios').astype(str)
    
    return df.sort_values('date', ascending=False).reset_index(drop=True)


def merge_aging_with_activities(df_aging, df_activities, col_payer=None, col_name=None, verbose=True):
    """
    Merge completo usando MergeEngine v7.0.
    
    Args:
        df_aging: DataFrame de Aging
        df_activities: DataFrame de Actividades (ya limpio)
        col_payer: Ignorado (detección automática)
        col_name: Ignorado (detección automática)
        verbose: Mostrar logs
    
    Returns:
        DataFrame merged con todas las métricas
    """
    engine = MergeEngine(verbose=verbose)
    return engine.merge(df_aging, df_activities)


def get_multi_agent_portfolio(df_merged, df_activities, agent_names, col_collector=None, verbose=False):
    """
    Filtra cartera por agentes seleccionados.
    
    Args:
        df_merged: DataFrame merged
        df_activities: Ignorado (ya no se necesita)
        agent_names: Lista de nombres de agentes
        col_collector: Ignorado (usa agentes_consolidados)
        verbose: Mostrar logs
    
    Returns:
        DataFrame filtrado
    """
    engine = MergeEngine(verbose=verbose)
    return engine.filter_by_agents(df_merged, agent_names)


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
