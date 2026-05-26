from datetime import datetime
from uuid import uuid4
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.infrastructure.database import Base


class SchemaVersion(Base):
    """Tracks DB schema version to guard against stale databases."""
    __tablename__ = "schema_version"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    file_name: Mapped[str] = mapped_column(String, index=True)
    upload_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contract-level risk summary (computed after per-clause analysis)
    overall_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overall_risk_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    top_risk_drivers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of clause numbers

    clauses: Mapped[List["Clause"]] = relationship("Clause", back_populates="contract", cascade="all, delete-orphan")


class Clause(Base):
    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))

    # Core identification
    clause_index: Mapped[int] = mapped_column(Integer)
    clause_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)  # sha256 for dedup/audit

    # Hierarchical structure metadata
    article_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)   # e.g. "4"
    clause_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)    # e.g. "3.1.2", "a)"
    heading: Mapped[Optional[str]] = mapped_column(String, nullable=True)          # Heading text
    depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)           # 0=Article, 1=Clause, etc.
    parent_clause: Mapped[Optional[str]] = mapped_column(String, nullable=True)    # Parent clause_number

    # Source position for future highlighting
    start_char: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_char: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Content
    clause_text: Mapped[str] = mapped_column(Text)

    # Classification
    clause_type: Mapped[str] = mapped_column(String, index=True)
    confidence_score: Mapped[float] = mapped_column(Float)

    # Risk analysis
    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String, index=True)
    risk_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)   # Power Imbalance / Financial Exposure / etc.
    risky_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)     # Precise triggering phrase
    exposed_party: Mapped[Optional[str]] = mapped_column(String, nullable=True)   # Party bearing the risk

    # Enrichment
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rewrite: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contract: Mapped["Contract"] = relationship("Contract", back_populates="clauses")
