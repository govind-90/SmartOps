"""History and Search Page (moved from pages)."""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime, timedelta, timezone
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.repository import AnalysisRepository
from utils.logger import get_logger

page_logger = get_logger(__name__)

st.set_page_config(
    page_title="History",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Analysis History & Search")


def render_search_results_from_session():
    """Render stored search results from session state (persists across reruns)."""
    if not st.session_state.get("search_results"):
        return

    analyses = st.session_state.search_results
    results_df = st.session_state.search_results_df
    csv = st.session_state.search_results_csv
    total_count = st.session_state.search_total_count

    st.markdown("---")
    st.markdown(f"### 📊 Results ({len(analyses)} of {total_count} total)")

    # Recreate styled dataframe for display
    def color_decision(val):
        if val == "APPROVE":
            return "background-color: #d4edda"
        elif val == "REVIEW_REQUIRED":
            return "background-color: #fff3cd"
        else:
            return "background-color: #f8d7da"

    styled_df = results_df.style.applymap(
        color_decision,
        subset=["Decision"]
    )

    st.dataframe(styled_df, use_container_width=True)

    # Export using stored CSV
    st.download_button(
        "📥 Download Search Results CSV",
        csv,
        f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        use_container_width=True,
    )

    # View details
    st.markdown("---")
    st.markdown("### 📄 View Details")

    results_data = [
        {
            "ID": a["id"],
            "Description": a["short_description"][:60] + "...",
            "Decision": a["final_decision"],
            "Risk": a["risk_score"],
            "Date": a["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(a["created_at"], "strftime") else a["created_at"],
        }
        for a in analyses
    ]

    selected_id = st.selectbox(
        "Select an analysis to view details",
        options=[r["ID"] for r in results_data],
        format_func=lambda x: f"ID {x} - {[r for r in results_data if r['ID'] == x][0]['Description']}",
    )

    if selected_id:
        try:
            analysis = AnalysisRepository.get_analysis(selected_id)
            if analysis:
                # Display details
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Decision", analysis["final_decision"])
                with col2:
                    st.metric("Risk Score", analysis["risk_score"])
                with col3:
                    st.metric("Confidence", f"{analysis['confidence']}%")
                with col4:
                    st.metric("Compliant", "✅" if analysis["compliance_compliant"] else "❌")

                st.markdown("---")

                # Tabs for different sections
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "Change Request",
                    "Assessment",
                    "Risk Factors",
                    "Recommendations",
                    "Compliance"
                ])

                with tab1:
                    st.markdown("#### Change Request Details")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Category**: {analysis['change_category']}")
                        st.write(f"**Type**: {analysis['change_type']}")
                        st.write(f"**Complexity**: {analysis['complexity']}")
                        st.write(f"**Services**: {analysis['impacted_services']}")

                    with col2:
                        st.write(f"**Window**: {analysis['planned_window']}")
                        st.write(f"**Created**: {analysis['created_at']}")

                with tab2:
                    st.markdown("#### Analysis Reasoning")
                    st.info(analysis["reasoning"])

                with tab3:
                    st.markdown("#### Risk Factors")
                    for i, factor in enumerate(analysis["risk_factors"], 1):
                        st.write(f"{i}. {factor}")

                with tab4:
                    st.markdown("#### Recommendations")
                    for i, rec in enumerate(analysis["recommendations"], 1):
                        st.write(f"{i}. {rec}")

                with tab5:
                    st.markdown("#### Compliance Assessment")
                    st.write(f"**Compliant**: {'✅ Yes' if analysis['compliance_compliant'] else '❌ No'}")
                    st.write(f"**Compliance Score**: {analysis['compliance_score']}/100")

                    if analysis["compliance_issues"]:
                        st.markdown("**Violations**:")
                        for issue in analysis["compliance_issues"]:
                            st.warning(f"- {issue.get('issue', 'Unknown issue')}")

        except Exception as e:
            st.error(f"Failed to load analysis details: {e}")
            page_logger.error(f"Failed to load analysis {selected_id}: {e}")

# Search/filter section
st.markdown("### 🔎 Search Filters")

col1, col2, col3 = st.columns(3)

with col1:
    search_text = st.text_input("Search Description", placeholder="e.g., 'API deployment'")

with col2:
    decision_filter = st.multiselect(
        "Decision Type",
        ["APPROVE", "REVIEW_REQUIRED", "REJECT"],
        default=["APPROVE", "REVIEW_REQUIRED", "REJECT"],
    )

with col3:
    risk_range = st.slider(
        "Risk Score Range",
        0, 100,
        (0, 100),
        step=5,
    )

# Normalize risk_range to a (min, max) tuple in case Streamlit returns a single int
if isinstance(risk_range, int):
    risk_min, risk_max = risk_range, risk_range
else:
    try:
        risk_min, risk_max = int(risk_range[0]), int(risk_range[1])
    except Exception:
        # Fallback to defaults
        risk_min, risk_max = 0, 100

# Date range
col1, col2, col3 = st.columns(3)

with col1:
    days_back = st.number_input("Days Back", min_value=1, max_value=365, value=30)
    start_date = datetime.utcnow() - timedelta(days=days_back)

with col2:
    st.info(f"From: {start_date.strftime('%Y-%m-%d')}")

with col3:
    limit = st.number_input("Results Per Page", min_value=10, max_value=100, value=25)

