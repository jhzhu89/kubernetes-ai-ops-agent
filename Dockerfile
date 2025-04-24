# Use Python 3.11 with Debian Bullseye as base for better debugging with full shell
FROM python:3.11-bullseye

# Install essential system packages: curl (for downloads), git (for cloning), gnupg (for scripts that require it)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      git \
      gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (includes npm & npx) for any npx-based tools you might need at runtime
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Download and install kubectl (Kubernetes CLI) from the official release channel
RUN KUBE_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt) && \
    curl -fsSL https://dl.k8s.io/release/$KUBE_VERSION/bin/linux/amd64/kubectl \
      -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl

# Download and install Helm (Kubernetes package manager)
RUN HELM_VERSION="v3.14.0" && \
    curl -fsSL https://get.helm.sh/helm-$HELM_VERSION-linux-amd64.tar.gz \
      | tar zxvf - --strip-components=1 linux-amd64/helm && \
    mv helm /usr/local/bin/helm && \
    chmod +x /usr/local/bin/helm

# Copy and build the custom MCP Kubernetes server instead of using npm version
COPY deps/mcp-server-kubernetes /app/deps/mcp-server-kubernetes
WORKDIR /app/deps/mcp-server-kubernetes
RUN npm install && npm run build && npm link

RUN pip install --no-cache-dir uv

# Copy Python dependency list and install all required packages (including uv)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy Prometheus MCP Server source and install it as a Python package
COPY deps/prometheus-mcp-server /app/deps/prometheus-mcp-server
RUN pip install --no-cache-dir /app/deps/prometheus-mcp-server

# Install the MCP server time package
RUN pip install --no-cache-dir mcp-server-time

# Set working directory for your Chainlit app
WORKDIR /app

# Copy application code
COPY src/ /app/src/
COPY chainlit.md /app/
COPY .chainlit/ /app/.chainlit/

# Expose ChainlitΓÇÖs default port
EXPOSE 9000

# Start your app via Chainlit
CMD ["chainlit", "run", "src/main.py", "--host", "0.0.0.0", "--port", "9000"]
