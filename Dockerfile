# Use Python 3.14-slim as the builder stage
FROM python:3.14-slim AS builder

# Install uv for extremely fast and reliable dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a non-root user (UID 1000) for security compatibility (e.g. Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files with correct owner permissions
COPY --chown=user:user pyproject.toml uv.lock ./

# Install dependencies (excluding dev tools and project self-installation)
RUN --mount=type=cache,target=/home/user/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Final runtime stage
FROM python:3.14-slim

# Create the same non-root user for runtime
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# Copy the dependencies from builder
COPY --from=builder --chown=user:user /home/user/app/.venv /home/user/app/.venv

# Copy application source files
COPY --chown=user:user src/ /home/user/app/src/

# Place the virtual environment's bin folder at the front of the PATH
ENV PATH="/home/user/app/.venv/bin:$PATH"

# Default fallback port (dynamic platforms like Render and Hugging Face inject a $PORT environment variable)
EXPOSE 8000

# Start FastAPI using uvicorn, binding to the PORT environment variable if defined, otherwise defaulting to 8000
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
