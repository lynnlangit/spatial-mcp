FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /app/servers/mcp-neoantigen /app/shared/utils /app/shared/common

# Copy temporarily staged shared utilities
COPY _shared_temp/utils/ /app/shared/utils/
COPY _shared_temp/common/ /app/shared/common/

# Copy server code
COPY . /app/servers/mcp-neoantigen/

# Install Python dependencies
WORKDIR /app/servers/mcp-neoantigen
RUN pip install --no-cache-dir -e .

# Set environment variables for SSE transport
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=3016
ENV PYTHONPATH=/app/shared/utils:${PYTHONPATH}
ENV NEOANTIGEN_DRY_RUN=false

# Expose port
EXPOSE 3016

# Run the server
CMD ["python", "-m", "mcp_neoantigen"]
