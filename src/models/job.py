import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import String, Text, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from core.client import Base

class JobStatus(str, PyEnum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    nice_to_have: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_required: Mapped[str | None] = mapped_column(Text, nullable=True)
    education: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj]
        ),
        default=JobStatus.DRAFT,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
