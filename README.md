---
title: AI Hiring Automation Platform
emoji: 🤖
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AI Hiring Automation Platform

An automated recruitment and screening assistant built with FastAPI, Pydantic, and PostgreSQL, powered by Gemini and Groq LLMs.

## Project Structure

- `src/main.py`: Entrypoint for the FastAPI application.
- `src/api/`: Application routes and controllers.
- `src/core/`: Application settings, configurations, and lifecycle hooks.
- `src/models/`: Database schemas and models.
- `src/repository/`: Data access layer.
- `src/service/`: Business logic.

## Deploying to Hugging Face Spaces

This project is configured to run as a Docker Space on Hugging Face. The container is configured with the following characteristics:
- Runs as non-root user (UID `1000`)
- Listens on port `7860`

### Local Development

This project uses `uv` for python environment and dependency management.

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Run the development server**:
   ```bash
   uv run uvicorn src.main:app --reload
   ```
