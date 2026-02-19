"""Main Streamlit application for Change Management Analysis System."""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import logger
from config.settings import settings

# Configure Streamlit page
st.set_page_config(
    page_title="Change Management Analysis System",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success { color: #28a745; font-weight: bold; }
    .warning { color: #ffc107; font-weight: bold; }
    .danger { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def main():
    """Main entry point for the application."""
    
    # Sidebar navigation
    st.sidebar.title("🔄 Change Management System")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Home",
            "📋 Single Analysis",
            "📁 Bulk Analysis",
            "📊 Analytics",
            "🔍 History",
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### Quick Info
    - **System Status**: ✅ Operational
    - **API**: Groq LLaMA 3.1
    - **Database**: SQLite
    - **RAG**: ChromaDB
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### Support
    - 📖 [Documentation](#)
    - 🐛 [Report Issue](#)
    - 💬 [Feedback](#)
    """)
    
    # Helper to (re)load view modules so they execute on each selection
    def _load_view(module_name: str) -> None:
        import importlib
        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
            except Exception:
                # Fallback to import_module if reload fails
                importlib.import_module(module_name)
        else:
            importlib.import_module(module_name)

    # Route pages
    if page == "🏠 Home":
        show_home()
    elif page == "📋 Single Analysis":
        _load_view("views.single_analysis")
    elif page == "📁 Bulk Analysis":
        _load_view("views.bulk_analysis")
    elif page == "📊 Analytics":
        _load_view("views.analytics_view")
    elif page == "🔍 History":
        _load_view("views.history_view")


def show_home():
    """Display home page."""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("🔄 Change Management Analysis System")
        st.markdown("""
        ## Welcome to the AI-powered Change Request Analyzer
        
        This system automatically analyzes production change requests and provides:
        
        ✅ **Intelligent Risk Assessment** - LLM-based analysis of change complexity and risk factors
        
        ✅ **Policy Compliance Checking** - RAG-based verification against company policies
        
        ✅ **Approval Recommendation** - Combined decision engine with risk scoring
        
        ✅ **Actionable Insights** - Specific recommendations for improvement
        
        ### Key Benefits
        - **30x Faster**: Analyze changes in seconds instead of minutes
        - **Consistent**: Same criteria applied to all changes
        - **Smart**: Learns from policies and best practices
        - **Safe**: Conservative in risk assessment, recommend review when uncertain
        """)
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        
        try:
            from data.repository import AnalysisRepository
            analytics = AnalysisRepository.get_analytics_data(days_back=7)
            
            st.metric("Total Analyzed", analytics.total_analyzed, delta="Last 7 days")
            st.metric("Approval Rate", f"{analytics.approval_rate}%")
            st.metric("Avg Risk Score", f"{analytics.average_risk_score:.1f}/100")
            
        except Exception as e:
            logger.warning(f"Failed to load analytics: {e}")
            st.info("No data yet - run your first analysis!")
    
    st.markdown("---")

    # Note: Navigation is available in the sidebar. Use the sidebar to switch pages.
    st.info("Use the sidebar (left) to navigate: Home, Single Analysis, Bulk Analysis, Analytics, History")

    # Features section
    st.markdown("""
    ### 🎯 How It Works
    
    1. **Input** - Provide change request details in the form
    2. **Analysis** - System analyzes with LLM, checks policies, calculates risk
    3. **Assessment** - Get decision (APPROVE/REVIEW/REJECT) with reasoning
    4. **Action** - Review recommendations and take action
    
    ### 📖 Documentation
    - [Change Request Format](docs/change_request_format.md)
    - [Policy Documentation](docs/policies.md)
    - [FAQ](docs/faq.md)
    """)


if __name__ == "__main__":
    logger.info("Starting Change Management Analysis System")
    main()
