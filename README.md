# Agentic Web Scraper And Automation (LangGraph + Playwright + Ollama + RAG)

A local-first agentic web automation project that scrapes a website, builds a small retrieval knowledge base (Chroma), plans actions using an Ollama chat model, and executes the plan with Playwright.
It is designed for simple tasks like navigating pages, filling forms, clicking buttons, and taking screenshots.

## Features

* Website scraping to collect page/form context
* RAG over scraped content using Chroma + local embeddings
* Action planning using a local LLM (Ollama)
* Playwright-based execution: navigate, fill, click, wait, screenshot
* Validation layer with heuristics (and optional LLM check)
* Logs + screenshots for debugging and proof

## Tech stack

* Python
* LangGraph (workflow orchestration)
* LangChain Ollama (LLM interface)
* Playwright (browser automation)
* ChromaDB (vector database)
* Sentence-Transformers / local embeddings (`all-MiniLM-L6-v2`)

## Project structure (typical)

* `src/main.py`: entry point
* `src/agent/`: LangGraph agent (planner / executor / validator / graph)
* `src/browser/`: Playwright adapter
* `src/scraper/`: website scraper
* `src/knowledge_base/`: embeddings + chroma store + retriever
* `requirements.txt`: dependencies
* `.env`: local secrets (do not commit)

## Setup

### 1) Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3) Install and run Ollama

Install Ollama:
[https://ollama.com/](https://ollama.com/)

Pull a model (example):

```bash
ollama pull llama3.2
```

## Configuration (`.env`)

Create a `.env` file in the project root **(never commit this file)**.

Example:

```ini
# Ollama
CHAT_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:

# Optional: LangSmith tracing (only if you use it)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=YOUR_LANGSMITH_KEY
LANGCHAIN_PROJECT=agentic-web-automation

# Optional: tuning
BROWSER_TIMEOUT=30000
MAX_RETRIES=2
```

**Notes:**

* If you do not use LangSmith, remove the `LANGCHAIN_*` variables or set tracing to false.

## Run

From the project root:

```bash
python -m src.main
```

## Using it on a new website

1. Change the `domain` and `task` in `src/main.py` (or wherever your entry point defines them).
2. Run once to scrape and rebuild the knowledge base for that domain.
3. Ensure the planner is dynamic (no hardcoded selectors) and the executor supports the actions produced by the planner.
4. For logins, ensure your task includes credentials clearly, for example:

   * *"Log in. Username is `user123`. Password is `pass123`. Then take a screenshot."*

**Important limitations:**

* CAPTCHA / Cloudflare checks are not supported.
* 2FA flows require extra handling (pause/wait for code entry).

