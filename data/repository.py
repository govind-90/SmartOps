"""Data access layer (Repository pattern) for database operations."""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import json

from data.database import db, ChangeRequestModel, AnalysisModel
from core.models import Decision, DatabaseAnalysis, AnalyticsData
from utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisRepository:
    """Repository for managing analysis data."""

    @staticmethod
    def save_analysis(
        short_description: str,
        long_description: str,
        change_type: str,
        change_category: str,
        implementation_steps: str,
        validation_steps: str,
        rollback_plan: str,
        planned_window: str,
        impacted_services: str,
        complexity: str,
        final_decision: str,
        risk_score: int,
        confidence: int,
        reasoning: str,
        risk_factors: List[str],
        red_flags: List[str],
        recommendations: List[str],
        compliance_compliant: bool,
        compliance_score: int,
        compliance_issues: List[dict],
    ) -> int:
        """
        Save a complete analysis (change request + result).
        
        Args:
            short_description: Brief change description
            long_description: Detailed description
            change_type: Type of change
            change_category: Category of change
            implementation_steps: Implementation details
            validation_steps: Validation details
            rollback_plan: Rollback procedure
            planned_window: Planned change window
            impacted_services: Affected services
            complexity: Complexity level
            final_decision: Final decision (APPROVE/REVIEW_REQUIRED/REJECT)
            risk_score: Risk score (0-100)
            confidence: Confidence score (0-100)
            reasoning: Detailed reasoning
            risk_factors: List of risk factors
            red_flags: List of red flags
            recommendations: List of recommendations
            compliance_compliant: Compliance status
            compliance_score: Compliance score
            compliance_issues: List of compliance issues
            
        Returns:
            int: Analysis ID
        """
        session = db.get_session()
        try:
            # Create change request
            change_request = ChangeRequestModel(
                short_description=short_description,
                long_description=long_description,
                change_type=change_type,
                change_category=change_category,
                implementation_steps=implementation_steps,
                validation_steps=validation_steps,
                rollback_plan=rollback_plan,
                planned_window=planned_window,
                impacted_services=impacted_services,
                complexity=complexity,
            )
            session.add(change_request)
            session.flush()  # Get the ID

            # Create analysis result
            analysis = AnalysisModel(
                change_request_id=change_request.id,
                final_decision=final_decision,
                risk_score=risk_score,
                confidence=confidence,
                reasoning=reasoning,
                risk_factors=json.dumps(risk_factors),
                red_flags=json.dumps(red_flags),
                recommendations=json.dumps(recommendations),
                compliance_compliant=1 if compliance_compliant else 0,
                compliance_score=compliance_score,
                compliance_issues=json.dumps(compliance_issues),
            )
            session.add(analysis)
            session.commit()

            logger.info(f"Analysis saved: ID={analysis.id}, Decision={final_decision}, Risk={risk_score}")
            return analysis.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save analysis: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def get_analysis(analysis_id: int) -> Optional[dict]:
        """
        Retrieve analysis by ID.
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            dict: Analysis data with change request, or None if not found
        """
        session = db.get_session()
        try:
            analysis = session.query(AnalysisModel).filter(
                AnalysisModel.id == analysis_id
            ).first()
            
            if not analysis:
                return None

            change_request = analysis.change_request
            return {
                "id": analysis.id,
                "change_request_id": analysis.change_request_id,
                "short_description": change_request.short_description,
                "long_description": change_request.long_description,
                "change_type": change_request.change_type,
                "change_category": change_request.change_category,
                "impacted_services": change_request.impacted_services,
                "complexity": change_request.complexity,
                "planned_window": change_request.planned_window,
                "final_decision": analysis.final_decision,
                "risk_score": analysis.risk_score,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "risk_factors": json.loads(analysis.risk_factors),
                "red_flags": json.loads(analysis.red_flags),
                "recommendations": json.loads(analysis.recommendations),
                "compliance_compliant": bool(analysis.compliance_compliant),
                "compliance_score": analysis.compliance_score,
                "compliance_issues": json.loads(analysis.compliance_issues),
                "created_at": analysis.created_at,
            }
        except Exception as e:
            logger.error(f"Failed to retrieve analysis {analysis_id}: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def search_analyses(
        decision: Optional[str] = None,
        risk_min: Optional[int] = None,
        risk_max: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        text_search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[dict], int]:
        """
        Search analyses with multiple filters.
        
        Args:
            decision: Filter by decision type
            risk_min: Minimum risk score
            risk_max: Maximum risk score
            start_date: Start date filter
            end_date: End date filter
            text_search: Search in description
            limit: Result limit
            offset: Result offset
            
        Returns:
            tuple: (List of analyses, total count)
        """
        session = db.get_session()
        try:
            query = session.query(AnalysisModel)

            # Apply filters
            filters = []
            if decision:
                filters.append(AnalysisModel.final_decision == decision)
            if risk_min is not None:
                filters.append(AnalysisModel.risk_score >= risk_min)
            if risk_max is not None:
                filters.append(AnalysisModel.risk_score <= risk_max)
            if start_date:
                filters.append(AnalysisModel.created_at >= start_date)
            if end_date:
                filters.append(AnalysisModel.created_at <= end_date)

            if filters:
                query = query.filter(and_(*filters))

            # Text search
            if text_search:
                query = query.join(ChangeRequestModel).filter(
                    ChangeRequestModel.short_description.ilike(f"%{text_search}%")
                )

            # Get total count
            total_count = query.count()

            # Apply pagination and ordering
            results = (
                query.order_by(desc(AnalysisModel.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )

            analyses = []
            for analysis in results:
                cr = analysis.change_request
                analyses.append({
                    "id": analysis.id,
                    "short_description": cr.short_description,
                    "final_decision": analysis.final_decision,
                    "risk_score": analysis.risk_score,
                    "created_at": analysis.created_at,
                })

            return analyses, total_count
        except Exception as e:
            logger.error(f"Failed to search analyses: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def get_analytics_data(
        days_back: int = 30,
    ) -> AnalyticsData:
        """
        Get aggregated analytics data.
        
        Args:
            days_back: Number of days to include
            
        Returns:
            AnalyticsData: Aggregated analytics
        """
        session = db.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            query = session.query(AnalysisModel).filter(
                AnalysisModel.created_at >= cutoff_date
            )
            analyses = query.all()

            if not analyses:
                return AnalyticsData()

            # Calculate stats
            total = len(analyses)
            approved = sum(1 for a in analyses if a.final_decision == "APPROVE")
            reviewed = sum(1 for a in analyses if a.final_decision == "REVIEW_REQUIRED")
            rejected = sum(1 for a in analyses if a.final_decision == "REJECT")

            approval_rate = (approved / total * 100) if total > 0 else 0
            avg_risk = sum(a.risk_score for a in analyses) / total if total > 0 else 0
            avg_confidence = sum(a.confidence for a in analyses) / total if total > 0 else 0

            # Category breakdown
            category_breakdown = {}
            for analysis in analyses:
                category = analysis.change_request.change_category
                category_breakdown[category] = category_breakdown.get(category, 0) + 1

            # Complexity breakdown
            complexity_breakdown = {}
            for analysis in analyses:
                complexity = analysis.change_request.complexity
                complexity_breakdown[complexity] = complexity_breakdown.get(complexity, 0) + 1

            # Decision breakdown
            decision_breakdown = {
                "APPROVE": approved,
                "REVIEW_REQUIRED": reviewed,
                "REJECT": rejected,
            }

            # Risk distribution
            risk_distribution = {
                "LOW": sum(1 for a in analyses if a.risk_score < 25),
                "MEDIUM": sum(1 for a in analyses if 25 <= a.risk_score <= 75),
                "HIGH": sum(1 for a in analyses if a.risk_score > 75),
            }

            return AnalyticsData(
                total_analyzed=total,
                total_approved=approved,
                total_reviewed=reviewed,
                total_rejected=rejected,
                approval_rate=round(approval_rate, 2),
                average_risk_score=round(avg_risk, 2),
                average_confidence=round(avg_confidence, 2),
                analysis_by_category=category_breakdown,
                analysis_by_complexity=complexity_breakdown,
                analysis_by_decision=decision_breakdown,
                risk_distribution=risk_distribution,
            )
        except Exception as e:
            logger.error(f"Failed to get analytics data: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def delete_analysis(analysis_id: int) -> bool:
        """
        Delete an analysis and associated change request.
        
        Args:
            analysis_id: Analysis ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        session = db.get_session()
        try:
            analysis = session.query(AnalysisModel).filter(
                AnalysisModel.id == analysis_id
            ).first()
            
            if not analysis:
                return False

            session.delete(analysis)
            session.commit()
            logger.info(f"Deleted analysis {analysis_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete analysis {analysis_id}: {e}")
            raise
        finally:
            session.close()
