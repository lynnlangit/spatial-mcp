FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /app/servers/mcp-fgbio /app/shared/utils /app/shared/common

# Copy temporarily staged shared utilities
COPY _shared_temp/utils/ /app/shared/utils/
COPY _shared_temp/common/ /app/shared/common/

# Copy server code
COPY . /app/servers/mcp-fgbio/

# Install Python dependencies
WORKDIR /app/servers/mcp-fgbio
RUN pip install --no-cache-dir -e .

# Set environment variables for SSE transport
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=3000
ENV PYTHONPATH=/app/shared/utils:${PYTHONPATH}
ENV FGBIO_DRY_RUN=false
ENV FGBIO_DATA_DIR=/app/data/reference
ENV FGBIO_CACHE_DIR=/app/data/cache

# Create data directories
RUN mkdir -p /app/data/reference /app/data/cache

# Expose port
EXPOSE 3000

# Run the server
CMD ["python", "-m", "mcp_fgbio"]
