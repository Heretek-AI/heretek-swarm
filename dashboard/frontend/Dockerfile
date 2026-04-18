# Heretek Swarm Frontend
# Multi-stage build for React application

# =============================================================================
# Stage 1: Build (skip - we pre-build locally)
# =============================================================================
FROM alpine AS build-placeholder
RUN echo "Build happens locally"

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM nginx:alpine as production

# Create non-root user for security (S6471 fix)
RUN addgroup -g 1001 -S appgroup && adduser -u 1001 -S appuser -G appgroup

# Copy custom nginx config (remove user directive)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create nginx directories for non-root user
RUN mkdir -p /var/cache/nginx/client_temp /run && \
    chown -R appuser:appgroup /var/cache/nginx /run

# Copy pre-built assets from local dist directory
COPY --chown=appuser:appgroup dist/ /usr/share/nginx/html/

# Expose port
EXPOSE 80

# Health check - use 127.0.0.1 instead of localhost (IPv6 vs IPv4 issue)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --spider http://127.0.0.1/ || exit 1

# Start nginx as non-root user
USER appuser

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
