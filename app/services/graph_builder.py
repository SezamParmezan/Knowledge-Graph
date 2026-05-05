import uuid
#
from loguru import logger
from .ai import AIService
from ..schemas.graph import GraphResponse, NodeSchema, EdgeSchema
from app.core.exceptions import SessionNotFoundError, NodeNotFoundError


class GraphBuilder:
    '''Class to build the graph with ai.py'''

    def __init__(self, ai_service: AIService):
        self.ai = ai_service
        self.sessions: dict[str, dict] = {} #session_id - graph nodes


    def _build_nodes(self, graph: dict) -> list[NodeSchema]:
        nodes_data = graph.get("nodes", [])
        return [NodeSchema(**node) for node in nodes_data]
    

    def _build_edges(self, graph: dict) -> list[EdgeSchema]:
        edges_data = graph.get("edges", [])
        return [EdgeSchema(**edge) for edge in edges_data]

    
    async def build(self, text, language, depth, source_type) -> GraphResponse:
        session_id = str(uuid.uuid4())
        logger.info(f"Building graph for session {session_id} with text: {text}, language: {language}, depth: {depth}, source_type: {source_type}")
        graph = await self.ai.build_graph(text, language, depth, source_type)
        self.sessions[session_id] = graph
        return GraphResponse(session_id=session_id, topic = graph.get("topic", text[:80]), nodes = self._build_nodes(graph), edges = self._build_edges(graph), meta = {"source_type": source_type})
    

    def get_session(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            raise SessionNotFoundError(session_id)
        return self.sessions.get(session_id, {})
    

    def get_node(self, session_id: str, node_id: str) -> dict:
        graph = self.get_session(session_id)
        nodes = graph.get("nodes", [])
        for node in nodes:
            if node["id"] == node_id:
                return node
        raise NodeNotFoundError(node_id)
    

    async def expand_node(self, session_id, node_id: str) -> dict:
        node = self.get_node(session_id, node_id)
        graph = self.get_session(session_id)
        
        result = await self.ai.expand_node(
            topic=graph["topic"],
            node_id=node_id,
            label=node["label"],
            definition=node["definition"],
        )

        graph["nodes"].extend(result.get("new_nodes", []))
        graph["edges"].extend(result.get("new_edges", []))

        return result