"""
Communication Graph Representation (Owned by Member 2).
Constructs LangGraph StateGraph nodes and edges from ArchitectureSpec.
"""

from app.schemas.architecture import ArchitectureSpec


class CommunicationGraphBuilder:
    """Builds an executable LangGraph topology graph."""

    def build_graph(self, architecture: ArchitectureSpec):
        raise NotImplementedError("CommunicationGraphBuilder belongs to Member 2 feature branch.")
