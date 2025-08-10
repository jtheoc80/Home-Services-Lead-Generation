# Three-stage Dockerfile for Next.js Standalone Build
# Optimized for production with minimal final image size

# Stage 1: Dependencies
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files and install only production dependencies
COPY package.json ./
RUN npm install --only=production && npm cache clean --force

# Stage 2: Builder  
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package files and install all dependencies (including dev)
COPY package.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Stage 3: Runner (final production image)
FROM node:18-alpine AS runner

# Set production environment
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone application from builder
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./frontend/.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./frontend/public

# Switch to non-root user
USER nextjs

# Expose port (will be set by environment variable)
EXPOSE 3000

# Set default PORT environment variable
ENV PORT=3000

# Start the standalone server
CMD ["node", "frontend/server.js"]