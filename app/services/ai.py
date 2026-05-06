import json
#
from ..core.config import settings

from loguru import logger
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential


class AIService:
    def __init__(self):
        #Set API key
        self.client = genai.Client(api_key=settings.ai_api_key)
        #Initialize model
        self.model = settings.ai_api_model

    
    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        return json.loads(text)


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=5, max=30),
        reraise=True,
    )
    async def build_graph(self, text: str, language: str, depth: int, source_type: str, temperature: float = 0.2) -> dict:
        '''So, the user_input is the string, it can be single scientific term or URL link
        The depth is the number of layers of the graph, for example, if depth is 2, then we will get the direct connections of the user_input and then get the connections of those connections.
        The max_pairs is the maximum number of neigbors of each node
        '''

        logger.info(f"Building graph with AI | source_type={source_type} | language={language} | depth={depth} | temperature={temperature}")

        if source_type == "url":
            prompt = f'''This is the text of the article: {text}. 
            Answer in this language: {language}.
            Build an interactive knowledge graph based on the content of this article. 
            The graph should have {depth} layers of connections. 
            Mark important nodes such as core concepts, formulas, translations, facts, etc. 
            You can add additional information that it is closely related to the content and may be interesting for user with no more than {temperature * 100:.0f}% off main topic.
            Add key features as "notes" aside the graph. 
            The graph should be in JSON format with "nodes" and "edges". 
            Be informative, accurate, but convey information in interesting way with examples where it is possible for marked nodes.
            Return ONLY valid JSON, no markdown, no explanations, strictly this structure:
            {{
            "topic": "...",
            "nodes": [{{"id": "...", "label": "...", "definition": "...", "importance": "core|major|minor", "examples": [], "notes": [], "tags": []}}],
            "edges": [{{"source": "...", "target": "...", "relation": "...", "weight": 0.8}}]
            }}'''

        else:
            prompt = f'''This is the term {text}. 
            Answer in this language: {language}.
            Build an interactive knowledge graph based on the content of this term and closely related concepts with no more than {temperature * 100:.0f}% off main topic. 
            The graph should have {depth} layers of connections. 
            Mark important nodes such as core concepts, formulas, translations, facts, etc. 
            Add key features as "notes" aside the graph. 
            The graph should be in JSON format with "nodes" and "edges". 
            Be informative, accurate, but convey information in interesting way with examples where it is possible for marked nodes.
            Return ONLY valid JSON, no markdown, no explanations, strictly this structure:
            {{
            "topic": "...",
            "nodes": [{{"id": "...", "label": "...", "definition": "...", "importance": "core|major|minor", "examples": [], "notes": [], "tags": []}}],
            "edges": [{{"source": "...", "target": "...", "relation": "...", "weight": 0.8}}]
            }}'''

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        logger.info(f"Graph built successfully with AI | source_type={source_type} | language={language} | depth={depth}")
        return self._parse_json(response.text) #type: ignore
    

    async def expand_node(self, topic: str, node_id: str, label: str, definition: str) -> dict:
        logger.info(f"Expanding node | topic={topic} | node_id={node_id} | label={label}")
        prompt = f'''Expand the node "{label}" in the knowledge graph about "{topic}".
        Node definition: {definition}
        
        Generate new child nodes and edges that go deeper into this concept.
        Return ONLY valid JSON, no markdown, no explanations, strictly this structure:
        {{
            "new_nodes": [{{"id": "...", "label": "...", "definition": "...", "importance": "major|minor", "examples": [], "notes": [], "tags": []}}],
            "new_edges": [{{"source": "{node_id}", "target": "...", "relation": "...", "weight": 0.7}}]
        }}'''

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        logger.info(f"Node expanded successfully | topic={topic} | node_id={node_id} | label={label}")
        return self._parse_json(response.text) #type: ignore
    

    async def answer(
        self,
        topic: str,
        question: str,
        rag_context: str = "",
        node_label: str = "",
        node_definition: str = "",
    ) -> str:
        node_context = ""
        if node_label:
            node_context = f'Context node: "{node_label}" — {node_definition}'

        prompt = f'''You are an assistant on the topic "{topic}".
        {node_context}
        Additional context: {rag_context or "none"}
        
        Question: {question}
        
        Answer clearly and to the point. Use examples where appropriate.'''

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return response.text #type: ignore