from sqlalchemy import Column, Integer, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
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
    status = Column(Text, nullable=False, default="pending")  # pending, started, completed, failed
    progress_status = Column(Text, nullable=True)  # Human-readable progress description
    message = Column(Text)
    language_stats = Column(JSON)
    loc_total = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    metrics = Column(JSON)
    components = Column(JSON, default=[])
    architecture_md = Column(Text)
    
    # Original diagrams
    mermaid_modules = Column(Text)
    mermaid_folders = Column(Text)
    
    # New intelligent dependency diagrams
    mermaid_modules_simple = Column(Text)
    mermaid_modules_balanced = Column(Text)
    mermaid_modules_detailed = Column(Text)
    
    token_budget = Column(JSON, default={"embed_calls": 0, "gen_calls": 0, "chunks": 0})
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()'))

class Example(Base):
    __tablename__ = "examples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True)  # Human readable name for dropdown
    repo_url = Column(Text, nullable=False)
    repo_owner = Column(Text)
    repo_name = Column(Text)
    default_branch = Column(Text)
    commit_sha = Column(Text)
    status = Column(Text, nullable=False, default="complete")
    message = Column(Text)
    language_stats = Column(JSON)
    loc_total = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    metrics = Column(JSON)
    components = Column(JSON, default=[])
    architecture_md = Column(Text)
    
    # Original diagrams
    mermaid_modules = Column(Text)
    mermaid_folders = Column(Text)
    
    # Intelligent dependency diagrams
    mermaid_modules_simple = Column(Text)
    mermaid_modules_balanced = Column(Text)
    mermaid_modules_detailed = Column(Text)
    
    token_budget = Column(JSON, default={"embed_calls": 0, "gen_calls": 0, "chunks": 0})
    description = Column(Text)  # Description for the example
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()')) 