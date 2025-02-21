# Valerii's LLM Proxy

A FastAPI-based proxy server for Large Language Models (LLMs) that provides a unified interface for various LLM providers.

## Features

- 🔄 Unified API interface compatible with OpenAI's API format
- 👥 User management and authentication
- 📊 Usage statistics tracking
- 🤖 Support for various LLM providers
- 🐳 Docker support for easy deployment
- 🖥️ CLI-based admin interface for user management and stats


## Installation, containerized
1. Clone the repository
```bash
git clone https://github.com/valaises/llm-proxy.git
```
2. Specify variables in .env file
```bash
cp .env.example .env
```
```bash
vim .env
```

#### Using Docker
```bash
docker build -t llm_proxy . && \
docker run -d \
  --name llm_proxy \
  --env-file .env \
  -p 7012:7012 \
  -v $(pwd)/db:/app/db \
  --restart unless-stopped \
  llm_proxy
```

or, alternatively, you can use docker compose
#### Using Docker Compose
```bash
docker compose up -d
```

## Installation, Local
1. Install uv

[about: uv - modern pip, pipx, poetry, venv replacement](https://docs.astral.sh/uv/getting-started/installation/)
```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

2. Clone the repository
```bash
git clone https://github.com/valaises/llm-proxy.git
```

3. Install llm-proxy
```bash
uv sync && sudo uv pip install -e
```
4. Specify env variables:
```
# obrigatory
LLM_PROXY_SECRET= 
# at least one LLM providers' api key
# OPENAI_API_KEY =
# GEMINI_API_KEY =
```
5. Start the server
```bash
python -m src.core.main
```

### Command Line Arguments

- `--host`: Specify the host address (default: 127.0.0.1)
- `--port`: Specify the port number (default: 8000)
- `--debug`: Enable debug logging (optional)

## Usage

### Create a User and get an API KEY

#### Using CLI Admin

(Docker): start interactive terminal
```bash
docker exec -it llm_proxy bash
```
Start admin CLI
```bash
python -m src.core.scripts.cli_admin
```

#### Using requests
1. Create a user
```bash
```bash
curl -X POST http://localhost:7012/v1/users-create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LLM_PROXY_SECRET" \
  -d '{
    "email": "user@example.com"
  }'
```

2. Create an API KEY for user
```bash
curl -X POST http://localhost:7012/v1/keys-create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LLM_PROXY_SECRET" \
  -d '{
    "user_id": 1,
    "scope": ""
  }'
```

### Make a Chat Request
```bash
curl http://localhost:7012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LLM_PROXY_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "developer",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ],
    "stream": false
  }'
```

## Accessing UsageStats
You can use DB Viewer to access SQLite DB or use a CLI tool

### CLI Tool Usage

(Docker): start interactive terminal
```bash
docker exec -it llm_proxy bash
```
```bash
python -m src.core.scripts.show_usage_stats
```

| User ID | Requests | Tokens In | Tokens Out | Cost In ($) | Cost Out ($) | Messages | Models Used       |
|---------|----------|-----------|------------|-------------|--------------|-----------|------------------|
| 4       | 4        | 76        | 44         | 0           | 0            | 8         | gpt-4o-2024-11-20 |
| TOTAL   | 4        | 76        | 44         | 0           | 0            | 8         | ALL              |
