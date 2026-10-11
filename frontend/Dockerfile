# Stage 1: Build production bundle
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Set API base URL to relative path for NGINX reverse proxying
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

# Stage 2: Minimal hardened NGINX runtime
FROM nginx:alpine AS runner

# Clean default html
RUN rm -rf /usr/share/nginx/html/*

# Copy custom NGINX configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled frontend assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=5s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
