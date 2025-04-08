# Docker Setup for LLM Text Preprocessing Tool

This document explains how to run the LLM Text Preprocessing Tool using Docker, which provides a consistent and isolated environment regardless of your operating system.

## Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Quick Start

The easiest way to use the containerized tool is with the provided script:

```bash
# Make the script executable (if needed)
chmod +x docker-run.sh

# Run the script with files you want to process
./docker-run.sh /path/to/your/document.pdf /path/to/another/file.docx
```

This will:
1. Copy the specified files to the `data/input/` directory
2. Build the Docker container
3. Process all files from `data/input/` and place results in `data/output/`

## Manual Setup

If you prefer to set up manually:

1. **Create data directories**:
   ```bash
   mkdir -p data/input data/output
   ```

2. **Copy files to process**:
   ```bash
   cp /path/to/your/documents/* data/input/
   ```

3. **Build and run the container**:
   ```bash
   docker-compose up --build
   ```

4. **Find results in the output directory**:
   ```bash
   ls -la data/output/
   ```

## Custom Configuration

You can use custom configuration files with the Docker container:

1. **Create a configuration file**:
   ```bash
   # Copy a sample configuration
   cp examples/config_examples/aggressive_cleaning.yaml data/config.yaml
   ```

2. **Edit the docker-compose.yml file**:
   ```yaml
   command: --config /data/config.yaml /data/input /data/output
   ```

3. **Run the container**:
   ```bash
   docker-compose up --build
   ```

## Advanced Usage

### Specify Output Format

```bash
docker-compose run --rm textcleaner --format json /data/input /data/output
```

### Process a Single File

```bash
docker-compose run --rm textcleaner /data/input/document.pdf /data/output/result.md
```

### Generate Configuration

```bash
docker-compose run --rm textcleaner generate-config --level aggressive --output /data/aggressive_config.yaml
```

### List Supported Formats

```bash
docker-compose run --rm textcleaner list-formats
```

## Troubleshooting

If you encounter issues:

1. **Check Docker logs**:
   ```bash
   docker-compose logs
   ```

2. **Verify file permissions**:
   Make sure the files in `data/input/` are readable by the Docker container.

3. **Check disk space**:
   Ensure you have enough disk space for the Docker images and containers.

4. **Update the container**:
   If you've made changes to the code, rebuild the container:
   ```bash
   docker-compose build --no-cache
   ```
