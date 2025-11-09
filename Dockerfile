FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKSPACE_DIR=/workspace \
    MCP_HTTP_REQUIRE_ORIGIN=true \
    ALLOWED_ORIGINS="https://chatgpt.com,https://chat.openai.com"

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# non-root
RUN useradd -m appuser && mkdir -p /workspace && chown -R appuser:appuser /workspace /app
USER appuser

EXPOSE 8080

CMD ["uvicorn", "http_mcp_oauth_bridge:app", "--host", "0.0.0.0", "--port", "8080"]

