"""Bulk Change Analysis Page (moved from pages)."""

import streamlit as st
from pathlib import Path
import sys
import time
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.llm_engine import LLMEngine
from core.rag_engine import RAGEngine
from core.risk_scorer import RiskScorer
from core.decision_engine import AnalysisOrchestrator, DecisionEngine
from utils.excel_handler import ExcelHandler
from data.repository import AnalysisRepository
from config.settings import settings
from utils.logger import get_logger

page_logger = get_logger(__name__)

st.set_page_config(
    page_title="Bulk Analysis",
    page_icon="📁",
    layout="wide",
)

st.title("📁 Bulk Change Analysis")
st.markdown("Upload an Excel file with multiple change requests for batch analysis")

# Initialize session state
if "engines_initialized" not in st.session_state:
    st.session_state.engines_initialized = False


@st.cache_resource
def initialize_engines():
    """Initialize engines."""
    try:
        with st.spinner("🔄 Initializing engines..."):
            llm = LLMEngine()
            rag = RAGEngine()
            scorer = RiskScorer()
            decider = DecisionEngine()
            return llm, rag, scorer, decider
    except Exception as e:
        page_logger.error(f"Failed to initialize engines: {e}")
        st.error(f"❌ Failed to initialize system: {str(e)}")
        raise


# File upload
uploaded_file = st.file_uploader(
    "Upload Excel file (.xlsx or .xls)",
    type=["xlsx", "xls"],
    help="Format must match sample template"
)

if uploaded_file:
    st.success(f"✅ File uploaded: {uploaded_file.name}")
    
    # Save uploaded file temporarily
    temp_path = f"/tmp/{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    try:
        # Parse Excel
        with st.spinner("📖 Reading Excel file..."):
            valid_requests, parse_errors, total_rows = ExcelHandler.read_excel(temp_path)
        
        st.info(f"📊 File Summary: {total_rows} total rows, {len(valid_requests)} valid, {len(parse_errors)} errors")
        
        if parse_errors:
            st.warning("⚠️ Parse Errors Detected")
            errors_df = pd.DataFrame([{
                "Row": e.row_number,
                "Column": e.column,
                "Error": e.error,
            } for e in parse_errors])
            st.dataframe(errors_df, use_container_width=True)
        
        if valid_requests:
            # Start analysis
            st.markdown("---")
            st.markdown("### 🔄 Batch Processing")
            
            if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                # Initialize engines
                if not st.session_state.engines_initialized:
                    llm_eng, rag_eng, risk_sc, dec_eng = initialize_engines()
                    st.session_state.engines_initialized = True
                else:
                    llm_eng = st.session_state.get("llm_engine")
                    rag_eng = st.session_state.get("rag_engine")
                    risk_sc = st.session_state.get("risk_scorer")
                    dec_eng = st.session_state.get("decision_engine")
                
                orchestrator = AnalysisOrchestrator(llm_eng, rag_eng, risk_sc, dec_eng)
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_placeholder = st.empty()
                errors_placeholder = st.empty()
                
                analyses_results = []
                processing_errors = []
                
                # Process each change
                for i, change_request in enumerate(valid_requests):
                    progress = (i + 1) / len(valid_requests)
                    progress_bar.progress(progress)
                    status_text.info(f"⏳ Processing {i+1}/{len(valid_requests)}: {change_request.short_description[:50]}...")
                    
                    try:
                        # Run analysis
                        llm_assessment, compliance, risk_scoring, final_decision, reasoning = orchestrator.analyze_change(change_request)
                        
                        # Save to database
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
                            compliance_compliant=compliance.compliant,
                            compliance_score=compliance.compliance_score,
                            compliance_issues=[v.dict() for v in compliance.violations],
                        )
                        
                        analyses_results.append({
                            "id": analysis_id,
                            "short_description": change_request.short_description,
                            "change_category": change_request.change_category.value,
                            "final_decision": final_decision.value,
                            "risk_score": risk_scoring.final_risk_score,
                            "confidence": llm_assessment.confidence,
                            "compliance": "✅" if compliance.compliant else "❌",
                        })
                        
                        # Rate limiting
                        time.sleep(settings.BULK_PROCESSING_DELAY_SECONDS)
                        
                    except Exception as e:
                        page_logger.error(f"Error processing row {i+1}: {e}")
                        processing_errors.append({
                            "row": i + 1,
                            "description": change_request.short_description,
                            "error": str(e),
                        })
                
                # Clear progress
                progress_bar.empty()
                status_text.empty()
                
                # Display results
                st.success(f"✅ Batch processing complete!")
                st.info(f"Processed: {len(analyses_results)} successful, {len(processing_errors)} errors")
                
                # Results table
                if analyses_results:
                    st.markdown("### 📊 Results")
                    results_df = pd.DataFrame(analyses_results)
                    
                    # Color coding
                    def color_decision(val):
                        if val == "APPROVE":
                            return "background-color: #d4edda"
                        elif val == "REVIEW_REQUIRED":
                            return "background-color: #fff3cd"
                        else:
                            return "background-color: #f8d7da"
                    
                    styled_df = results_df.style.applymap(
                        color_decision,
                        subset=["final_decision"]
                    )
                    
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Export option
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            "analysis_results.csv",
                            "text/csv",
                            use_container_width=True,
                        )
                    
                    with col2:
                        # Export to Excel
                        try:
                            output_file = ExcelHandler.write_results_to_excel(
                                "/tmp/analysis_results.xlsx",
                                analyses_results
                            )
                            with open(output_file, "rb") as f:
                                excel_data = f.read()
                            st.download_button(
                                "📥 Download Excel",
                                excel_data,
                                "analysis_results.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                            )
                        except Exception as e:
                            st.warning(f"Could not generate Excel export: {e}")
                
                # Errors
                if processing_errors:
                    st.markdown("### ❌ Processing Errors")
                    errors_df = pd.DataFrame(processing_errors)
                    st.dataframe(errors_df, use_container_width=True)
                
                # Summary stats
                st.markdown("### 📈 Summary Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                approval_count = len([r for r in analyses_results if r["final_decision"] == "APPROVE"])
                review_count = len([r for r in analyses_results if r["final_decision"] == "REVIEW_REQUIRED"])
                reject_count = len([r for r in analyses_results if r["final_decision"] == "REJECT"])
                avg_risk = sum([r["risk_score"] for r in analyses_results]) / len(analyses_results) if analyses_results else 0
                
                with col1:
                    st.metric("Approved", approval_count)
                with col2:
                    st.metric("Needs Review", review_count)
                with col3:
                    st.metric("Rejected", reject_count)
                with col4:
                    st.metric("Avg Risk Score", f"{avg_risk:.1f}")
    
    except ValueError as e:
        st.error(f"❌ {str(e)}")
        page_logger.error(f"Validation error: {e}")
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        page_logger.error(f"Error processing file: {e}")

# Template info
st.markdown("---")
st.markdown("""
### 📝 Excel Format Requirements
The Excel file must have these columns:
- Short Description
- Long Description
- Change Type (standard/normal/emergency)
- Change Category (configuration/infrastructure/deployment/database)
- Implementation Steps
- Validation Steps
- Rollback Plan
- Planned Window (ISO datetime)
- Impacted Services
- Complexity (low/medium/high)

[Download Sample Template](../../sample_data/sample_changes.xlsx)
""")
