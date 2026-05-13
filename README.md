<div align="center">

# 🕸️ Knowledge Graph

**Turn any term or article into an interactive knowledge graph**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq_API-LLaMA_3.3-F55036?style=flat-square)](https://console.groq.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG-orange?style=flat-square)](https://www.trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

*A personal pet project — built to learn, explore, and break things.*

[Features](#features) · [Stack](#stack) · [Getting Started](#getting-started) · [Usage](#usage) · [Known Issues](#known-issues)

---

![Knowledge Graph Demo](https://raw.githubusercontent.com/SezamParmezan/Knowledge-Graph/main/static/img/demo.png)

</div>

---

## What is this?

You type a term like **"Gradient Descent"** or paste a link to an article — and the app builds a **visual, interactive knowledge graph** out of it. Nodes are concepts, edges are relationships. You can click any node to expand it deeper, read definitions and examples, and ask questions about it in a built-in chat.

Built as a pet project to learn FastAPI, RAG pipelines, and graph visualization. Still rough around the edges, but functional.

---

## Features

- **Term → Graph** — enter any scientific or technical term, get a full knowledge graph in seconds
- **URL → Graph** — paste an article URL, the app scrapes and analyzes it (Wikipedia, arXiv, blogs)
- **Expandable nodes** — click any node to drill deeper into that concept
- **Built-in chat** — ask questions in the context of a selected node, powered by RAG
- **RAG pipeline** — article content is chunked and indexed in ChromaDB for accurate answers
- **SSE streaming** — real-time progress updates while the graph is being built
- **Depth control** — choose between overview (1), detailed (2), and deep dive (3)
- **Multilingual** — English and Russian supported

---

## Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, Uvicorn |
| **AI / LLM** | Groq API (`llama-3.3-70b-versatile`) |
| **Vector DB** | ChromaDB |
| **RAG** | Custom chunking + ChromaDB retrieval |
| **Scraping** | trafilatura, httpx, BeautifulSoup, Playwright |
| **Graph** | D3.js force-directed graph |
| **Frontend** | Jinja2 templates, Tailwind CSS, vanilla JS |
| **Caching** | DiskCache |
| **Logging** | Loguru |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js (for Tailwind CSS compilation)
- A free [Groq API key](https://console.groq.com)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/SezamParmezan/Knowledge-Graph.git
cd Knowledge-Graph

# 2. Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser (for JS-heavy sites)
playwright install chromium

# 5. Install Node dependencies and build CSS
npm install
npm run build
```

### Configuration

```bash
cp .env.example .env
```

Open `.env` and set your API key:

```env
AI_API_KEY=your_groq_api_key_here
AI_API_MODEL=llama-3.3-70b-versatile
```

Get your free Groq key at [console.groq.com](https://console.groq.com) — no credit card required.

### Run

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

---

## Usage

1. **Enter a term** like `Transformer architecture` or `Quantum entanglement`
2. **Or paste a URL** to any article (Wikipedia, arXiv, blogs)
3. **Choose depth** — 1 for a quick overview, 3 for a deep dive
4. **Click Build** — watch the graph appear in real time via SSE
5. **Click any node** to see its definition, examples, and notes
6. **Expand** a node to generate deeper child concepts
7. **Ask** anything in the chat panel — answers are grounded in the source content

---

## Project Structure

```
app/
├── api/               # FastAPI route handlers
│   ├── graph.py       # POST /api/graph/build, GET /api/graph/{id}
│   ├── nodes.py       # GET/POST node endpoints
│   └── chat.py        # POST /api/chat
├── core/              # Config, exceptions, logging, DI
├── schemas/           # Pydantic request/response models
├── services/          # Business logic
│   ├── ai.py          # Groq API, prompt engineering
│   ├── scraper.py     # URL → text (trafilatura + Playwright fallback)
│   ├── rag.py         # ChromaDB indexing and retrieval
│   └── graph_builder.py # Graph assembly and session management
templates/             # Jinja2 HTML templates
static/                # CSS (Tailwind) + JS (D3.js)
```

---

## Known Issues

This is an early version and has several rough edges:

- **Graph quality varies** — depends heavily on the LLM response. The free Groq tier with `llama-3.3-70b-versatile` at low temperature (0.2) produces decent but not perfect graphs. Some nodes may be vague or edges nonsensical
- **Sessions are in-memory** — restart the server and all graphs are gone. No persistence yet
- **URL scraping is unreliable** — some sites block bots or use heavy JavaScript. Playwright helps but isn't perfect
- **No auth** — single-user local app, not designed for multi-user deployment
- **Rate limits** — free Groq tier has daily limits, you may hit them with heavy use

---

## Roadmap

- [ ] SQLite session persistence
- [ ] Better prompt engineering for higher graph quality
- [ ] Export graph as PNG / JSON
- [ ] Dark mode toggle
- [ ] Support more languages

---

## License

MIT — do whatever you want with it.

---

<div align="center">

Built with 🧠 and too much coffee · [@SezamParmezan](https://github.com/SezamParmezan)

</div>