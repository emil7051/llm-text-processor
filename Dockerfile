FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Tesseract OCR for PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libreoffice \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create volume for input/output data
VOLUME ["/data"]

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the entrypoint
ENTRYPOINT ["llm-preprocess"]

# Default command (can be overridden)
CMD ["--help"]
