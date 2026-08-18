"""
Base Agent Interface & Runtime Primitive (Owned by Member 2).
"""

from typing import Dict, Any, List
from app.schemas.architecture import AgentConfigSchema


class BaseAgent:
    """Base runtime wrapper for dynamic agents."""

    def __init__(self, config: AgentConfigSchema):
        self.config = config

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("BaseAgent implementation belongs to Member 2 feature branch.")
