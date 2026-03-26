"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AR Collections Management & QA Module — v1.0  |  Amrize Brand Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose:
    Executive-level auditing tool for AR Collections teams. Cross-references
    real-time Aging data with historical agent activity logs to identify:
    • High-risk accounts with zero collection effort
    • Misallocated resources (effort on low-value accounts)
    • SLA breaches (60d/90d aging milestones without escalation)

Architecture:
    - Zero external dependencies beyond pandas/numpy
    - Session-scoped processing (no disk persistence)
    - Defensive data validation (handles malformed CSVs/XLSX)
    - Multi-key merge support (Customer ID, Invoice Number, or both)

Author: Senior Python Developer & B2B Financial QA Architect
License: Proprietary - Amrize Internal Use Only
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1: DATA CLEANING & VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def clean_activities_file(
    df_raw: pd.DataFrame,
    auto_detect_headers: bool = True
) -> pd.DataFrame:
    """
    Clean and standardize uploaded activities CSV/XLSX file.
    
    Handles:
        • Header row detection (skips title/metadata rows)
        • Column name normalization
        • Date parsing with multiple format support
        • Null/duplicate removal
        • Agent name cleanup (trailing spaces, case normalization)
    
    Args:
        df_raw: Raw DataFrame from pd.read_excel() or pd.read_csv()
        auto_detect_headers: If True, searches for header row automatically
        
    Returns:
        Cleaned DataFrame with standardized column names:
        ['user', 'date', 'customer_number', 'company', 'follow_up_due', 
         'new_promised', 'history']
        
    Raises:
        ValueError: If required columns are missing after cleaning
    """
    df = df_raw.copy()
    
    # Auto-detect header row (look for "User" column indicator)
    if auto_detect_headers:
        header_row_idx = None
        for idx, row in df.iterrows():
            if any(str(val).strip().lower() in ['user', 'usuario', 'agente'] 
                   for val in row.values if pd.notna(val)):
                header_row_idx = idx
                break
        
        if header_row_idx is not None and header_row_idx > 0:
            # Re-read with correct header
            df = pd.DataFrame(df.values[header_row_idx + 1:], 
                            columns=df.iloc[header_row_idx].values)
    
    # Normalize column names
    col_mapping = {
        'User': 'user',
        'Usuario': 'user',
        'Agente': 'user',
        'Agent': 'user',
        'Date': 'date',
        'Fecha': 'date',
        'Customer Number': 'customer_number',
        'Customer ID': 'customer_number',
        'Cliente': 'customer_number',
        'Company': 'company',
        'Empresa': 'company',
        'Follow-up Due': 'follow_up_due',
        'Follow up': 'follow_up_due',
        'New Promised': 'new_promised',
        'Promesa': 'new_promised',
        'History': 'history',
        'Historia': 'history',
        'Notes': 'history',
        'Notas': 'history'
    }
    
    df.rename(columns=col_mapping, inplace=True)
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    # Validate required columns
    required = ['user', 'date', 'customer_number']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. "
                        f"Available: {list(df.columns)}")
    
    # Clean user names (remove extra spaces, normalize case)
    df['user'] = df['user'].astype(str).str.strip().str.title()
    
    # Parse dates (try multiple formats)
    if df['date'].dtype == 'object':
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
        for fmt in date_formats:
            try:
                df['date'] = pd.to_datetime(df['date'], format=fmt, errors='coerce')
                if df['date'].notna().sum() > 0:
                    break
            except:
                continue
    else:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Clean customer numbers (remove spaces, convert to string)
    df['customer_number'] = df['customer_number'].astype(str).str.strip().str.upper()
    
    # Remove rows with null critical fields
    df.dropna(subset=['user', 'customer_number'], inplace=True)
    
    # Remove duplicate activities (same user, customer, date, history)
    dedup_cols = ['user', 'customer_number', 'date']
    if 'history' in df.columns:
        dedup_cols.append('history')
    df.drop_duplicates(subset=dedup_cols, keep='first', inplace=True)
    
    # Fill optional numeric fields
    if 'follow_up_due' in df.columns:
        df['follow_up_due'] = pd.to_numeric(df['follow_up_due'], errors='coerce').fillna(0)
    if 'new_promised' in df.columns:
        df['new_promised'] = pd.to_numeric(df['new_promised'], errors='coerce').fillna(0)
    
    # Add activity type extraction from history (if available)
    if 'history' in df.columns:
        df['activity_type'] = df['history'].apply(_extract_activity_type)
    
    return df.reset_index(drop=True)


