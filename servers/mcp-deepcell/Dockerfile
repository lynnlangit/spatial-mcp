FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# build-essential: C compiler and build tools (needed for deepcell-toolbox)
# libgomp1: Required by TensorFlow for OpenMP support
# libhdf5-dev: Required for DeepCell model loading
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libgomp1 \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /app/servers/mcp-deepcell /app/shared/utils /app/shared/common

# Copy temporarily staged shared utilities
COPY _shared_temp/utils/ /app/shared/utils/
COPY _shared_temp/common/ /app/shared/common/

# Copy server code
COPY . /app/servers/mcp-deepcell/

# Install Python dependencies
WORKDIR /app/servers/mcp-deepcell
RUN pip install --no-cache-dir -e .

# Set environment variables for SSE transport
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=3007
ENV PORT=3007

# DeepCell configuration
ENV DEEPCELL_DRY_RUN=false
ENV DEEPCELL_OUTPUT_DIR=/app/data/output
ENV DEEPCELL_MODEL_CACHE_DIR=/app/data/models
ENV DEEPCELL_USE_GPU=false

# TensorFlow configuration (CPU-only for Cloud Run)
ENV TF_CPP_MIN_LOG_LEVEL=2

# Create data directories
RUN mkdir -p /app/data/output /app/data/models

# Expose port
EXPOSE 3007

# Run the server
CMD ["python", "-m", "mcp_deepcell"]
