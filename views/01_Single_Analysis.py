"""Single Change Request Analysis Page (moved from pages)."""

import streamlit as st
from datetime import datetime
import json
from pathlib import Path
import sys
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.models import (
    ChangeRequest, ChangeType, ChangeCategory, Complexity, AnalysisResult
)
from core.llm_engine import LLMEngine
from core.rag_engine import RAGEngine
from core.risk_scorer import RiskScorer
from core.decision_engine import DecisionEngine, AnalysisOrchestrator
from data.repository import AnalysisRepository
from utils.logger import logger, get_logger
from utils.validators import validate_change_request

page_logger = get_logger(__name__)

st.set_page_config(
    page_title="Single Analysis",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Change Request Analysis")
st.markdown("Analyze a single change request and get detailed assessment")

# Initialize session state
if "analysisresult" not in st.session_state:
    st.session_state.analysis_result = None
if "engines_initialized" not in st.session_state:
    st.session_state.engines_initialized = False
if "llm_engine" not in st.session_state:
    st.session_state.llm_engine = None
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None
if "risk_scorer" not in st.session_state:
    st.session_state.risk_scorer = None
if "decision_engine" not in st.session_state:
    st.session_state.decision_engine = None


@st.cache_resource
def initialize_engines():
    """Initialize LLM, RAG, and other engines."""
    try:
        with st.spinner("🔄 Initializing AI engines..."):
            llm = LLMEngine()
            rag = RAGEngine()
            scorer = RiskScorer()
            decider = DecisionEngine()
            page_logger.info("All engines initialized successfully")
            return llm, rag, scorer, decider
    except Exception as e:
        page_logger.error(f"Failed to initialize engines: {e}")
        st.error(f"❌ Failed to initialize system: {str(e)}")
        raise


def render_decision_banner(decision, risk_score, confidence):
    """Render decision banner with color coding."""
    
    # Color mapping
    color_map = {
        "APPROVE": "#28a745",
        "REVIEW_REQUIRED": "#ffc107",
        "REJECT": "#dc3545",
    }
    
    color = color_map.get(decision, "#6c757d")
    emoji_map = {
        "APPROVE": "✅",
        "REVIEW_REQUIRED": "⚠️",
        "REJECT": "❌",
    }
    emoji = emoji_map.get(decision, "ℹ️")
    
    st.markdown(f"""
    <div style="
        background-color: {color}20;
        border-left: 5px solid {color};
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    ">
        <h2 style="color: {color}; margin: 0;">
            {emoji} {decision.replace('_', ' ')}
        </h2>
        <p style="margin: 0.5rem 0 0 0;">
            Risk Score: <strong>{risk_score}/100</strong> | 
            Confidence: <strong>{confidence}%</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(risk_assessment, compliance_result, risk_scoring):
    """Render analysis metrics."""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Risk Score", f"{risk_scoring.final_risk_score}/100",
                 delta=f"{risk_assessment.risk_score - risk_scoring.final_risk_score:+d} (LLM)")
    
    with col2:
        st.metric("Confidence", f"{risk_assessment.confidence}%")
    
    with col3:
        st.metric("Compliance Score", f"{compliance_result.compliance_score}%",
                 delta="✅ Compliant" if compliance_result.compliant else "⚠️ Issues")
    
    with col4:
        st.metric("Risk Level", risk_scoring.risk_level.value)


def render_analysis_details(llm_assessment, compliance_result, risk_scoring):
    """Render detailed analysis information."""
    
    st.markdown("### 📊 Analysis Details")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Risk Factors", 
        "Compliance",
        "Recommendations",
        "Validation",
        "Scoring Breakdown"
    ])
    
    with tab1:
        st.markdown("#### Risk Factors Identified")
        if llm_assessment.risk_factors:
            for i, factor in enumerate(llm_assessment.risk_factors, 1):
                st.write(f"{i}. {factor}")
        else:
            st.info("No significant risk factors identified")
        
        if llm_assessment.red_flags:
            st.markdown("#### 🚨 Red Flags")
            for flag in llm_assessment.red_flags:
                st.warning(f"⚠️ {flag}")
    
    with tab2:
        st.markdown(f"**Compliance Status**: {'✅ Compliant' if compliance_result.compliant else '❌ Non-Compliant'}")
        st.markdown(f"**Compliance Score**: {compliance_result.compliance_score}/100")
        
        if compliance_result.violations:
            st.markdown("#### 🚫 Policy Violations")
            for violation in compliance_result.violations:
                severity_color = "🔴" if violation.severity == "CRITICAL" else "🟡"
                with st.expander(f"{severity_color} {violation.policy} - {violation.severity}"):
                    st.markdown(f"**Issue**: {violation.issue}")
                    st.markdown(f"**Policy Section**: {violation.violated_section}")
                    st.markdown(f"**Quote**: > {violation.policy_quote}")
                    st.markdown(f"**How to Fix**: {violation.remediation}")
        else:
            st.success("✅ No policy violations detected")
        
        if compliance_result.compliant_aspects:
            st.markdown("#### ✅ Compliant Aspects")
            for aspect in compliance_result.compliant_aspects:
                st.success(f"✓ {aspect}")
    
    with tab3:
        st.markdown("#### Recommendations for Improvement")
        if llm_assessment.recommendations:
            for i, rec in enumerate(llm_assessment.recommendations, 1):
                st.write(f"{i}. {rec}")
        else:
            st.info("No specific recommendations needed")
        
        if llm_assessment.validation_suggestions:
            st.markdown("#### Validation Suggestions")
            for i, validation in enumerate(llm_assessment.validation_suggestions, 1):
                st.write(f"{i}. {validation}")
    
    with tab4:
        if llm_assessment.critical_concerns:
            st.markdown("#### ⚠️ Critical Concerns")
            for concern in llm_assessment.critical_concerns:
                st.error(f"🚨 {concern}")
        
        if llm_assessment.positive_aspects:
            st.markdown("#### ✅ Positive Aspects")
            for aspect in llm_assessment.positive_aspects:
                st.success(f"✓ {aspect}")
        
        if llm_assessment.missing_information:
            st.markdown("#### ⓘ Missing Information")
            for item in llm_assessment.missing_information:
                st.info(f"ℹ️ {item}")
    
    with tab5:
        st.json(risk_scoring.scoring_breakdown, expanded=False)


# Main form
with st.form("change_analysis_form"):
    st.markdown("### Change Request Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        short_desc = st.text_input(
            "Short Description *",
            help="Brief summary (10-200 characters)",
            max_chars=200,
            placeholder="Update API rate limiting to 500 req/sec"
        )
        
        change_type = st.selectbox(
            "Change Type *",
            [t.value for t in ChangeType],
            help="Type of change: standard, normal, or emergency"
        )
        
        change_category = st.selectbox(
            "Change Category *",
            [c.value for c in ChangeCategory],
            help="What area does this change affect?"
        )
        
        complexity = st.selectbox(
            "Complexity *",
            [c.value for c in Complexity],
            help="Technical complexity level"
        )
    
    with col2:
        long_desc = st.text_area(
            "Long Description *",
            help="Detailed explanation of the change",
            placeholder="Detailed description of why, what, and how..."
        )
        
        planned_window = st.text_input(
            "Planned Window (ISO datetime) *",
            help="Format: 2024-02-20T22:00:00Z",
            placeholder="2024-02-20T22:00:00Z"
        )
        
        impacted_services = st.text_area(
            "Impacted Services *",
            help="Comma-separated list of affected services",
            height=80,
            placeholder="API Gateway, Authentication Service, Database"
        )
    
    st.markdown("### Implementation & Validation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        impl_steps = st.text_area(
            "Implementation Steps *",
            help="Step-by-step instructions",
            height=150,
            placeholder="1. SSH to server\n2. Update config file\n3. Restart service"
        )
        
        rollback_plan = st.text_area(
            "Rollback Plan *",
            help="How to revert if issues occur",
            height=150,
            placeholder="1. Restore previous config\n2. Restart service"
        )
    
    with col2:
        validation_steps = st.text_area(
            "Validation Steps *",
            help="How to verify the change worked",
            height=150,
            placeholder="1. Test endpoint works\n2. Monitor error rate\n3. Verify latency"
        )
    
    # Submit button
    submit = st.form_submit_button(
        "🔍 Analyze Change Request",
        use_container_width=True,
        type="primary"
    )

# Process submission
if submit:
    # Validate inputs
    form_data = {
        "short_description": short_desc,
        "long_description": long_desc,
        "change_type": change_type,
        "change_category": change_category,
        "implementation_steps": impl_steps,
        "validation_steps": validation_steps,
        "rollback_plan": rollback_plan,
        "planned_window": planned_window,
        "impacted_services": impacted_services,
        "complexity": complexity,
    }
    
    is_valid, change_request, errors = validate_change_request(form_data)
    
    if not is_valid:
        st.error("❌ Validation errors:")
        for error in errors:
            st.write(f"- {error}")
    else:
        # Initialize engines
        if not st.session_state.engines_initialized:
            try:
                llm_eng, rag_eng, risk_sc, dec_eng = initialize_engines()
                st.session_state.llm_engine = llm_eng
                st.session_state.rag_engine = rag_eng
                st.session_state.risk_scorer = risk_sc
                st.session_state.decision_engine = dec_eng
                st.session_state.engines_initialized = True
            except Exception as e:
                st.error(f"Failed to initialize engines: {e}")
                st.stop()
        
        # Run analysis
        with st.spinner("🔄 Analyzing change request..."):
            progress_placeholder = st.empty()
            
            try:
                # Initialize orchestrator
                orchestrator = AnalysisOrchestrator(
                    st.session_state.llm_engine,
                    st.session_state.rag_engine,
                    st.session_state.risk_scorer,
                    st.session_state.decision_engine,
                )
                
                # Run analysis
                progress_placeholder.info("📊 Running LLM analysis...")
                llm_assessment, compliance_result, risk_scoring, final_decision, reasoning = orchestrator.analyze_change(change_request)
                progress_placeholder.empty()
                
                # Display results
                st.success("✅ Analysis Complete!")
                
                # Decision banner
                render_decision_banner(
                    final_decision.value,
                    risk_scoring.final_risk_score,
                    llm_assessment.confidence
                )
                
                # Metrics
                render_metrics(llm_assessment, compliance_result, risk_scoring)
                
                st.markdown(f"### 📝 Reasoning\n{reasoning}")
                
                # Detailed analysis
                render_analysis_details(llm_assessment, compliance_result, risk_scoring)
                
                # Save to database
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    if st.button("💾 Save Analysis to Database", use_container_width=True):
                        try:
                            analysis_id = AnalysisRepository.save_analysis(
                                short_description=change_request.short_description,
                                long_description=change_request.long_description,
                                change_type=change_request.change_type.value,
                                change_category=change_request.change_category.value,
                                implementation_steps=change_request.implementation_steps,
                                validation_steps=change_request.validation_steps,
                                rollback_plan=change_request.rollback_plan,
                                planned_window=change_request.planned_window,
                                impacted_services=change_request.impacted_services,
                                complexity=change_request.complexity.value,
                                final_decision=final_decision.value,
                                risk_score=risk_scoring.final_risk_score,
                                confidence=llm_assessment.confidence,
                                reasoning=reasoning,
                                risk_factors=llm_assessment.risk_factors,
                                red_flags=llm_assessment.red_flags,
                                recommendations=llm_assessment.recommendations,
                                compliance_compliant=compliance_result.compliant,
                                compliance_score=compliance_result.compliance_score,
                                compliance_issues=[v.dict() for v in compliance_result.violations],
                            )
                            st.success(f"✅ Analysis saved! ID: {analysis_id}")
                            page_logger.info(f"Analysis saved with ID: {analysis_id}")
                        except Exception as e:
                            st.error(f"Failed to save: {str(e)}")
                            page_logger.error(f"Failed to save analysis: {e}")
                
                with col2:
                    if st.button("📋 Copy JSON", use_container_width=True):
                        st.code(json.dumps({
                            "short_description": change_request.short_description,
                            "long_description": change_request.long_description,
                            "final_decision": final_decision.value,
                            "risk_score": risk_scoring.final_risk_score,
                        }, ensure_ascii=False, indent=2))
                
                with col3:
                    # Download JSON of the result
                    result_json = json.dumps({
                        "short_description": change_request.short_description,
                        "long_description": change_request.long_description,
                        "final_decision": final_decision.value,
                        "risk_score": risk_scoring.final_risk_score,
                        "reasoning": reasoning,
                    }, ensure_ascii=False, indent=2)

                    st.download_button(
                        "📥 Download JSON",
                        data=result_json,
                        file_name="analysis_result.json",
                        mime="application/json",
                        use_container_width=True,
                    )

                    if st.button("🔁 New Analysis", use_container_width=True):
                        st.experimental_rerun()
            except Exception as e:
                page_logger.error(f"Analysis failed: {e}")
                st.error(f"❌ Analysis failed: {e}")
