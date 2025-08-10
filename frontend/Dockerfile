# Two-stage Dockerfile for Vite-based React frontend

# Stage 1: Build stage
# Use Node.js 20 for building the application
FROM node:20 AS build

# Set working directory for build stage
WORKDIR /app

# Copy package files for dependency installation
# Copy package*.json first for better Docker layer caching
COPY frontend/package*.json ./

# Install dependencies using npm ci for faster, reliable builds
RUN npm ci

# Copy frontend source code
COPY frontend/ .

# Build the application for production
RUN npm run build

# Stage 2: Production stage
# Use Alpine variant for smaller final image size
FROM node:20-alpine AS production

# Install serve globally to serve static files
RUN npm install -g serve

# Set environment variable for port with default
ENV PORT=3000

# Copy built application from build stage
# Copy the dist folder to /dist in the production image
COPY --from=build /app/dist /dist

# Expose port 3000 for the frontend application
EXPOSE 3000

# Serve the application on the specified port
# Bind to $PORT environment variable with default fallback to 3000
CMD ["sh", "-c", "serve -s /dist -l ${PORT:-3000}"]