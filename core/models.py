"""Pydantic models for Change Management Analysis System."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ChangeType(str, Enum):
    """Change type classification."""
    STANDARD = "standard"
    NORMAL = "normal"
    EMERGENCY = "emergency"


class ChangeCategory(str, Enum):
    """Change category classification."""
    CONFIGURATION = "configuration"
    INFRASTRUCTURE = "infrastructure"
    DEPLOYMENT = "deployment"
    DATABASE = "database"


class Complexity(str, Enum):
    """Complexity level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Decision(str, Enum):
    """Analysis decision."""
    APPROVE = "APPROVE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECT = "REJECT"


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ChangeRequest(BaseModel):
    """Input data model for a production change request."""

    short_description: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Brief summary of the change (10-200 characters)"
    )
    long_description: str = Field(
        ...,
        min_length=20,
        description="Detailed description of the change"
    )
    change_type: ChangeType = Field(
        ...,
        description="Type of change: standard, normal, or emergency"
    )
    change_category: ChangeCategory = Field(
        ...,
        description="Category of change"
    )
    implementation_steps: str = Field(
        ...,
        min_length=10,
        description="Step-by-step implementation instructions"
    )
    validation_steps: str = Field(
        ...,
        min_length=10,
        description="How will the change be validated/tested"
    )
    rollback_plan: str = Field(
        ...,
        min_length=10,
        description="Procedure to rollback if issues occur"
    )
    planned_window: str = Field(
        ...,
        description="ISO datetime format for planned change window"
    )
    impacted_services: str = Field(
        ...,
        description="Comma-separated list of affected services"
    )
    complexity: Complexity = Field(
        ...,
        description="Technical complexity: low, medium, or high"
    )

    @field_validator("planned_window")
    @classmethod
    def validate_planned_window(cls, v: str) -> str:
        """Validate ISO datetime format."""
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError as exc:
            raise ValueError("Invalid ISO datetime format") from exc

    @field_validator("impacted_services")
    @classmethod
    def validate_services(cls, v: str) -> str:
        """Ensure services list is not empty."""
        services = [s.strip() for s in v.split(",") if s.strip()]
        if not services:
            raise ValueError("At least one service must be specified")
        return v

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "short_description": "Update API rate limiting configuration",
                "long_description": "Update rate limiting for API endpoints to reduce DDoS impact...",
                "change_type": "standard",
                "change_category": "configuration",
                "implementation_steps": "1. Update nginx config...\n2. Reload service...",
                "validation_steps": "1. Run load test...\n2. Monitor metrics...",
                "rollback_plan": "Revert config file and reload service",
                "planned_window": "2024-02-20T22:00:00Z",
                "impacted_services": "API Gateway, Rate Limiter",
                "complexity": "low"
            }
        }


class RiskAssessment(BaseModel):
    """LLM-based risk assessment output."""

    decision: Decision
    risk_score: int = Field(..., ge=0, le=100)
    confidence: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    reasoning: str
    risk_factors: List[str]
    red_flags: List[str]
    missing_information: List[str]
    recommendations: List[str]
    validation_suggestions: List[str]
    critical_concerns: List[str]
    positive_aspects: List[str]


class ComplianceIssue(BaseModel):
    """Single compliance issue."""

    policy: str
    violated_section: str
    policy_quote: str
    issue: str
    severity: str = Field(..., pattern="^(CRITICAL|WARNING)$")
    remediation: str


class ComplianceResult(BaseModel):
    """Policy compliance checking result."""

    compliant: bool
    compliance_score: int = Field(..., ge=0, le=100)
    violations: List[ComplianceIssue] = []
    compliant_aspects: List[str] = []
    improvement_suggestions: List[str] = []
    policies_reviewed: List[str] = []


class RiskScoringResult(BaseModel):
    """Hybrid risk scoring result."""

    llm_risk_score: int = Field(..., ge=0, le=100, description="Risk from LLM analysis (40% weight)")
    rule_based_risk_score: int = Field(..., ge=0, le=100, description="Rule-based risk score (60% weight)")
    final_risk_score: int = Field(..., ge=0, le=100, description="Weighted combined score")
    risk_level: RiskLevel
    scoring_breakdown: dict = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Final combined analysis result."""

    change_request: ChangeRequest
    llm_assessment: RiskAssessment
    compliance_result: ComplianceResult
    risk_scoring: RiskScoringResult
    final_decision: Decision
    final_reasoning: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Config for serialization."""
        arbitrary_types_allowed = True


class DatabaseAnalysis(BaseModel):
    """Analysis result as stored in database."""

    id: Optional[int] = None
    change_request_id: Optional[int] = None
    short_description: str
    long_description: str
    change_type: str
    change_category: str
    impacted_services: str
    complexity: str
    final_decision: str
    risk_score: int
    confidence: int
    reasoning: str
    risk_factors: str  # JSON string
    recommendations: str  # JSON string
    compliance_issues: str  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Config."""
        arbitrary_types_allowed = True


class AnalyticsData(BaseModel):
    """Analytics aggregation data."""

    total_analyzed: int = 0
    total_approved: int = 0
    total_reviewed: int = 0
    total_rejected: int = 0
    approval_rate: float = 0.0
    average_risk_score: float = 0.0
    average_confidence: float = 0.0
    analysis_by_category: dict = Field(default_factory=dict)
    analysis_by_complexity: dict = Field(default_factory=dict)
    analysis_by_decision: dict = Field(default_factory=dict)
    risk_distribution: dict = Field(default_factory=dict)  # Score ranges


class BulkAnalysisRequest(BaseModel):
    """Request for bulk analysis processing."""

    file_path: str
    total_rows: int


class BulkAnalysisProgress(BaseModel):
    """Progress tracking for bulk analysis."""

    total: int
    processed: int
    successful: int
    failed: int
    progress_percent: float

    @property
    def remaining(self) -> int:
        """Calculate remaining items."""
        return self.total - self.processed


class ParseError(BaseModel):
    """Error during Excel parsing."""

    row_number: int
    column: str
    error: str
    value: Optional[str] = None
