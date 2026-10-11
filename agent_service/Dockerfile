FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --omit=dev

# Copy service source code
COPY . .

# Expose agent daemon port
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=5s \
  CMD node -e "fetch('http://localhost:8001/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

# Start Pi Agent HTTP server daemon
CMD ["node", "server.mjs"]
