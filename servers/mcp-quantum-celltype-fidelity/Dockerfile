FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /app/servers/mcp-quantum-celltype-fidelity /app/shared/utils

# Copy temporarily staged shared utilities
COPY _shared_temp/utils/ /app/shared/utils/

# Copy server code
COPY . /app/servers/mcp-quantum-celltype-fidelity/

# Install Python dependencies
WORKDIR /app/servers/mcp-quantum-celltype-fidelity
# Upgrade pip and setuptools first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
# Install the package (this will pull in all dependencies including fastmcp>=0.1.0)
RUN pip install --no-cache-dir -e .

# Set environment variables for SSE transport
ENV MCP_TRANSPORT=sse
ENV MCP_TOOL_TIMEOUT=180
ENV QUANTUM_BACKEND=cpu
ENV QUANTUM_DATA_DIR=/app/data/quantum
ENV QUANTUM_CACHE_DIR=/app/data/cache/quantum

# Create data directories
RUN mkdir -p /app/data/quantum /app/data/cache/quantum

# Expose port (Cloud Run will set PORT environment variable)
EXPOSE 8080

# Run the server
CMD ["python", "-m", "quantum_celltype_fidelity.server"]
