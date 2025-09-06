# Multi-stage build for smaller final image
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 (required for latest npm)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

WORKDIR /app

# Copy dependency files
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Install Claude CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Final stage
FROM python:3.12-slim

# Install Node.js runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install Claude CLI globally as root
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Claude CLI is installed globally, no node_modules needed

# Copy application code
COPY --chown=appuser:appuser . .

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

# Create directory for Claude config (will be mounted as volume)
RUN mkdir -p /home/appuser/.config && chown -R appuser:appuser /home/appuser/.config

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    CLAUDE_CODE_PATH=/usr/bin/claude

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]