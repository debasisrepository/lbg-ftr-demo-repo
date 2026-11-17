# Build stage
FROM node:22-slim AS builder

WORKDIR /app

# Copy shared config from repository root
COPY shared_config.json /app/shared_config.json

# Copy frontend dependency files
COPY frontend/package*.json /app/frontend/

# Set working directory to frontend
WORKDIR /app/frontend

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/src/ ./src/
COPY frontend/public/ ./public/
COPY frontend/index.html ./
COPY frontend/tsconfig.json ./
COPY frontend/tsconfig.node.json ./
COPY frontend/vite.config.ts ./
COPY frontend/tailwind.config.js ./
COPY frontend/postcss.config.js ./
COPY frontend/eslint.config.js ./

# Build application
RUN npm run build

# Runtime stage
FROM nginx:alpine

# Accept backend host as build arg
ARG BACKEND_HOST=backend
ENV BACKEND_HOST=${BACKEND_HOST}

# Copy built assets
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Copy nginx configuration template
COPY frontend/default.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
