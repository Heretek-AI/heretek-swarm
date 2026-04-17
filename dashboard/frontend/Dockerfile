# Heretek Swarm Frontend
# Multi-stage build for React application

# =============================================================================
# Stage 1: Build
# =============================================================================
FROM node:20-alpine as build

# VITE_API_HOST is a non-sensitive build argument
ARG VITE_API_HOST

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code — only src, public, and package files needed for build
COPY src/ public/ package.json package-lock.json ./

# Build application - skip strict type checking for deployment
# VITE_API_HOST is passed as build argument and becomes available at build time
RUN npm run build:skip-type-check

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM nginx:alpine as production

# Create non-root user for security (S6471 fix)
RUN addgroup -g 1001 -S appgroup && adduser -u 1001 -S appuser -G appgroup

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check - use 127.0.0.1 instead of localhost (IPv6 vs IPv4 issue)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --spider http://127.0.0.1/ || exit 1

# Switch to non-root user before running (S6471 fix)
USER appuser

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
