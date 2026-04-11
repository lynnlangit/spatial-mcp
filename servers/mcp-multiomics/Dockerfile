FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /app/servers/mcp-multiomics /app/shared/utils /app/shared/common

# Copy temporarily staged shared utilities
COPY _shared_temp/utils/ /app/shared/utils/
COPY _shared_temp/common/ /app/shared/common/

# Copy server code
COPY . /app/servers/mcp-multiomics/

# Install Python dependencies
# Set RPY2_CFFI_MODE=ABI to build rpy2 without R (Python fallback available)
WORKDIR /app/servers/mcp-multiomics
ENV RPY2_CFFI_MODE=ABI
RUN pip install --no-cache-dir -e .

# Set environment variables for SSE transport
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=3001
ENV PYTHONPATH=/app/shared/utils:${PYTHONPATH}
ENV MULTIOMICS_DRY_RUN=false
ENV MULTIOMICS_DATA_DIR=/app/data/multiomics
ENV MULTIOMICS_CACHE_DIR=/app/data/cache/multiomics

# Create data directories
RUN mkdir -p /app/data/multiomics /app/data/cache/multiomics

# Expose port
EXPOSE 3001

# Run the server
CMD ["python", "-m", "mcp_multiomics"]
