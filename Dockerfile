# Use Python 3.14-slim as the base image
FROM python:3.14-slim AS builder

# Install uv for extremely fast and reliable dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Enable bytecode compilation for faster startup times
ENV UV_COMPILE_BYTECODE=1

# Copy only the files needed for dependency installation
COPY pyproject.toml uv.lock ./

# Install the project's dependencies (excluding the project itself and dev dependencies)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Final runtime stage
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Copy the installed dependencies environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy the application source code
COPY src/ /app/src/

# Place the virtual environment's bin folder at the front of the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose port 8080 (Cloud Run's default port)
EXPOSE 8080

# Start the FastAPI application using uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
