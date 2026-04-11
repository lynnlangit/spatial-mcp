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
RUN mkdir -p /app/servers/mcp-perturbation /app/shared/utils /app/shared/common

# Copy temporarily staged shared utilities
COPY _shared_temp/utils/ /app/shared/utils/
COPY _shared_temp/common/ /app/shared/common/

# Copy server code
COPY . /app/servers/mcp-perturbation/

# Install Python dependencies
WORKDIR /app/servers/mcp-perturbation
# Upgrade pip and setuptools first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
# Install the package (this will pull in all dependencies including fastmcp>=0.2.0)
RUN pip install --no-cache-dir -e .

# Set environment variables for SSE transport
ENV MCP_TRANSPORT=sse
ENV PERTURBATION_DRY_RUN=false
ENV PERTURBATION_DATA_DIR=/app/data/perturbation
ENV PERTURBATION_MODEL_DIR=/app/data/models/perturbation

# Create data directories
RUN mkdir -p /app/data/perturbation /app/data/models/perturbation

# Expose port (Cloud Run will set PORT environment variable)
EXPOSE 8080

# Run the server
CMD ["python", "-m", "mcp_perturbation"]
