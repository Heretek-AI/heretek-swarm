# Heretek Swarm Frontend
# Multi-stage build for React application

# =============================================================================
# Stage 1: Build
# =============================================================================
FROM node:20-alpine as build

ARG VITE_API_HOST

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build application - skip strict type checking for deployment
# VITE_API_HOST is passed as build argument and becomes available at build time
RUN npm run build:skip-type-check

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM nginx:alpine as production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
