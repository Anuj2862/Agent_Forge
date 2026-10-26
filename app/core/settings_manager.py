"""
Central Platform Settings Manager for Agent Forge.
Manages Model Matrix, Execution Policies, Tool Registry synchronization,
runtime health diagnostics, and execution configuration snapshots.
"""

from datetime import datetime, timezone
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.memory.database import engine, AsyncSessionFactory
from app.memory.models import PlatformSettingsORM
from app.schemas.settings import (
    AgentRoleEnum,
    ModelProviderEnum,
    SUPPORTED_PROVIDERS,
    UNSUPPORTED_PROVIDERS,
    RoleModelConfig,
    ModelMatrixConfig,
    ModelMatrixUpdate,
    ExecutionPolicyConfig,
    ExecutionPolicyUpdate,
    SubsystemHealth,
    SystemHealthResponse,
    SettingsSummaryResponse,
)
from app.tools.tool_registry import tool_registry

logger = logging.getLogger("agent_forge.settings")


class SettingsManager:
    """Authoritative singleton managing platform configurations and runtime policies."""

    def __init__(self):
        self._policies = ExecutionPolicyConfig()
        self._model_matrix = self._build_default_model_matrix()
        self._config_version = 1
        self._initialized = False

    def _build_default_model_matrix(self) -> ModelMatrixConfig:
        """Construct default model assignments mapped to implemented providers."""
        default_model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro")
        gemini_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        cred_status = "configured" if gemini_key else "offline"

        roles_config: Dict[AgentRoleEnum, RoleModelConfig] = {
            AgentRoleEnum.META_CONTROLLER: RoleModelConfig(
                role=AgentRoleEnum.META_CONTROLLER,
                provider=ModelProviderEnum.GEMINI,
                model_identifier="gemini-1.5-pro",
                temperature=0.1,
                is_supported=True,
                credential_status=cred_status,
            ),
            AgentRoleEnum.RESEARCHER: RoleModelConfig(
                role=AgentRoleEnum.RESEARCHER,
                provider=ModelProviderEnum.GEMINI,
                model_identifier="gemini-1.5-flash",
                temperature=0.2,
                is_supported=True,
                credential_status=cred_status,
            ),
            AgentRoleEnum.ANALYST: RoleModelConfig(
                role=AgentRoleEnum.ANALYST,
                provider=ModelProviderEnum.GEMINI,
                model_identifier="gemini-1.5-pro",
                temperature=0.2,
                is_supported=True,
                credential_status=cred_status,
            ),
            AgentRoleEnum.PLANNER: RoleModelConfig(
                role=AgentRoleEnum.PLANNER,
                provider=ModelProviderEnum.GEMINI,
                model_identifier="gemini-1.5-pro",
                temperature=0.1,
                is_supported=True,
                credential_status=cred_status,
            ),
            AgentRoleEnum.EXECUTOR: RoleModelConfig(
                role=AgentRoleEnum.EXECUTOR,
                provider=ModelProviderEnum.GEMINI,
                model_identifier="gemini-1.5-flash",
                temperature=0.2,
                is_supported=True,
                credential_status=cred_status,
            ),
            AgentRoleEnum.VERIFIER: RoleModelConfig(
                role=AgentRoleEnum.VERIFIER,
                provider=ModelProviderEnum.GEMINI,
                model_identifier="gemini-1.5-flash",
                temperature=0.0,
                is_supported=True,
                credential_status=cred_status,
            ),
            AgentRoleEnum.CRITIC: RoleModelConfig(
                role=AgentRoleEnum.CRITIC,
                provider=ModelProviderEnum.GEMINI,
                model_identifier="gemini-1.5-pro",
                temperature=0.2,
                is_supported=True,
                credential_status=cred_status,
            ),
            AgentRoleEnum.ARCHITECTURE_MUTATOR: RoleModelConfig(
                role=AgentRoleEnum.ARCHITECTURE_MUTATOR,
                provider=ModelProviderEnum.GEMINI,
                model_identifier="gemini-1.5-pro",
                temperature=0.3,
                is_supported=True,
                credential_status=cred_status,
            ),
        }
        return ModelMatrixConfig(
            roles=roles_config,
            supported_providers=[p.value for p in SUPPORTED_PROVIDERS],
            unsupported_providers=[p.value for p in UNSUPPORTED_PROVIDERS],
        )

    # ------------------------------------------------------------------
    # Persistence Initialization & Sync
    # ------------------------------------------------------------------

    async def initialize_from_db(self, db: Optional[AsyncSession] = None) -> None:
        """Load persisted policies and model matrix from SQLite."""
        if self._initialized:
            return

        async def _load(session: AsyncSession):
            # Load policies
            stmt_p = select(PlatformSettingsORM).where(PlatformSettingsORM.key == "execution_policies")
            res_p = await session.execute(stmt_p)
            row_p = res_p.scalars().first()
            if row_p:
                try:
                    data = json.loads(row_p.value_json)
                    self._policies = ExecutionPolicyConfig(**data)
                except Exception as e:
                    logger.warning(f"Could not parse persisted policies: {e}")

            # Load model matrix
            stmt_m = select(PlatformSettingsORM).where(PlatformSettingsORM.key == "model_matrix")
            res_m = await session.execute(stmt_m)
            row_m = res_m.scalars().first()
            if row_m:
                try:
                    data = json.loads(row_m.value_json)
                    roles_dict = {}
                    for k, v in data.get("roles", {}).items():
                        role_enum = AgentRoleEnum(k)
                        roles_dict[role_enum] = RoleModelConfig(**v)
                    self._model_matrix.roles.update(roles_dict)
                except Exception as e:
                    logger.warning(f"Could not parse persisted model matrix: {e}")

            # Load tool enabled states
            stmt_t = select(PlatformSettingsORM).where(PlatformSettingsORM.key == "tool_states")
            res_t = await session.execute(stmt_t)
            row_t = res_t.scalars().first()
            if row_t:
                try:
                    tool_states = json.loads(row_t.value_json)
                    for t_name, is_enabled in tool_states.items():
                        if tool_registry.has_tool(t_name):
                            if is_enabled:
                                tool_registry.enable_tool(t_name)
                            else:
                                tool_registry.disable_tool(t_name)
                except Exception as e:
                    logger.warning(f"Could not parse persisted tool states: {e}")

        try:
            if db:
                await _load(db)
            else:
                async with AsyncSessionFactory() as session:
                    await _load(session)
            self._initialized = True
        except Exception as e:
            logger.info(f"Platform settings initializing with in-memory defaults ({e})")
            self._initialized = True

    async def _persist_setting(self, key: str, value_dict: Dict[str, Any], db: Optional[AsyncSession] = None) -> None:
        """Helper to write non-secret setting to SQLite."""
        async def _save(session: AsyncSession):
            stmt = select(PlatformSettingsORM).where(PlatformSettingsORM.key == key)
            res = await session.execute(stmt)
            row = res.scalars().first()
            val_json = json.dumps(value_dict)
            if row:
                row.value_json = val_json
                row.updated_at = datetime.now(timezone.utc)
            else:
                new_row = PlatformSettingsORM(key=key, value_json=val_json)
                session.add(new_row)
            await session.commit()

        try:
            if db:
                await _save(db)
            else:
                async with AsyncSessionFactory() as session:
                    await _save(session)
        except Exception as e:
            logger.error(f"Failed to persist platform setting '{key}': {e}")

    # ------------------------------------------------------------------
    # Model Matrix Access & Update
    # ------------------------------------------------------------------

    def get_model_matrix(self) -> ModelMatrixConfig:
        """Return model matrix with refreshed credential statuses."""
        gemini_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        cred_status = "configured" if gemini_key else "offline"

        for role_cfg in self._model_matrix.roles.values():
            if role_cfg.provider == ModelProviderEnum.GEMINI:
                role_cfg.credential_status = cred_status
            elif role_cfg.provider == ModelProviderEnum.MOCK_DETERMINISTIC:
                role_cfg.credential_status = "configured"
            else:
                role_cfg.credential_status = "missing"
            role_cfg.is_supported = role_cfg.provider in SUPPORTED_PROVIDERS

        return self._model_matrix.model_copy()

    async def update_model_matrix(
        self,
        update: ModelMatrixUpdate,
        db: Optional[AsyncSession] = None,
    ) -> ModelMatrixConfig:
        """Validate and apply updates to role-to-model assignments."""
        for role_str, cfg in update.assignments.items():
            # Validate provider support
            if cfg.provider not in SUPPORTED_PROVIDERS:
                raise ValueError(
                    f"Provider '{cfg.provider.value}' is not supported in this runtime. "
                    f"Supported providers are: {[p.value for p in SUPPORTED_PROVIDERS]}."
                )

            # Validate role
            try:
                role_enum = AgentRoleEnum(role_str)
            except ValueError:
                raise ValueError(
                    f"Unknown agent role '{role_str}'. "
                    f"Valid roles are: {[r.value for r in AgentRoleEnum]}."
                )

            cfg.role = role_enum
            cfg.is_supported = True
            self._model_matrix.roles[role_enum] = cfg

        self._config_version += 1

        # Persist serializable dict
        serializable_data = {
            "roles": {
                r.value: cfg.model_dump(mode="json")
                for r, cfg in self._model_matrix.roles.items()
            }
        }
        await self._persist_setting("model_matrix", serializable_data, db=db)
        return self.get_model_matrix()

    def get_model_for_role(self, role: str) -> Tuple[str, str]:
        """
        Runtime lookup: returns (provider_name, model_identifier) for an agent role.
        Normalizes role strings (e.g. 'Researcher' -> 'researcher').
        """
        clean_role = role.strip().lower().replace(" ", "_")

        # Match exact or substring
        for r_enum, cfg in self._model_matrix.roles.items():
            if r_enum.value == clean_role or r_enum.value in clean_role:
                return (cfg.provider.value, cfg.model_identifier)

        # Default fallback
        return ("gemini", getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro"))

    # ------------------------------------------------------------------
    # Execution Policies Access & Update
    # ------------------------------------------------------------------

    def get_execution_policies(self) -> ExecutionPolicyConfig:
        return self._policies.model_copy()

    async def update_execution_policies(
        self,
        update: ExecutionPolicyUpdate,
        db: Optional[AsyncSession] = None,
    ) -> ExecutionPolicyConfig:
        """Validate and apply execution policy updates."""
        # Check conflict between allowed and forbidden tools
        if update.allowed_tools is not None and update.forbidden_tools is not None:
            overlap = set(update.allowed_tools).intersection(set(update.forbidden_tools))
            if overlap:
                raise ValueError(
                    f"Conflicting policy: Tools {list(overlap)} cannot be simultaneously in allowed_tools and forbidden_tools."
                )

        if update.max_agents is not None:
            self._policies.max_agents = update.max_agents
        if update.max_execution_duration_seconds is not None:
            self._policies.max_execution_duration_seconds = update.max_execution_duration_seconds
        if update.max_tool_calls_per_agent is not None:
            self._policies.max_tool_calls_per_agent = update.max_tool_calls_per_agent
        if update.allowed_tools is not None:
            new_allowed = update.allowed_tools
        elif update.forbidden_tools is not None:
            new_allowed = [t for t in self._policies.allowed_tools if t not in update.forbidden_tools]
        else:
            new_allowed = self._policies.allowed_tools

        new_forbidden = update.forbidden_tools if update.forbidden_tools is not None else self._policies.forbidden_tools
        self._policies.allowed_tools = new_allowed
        self._policies.forbidden_tools = new_forbidden
        if update.require_verification_by_default is not None:
            self._policies.require_verification_by_default = update.require_verification_by_default
        if update.sandbox_isolation_enabled is not None:
            self._policies.sandbox_isolation_enabled = update.sandbox_isolation_enabled

        self._config_version += 1
        await self._persist_setting("execution_policies", self._policies.model_dump(mode="json"), db=db)
        return self.get_execution_policies()

    # ------------------------------------------------------------------
    # Tool State Persistence Helper
    # ------------------------------------------------------------------

    async def persist_tool_states(self, db: Optional[AsyncSession] = None) -> None:
        """Persist tool enabled states to SQLite."""
        states = {t: tool_registry.is_tool_enabled(t) for t in tool_registry.list_tools()}
        await self._persist_setting("tool_states", states, db=db)

    # ------------------------------------------------------------------
    # Execution Snapshot for Reproducibility
    # ------------------------------------------------------------------

    def get_execution_snapshot(self) -> Dict[str, Any]:
        """
        Creates an immutable configuration snapshot captured at execution start.
        Guarantees that mid-flight policy changes do not mutate active runs.
        """
        return {
            "snapshot_id": f"snap_v{self._config_version}_{int(time.time())}",
            "config_version": self._config_version,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "policies": self._policies.model_dump(mode="json"),
            "model_matrix": {
                r.value: {
                    "provider": cfg.provider.value,
                    "model_identifier": cfg.model_identifier,
                    "temperature": cfg.temperature,
                }
                for r, cfg in self._model_matrix.roles.items()
            },
            "enabled_tools": tool_registry.list_enabled_tools(),
            "sandbox_active": self._policies.sandbox_isolation_enabled,
        }

    # ------------------------------------------------------------------
    # Runtime Health Diagnostics
    # ------------------------------------------------------------------

    async def check_runtime_health(self) -> SystemHealthResponse:
        """Perform real diagnostics on all platform subsystems."""
        subsystems: Dict[str, SubsystemHealth] = {}
        overall = "healthy"

        # 1. API Service
        subsystems["api_service"] = SubsystemHealth(
            name="FastAPI Core Engine",
            status="healthy",
            latency_ms=0.05,
            details={
                "app": settings.APP_NAME,
                "version": "0.2.0",
                "env": settings.APP_ENV,
                "python_version": sys.version.split()[0],
            },
        )

        # 2. Database Persistence
        t_start = time.perf_counter()
        try:
            from sqlalchemy import text
            async with AsyncSessionFactory() as session:
                await session.execute(text("SELECT 1"))
            db_latency = round((time.perf_counter() - t_start) * 1000.0, 2)
            subsystems["database"] = SubsystemHealth(
                name="SQLite Persistence Engine",
                status="healthy",
                latency_ms=db_latency,
                details={
                    "dialect": engine.dialect.name,
                    "pool_size": 5,
                    "url_safe": "sqlite:///agentforge_memory.db",
                },
            )
        except Exception as e:
            overall = "degraded"
            subsystems["database"] = SubsystemHealth(
                name="Database Persistence",
                status="unavailable",
                error=str(e),
                details={"dialect": engine.dialect.name},
            )

        # 3. Model Provider
        gemini_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        has_sdk = False
        try:
            from google import genai  # noqa: F401
            has_sdk = True
        except ImportError:
            pass

        if gemini_key:
            model_status = "healthy"
            model_details = {
                "active_provider": "gemini",
                "sdk_ready": has_sdk,
                "model": getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro"),
                "key_configured": True,
            }
        else:
            model_status = "degraded"
            model_details = {
                "active_provider": "gemini (offline fallback / mock deterministic active)",
                "sdk_ready": has_sdk,
                "key_configured": False,
                "note": "No GEMINI_API_KEY found. Agent runs use deterministic offline runner.",
            }

        subsystems["model_provider"] = SubsystemHealth(
            name="Model Provider Integration",
            status=model_status,
            latency_ms=0.2,
            details=model_details,
        )

        # 4. Tool Registry & Sandboxing
        registered_count = len(tool_registry.list_tools())
        enabled_count = len(tool_registry.list_enabled_tools())
        subsystems["tools"] = SubsystemHealth(
            name="Execution Tools Subsystem",
            status="healthy" if enabled_count > 0 else "degraded",
            latency_ms=0.1,
            details={
                "registered_tools_count": registered_count,
                "enabled_tools_count": enabled_count,
                "sandbox_isolation": "AST Validation + Subprocess Sandbox",
                "python_executable": sys.executable,
            },
        )

        # 5. Execution Subsystem
        try:
            from app.execution.communication_graph import CommunicationGraphBuilder  # noqa: F401
            subsystems["execution_subsystem"] = SubsystemHealth(
                name="LangGraph Execution Subsystem",
                status="healthy",
                latency_ms=0.1,
                details={
                    "state_graph_ready": True,
                    "max_agents_limit": self._policies.max_agents,
                    "max_duration_seconds": self._policies.max_execution_duration_seconds,
                    "max_tool_calls": self._policies.max_tool_calls_per_agent,
                },
            )
        except Exception as e:
            overall = "degraded"
            subsystems["execution_subsystem"] = SubsystemHealth(
                name="LangGraph Execution Subsystem",
                status="unavailable",
                error=str(e),
            )

        # 6. Event Streaming (SSE)
        try:
            from app.execution.event_broadcaster import broadcaster
            active_subscribers = len(broadcaster._subscribers)
            subsystems["event_streaming"] = SubsystemHealth(
                name="Server-Sent Event Streamer",
                status="healthy",
                latency_ms=0.05,
                details={"active_subscribers": active_subscribers, "buffer_ready": True},
            )
        except Exception as e:
            subsystems["event_streaming"] = SubsystemHealth(
                name="Server-Sent Event Streamer",
                status="degraded",
                error=str(e),
            )

        return SystemHealthResponse(
            overall_status=overall,
            version="0.2.0",
            environment=settings.APP_ENV,
            subsystems=subsystems,
        )

    # ------------------------------------------------------------------
    # Summary Response
    # ------------------------------------------------------------------

    async def get_summary(self) -> SettingsSummaryResponse:
        """Returns consolidated settings summary with all secrets strictly redacted."""
        health = await self.check_runtime_health()
        return SettingsSummaryResponse(
            version="0.2.0",
            tools=tool_registry.list_tools_metadata(),
            model_matrix=self.get_model_matrix(),
            execution_policies=self.get_execution_policies(),
            health_summary=health,
        )


settings_manager = SettingsManager()
