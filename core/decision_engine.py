"""Decision engine for final analysis decisions."""

from typing import List
from core.models import (
    RiskAssessment,
    ComplianceResult,
    RiskScoringResult,
    Decision,
)
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    """Engine for making final change approval decisions."""

    def __init__(self) -> None:
        """Initialize decision engine with configured thresholds."""
        self.approve_threshold = settings.RISK_APPROVE_THRESHOLD
        self.reject_threshold = settings.RISK_REJECT_THRESHOLD

    def make_decision(
        self,
        llm_assessment: RiskAssessment,
        compliance_result: ComplianceResult,
        risk_scoring: RiskScoringResult,
    ) -> tuple[Decision, str]:
        """
        Make final decision based on all analysis signals.
        
        Args:
            llm_assessment: LLM-based risk assessment
            compliance_result: Policy compliance check result
            risk_scoring: Hybrid risk scoring result
            
        Returns:
            tuple: (Final decision, Reasoning string)
        """
        reasoning_parts: List[str] = []

        # Check 1: Compliance violations (highest priority)
        if not compliance_result.compliant and compliance_result.violations:
            critical_violations = [
                v for v in compliance_result.violations
                if v.severity == "CRITICAL"
            ]
            if critical_violations:
                reasoning_parts.append(
                    f"Critical compliance violations detected ({len(critical_violations)}): "
                    f"{', '.join(v.issue for v in critical_violations[:2])}"
                )
                logger.info("Decision: REVIEW_REQUIRED (critical compliance violations)")
                return Decision.REVIEW_REQUIRED, self._format_reasoning(reasoning_parts)

        # Check 2: Risk score thresholds
        final_risk = risk_scoring.final_risk_score

        if final_risk < self.approve_threshold:
            reasoning_parts.append(
                f"Low risk score ({final_risk}) below approval threshold ({self.approve_threshold})"
            )

            # Additional check: LLM recommendation for low-risk changes
            if llm_assessment.decision != Decision.REJECT:
                reasoning_parts.append(
                    f"LLM assessment: {llm_assessment.decision.value}"
                )
                if compliance_result.compliant:
                    logger.info("Decision: APPROVE (low risk, compliant, positive LLM)")
                    return Decision.APPROVE, self._format_reasoning(reasoning_parts)
                else:
                    # Low risk but compliance issues - review
                    reasoning_parts.append(
                        f"Compliance score: {compliance_result.compliance_score}/100"
                    )
                    logger.info("Decision: REVIEW_REQUIRED (low risk but compliance concerns)")
                    return (
                        Decision.REVIEW_REQUIRED,
                        self._format_reasoning(reasoning_parts)
                    )

        elif final_risk > self.reject_threshold:
            reasoning_parts.append(
                f"High risk score ({final_risk}) exceeds rejection threshold ({self.reject_threshold})"
            )
            reasoning_parts.append(
                f"Risk factors: {', '.join(llm_assessment.risk_factors[:3])}"
            )

            # Only auto-reject if compliant
            if compliance_result.compliant:
                logger.info("Decision: REJECT (high risk)")
                return Decision.REJECT, self._format_reasoning(reasoning_parts)
            else:
                # High risk and non-compliant - definitely review
                logger.info("Decision: REVIEW_REQUIRED (high risk + non-compliant)")
                return Decision.REVIEW_REQUIRED, self._format_reasoning(reasoning_parts)

        else:
            # Medium risk - needs review
            reasoning_parts.append(
                f"Medium risk score ({final_risk}): requires expert review"
            )
            reasoning_parts.append(
                f"Compliance status: {'Compliant' if compliance_result.compliant else 'Non-compliant'}"
            )

            # Use LLM recommendation as tiebreaker
            if llm_assessment.decision == Decision.REJECT:
                reasoning_parts.append("LLM recommends rejection")
                logger.info("Decision: REJECT (LLM recommendation)")
                return Decision.REJECT, self._format_reasoning(reasoning_parts)

            logger.info("Decision: REVIEW_REQUIRED (medium risk)")
            return Decision.REVIEW_REQUIRED, self._format_reasoning(reasoning_parts)

    def validate_change_safety(
        self,
        llm_assessment: RiskAssessment,
        compliance_result: ComplianceResult,
    ) -> tuple[bool, str]:
        """
        Validate change for critical safety issues.
        
        Args:
            llm_assessment: LLM assessment result
            compliance_result: Compliance check result
            
        Returns:
            tuple: (Safe, Reason if unsafe)
        """
        # Check for critical concerns
        if llm_assessment.critical_concerns:
            return False, f"Critical concerns: {'; '.join(llm_assessment.critical_concerns)}"

        # Check for missing rollback plan
        red_flags = [f.lower() for f in llm_assessment.red_flags]
        if any("rollback" in f for f in red_flags):
            return False, "Missing or unclear rollback plan detected"

        # Check for critical compliance violations
        if not compliance_result.compliant:
            critical = [v for v in compliance_result.violations if v.severity == "CRITICAL"]
            if critical:
                return (
                    False,
                    f"Critical compliance violations: {critical[0].issue}"
                )

        return True, ""

    @staticmethod
    def _format_reasoning(parts: List[str]) -> str:
        """
        Format reasoning parts into a coherent explanation.
        
        Args:
            parts: List of reasoning parts
            
        Returns:
            str: Formatted reasoning
        """
        if not parts:
            return "Analysis completed."

        return " ".join(parts)


class AnalysisOrchestrator:
    """Orchestrates the complete analysis workflow."""

    def __init__(
        self,
        llm_engine,
        rag_engine,
        risk_scorer,
        decision_engine,
    ) -> None:
        """
        Initialize orchestrator with all engines.
        
        Args:
            llm_engine: LLM analysis engine
            rag_engine: RAG compliance engine
            risk_scorer: Risk scoring engine
            decision_engine: Decision making engine
        """
        self.llm_engine = llm_engine
        self.rag_engine = rag_engine
        self.risk_scorer = risk_scorer
        self.decision_engine = decision_engine

    def analyze_change(self, change_request) -> tuple:
        """
        Perform complete analysis of a change request.
        
        Args:
            change_request: The change request to analyze
            
        Returns:
            tuple: (llm_assessment, compliance_result, risk_scoring, final_decision, reasoning)
            
        Raises:
            Exception: If any stage of analysis fails
        """
        try:
            logger.info(f"Starting analysis: {change_request.short_description[:50]}...")

            # Stage 1: LLM analysis
            logger.debug("Stage 1: LLM Analysis")
            llm_assessment = self.llm_engine.analyze_change(change_request)

            # Stage 2: Compliance checking
            logger.debug("Stage 2: Compliance Checking")
            change_summary = (
                f"{change_request.short_description}\n\n"
                f"{change_request.implementation_steps}\n\n"
                f"Rollback: {change_request.rollback_plan}"
            )
            compliance_result = self.rag_engine.check_compliance(change_summary)

            # Stage 3: Risk scoring
            logger.debug("Stage 3: Risk Scoring")
            risk_scoring = self.risk_scorer.calculate_risk_score(
                change_request,
                llm_assessment,
            )

            # Stage 4: Decision making
            logger.debug("Stage 4: Decision Making")
            final_decision, reasoning = self.decision_engine.make_decision(
                llm_assessment,
                compliance_result,
                risk_scoring,
            )

            logger.info(
                f"Analysis complete: {final_decision.value}, "
                f"Risk={risk_scoring.final_risk_score}, "
                f"Compliant={compliance_result.compliant}"
            )

            return llm_assessment, compliance_result, risk_scoring, final_decision, reasoning

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
