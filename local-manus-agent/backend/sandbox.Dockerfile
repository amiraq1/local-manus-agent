# Sandbox environment for Local Manus Agent
# Provides Python, Node.js, and basic shell tools in a secure non-root container.
#
# Build:
#   docker build -f sandbox.Dockerfile -t local-manus-sandbox:latest .
#
FROM node:20-slim

# Install Python and basic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    jq \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 sandbox && \
    useradd -u 1000 -g sandbox -m -s /bin/bash sandbox

# Create workspace directory
RUN mkdir -p /workspace && chown sandbox:sandbox /workspace

# Create tmp directory writable by sandbox user
RUN mkdir -p /tmp && chmod 1777 /tmp

# Switch to non-root user
USER sandbox
WORKDIR /workspace

# Default command (keeps container alive for exec)
CMD ["sleep", "3600"]
