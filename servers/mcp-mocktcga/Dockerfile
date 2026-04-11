FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /app/servers/mcp-mocktcga /app/shared/utils /app/shared/common

# Copy temporarily staged shared utilities
COPY _shared_temp/utils/ /app/shared/utils/
COPY _shared_temp/common/ /app/shared/common/

# Copy server code
COPY . /app/servers/mcp-mocktcga/

# Install Python dependencies
WORKDIR /app/servers/mcp-mocktcga
RUN pip install --no-cache-dir -e .

# Set environment variables for SSE transport
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=3003
ENV PYTHONPATH=/app/shared/utils:${PYTHONPATH}
ENV MOCKTCGA_DRY_RUN=false
ENV MOCKTCGA_DATA_DIR=/app/data/tcga
ENV MOCKTCGA_CACHE_DIR=/app/data/cache/tcga

# Create data directories
RUN mkdir -p /app/data/tcga /app/data/cache/tcga

# Expose port
EXPOSE 3003

# Run the server
CMD ["python", "-m", "mcp_mocktcga"]
