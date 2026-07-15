# Use Python 3.14-slim as the builder stage
FROM python:3.14-slim AS builder

# Install uv for extremely fast and reliable dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Hugging Face Spaces requires running as a non-root user (UID 1000)
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

# Hugging Face Spaces expects the container to listen on port 7860
EXPOSE 7860

# Run FastAPI app using uvicorn on port 7860
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]
