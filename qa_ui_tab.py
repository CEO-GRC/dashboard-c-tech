"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Management & QA Tab — UI Component for AR Collections Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Integration: Add this module to dashboard_cobros.py as Tab 6
Authentication: Separate password gate for management-level access
Functionality: Upload activities log, audit agent performance, export reports

Dependencies: Streamlit, Pandas, qa_module.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from qa_module import (
    clean_activities_file,
    prepare_aging_for_qa,
    qa_merge_and_audit,
    calculate_qa_kpis,
    export_qa_report_excel,
    validate_file_upload,
    safe_read_uploaded_file
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION & CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Amrize brand colors (match dashboard_cobros.py)
AMZ_MIDNIGHT = "#011E6A"
AMZ_SKY = "#00A7E1"
AMZ_ROYAL = "#0047AB"
S_GREEN = "#10B981"
S_RED = "#EF4444"
S_AMBER = "#F59E0B"
S_YELLOW = "#FBBF24"

# Default management password (can be overridden in st.secrets)
DEFAULT_MGMT_PASSWORD = "MGMT2024"


def get_mgmt_password() -> str:
    """Get management password from secrets or fallback to default."""
    try:
        return st.secrets.get("MGMT_PASSWORD", DEFAULT_MGMT_PASSWORD)
    except:
        return DEFAULT_MGMT_PASSWORD


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SESSION STATE INITIALIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_qa_session_state():
    """Initialize QA-specific session state variables."""
    if 'qa_authenticated' not in st.session_state:
        st.session_state.qa_authenticated = False
    if 'qa_audit_results' not in st.session_state:
        st.session_state.qa_audit_results = None
    if 'qa_activities_df' not in st.session_state:
        st.session_state.qa_activities_df = None
    if 'qa_last_upload' not in st.session_state:
        st.session_state.qa_last_upload = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTHENTICATION GATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_qa_auth_gate() -> bool:
    """
    Render management authentication interface.
    Returns True if authenticated, False otherwise.
    """
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {AMZ_MIDNIGHT} 0%, {AMZ_ROYAL} 100%);
                padding: 2rem; border-radius: 12px; margin-bottom: 2rem;'>
        <h2 style='color: white; margin: 0; font-weight: 600;'>
            🔐 Management & QA Access
        </h2>
        <p style='color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.95rem;'>
            Restricted area — Executive-level auditing tools
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("qa_auth_form"):
        st.markdown("#### Enter Management Password")
        password_input = st.text_input(
            "Password",
            type="password",
            placeholder="Enter management access code",
            help="Contact your system administrator if you don't have access"
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("🔓 Unlock", use_container_width=True)
        
        if submitted:
            if password_input.strip() == get_mgmt_password():
                st.session_state.qa_authenticated = True
                st.success("✅ Access granted — Welcome to Management QA")
                st.rerun()
            else:
                st.error("❌ Invalid password — Access denied")
    
    # Info box
    st.info("""
    **What's inside Management & QA:**
    - Upload historical activity logs (CSV/XLSX)
    - Cross-reference with current Aging data
    - Identify high-risk accounts with zero collection effort
    - Detect SLA breaches (60d/90d milestones)
    - Audit agent performance and resource allocation
    - Export comprehensive Excel audit reports
    """)
    
    return st.session_state.qa_authenticated


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE UPLOAD INTERFACE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_file_uploader():
    """Render activities file upload component."""
    st.markdown(f"""
    <div style='background: linear-gradient(to right, {AMZ_SKY}, {AMZ_ROYAL}); 
                padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;'>
        <h3 style='color: white; margin: 0; font-weight: 600;'>
            📤 Upload Activity Log
        </h3>
        <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.9rem;'>
            Upload historical agent activity report (CSV or XLSX)
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose activity log file",
        type=['csv', 'xlsx', 'xls'],
        help="Supported formats: CSV, XLSX, XLS | Max size: 50MB",
        key="qa_file_upload"
    )
    
    if uploaded_file is not None:
        # Validate file
        is_valid, msg = validate_file_upload(uploaded_file)
        
        if not is_valid:
            st.error(f"❌ {msg}")
            return None
        
        # Show file info
        st.success(f"✅ File loaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
        
        # Process button
        if st.button("🔍 Process & Analyze", type="primary", use_container_width=True):
            with st.spinner("Processing activity log..."):
                try:
                    # Read file
                    df_raw = safe_read_uploaded_file(uploaded_file)
                    
                    # Clean and standardize
                    df_clean = clean_activities_file(df_raw)
                    
                    # Store in session state
                    st.session_state.qa_activities_df = df_clean
                    st.session_state.qa_last_upload = datetime.now()
                    
                    st.success(f"✅ Processed {len(df_clean):,} activities from {df_clean['user'].nunique()} agents")
                    
                    # Show preview
                    with st.expander("📋 Preview Processed Data", expanded=False):
                        st.dataframe(df_clean.head(10), use_container_width=True)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Activities", f"{len(df_clean):,}")
                        with col2:
                            st.metric("Unique Agents", df_clean['user'].nunique())
                        with col3:
                            st.metric("Unique Customers", df_clean['customer_number'].nunique())
                    
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
                    return None
        
        return st.session_state.qa_activities_df
    
    else:
        st.info("👆 Upload an activity log file to begin QA analysis")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN QA AUDIT INTERFACE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_qa_dashboard(df_aging: pd.DataFrame, df_activities: pd.DataFrame):
    """
    Render main QA audit dashboard with KPIs and red flags.
    
    Args:
        df_aging: Current AR Aging DataFrame from main dashboard
        df_activities: Cleaned activities DataFrame from upload
    """
    st.markdown(f"""
    <div style='background: {AMZ_MIDNIGHT}; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;'>
        <h3 style='color: white; margin: 0; font-weight: 600;'>
            🎯 QA Audit Results
        </h3>
        <p style='color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;'>
            Last updated: {st.session_state.qa_last_upload.strftime('%Y-%m-%d %H:%M') if st.session_state.qa_last_upload else 'N/A'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Configuration sidebar
    with st.expander("⚙️ Audit Configuration", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            lookback_days = st.number_input(
                "Activity Lookback (days)",
                min_value=7,
                max_value=90,
                value=15,
                help="How many days back to consider 'recent' activity"
            )
        
        with col2:
            sla_threshold = st.number_input(
                "SLA Breach Threshold (days)",
                min_value=30,
                max_value=180,
                value=60,
                help="Days overdue before SLA breach flag"
            )
        
        with col3:
            high_risk_method = st.radio(
                "High-Risk Definition",
                ["Top 20% by Balance", "Manual Threshold"],
                help="How to classify high-risk accounts"
            )
        
        if high_risk_method == "Manual Threshold":
            high_risk_threshold = st.number_input(
                "High-Risk $ Threshold",
                min_value=1000,
                max_value=1000000,
                value=10000,
                step=1000
            )
        else:
            high_risk_threshold = None
    
    # Run audit button
    if st.button("🚀 Run QA Audit", type="primary", use_container_width=True):
        with st.spinner("Running comprehensive QA audit..."):
            try:
                # Prepare Aging data
                df_aging_prepared = prepare_aging_for_qa(
                    df_aging,
                    customer_id_col='Customer',  # Adjust based on your actual column
                    balance_col='Balance',
                    days_col='Days'
                )
                
                # Run audit
                audit_results = qa_merge_and_audit(
                    df_aging_prepared,
                    df_activities,
                    lookback_days=lookback_days,
                    high_risk_threshold=high_risk_threshold,
                    sla_breach_days=sla_threshold
                )
                
                # Store results
                st.session_state.qa_audit_results = audit_results
                
                st.success("✅ QA Audit completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Audit error: {str(e)}")
                return
    
    # Display results if available
    if st.session_state.qa_audit_results is not None:
        display_qa_results(st.session_state.qa_audit_results)
    else:
        st.info("👆 Click 'Run QA Audit' to analyze data")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESULTS VISUALIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def display_qa_results(audit_results: dict):
    """Display QA audit results with KPIs and detailed tables."""
    
    # Calculate KPIs
    kpis = calculate_qa_kpis(audit_results)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EXECUTIVE KPI CARDS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    st.markdown("### 📊 Executive KPIs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pct = kpis['pct_high_risk_neglected']
        color = S_RED if pct > 25 else (S_AMBER if pct > 10 else S_GREEN)
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 8px; 
                    border-left: 5px solid {color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <div style='color: #64748b; font-size: 0.85rem; font-weight: 600; 
                        text-transform: uppercase; margin-bottom: 0.5rem;'>
                % High-Risk Portfolio Neglected
            </div>
            <div style='font-size: 2.5rem; font-weight: 700; color: {color};'>
                {pct:.1f}%
            </div>
            <div style='color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;'>
                {kpis['high_risk_neglected_count']:,} accounts | ${kpis['high_risk_neglected_exposure']:,.0f} exposure
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        top_agents = kpis['top_agents_by_impact']
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 8px; 
                    border-left: 5px solid {AMZ_SKY}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <div style='color: #64748b; font-size: 0.85rem; font-weight: 600; 
                        text-transform: uppercase; margin-bottom: 0.5rem;'>
                Top Performing Agents
            </div>
            <div style='font-size: 1.2rem; font-weight: 600; color: {AMZ_MIDNIGHT}; 
                        line-height: 1.6;'>
                {'<br>'.join([f"🥇 {agent}" if i == 0 else f"🥈 {agent}" if i == 1 else f"🥉 {agent}" 
                              for i, agent in enumerate(top_agents[:3])]) if top_agents else 'No data'}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        critical_count = kpis['critical_accounts_90d_plus']
        critical_color = S_RED if critical_count > 10 else (S_AMBER if critical_count > 0 else S_GREEN)
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 8px; 
                    border-left: 5px solid {critical_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <div style='color: #64748b; font-size: 0.85rem; font-weight: 600; 
                        text-transform: uppercase; margin-bottom: 0.5rem;'>
                Critical Abandoned (90d+)
            </div>
            <div style='font-size: 2.5rem; font-weight: 700; color: {critical_color};'>
                {critical_count}
            </div>
            <div style='color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;'>
                ${kpis['critical_exposure_90d_plus']:,.0f} total exposure
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RED FLAG TABLES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Flag 1: High-Risk Neglect
    st.markdown(f"""
    ### 🚨 Red Flag #1: High-Risk Neglect
    <p style='color: #64748b; margin-top: -0.5rem;'>
        Accounts in top 20% by balance with ZERO activity in lookback period
    </p>
    """, unsafe_allow_html=True)
    
    neglect_df = audit_results['high_risk_neglect']
    if len(neglect_df) > 0:
        display_cols = ['customer_number', 'company', 'balance', 'days_overdue', 
                       'risk_tier', 'days_since_activity']
        st.dataframe(
            neglect_df[display_cols].head(20),
            use_container_width=True,
            hide_index=True
        )
        st.caption(f"Showing top 20 of {len(neglect_df):,} total neglected accounts")
    else:
        st.success("✅ No high-risk neglect detected — All high-value accounts have recent activity")
    
    st.markdown("---")
    
    # Flag 2: SLA Breaches
    st.markdown(f"""
    ### ⏰ Red Flag #2: SLA Breaches
    <p style='color: #64748b; margin-top: -0.5rem;'>
        Accounts past SLA threshold without escalation or promise-to-pay activity
    </p>
    """, unsafe_allow_html=True)
    
    sla_df = audit_results['sla_breaches']
    if len(sla_df) > 0:
        display_cols = ['customer_number', 'company', 'balance', 'days_overdue', 
                       'severity', 'activity_count', 'escalation_count']
        st.dataframe(
            sla_df[display_cols].head(20),
            use_container_width=True,
            hide_index=True
        )
        st.caption(f"Showing top 20 of {len(sla_df):,} total SLA breaches")
    else:
        st.success("✅ No SLA breaches — All overdue accounts have proper escalation")
    
    st.markdown("---")
    
    # Flag 3: Misallocated Effort
    st.markdown(f"""
    ### 💸 Red Flag #3: Misallocated Effort
    <p style='color: #64748b; margin-top: -0.5rem;'>
        Low-value accounts consuming excessive agent resources
    </p>
    """, unsafe_allow_html=True)
    
    misalloc_df = audit_results['misallocated_effort']
    if len(misalloc_df) > 0:
        display_cols = ['customer_number', 'company', 'balance', 'activity_count', 
                       'agents_assigned', 'effort_waste_score']
        st.dataframe(
            misalloc_df[display_cols].head(20),
            use_container_width=True,
            hide_index=True
        )
        st.caption(f"Showing top 20 of {len(misalloc_df):,} low-priority accounts with excessive activity")
    else:
        st.success("✅ Efficient resource allocation — Agents focused on high-impact accounts")
    
    st.markdown("---")
    
    # Agent Performance Table
    st.markdown("### 👥 Agent Performance Metrics")
    
    agent_perf = audit_results['agent_performance']
    if len(agent_perf) > 0:
        # Reset index to show agent names
        agent_display = agent_perf.reset_index()
        st.dataframe(
            agent_display,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No agent performance data available")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EXPORT BUTTON
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    st.markdown("---")
    st.markdown("### 📥 Export Reports")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # Excel export
        excel_file = export_qa_report_excel(audit_results)
        st.download_button(
            label="📊 Download Full Excel Report",
            data=excel_file,
            file_name=f"QA_Audit_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        # CSV export (merged data)
        csv_data = audit_results['merged'].to_csv(index=False)
        st.download_button(
            label="📄 Download CSV (Merged Data)",
            data=csv_data,
            file_name=f"QA_Merged_Data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN TAB RENDER FUNCTION (call from dashboard_cobros.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_qa_tab(df_aging: pd.DataFrame):
    """
    Main entry point for QA tab. Call this from dashboard_cobros.py Tab 6.
    
    Args:
        df_aging: Current Aging DataFrame from main dashboard
        
    Example integration in dashboard_cobros.py:
        ```python
        from qa_ui_tab import render_qa_tab
        
        with tabs[5]:  # Tab 6
            render_qa_tab(df)  # Pass current Aging DataFrame
        ```
    """
    # Initialize session state
    init_qa_session_state()
    
    # Authentication gate
    if not render_qa_auth_gate():
        return  # Stop here if not authenticated
    
    # Main content (only shown after authentication)
    st.markdown("---")
    
    # File uploader
    df_activities = render_file_uploader()
    
    # If activities loaded, show audit dashboard
    if df_activities is not None and df_aging is not None:
        st.markdown("---")
        render_qa_dashboard(df_aging, df_activities)
    elif df_aging is None:
        st.warning("⚠️ No Aging data available. Please load Aging data in Tab 1 first.")
