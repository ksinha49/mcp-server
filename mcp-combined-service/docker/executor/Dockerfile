# MCP Code Executor Container
#
# Sandboxed Node.js environment for executing agent-generated TypeScript code.
# Runs with minimal privileges and restricted syscalls.

FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY code-api/package.json code-api/package-lock.json* ./

# Install dependencies
RUN npm ci --production=false

# Copy source code
COPY code-api/ .

# Build TypeScript
RUN npm run build

# Production image
FROM node:20-alpine

# Security: Run as non-root user
RUN addgroup -g 1000 executor && \
    adduser -D -u 1000 -G executor executor

WORKDIR /app

# Copy only production dependencies and built files
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist

# Set ownership
RUN chown -R executor:executor /app

# Switch to non-root user
USER executor

# Environment variables
ENV NODE_ENV=production
ENV DENO_PORT=3000

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start server
ENTRYPOINT ["node", "dist/server.js"]
