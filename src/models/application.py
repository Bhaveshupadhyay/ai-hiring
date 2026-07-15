import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.client import Base

class ApplicationStatus(str, PyEnum):
    PENDING = "pending"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    INTERVIEWING = "interviewing"
    APPROVED = "approved"

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    ai_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hm_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(
            ApplicationStatus,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj]
        ),
        default=ApplicationStatus.PENDING,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    candidate = relationship("Candidate")
    job = relationship("Job")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
