# MCP Combined Service Dockerfile
# All-in-one deployment with configurable providers and code execution
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Deno
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno (for code execution sandbox)
RUN curl -fsSL https://deno.land/install.sh | sh
ENV DENO_INSTALL="/root/.deno"
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy code-api for Deno sandbox
COPY code-api/ ./code-api/

# Copy docker infrastructure
COPY docker/ ./docker/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    # Move Deno to user home
    mkdir -p /home/appuser/.deno && \
    cp -r /root/.deno/* /home/appuser/.deno/ && \
    chown -R appuser:appuser /home/appuser/.deno

USER appuser

# Update PATH for non-root user
ENV DENO_INSTALL="/home/appuser/.deno"
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

# Default to all providers enabled
ENV ENABLED_PROVIDERS=outlook,sharepoint,teams,azuredevops,snowflake

# Code execution settings (disabled by default)
ENV CODE_EXECUTION_ENABLED=false
ENV SANDBOX_MODE=deno
ENV DENO_SERVER_PORT=8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000
EXPOSE 8001

# Default command
CMD ["python", "-m", "app.main", "--transport", "http", "--port", "8000"]
