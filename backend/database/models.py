from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from backend.database.connection import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_url = Column(Text, nullable=False)
    repo_owner = Column(Text)
    repo_name = Column(Text)
    default_branch = Column(Text)
    commit_sha = Column(Text)
    status = Column(Text, nullable=False, default="queued")
    message = Column(Text)
    language_stats = Column(JSON)
    loc_total = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    metrics = Column(JSON)
    architecture_md = Column(Text)
    mermaid_modules = Column(Text)
    mermaid_folders = Column(Text)
    token_budget = Column(JSON, default={"embed_calls": 0, "gen_calls": 0, "chunks": 0})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    files = relationship("File", back_populates="analysis", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    path = Column(Text, nullable=False)
    language = Column(Text)
    loc = Column(Integer, default=0)
    fan_in = Column(Integer, default=0)
    fan_out = Column(Integer, default=0)
    centrality = Column(Float, default=0.0)
    hash = Column(Text)
    snippet = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analysis = relationship("Analysis", back_populates="files")

class Example(Base):
    __tablename__ = "examples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_url = Column(Text, nullable=False, unique=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"))
    label = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analysis = relationship("Analysis") 