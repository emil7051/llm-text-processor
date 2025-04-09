# TextCleaner - Optimized Docker Image
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

# Copy project files first
COPY pyproject.toml README.md MANIFEST.in ./
COPY src/ ./src/

# Install the package and its dependencies using pyproject.toml
# Assuming standard dependencies are sufficient for the image.
# Add optional groups if needed, e.g., .[office,pdf]
RUN pip install --no-cache-dir .

# ======== Runtime Stage ========
FROM python:3.9-slim

# Set labels for better metadata
LABEL maintainer="TextCleaner Team"
LABEL version="0.5.3"
LABEL description="Container for preprocessing text documents for LLMs"

# Set working directory
WORKDIR /app

# Install runtime system dependencies (minimal)
# Group related packages and clean up in the same layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependencies needed by some libraries (if any) - verify if needed
    # Example: libxml2-dev libxslt1-dev if lxml needs them at runtime
    # Example: libgl1-mesa-glx for certain graphical libs (unlikely here)
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only the installed package from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/textcleaner /usr/local/bin/textcleaner

# Copy configuration and example files
# Ensure config directory exists
RUN mkdir -p /app/config
COPY src/textcleaner/config/default_config.yaml /app/config/
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
# Pip install should put textcleaner in the path
HEALTHCHECK CMD textcleaner --version || exit 1

# Set the entrypoint to the textcleaner command installed by pip
ENTRYPOINT ["textcleaner"]

# Default command shows help (can be overridden)
CMD ["--help"]

# Usage examples (in comments for documentation):
# Process a single file:
#   docker run -v $(pwd)/data:/app/data textcleaner process /app/data/input/document.pdf /app/data/output/document.md
# 
# Process a directory:
#   docker run -v $(pwd)/data:/app/data textcleaner process /app/data/input /app/data/output
