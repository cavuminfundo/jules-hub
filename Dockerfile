# Stage 1: Build Frontend UI
FROM node:20-alpine AS ui-builder

USER root
ENV NODE_ENV=development
WORKDIR /app/ui

# Install dependencies including devDependencies for build
COPY ui/package.json ui/package-lock.json* ./
RUN npm install --include=dev

# Copy source and config files
COPY ui/src/ ./src/
COPY ui/index.html ui/vite.config.ts ui/tsconfig*.json ui/tailwind.config.js ui/postcss.config.js ./

# Compile production bundle into /app/ui/dist
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim

# Install git and uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
 && rm -rf /var/lib/apt/lists/*

# Create non-root user julius (UID 1000, GID 1000)
RUN groupadd -g 1000 julius && \
    useradd -u 1000 -g 1000 -m -s /bin/bash julius

WORKDIR /app

# Copy dependency metadata and application source
COPY pyproject.toml README.md ./
COPY hub/ ./hub/

# Install python dependencies via uv
RUN uv pip install --system -e .

# Copy UI build artifacts from Stage 1
COPY --from=ui-builder /app/ui/dist ./ui/dist

# Set ownership of /app to julius
RUN chown -R 1000:1000 /app

# Configure safe git directory for host volume mounts
RUN git config --system --add safe.directory "*"

# Configure non-root environment and user
ENV PATH="/home/julius/.local/bin:${PATH}"
USER 1000:1000

EXPOSE 4100

ENTRYPOINT ["uvicorn", "hub.app:app", "--host", "0.0.0.0", "--port", "4100"]
