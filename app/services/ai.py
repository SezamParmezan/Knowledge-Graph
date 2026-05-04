from google import genai
import json
#
from ..core.config import settings


class AIService:
    def __init__(self):
        #Set API key
        self.client = genai.Client(api_key=settings.ai_api_key)
        #Initialize model
        self.model = "gemini-1.5-flash"

    
    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        return json.loads(text)


    async def build_graph(self, text: str, language: str, depth: int, source_type: str, temperature: float = 0.2) -> dict:
        '''So, the user_input is the string, it can be single scientific term or URL link
        The depth is the number of layers of the graph, for example, if depth is 2, then we will get the direct connections of the user_input and then get the connections of those connections.
        The max_pairs is the maximum number of neigbors of each node
        '''

        if source_type == "url":
            prompt = f'''This is the text of the article: {text}. 
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
        return self._parse_json(response.text)