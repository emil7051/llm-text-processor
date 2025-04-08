# LLM Text Preprocessing Tool - Optimized Docker Image
# Multi-stage build for better efficiency and smaller image size

# ======== Builder Stage ========
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements separately to leverage Docker layer caching
# This way, dependencies are only reinstalled if requirements.txt changes
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the package files needed for installation
COPY setup.py pyproject.toml ./
COPY src/ ./src/

# Build wheel package
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels -e .

# ======== Runtime Stage ========
FROM python:3.9-slim

# Set labels for better metadata
LABEL maintainer="LLM Text Processor Team"
LABEL version="1.0.0"
LABEL description="Container for preprocessing text documents for LLMs"

# Set working directory
WORKDIR /app

# Install runtime system dependencies
# Group related packages and clean up in the same layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PDF processing tools
    tesseract-ocr \
    poppler-utils \
    # Office document processing
    libreoffice \
    # Additional utilities
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder stage
COPY --from=builder /app/wheels /app/wheels

# Install the wheels
RUN pip install --no-cache-dir /app/wheels/*

# Copy configuration and example files
COPY src/llm_text_processor/config/default_config.yaml /app/config/
COPY examples/ /app/examples/

# Create directories for input and output data
RUN mkdir -p /app/data/input /app/data/output

# Create volume for persisting data
VOLUME ["/app/data"]

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/config/default_config.yaml

# Document the exposed ports (if any web interface is added in the future)
# EXPOSE 8080

# Create a non-root user for better security
RUN groupadd -r textprocessor && useradd -r -g textprocessor textprocessor
RUN chown -R textprocessor:textprocessor /app
USER textprocessor

# Add a health check to verify the container is running properly
HEALTHCHECK CMD llm-preprocess --version || exit 1

# Set the entrypoint to the CLI command
ENTRYPOINT ["llm-preprocess"]

# Default command shows help (can be overridden)
CMD ["--help"]

# Usage examples (in comments for documentation):
# Process a single file:
#   docker run -v $(pwd)/data:/app/data llm-text-processor /app/data/input/document.pdf /app/data/output/document.md
# 
# Process a directory:
#   docker run -v $(pwd)/data:/app/data llm-text-processor --batch /app/data/input /app/data/output
