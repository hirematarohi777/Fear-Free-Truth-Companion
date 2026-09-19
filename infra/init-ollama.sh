#!/usr/bin/env bash
# Fear-Free Family Truth Companion - Model Setup Script
set -e

MODEL_NAME=${OLLAMA_MODEL:-"qwen2.5:7b"}
OLLAMA_HOST=${OLLAMA_BASE_URL:-"http://localhost:11434"}

echo "Checking Ollama service at ${OLLAMA_HOST}..."
curl -fsSL "${OLLAMA_HOST}/api/tags" > /dev/null || {
  echo "Error: Ollama server is not reachable at ${OLLAMA_HOST}."
  echo "Please start Ollama first (e.g., docker compose up -d ollama or ollama serve)."
  exit 1
}

echo "Checking if model '${MODEL_NAME}' is already downloaded..."
if curl -s "${OLLAMA_HOST}/api/tags" | grep -q "${MODEL_NAME}"; then
  echo "Model '${MODEL_NAME}' is already installed and ready."
  exit 0
fi

echo "Pulling model '${MODEL_NAME}' from Ollama registry. This may take several minutes depending on network bandwidth..."
if command -v ollama &> /dev/null; then
  ollama pull "${MODEL_NAME}"
else
  curl -X POST "${OLLAMA_HOST}/api/pull" -d "{\"name\": \"${MODEL_NAME}\"}"
fi

echo "Model '${MODEL_NAME}' pulled successfully!"
