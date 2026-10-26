"""
SQLAlchemy ORM Models for Agent Forge Persistence.
Authoritative persistent stores replacing ephemeral in-memory dictionaries.
"""

from datetime import datetime, timezone
import json
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.memory.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class TaskRecordORM(Base):
    """SQLAlchemy ORM model for persistent user tasks."""

    __tablename__ = "tasks"

    task_id = Column(String(64), primary_key=True, index=True)
    user_prompt = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="architecture_ready")
    run_number = Column(Integer, nullable=False, default=1)
    task_spec_json = Column(Text, nullable=False)
    latest_architecture_id = Column(String(64), nullable=True)
    latest_execution_id = Column(String(64), nullable=True)
    latest_evaluation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)


class ArchitectureRecordORM(Base):
    """SQLAlchemy ORM model for architecture versions (V1, V2, etc.)."""

    __tablename__ = "architectures"

    architecture_id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), index=True, nullable=False)
    version = Column(String(16), nullable=False, default="v1")
    parent_architecture_id = Column(String(64), nullable=True)
    topology = Column(String(32), nullable=False, default="pipeline")
    agent_count = Column(Integer, nullable=False, default=1)
    architecture_spec_json = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utc_now)


class ExecutionRecordORM(Base):
    """SQLAlchemy ORM model for agent execution runs and traces."""

    __tablename__ = "executions"

    execution_id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), index=True, nullable=False)
    architecture_id = Column(String(64), index=True, nullable=False)
    run_number = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="completed")
    duration_seconds = Column(Float, nullable=False, default=0.0)
    execution_result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utc_now)


class EvaluationRecordORM(Base):
    """SQLAlchemy ORM model for evaluations and reflections."""

    __tablename__ = "evaluations"

    evaluation_id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), index=True, nullable=False)
    execution_id = Column(String(64), index=True, nullable=False)
    architecture_id = Column(String(64), index=True, nullable=False)
    run_number = Column(Integer, nullable=False, default=1)
    success_rating = Column(Float, nullable=False, default=0.0)
    evaluation_result_json = Column(Text, nullable=False)
    reflection_result_json = Column(Text, nullable=False)
    memory_record_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)


class EvolutionDecisionORM(Base):
    """SQLAlchemy ORM model for deterministic evolution decisions."""

    __tablename__ = "evolution_decisions"

    decision_id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), index=True, nullable=False)
    v1_architecture_id = Column(String(64), nullable=False)
    v2_architecture_id = Column(String(64), nullable=False)
    v1_execution_id = Column(String(64), nullable=True)
    v2_execution_id = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False)  # ACCEPTED, REJECTED, INCONCLUSIVE
    score_delta = Column(Float, nullable=False, default=0.0)
    decision_json = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utc_now)


class ExecutionEventORM(Base):
    """SQLAlchemy ORM model for real-time and historical execution lifecycle events."""

    __tablename__ = "execution_events"

    event_id = Column(String(64), primary_key=True, index=True)
    execution_id = Column(String(64), index=True, nullable=False)
    task_id = Column(String(64), index=True, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    event_type = Column(String(64), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=_utc_now)
    status = Column(String(32), nullable=False, default="running")
    agent_id = Column(String(64), nullable=True)
    stage = Column(String(64), nullable=False, default="agent_execution")
    message = Column(Text, nullable=False)
    data_json = Column(Text, nullable=False, default="{}")
    error = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_exec_events_seq", "execution_id", "sequence_number", unique=True),
    )


class PlatformSettingsORM(Base):
    """SQLAlchemy ORM model for persisting platform-wide settings (policies, model matrix, tool states)."""

    __tablename__ = "platform_settings"

    key = Column(String(64), primary_key=True, index=True)
    value_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)


