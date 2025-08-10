# Multi-stage Dockerfile for Next.js Home Services Lead Generation Frontend
# Converted from Vite-based to Next.js following best practices:
# - Uses `next build` instead of Vite build commands
# - Uses `next start` instead of serve for production
# - Copies Next.js specific artifacts (.next, public, next.config.js)
# - Exposes port 3000 and starts with npm start as required

# Stage 1: Build dependencies and application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and install dependencies (including dev dependencies for build)
COPY package.json ./
RUN npm install

# Copy source code and build using Next.js
COPY . .
RUN npm run build

# Stage 2: Production runtime
FROM node:18-alpine AS runner

# Set environment variables for Next.js production
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

# Copy built Next.js application artifacts from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/next.config.js ./next.config.js

# Switch to non-root user
USER nextjs

# Expose port 3000 as required
EXPOSE 3000

# Start the Next.js application using npm start (which runs `next start`)
CMD ["npm", "start"]