# Frontend Dockerfile - Multi-stage build with nginx
FROM node:22-slim AS build

WORKDIR /app

# Accept backend host as build argument
ARG BACKEND_HOST=backend

# Copy shared config from repository root
COPY shared_config.json /app/shared_config.json

# Copy frontend package files
COPY frontend/package*.json /app/frontend/

# Install dependencies
WORKDIR /app/frontend
RUN npm ci

# Copy frontend source code
COPY frontend/ /app/frontend/

# Build the application
RUN npm run build

# Runtime stage with nginx
FROM nginx:alpine

# Accept backend host as build argument for runtime
ARG BACKEND_HOST=backend
ENV BACKEND_HOST=${BACKEND_HOST}

# Copy built assets
COPY --from=build /app/frontend/dist /usr/share/nginx/html

# Copy nginx configuration template
COPY frontend/default.conf.template /etc/nginx/templates/default.conf.template

# Expose the frontend port
EXPOSE 80

# nginx automatically processes templates in /etc/nginx/templates
CMD ["nginx", "-g", "daemon off;"]
