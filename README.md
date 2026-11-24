# Discourse Dissector

**CSC-5240 Agentic Project**  
Created by **Anthony Hardy** and **Johnathon Bryant**

Discourse Dissector is a desktop application that extracts arguable or factual statements from a news article URL, retrieves web sources supporting and opposing a selected statement, generates dual-stance arguments with source citations using local LLMs, runs a self-judgment check on each argument, and exports the results to LaTeX and PDF.

## Features

* **Article URL Validation & Extraction:** Validates `http`/`https` article links (rejecting YouTube links) and extracts main article text with `trafilatura`.
* **Schema-Constrained Statement Extraction:** Uses a local Ollama model (`llama3.2:3b` or `qwen2.5:3b`) with a `Pydantic` (`StatementList`) JSON schema to extract testable statements, followed by cleanup and sentence splitting.
* **Dual-Stance Search & Argumentation:** Queries `Tavily` with separate prompts to find supporting and opposing sources (1 to 3 resources), deduplicates URLs, filters candidate articles by keywords, and generates separate **FOR** and **AGAINST** arguments with `[Source x: link]` citations.
* **Self-Judgment:** Runs a follow-up check (`JudgeIfStatementSensical`) on the generated FOR and AGAINST arguments and appends the judgment to the results.
* **Responsive Desktop GUI:** Built with `tkinter` and `ttk` using background daemon threads and a `queue.Queue` so scraping and model calls do not freeze the interface.
* **LaTeX & PDF Export:** Escapes special LaTeX characters, writes a `.tex` report, and compiles a `.pdf` via `pdflatex` if installed on the system.

## Prerequisites

* **Python 3.10+**
* **Ollama** running locally on `http://localhost:11434` with your chosen model(s) pulled (e.g., `llama3.2:3b`, `qwen2.5:3b`)
* **Tavily API Key** (`TAVILY_API_KEY`)
* **LaTeX distribution (`pdflatex`)** *(optional)* — required if you want automatic `.pdf` compilation in addition to `.tex` export

## Installation

1. Clone or download the project files.
2. Install the required Python packages:
   ```bash
   pip install requests trafilatura pydantic instructor ollama tavily-python python-dotenv
