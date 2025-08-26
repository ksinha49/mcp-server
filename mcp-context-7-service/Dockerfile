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

# Copy built artifacts
COPY --from=builder /app/dist ./dist

# Copy package files for production install
COPY package.json bun.lock ./

# Install only production dependencies
RUN bun install --production --no-scripts

# Expose HTTP port
EXPOSE 8080

# Default command
CMD ["bun", "dist/index.js", "--transport", "http", "--port", "8080"]