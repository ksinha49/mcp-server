# Multi-stage Bun-based Dockerfile
# ----- Build Stage -----
FROM oven/bun:1 AS builder
WORKDIR /app

# Copy package and configuration
COPY bun.lock package.json tsconfig.json ./

# Copy source code
COPY src ./src

# Install dependencies and build
RUN bun install && bun run build

# ----- Production Stage -----
FROM oven/bun:1
WORKDIR /app

# Install curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy built artifacts
COPY --from=builder /app/dist ./dist

# Copy package files for production install
COPY package.json bun.lock ./

# Install only production dependencies
RUN bun install --production --no-scripts

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Default port (can be overridden at runtime) - Context7 uses 8006
ENV PORT=8006

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

# Expose HTTP port
EXPOSE 8006

# Default command
CMD ["bun", "dist/index.js", "--transport", "http", "--port", "8006"]
