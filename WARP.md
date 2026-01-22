# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common commands

Setup (macOS/Linux):

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure the LLM provider (default is Ollama):
- Edit `llm_config.py` and set `LLM_TYPE` and provider settings.
- Ollama: ensure the model referenced by `model_name` is available and the server is running.

```sh
# start local Ollama server
ollama serve
```

Run the app:

```sh
python Web-LLM.py
```

Runtime usage (research mode):
- Start a research session by typing `@` followed by your topic, then press CTRL+D to submit on macOS/Linux.
- While research is running: `s` = status, `f` = current focus, `p` = pause and assess, `q` = quit and summarize.
- After summarization, conversation mode lets you ask follow‑ups about the collected research.

Helpful developer utilities:

```sh
# run scraper standalone smoke test
python web_scraper.py

# tail logs while debugging
mkdir -p logs && tail -f logs/web_llm.log logs/research_llm.log
```

Notes:
- No test suite or linter is configured in this repo. There are no `tests/` or tool configs present.
- Generated research transcripts are written to `research_session_*.txt` in the project root.

## High‑level architecture

The project is a terminal‑based automated web researcher orchestrated by a local or remote LLM. It repeatedly (1) plans focus areas, (2) formulates queries, (3) searches the web, (4) scrapes pages, and (5) aggregates findings into a session document before producing a final summary and entering a Q&A mode.

Key components and responsibilities:

- Entry point and CLI orchestration (`Web-LLM.py`)
  - Initializes logging, prints usage, and validates LLM connectivity using `llm_config.get_llm_config()`.
  - Constructs:
    - `LLMWrapper` (provider abstraction)
    - `UltimateLLMResponseParser` (response parsing)
    - `EnhancedSelfImprovingSearch` (query formulation, search, selection, scraping)
    - `ResearchManager` (research lifecycle and UI)
  - Main loop interprets input: `@` enters research mode. Research mode delegates to `ResearchManager` for a full‑screen curses UI and control commands (s/f/p/q). After termination it prints the summary and starts conversation mode for follow‑ups.

- LLM abstraction (`llm_wrapper.py`, `llm_config.py`)
  - Supports `ollama`, `openai`, `anthropic`, and `llama_cpp` via a single `generate()` API.
  - Ollama path uses the HTTP `/api/generate` streaming endpoint; OpenAI/Anthropic require API keys via env vars if selected.
  - `llm_config.py` holds per‑provider settings (model name, temperature, context window, etc.). Default `LLM_TYPE` is `"ollama"`.

- Parsing and analysis (`llm_response_parser.py`, `strategic_analysis_parser.py`)
  - `UltimateLLMResponseParser` normalizes LLM outputs (e.g., decisions, selections) and routes “research” responses to `StrategicAnalysisParser`.
  - `StrategicAnalysisParser` extracts prioritized research focus areas and assembles an `AnalysisResult` with metadata.

- Web search + selection + scraping (`Self_Improving_Search.py`, `web_scraper.py`)
  - `EnhancedSelfImprovingSearch` prompts the LLM to craft concise search queries and pick the top 2 relevant results from DuckDuckGo (with retry/backoff on rate limits).
  - Selected URLs are fetched via `web_scraper.WebScraper` (Requests + BeautifulSoup). Robots checks are currently disabled in `can_fetch()`; per‑domain rate limiting is applied. Page content is trimmed and normalized before returning.

- Research lifecycle and UI (`research_manager.py`)
  - Manages the end‑to‑end research loop: generate focus areas, formulate per‑area queries, search, scrape, and append findings to a session document (`research_session_N.txt`).
  - Tracks progress, current focus, and visited URLs; monitors document size vs configured context (`n_ctx`).
  - Provides a curses‑based `TerminalUI` with a fixed input area and status line; handles commands `s`, `f`, `p`, `q`.
  - On termination, it synthesizes a formatted summary using the accumulated findings, writes it to the session document, and starts a conversation mode that answers questions grounded in the research content.

## Important files
- `Web-LLM.py`: program entry, initializes subsystems, user interaction loop.
- `llm_config.py`: provider selection and hyperparameters (default: Ollama).
- `llm_wrapper.py`: provider‑agnostic LLM interface.
- `Self_Improving_Search.py`: query formulation, search, result selection, content synthesis.
- `web_scraper.py`: HTTP fetch + HTML parsing and cleanup utilities.
- `llm_response_parser.py`, `strategic_analysis_parser.py`: response/analysis parsing to structured data.
- `research_manager.py`: high‑level controller, curses UI, session document management, summarization, conversation mode.

Caveats:
- `Web-LLM.py` references a search (`/`) path, but no `handle_search_mode` implementation exists in the file; use `@` research mode as the supported flow.
