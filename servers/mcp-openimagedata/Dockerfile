FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /app/servers/mcp-openimagedata /app/shared/utils /app/shared/common

# Copy temporarily staged shared utilities
COPY _shared_temp/utils/ /app/shared/utils/
COPY _shared_temp/common/ /app/shared/common/

# Copy server code
COPY . /app/servers/mcp-openimagedata/

# Install Python dependencies
WORKDIR /app/servers/mcp-openimagedata
RUN pip install --no-cache-dir -e .

# Set environment variables for SSE transport
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=3004
ENV IMAGE_DRY_RUN=false
ENV IMAGE_DATA_DIR=/app/data/images
ENV IMAGE_CACHE_DIR=/app/data/cache/images

# Create data directories
RUN mkdir -p /app/data/images /app/data/cache/images

# Expose port
EXPOSE 3004

# Run the server
CMD ["python", "-m", "mcp_openimagedata"]
