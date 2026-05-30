# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-build

ARG VITE_TRACESTRACK_KEY=""
ENV VITE_TRACESTRACK_KEY=${VITE_TRACESTRACK_KEY}

WORKDIR /build

# Copy package files
COPY frontend/package.json frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend
COPY frontend/ ./

# Build the frontend
RUN npm run build

# Stage 2: Production image
FROM python:3.12-slim

# Install system dependencies required for PostGIS and GDAL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./

# Copy built frontend from stage 1
COPY --from=frontend-build /build/dist ./frontend/dist

# Create media directory for uploads
RUN mkdir -p /app/media

# Expose the port
EXPOSE 8000

# Run migrations and start the application
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
