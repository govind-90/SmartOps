"""Risk scoring engine combining LLM and rule-based approaches."""

from datetime import datetime
from core.models import (
    ChangeRequest,
    RiskAssessment,
    RiskScoringResult,
    RiskLevel,
)
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class RiskScorer:
    """Hybrid risk scoring combining LLM and rule-based scoring."""

    # Risk scoring constants
    COMPLEXITY_SCORES = {
        "low": 10,
        "medium": 30,
        "high": 60,
    }

    CATEGORY_SCORES = {
        "configuration": 10,
        "deployment": 20,
        "infrastructure": 30,
        "database": 40,
    }

    IMPACT_SCORES = {
        1: 10,
        2: 20,
        3: 30,
        4: 40,
        5: 50,
        6: 70,  # 6+ services
    }

    def calculate_risk_score(
        self,
        change_request: ChangeRequest,
        llm_assessment: RiskAssessment,
    ) -> RiskScoringResult:
        """
        Calculate hybrid risk score combining LLM and rule-based approaches.
        
        Args:
            change_request: The change request
            llm_assessment: LLM analysis result
            
        Returns:
            RiskScoringResult: Combined risk score result
        """
        # LLM risk score (40% weight)
        llm_risk = llm_assessment.risk_score

        # Rule-based risk score (60% weight)
        rule_based_risk = self._calculate_rule_based_score(change_request)

        # Calculate weighted final score
        final_risk_score = int(
            (llm_risk * 0.4) + (rule_based_risk * 0.6)
        )

        # Determine risk level
        if final_risk_score < 40:
            risk_level = RiskLevel.LOW
        elif final_risk_score > 70:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.MEDIUM

        scoring_breakdown = {
            "llm_risk_score": llm_risk,
            "llm_weight": "40%",
            "rule_based_risk_score": rule_based_risk,
            "rule_based_weight": "60%",
            "complexity_points": self.COMPLEXITY_SCORES.get(change_request.complexity.value, 20),
            "category_points": self.CATEGORY_SCORES.get(change_request.change_category.value, 15),
            "impact_points": self._calculate_impact_score(change_request),
            "documentation_penalty": self._calculate_documentation_penalty(change_request),
            "timing_penalty": self._calculate_timing_penalty(change_request),
        }

        result = RiskScoringResult(
            llm_risk_score=llm_risk,
            rule_based_risk_score=rule_based_risk,
            final_risk_score=final_risk_score,
            risk_level=risk_level,
            scoring_breakdown=scoring_breakdown,
        )

        logger.info(
            f"Risk score calculated: LLM={llm_risk}, RuleBased={rule_based_risk}, "
            f"Final={final_risk_score}, Level={risk_level.value}"
        )

        return result

    def _calculate_rule_based_score(self, change_request: ChangeRequest) -> int:
        """
        Calculate rule-based risk score.
        
        Args:
            change_request: The change request
            
        Returns:
            int: Rule-based risk score (0-100)
        """
        score = 0

        # Complexity component (0-60)
        complexity_score = self.COMPLEXITY_SCORES.get(
            change_request.complexity.value,
            30
        )
        score += complexity_score

        # Category component (0-40)
        category_score = self.CATEGORY_SCORES.get(
            change_request.change_category.value,
            20
        )
        score += category_score

        # Impact component (0-70)
        impact_score = self._calculate_impact_score(change_request)
        score += impact_score

        # Documentation quality (penalty 0-20)
        doc_penalty = self._calculate_documentation_penalty(change_request)
        score += doc_penalty

        # Timing (penalty 0-30)
        timing_score = self._calculate_timing_penalty(change_request)
        score += timing_score

        # Rollback completeness (penalty 0-20)
        rollback_score = self._calculate_rollback_score(change_request)
        score += rollback_score

        # Validation completeness (penalty 0-20)
        validation_score = self._calculate_validation_score(change_request)
        score += validation_score

        # Clamp to 0-100
        return min(100, max(0, score))

    def _calculate_impact_score(self, change_request: ChangeRequest) -> int:
        """Calculate impact based on number of affected services."""
        services = [s.strip() for s in change_request.impacted_services.split(",") if s.strip()]
        num_services = len(services)

        # Cap at 6+
        service_count = min(num_services, 6)

        return self.IMPACT_SCORES.get(service_count, 70)

    def _calculate_documentation_penalty(self, change_request: ChangeRequest) -> int:
        """
        Calculate documentation quality penalty.
        
        Returns:
            int: Penalty points (0-20)
        """
        penalty = 0

        # Short description length (min 10, max 200)
        if len(change_request.short_description) < 20:
            penalty += 5
        elif len(change_request.short_description) < 50:
            penalty += 2

        # Long description length (should be substantial)
        if len(change_request.long_description) < 100:
            penalty += 8
        elif len(change_request.long_description) < 200:
            penalty += 3

        # Implementation steps (should be detailed)
        impl_lines = len(change_request.implementation_steps.split("\n"))
        if impl_lines < 2:
            penalty += 8
        elif impl_lines < 3:
            penalty += 3

        return min(20, penalty)

    def _calculate_timing_penalty(self, change_request: ChangeRequest) -> int:
        """
        Calculate timing risk penalty.
        
        Returns:
            int: Penalty points (0-30)
        """
        penalty = 0

        try:
            planned_dt = datetime.fromisoformat(change_request.planned_window)
            hour = planned_dt.hour
            weekday = planned_dt.weekday()

            # Business hours (09:00-17:00) add 10 points
            if 9 <= hour < 17:
                penalty += 10

            # Weekday adds 5 points
            if weekday < 5:  # Monday=0, Friday=4
                penalty += 5

            # Early morning (00:00-08:00) - lower penalty (5)
            # Late night (18:00-23:59) - moderate (15)
            if 0 <= hour < 8:
                penalty += 5
            elif 18 <= hour < 24:
                penalty += 15

            # Emergency changes during hours: additional penalty
            if change_request.change_type.value == "emergency" and 9 <= hour < 17:
                penalty += 10

        except ValueError:
            logger.warning(f"Invalid date format: {change_request.planned_window}")
            penalty += 5

        return min(30, penalty)

    def _calculate_rollback_score(self, change_request: ChangeRequest) -> int:
        """
        Calculate rollback completeness penalty.
        
        Returns:
            int: Penalty points (0-20)
        """
        penalty = 0

        # Check for common "no rollback" indicators
        rollback_text = change_request.rollback_plan.lower()
        if rollback_text.startswith("none") or rollback_text.startswith("n/a"):
            penalty += 20
        elif len(change_request.rollback_plan) < 30:
            penalty += 10
        elif "rollback" not in rollback_text and "revert" not in rollback_text:
            penalty += 15

        return min(20, penalty)

    def _calculate_validation_score(self, change_request: ChangeRequest) -> int:
        """
        Calculate validation completeness penalty.
        
        Returns:
            int: Penalty points (0-20)
        """
        penalty = 0

        validation_text = change_request.validation_steps.lower()

        # Check for validation specificity
        if len(change_request.validation_steps) < 30:
            penalty += 15
        elif len(change_request.validation_steps) < 100:
            penalty += 8

        # Check for specific test mentions
        test_keywords = ["test", "monitor", "verify", "validate", "check", "assert"]
        has_tests = any(keyword in validation_text for keyword in test_keywords)
        if not has_tests:
            penalty += 10

        return min(20, penalty)
