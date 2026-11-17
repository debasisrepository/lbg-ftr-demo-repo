FROM node:22-alpine AS builder

WORKDIR /app

# Copy shared config first (from repo root)
COPY shared_config.json /app/shared_config.json

# Copy frontend package files
COPY frontend/package*.json /app/frontend/

# Set working directory to frontend
WORKDIR /app/frontend

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ /app/frontend/

# Build the app
RUN npm run build

# Production stage
FROM nginx:1.27-alpine

# Copy custom nginx config template
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy built assets from builder
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Backend host can be overridden at build time
ARG BACKEND_HOST=backend
ENV BACKEND_HOST=${BACKEND_HOST}

EXPOSE 80
# Preview port annotation
# x-preview-port: 80

CMD ["nginx", "-g", "daemon off;"]
