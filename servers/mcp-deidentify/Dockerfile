FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /app/servers/mcp-deidentify /app/shared/utils /app/shared/common

# Copy temporarily staged shared utilities
COPY _shared_temp/utils/ /app/shared/utils/
COPY _shared_temp/common/ /app/shared/common/

# Copy server code
COPY . /app/servers/mcp-deidentify/

# Install Python dependencies
WORKDIR /app/servers/mcp-deidentify
RUN pip install --no-cache-dir -e .

# Set environment variables for SSE transport
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=3017
ENV PYTHONPATH=/app/shared/utils:${PYTHONPATH}

# Stage 0 de-identification runs live. DEIDENTIFY_DRY_RUN=true returns synthetic
# fixtures, which for this server is a safety failure rather than a safe default,
# so it must be opted into explicitly. Requires ANTHROPIC_API_KEY at runtime.
ENV DEIDENTIFY_DRY_RUN=false
ENV DEIDENTIFY_DATE_POLICY=SAFE_HARBOR

# Expose port
EXPOSE 3017

# Run the server
CMD ["python", "-m", "mcp_deidentify"]
