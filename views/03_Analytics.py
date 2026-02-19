"""Analytics Dashboard Page (moved from pages)."""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.repository import AnalysisRepository
from utils.logger import get_logger

page_logger = get_logger(__name__)

st.set_page_config(
    page_title="Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Analytics Dashboard")

# Date range filter
col1, col2 = st.columns(2)
with col1:
    days_back = st.slider("Days Back", min_value=1, max_value=90, value=30)
with col2:
    st.info(f"📅 Showing last {days_back} days of data")

try:
    # Get analytics data
    analytics = AnalysisRepository.get_analytics_data(days_back=days_back)
    
    if analytics.total_analyzed == 0:
        st.warning("No data available yet. Analyze some changes first!")
    else:
        # KPI Cards
        st.markdown("### 📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Analyzed",
                analytics.total_analyzed,
                f"Last {days_back} days"
            )
        
        with col2:
            st.metric(
                "Approval Rate",
                f"{analytics.approval_rate}%",
                delta=f"{analytics.total_approved} approved"
            )
        
        with col3:
            st.metric(
                "Avg Risk Score",
                f"{analytics.average_risk_score:.1f}",
                "out of 100"
            )
        
        with col4:
            st.metric(
                "Avg Confidence",
                f"{analytics.average_confidence:.1f}%",
                "Assessment confidence"
            )
        
        st.markdown("---")
        
        # Charts
        st.markdown("### 📈 Visualizations")
        
        col1, col2 = st.columns(2)
        
        # Decision Distribution
        with col1:
            st.markdown("#### Decision Breakdown")
            decision_data = analytics.analysis_by_decision
            fig = go.Figure(data=[go.Pie(
                labels=list(decision_data.keys()),
                values=list(decision_data.values()),
                marker=dict(colors=["#28a745", "#ffc107", "#dc3545"]),
                hole=0.3,
            )])
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        
        # Risk Distribution
        with col2:
            st.markdown("#### Risk Distribution")
            risk_data = analytics.risk_distribution
            fig = go.Figure(data=[go.Bar(
                x=list(risk_data.keys()),
                y=list(risk_data.values()),
                marker=dict(color=["#28a745", "#ffc107", "#dc3545"]),
            )])
            fig.update_layout(
                height=400,
                xaxis_title="Risk Level",
                yaxis_title="Count",
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        # Category Breakdown
        with col1:
            if analytics.analysis_by_category:
                st.markdown("#### Changes by Category")
                category_data = analytics.analysis_by_category
                fig = go.Figure(data=[go.Bar(
                    x=list(category_data.keys()),
                    y=list(category_data.values()),
                    marker=dict(color="#1f77b4"),
                )])
                fig.update_layout(
                    height=400,
                    xaxis_title="Category",
                    yaxis_title="Count",
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis_tickangle=-45,
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Complexity Breakdown
        with col2:
            if analytics.analysis_by_complexity:
                st.markdown("#### Changes by Complexity")
                complexity_data = analytics.analysis_by_complexity
                fig = go.Figure(data=[go.Bar(
                    x=list(complexity_data.keys()),
                    y=list(complexity_data.values()),
                    marker=dict(color="#ff7f0e"),
                )])
                fig.update_layout(
                    height=400,
                    xaxis_title="Complexity",
                    yaxis_title="Count",
                    margin=dict(l=0, r=0, t=0, b=0),
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Summary table
        st.markdown("---")
        st.markdown("### 📋 Summary Data")
        
        summary_data = {
            "Metric": [
                "Total Analyzed",
                "Approved",
                "Needs Review",
                "Rejected",
                "Approval Rate",
                "Avg Risk Score",
                "Avg Confidence",
            ],
            "Value": [
                f"{analytics.total_analyzed}",
                f"{analytics.total_approved}",
                f"{analytics.total_reviewed}",
                f"{analytics.total_rejected}",
                f"{analytics.approval_rate}%",
                f"{analytics.average_risk_score:.2f}",
                f"{analytics.average_confidence:.2f}%",
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
        
        # Export
        col1, col2 = st.columns(2)
        with col1:
            csv = summary_df.to_csv(index=False)
            st.download_button(
                "📥 Download Analytics CSV",
                csv,
                "analytics_summary.csv",
                "text/csv",
                use_container_width=True,
            )

except Exception as e:
    page_logger.error(f"Failed to load analytics: {e}")
    st.error(f"❌ Failed to load analytics: {str(e)}")

st.markdown("---")
st.markdown("""
### 📊 About These Metrics
- **Approval Rate**: Percentage of changes with APPROVE decision
- **Risk Score**: Combined score from LLM analysis and rule-based calculation
- **Confidence**: LLM assessment confidence level
- **Risk Distribution**: Changes categorized as LOW (<25), MEDIUM (25-75), HIGH (>75)
""")
