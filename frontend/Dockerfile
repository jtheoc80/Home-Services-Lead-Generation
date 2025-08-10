# Multi-stage Dockerfile for Next.js Home Services Lead Generation Frontend

# Stage 1: Build dependencies and application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Production runtime
FROM node:18-alpine AS runner

# Set environment variables
ENV NODE_ENV=production \
    PORT=3000 \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy package.json and install only production dependencies
COPY package.json ./
RUN npm install --only=production && npm cache clean --force

# Copy built application from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/next.config.js ./next.config.js

# Switch to non-root user
USER nextjs

# Expose port 3000
EXPOSE 3000

# Start the Next.js application
CMD ["npm", "start"]