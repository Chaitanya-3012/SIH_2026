FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies with CPU-only PyTorch
RUN uv pip install --system --no-cache --index-url https://download.pytorch.org/whl/cpu torch && \
    uv sync --frozen --no-cache --no-install-project

# Copy source code and artifacts
COPY ml_artifacts/ ./ml_artifacts/
COPY data/ ./data/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]