# Search button
if st.button("🔍 Search", use_container_width=True, type="primary"):
    try:
        # Convert decision filter to individual filters or search logic
        analyses, total_count = AnalysisRepository.search_analyses(
            decision=None,  # We'll filter manually if needed
            risk_min=risk_min,
            risk_max=risk_max,
            start_date=start_date,
            text_search=search_text if search_text else None,
            limit=limit,
            offset=0,
        )
        
        # Filter by decision
        if decision_filter and len(decision_filter) < 3:
            analyses = [a for a in analyses if a["final_decision"] in decision_filter]
        
        # Display results
        st.markdown("---")
        st.markdown(f"### 📊 Results ({len(analyses)} of {total_count} total)")
        
        if analyses:
            # Create DataFrame for display
            results_data = []
            for analysis in analyses:
                results_data.append({
                    "ID": analysis["id"],
                    "Description": analysis["short_description"][:60] + "...",
                    "Decision": analysis["final_decision"],
                    "Risk": analysis["risk_score"],
                    "Date": analysis["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(analysis["created_at"], "strftime") else analysis["created_at"],
                })
            
            results_df = pd.DataFrame(results_data)
            
            # Color code decisions
            def color_decision(val):
                if val == "APPROVE":
                    return "background-color: #d4edda"
                elif val == "REVIEW_REQUIRED":
                    return "background-color: #fff3cd"
                else:
                    return "background-color: #f8d7da"
            
            styled_df = results_df.style.applymap(
                color_decision,
                subset=["Decision"]
            )
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Export
            csv = results_df.to_csv(index=False)

            # Persist search results to session state so they survive reruns
            st.session_state.search_results = analyses
            st.session_state.search_results_df = results_df
            st.session_state.search_results_csv = csv
            st.session_state.search_total_count = total_count

            # Provide download button (reads from the CSV stored in session)
            st.download_button(
                "📥 Download Search Results CSV",
                st.session_state.search_results_csv,
                f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True,
            )
            
            # View details
            st.markdown("---")
            st.markdown("### 📄 View Details")
            
            selected_id = st.selectbox(
                "Select an analysis to view details",
                options=[a["ID"] for a in results_data],
                format_func=lambda x: f"ID {x} - {[r for r in results_data if r['ID'] == x][0]['Description']}",
            )
            
            if selected_id:
                try:
                    analysis = AnalysisRepository.get_analysis(selected_id)
                    
                    if analysis:
                        # Display details
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Decision", analysis["final_decision"])
                        with col2:
                            st.metric("Risk Score", analysis["risk_score"])
                        with col3:
                            st.metric("Confidence", f"{analysis['confidence']}%")
                        with col4:
                            st.metric("Compliant", "✅" if analysis["compliance_compliant"] else "❌")
                        
                        st.markdown("---")
                        
                        # Tabs for different sections
                        tab1, tab2, tab3, tab4, tab5 = st.tabs([
                            "Change Request",
                            "Assessment",
                            "Risk Factors",
                            "Recommendations",
                            "Compliance"
                        ])
                        
                        with tab1:
                            st.markdown("#### Change Request Details")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Category**: {analysis['change_category']}")
                                st.write(f"**Type**: {analysis['change_type']}")
                                st.write(f"**Complexity**: {analysis['complexity']}")
                                st.write(f"**Services**: {analysis['impacted_services']}")
                            
                            with col2:
                                st.write(f"**Window**: {analysis['planned_window']}")
                                st.write(f"**Created**: {analysis['created_at']}")
                        
                        with tab2:
                            st.markdown("#### Analysis Reasoning")
                            st.info(analysis["reasoning"])
                        
                        with tab3:
                            st.markdown("#### Risk Factors")
                            for i, factor in enumerate(analysis["risk_factors"], 1):
                                st.write(f"{i}. {factor}")
                        
                        with tab4:
                            st.markdown("#### Recommendations")
                            for i, rec in enumerate(analysis["recommendations"], 1):
                                st.write(f"{i}. {rec}")
                        
                        with tab5:
                            st.markdown("#### Compliance Assessment")
                            st.write(f"**Compliant**: {'✅ Yes' if analysis['compliance_compliant'] else '❌ No'}")
                            st.write(f"**Compliance Score**: {analysis['compliance_score']}/100")
                            
                            if analysis["compliance_issues"]:
                                st.markdown("**Violations**:")
                                for issue in analysis["compliance_issues"]:
                                    st.warning(f"- {issue.get('issue', 'Unknown issue')}")
                
                except Exception as e:
                    st.error(f"Failed to load analysis details: {e}")
                    page_logger.error(f"Failed to load analysis {selected_id}: {e}")
        else:
            st.info("No results found. Try adjusting your filters.")
    
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        page_logger.error(f"Search error: {e}")

# If there are stored search results from a previous run, re-render them so
# download/selection doesn't cause the UI to disappear on reruns.
render_search_results_from_session()

# Quick stats
st.markdown("---")
st.markdown("### 📈 Quick Navigation")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Show Recent Approvals", use_container_width=True):
        st.session_state.search_filter = "APPROVE"
        st.rerun()

with col2:
    if st.button("Show Needing Review", use_container_width=True):
        st.session_state.search_filter = "REVIEW_REQUIRED"
        st.rerun()

with col3:
    if st.button("Show Rejections", use_container_width=True):
        st.session_state.search_filter = "REJECT"
        st.rerun()
