# Frontend Dockerfile - multi-stage build

# Build stage
FROM node:22-slim as builder

WORKDIR /app

# Copy shared config first
COPY shared_config.json /app/shared_config.json

# Copy frontend dependency files
COPY frontend/package*.json /app/frontend/

# Change to frontend directory and install dependencies
WORKDIR /app/frontend
RUN npm ci

# Copy frontend application code
COPY frontend/ /app/frontend/

# Build application
RUN npm run build

# Production stage with nginx
FROM nginx:1.27-alpine

# Accept backend host as build arg
ARG BACKEND_HOST=backend
ENV BACKEND_HOST=${BACKEND_HOST}

# Copy built assets from builder
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Copy nginx template for API proxy
COPY frontend/default.conf.template /etc/nginx/templates/default.conf.template

# Expose port 80
EXPOSE 80

# nginx will substitute env vars in templates and start
CMD ["nginx", "-g", "daemon off;"]
