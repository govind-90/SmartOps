"""Database models and ORM configuration."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class ChangeRequestModel(Base):
    """ORM model for stored change requests."""

    __tablename__ = "change_requests"

    id = Column(Integer, primary_key=True, index=True)
    short_description = Column(String(200), nullable=False, index=True)
    long_description = Column(Text, nullable=False)
    change_type = Column(String(50), nullable=False, index=True)
    change_category = Column(String(50), nullable=False, index=True)
    implementation_steps = Column(Text, nullable=False)
    validation_steps = Column(Text, nullable=False)
    rollback_plan = Column(Text, nullable=False)
    planned_window = Column(String(50), nullable=False)
    impacted_services = Column(String(500), nullable=False)
    complexity = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    analyses = relationship("AnalysisModel", back_populates="change_request", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ChangeRequest {self.id}: {self.short_description[:50]}>"


class AnalysisModel(Base):
    """ORM model for analysis results."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    change_request_id = Column(Integer, ForeignKey("change_requests.id"), nullable=False, index=True)
    final_decision = Column(String(50), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False, index=True)
    confidence = Column(Integer, nullable=False)
    reasoning = Column(Text, nullable=False)
    risk_factors = Column(Text, nullable=False)  # JSON string
    red_flags = Column(Text, nullable=False)  # JSON string
    recommendations = Column(Text, nullable=False)  # JSON string
    compliance_compliant = Column(Integer, default=1)  # Boolean as integer
    compliance_score = Column(Integer, nullable=False)
    compliance_issues = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    change_request = relationship("ChangeRequestModel", back_populates="analyses")

    __table_args__ = (
        Index("idx_decision_created", "final_decision", "created_at"),
        Index("idx_risk_created", "risk_score", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Analysis {self.id}: {self.final_decision}>"


class Database:
    """Database connection and session management."""

    def __init__(self, database_url: str | None = None) -> None:
        """
        Initialize database connection.
        
        Args:
            database_url: SQLite connection URL. Defaults to settings.DATABASE_PATH
        """
        if database_url is None:
            database_url = f"sqlite:///{settings.DATABASE_PATH}"

        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        self._create_tables()
        logger.info("Database initialized")

    def _create_tables(self) -> None:
        """Create all tables if they don't exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()

    def close(self) -> None:
        """Close database connection."""
        self.engine.dispose()
        logger.info("Database connection closed")


# Global database instance
db = Database()
