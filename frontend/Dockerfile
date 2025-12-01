# =============================================================================
# PEA RE Forecast Platform - Frontend Dockerfile
# =============================================================================

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Build arguments
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Expose port
EXPOSE 3000

# Development command (override in production)
CMD ["npm", "run", "dev"]
