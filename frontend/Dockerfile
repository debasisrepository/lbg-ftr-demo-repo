# Frontend Dockerfile (multi-stage: build + nginx)
FROM node:22-slim AS build

WORKDIR /app/frontend

# Copy dependency files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy application source
COPY frontend/ ./

# Build production bundle
RUN npm run build

# Nginx runtime stage
FROM nginx:alpine AS runtime

# Copy built assets from build stage
COPY --from=build /app/frontend/dist /usr/share/nginx/html

# Copy nginx configuration template
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template

# Backend host for API proxy
ARG BACKEND_HOST=backend
ENV BACKEND_HOST=${BACKEND_HOST}

# Expose frontend port
EXPOSE 80

# nginx starts automatically and reads templates