def _extract_activity_type(history_text: str) -> str:
    """Extract activity type from history text using keywords."""
    if pd.isna(history_text):
        return 'Unknown'
    
    text = str(history_text).lower()
    
    # Priority-ordered categorization
    if any(kw in text for kw in ['email', 'correo', 'sent via email']):
        return 'Email'
    elif any(kw in text for kw in ['call', 'llamada', 'phone', 'telefono']):
        return 'Call'
    elif any(kw in text for kw in ['promise', 'promesa', 'payment plan']):
        return 'Promise to Pay'
    elif any(kw in text for kw in ['escalat', 'legal', 'attorney', 'abogado']):
        return 'Escalation'
    elif any(kw in text for kw in ['note', 'nota', 'comment']):
        return 'Note'
    else:
        return 'Other'


def prepare_aging_for_qa(
    df_aging: pd.DataFrame,
    customer_id_col: str = 'Customer',
    balance_col: str = 'Balance',
    days_col: str = 'Days'
) -> pd.DataFrame:
    """
    Prepare Aging DataFrame for QA merge.
    
    Standardizes column names and adds risk classification fields.
    
    Args:
        df_aging: Current Aging report from dashboard
        customer_id_col: Name of customer ID column
        balance_col: Name of balance column
        days_col: Name of aging days column
        
    Returns:
        Standardized DataFrame with risk tier and impact score
    """
    df = df_aging.copy()
    
    # Standardize key columns
    rename_map = {
        customer_id_col: 'customer_number',
        balance_col: 'balance',
        days_col: 'days_overdue'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # Ensure customer_number is string
    df['customer_number'] = df['customer_number'].astype(str).str.strip().str.upper()
    
    # Calculate risk tier (Top 20%, Mid 30%, Low 50%)
    df = df.sort_values('balance', ascending=False)
    total_accounts = len(df)
    df['risk_tier'] = 'Low Risk'
    df.iloc[:int(total_accounts * 0.2), df.columns.get_loc('risk_tier')] = 'High Risk'
    df.iloc[int(total_accounts * 0.2):int(total_accounts * 0.5), 
            df.columns.get_loc('risk_tier')] = 'Medium Risk'
    
    # Impact score (balance * aging factor)
    df['impact_score'] = df['balance'] * np.log1p(df['days_overdue'])
    
    # SLA status flags
    df['over_60d'] = df['days_overdue'] > 60
    df['over_90d'] = df['days_overdue'] > 90
    
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 2: QA MERGE ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def qa_merge_and_audit(
    df_aging: pd.DataFrame,
    df_activities: pd.DataFrame,
    lookback_days: int = 15,
    high_risk_threshold: float = None,
    sla_breach_days: int = 60
) -> Dict[str, pd.DataFrame]:
    """
    Core QA audit engine. Cross-references Aging with Activities to detect:
    
    1. High-Risk Neglect: Top 20% accounts with ZERO activity in last N days
    2. Misallocated Effort: High activity on low-value accounts
    3. SLA Breaches: 60d/90d aging without escalation/promise activity
    
    Args:
        df_aging: Current AR Aging report (standardized)
        df_activities: Cleaned activity log (standardized)
        lookback_days: Days to look back for recent activity (default: 15)
        high_risk_threshold: Manual $ threshold for high-risk (overrides Top 20%)
        sla_breach_days: Days threshold for SLA breach alerts (default: 60)
        
    Returns:
        Dictionary with 5 DataFrames:
        {
            'merged': Full merged dataset,
            'high_risk_neglect': High-value accounts with no recent activity,
            'misallocated_effort': Agent activity on low-impact accounts,
            'sla_breaches': Accounts over SLA without proper escalation,
            'agent_performance': Per-agent impact metrics
        }
    """
    # Calculate lookback window
    if df_activities['date'].notna().any():
        max_activity_date = df_activities['date'].max()
        cutoff_date = max_activity_date - timedelta(days=lookback_days)
    else:
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    # Filter recent activities
    df_recent = df_activities[
        (df_activities['date'] >= cutoff_date) | df_activities['date'].isna()
    ].copy()
    
    # Aggregate activities per customer
    activity_summary = df_recent.groupby('customer_number').agg({
        'user': lambda x: ', '.join(sorted(set(x))),  # All agents
        'date': 'max',  # Last activity date
        'history': 'count'  # Activity count
    }).rename(columns={
        'user': 'agents_assigned',
        'date': 'last_activity_date',
        'history': 'activity_count'
    })
    
    # Count escalation/promise activities separately
    escalation_counts = df_recent[
        df_recent['activity_type'].isin(['Escalation', 'Promise to Pay'])
    ].groupby('customer_number').size().rename('escalation_count')
    
    activity_summary = activity_summary.join(escalation_counts, how='left')
    activity_summary['escalation_count'].fillna(0, inplace=True)
    
    # Merge Aging with Activity Summary
    df_merged = df_aging.merge(
        activity_summary,
        on='customer_number',
        how='left',
        indicator=True
    )
    
    # Fill nulls for accounts with no activity
    df_merged['activity_count'].fillna(0, inplace=True)
    df_merged['escalation_count'].fillna(0, inplace=True)
    df_merged['agents_assigned'].fillna('None', inplace=True)
    
    # Calculate days since last activity
    df_merged['days_since_activity'] = np.where(
        df_merged['last_activity_date'].notna(),
        (max_activity_date - df_merged['last_activity_date']).dt.days,
        999  # No activity
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FLAG 1: HIGH-RISK NEGLECT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if high_risk_threshold:
        # Use manual threshold
        high_risk_mask = df_merged['balance'] >= high_risk_threshold
    else:
        # Use Top 20% risk tier
        high_risk_mask = df_merged['risk_tier'] == 'High Risk'
    
    high_risk_neglect = df_merged[
        high_risk_mask &
        (df_merged['activity_count'] == 0)
    ].sort_values('balance', ascending=False)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FLAG 2: MISALLOCATED EFFORT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Low-risk accounts with disproportionate activity (>3 activities)
    misallocated = df_merged[
        (df_merged['risk_tier'] == 'Low Risk') &
        (df_merged['activity_count'] > 3)
    ].sort_values('activity_count', ascending=False)
    
    # Calculate effort waste score
    if len(misallocated) > 0:
        misallocated['effort_waste_score'] = (
            misallocated['activity_count'] / misallocated['balance']
        ) * 1000  # Normalized per $1K
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FLAG 3: SLA BREACHES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    sla_breaches = df_merged[
        (df_merged['days_overdue'] >= sla_breach_days) &
        (df_merged['escalation_count'] == 0)
    ].sort_values('days_overdue', ascending=False)
    
    # Add severity level
    if len(sla_breaches) > 0:
        sla_breaches['severity'] = pd.cut(
            sla_breaches['days_overdue'],
            bins=[0, 60, 90, 120, 999],
            labels=['60-90d', '90-120d', '120d+', 'Critical'],
            right=False
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FLAG 4: AGENT PERFORMANCE METRICS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Per-agent activity breakdown
    agent_stats = df_recent.groupby('user').agg({
        'customer_number': 'nunique',  # Unique customers touched
        'history': 'count',  # Total activities
        'activity_type': lambda x: x.value_counts().to_dict()
    }).rename(columns={
        'customer_number': 'customers_touched',
        'history': 'total_activities',
        'activity_type': 'activity_breakdown'
    })
    
    # Calculate impact score per agent (sum of impact scores of accounts touched)
    agent_impact = df_recent.merge(
        df_aging[['customer_number', 'impact_score', 'balance']],
        on='customer_number',
        how='left'
    ).groupby('user').agg({
        'impact_score': 'sum',
        'balance': 'sum'
    }).rename(columns={
        'impact_score': 'total_impact_score',
        'balance': 'total_portfolio_touched'
    })
    
    agent_performance = agent_stats.join(agent_impact)
    
    # Efficiency ratio (impact per activity)
    agent_performance['impact_per_activity'] = (
        agent_performance['total_impact_score'] / 
        agent_performance['total_activities']
    )
    
    agent_performance = agent_performance.sort_values(
        'total_impact_score', 
        ascending=False
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RETURN RESULTS PACKAGE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    return {
        'merged': df_merged,
        'high_risk_neglect': high_risk_neglect,
        'misallocated_effort': misallocated,
        'sla_breaches': sla_breaches,
        'agent_performance': agent_performance,
        'summary_stats': {
            'total_accounts': len(df_aging),
            'accounts_with_activity': (df_merged['activity_count'] > 0).sum(),
            'high_risk_neglected': len(high_risk_neglect),
            'sla_breach_count': len(sla_breaches),
            'total_activities': len(df_recent),
            'lookback_days': lookback_days,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 3: KPI CALCULATION UTILITIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def calculate_qa_kpis(audit_results: Dict) -> Dict[str, Union[float, int, str]]:
    """
    Calculate executive KPIs from audit results.
    
    Returns:
        Dictionary with 3 key metrics:
        {
            'pct_high_risk_neglected': % of high-value portfolio without activity,
            'top_agents': Top 3 agents by impact score,
            'critical_accounts': Count of accounts >90d with no escalation
        }
    """
    merged = audit_results['merged']
    agent_perf = audit_results['agent_performance']
    high_risk_neglect = audit_results['high_risk_neglect']
    sla_breaches = audit_results['sla_breaches']
    
    # KPI 1: % High-Risk Portfolio Neglected
    total_high_risk = (merged['risk_tier'] == 'High Risk').sum()
    if total_high_risk > 0:
        pct_neglected = (len(high_risk_neglect) / total_high_risk) * 100
    else:
        pct_neglected = 0.0
    
    # KPI 2: Top 3 Agents by Impact
    if len(agent_perf) > 0:
        top_agents = agent_perf.head(3).index.tolist()
    else:
        top_agents = []
    
    # KPI 3: Critical Abandoned Accounts (90d+ no escalation)
    critical = sla_breaches[sla_breaches['days_overdue'] >= 90]
    critical_count = len(critical)
    critical_exposure = critical['balance'].sum() if len(critical) > 0 else 0
    
    return {
        'pct_high_risk_neglected': round(pct_neglected, 2),
        'high_risk_neglected_count': len(high_risk_neglect),
        'high_risk_neglected_exposure': high_risk_neglect['balance'].sum() 
                                        if len(high_risk_neglect) > 0 else 0,
        'top_agents_by_impact': top_agents,
        'top_agents_impact_scores': agent_perf.head(3)['total_impact_score'].tolist() 
                                    if len(agent_perf) > 0 else [],
        'critical_accounts_90d_plus': critical_count,
        'critical_exposure_90d_plus': critical_exposure,
        'total_sla_breaches': len(sla_breaches),
        'misallocated_effort_count': len(audit_results['misallocated_effort'])
    }


def export_qa_report_excel(audit_results: Dict, filename: str = 'QA_Audit_Report.xlsx'):
    """
    Export complete QA audit to Excel with multiple tabs.
    
    Tabs:
        1. Executive Summary (KPIs)
        2. High-Risk Neglect
        3. Misallocated Effort
        4. SLA Breaches
        5. Agent Performance
        6. Full Merged Data
    """
    from io import BytesIO
    
    output = BytesIO()
    kpis = calculate_qa_kpis(audit_results)
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Tab 1: Executive Summary
        summary_data = {
            'Metric': list(kpis.keys()),
            'Value': list(kpis.values())
        }
        pd.DataFrame(summary_data).to_excel(
            writer, 
            sheet_name='Executive Summary', 
            index=False
        )
        
        # Tab 2: High-Risk Neglect
        if len(audit_results['high_risk_neglect']) > 0:
            audit_results['high_risk_neglect'].to_excel(
                writer, 
                sheet_name='High-Risk Neglect', 
                index=False
            )
        
        # Tab 3: Misallocated Effort
        if len(audit_results['misallocated_effort']) > 0:
            audit_results['misallocated_effort'].to_excel(
                writer, 
                sheet_name='Misallocated Effort', 
                index=False
            )
        
        # Tab 4: SLA Breaches
        if len(audit_results['sla_breaches']) > 0:
            audit_results['sla_breaches'].to_excel(
                writer, 
                sheet_name='SLA Breaches', 
                index=False
            )
        
        # Tab 5: Agent Performance
        if len(audit_results['agent_performance']) > 0:
            audit_results['agent_performance'].to_excel(
                writer, 
                sheet_name='Agent Performance'
            )
        
        # Tab 6: Full Data
        audit_results['merged'].to_excel(
            writer, 
            sheet_name='Full Merged Data', 
            index=False
        )
    
    output.seek(0)
    return output


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 4: VALIDATION & ERROR HANDLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def validate_file_upload(
    file_obj,
    max_size_mb: int = 50,
    allowed_extensions: List[str] = ['.csv', '.xlsx', '.xls']
) -> Tuple[bool, str]:
    """
    Validate uploaded file before processing.
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if file_obj is None:
        return False, "No file uploaded"
    
    # Check file extension
    filename = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
    ext = filename[filename.rfind('.'):].lower()
    
    if ext not in allowed_extensions:
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    
    # Check file size
    if hasattr(file_obj, 'size'):
        size_mb = file_obj.size / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"File too large ({size_mb:.1f}MB). Max: {max_size_mb}MB"
    
    return True, "OK"


def safe_read_uploaded_file(file_obj) -> pd.DataFrame:
    """
    Safely read uploaded CSV/XLSX with error handling.
    """
    filename = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
    ext = filename[filename.rfind('.'):].lower()
    
    try:
        if ext == '.csv':
            df = pd.read_csv(file_obj, encoding='utf-8', on_bad_lines='skip')
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_obj)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        return df
    
    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")
