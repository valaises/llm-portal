# LLM Portal

A FastAPI-based proxy server for Large Language Models (LLMs) that provides a unified interface for various LLM providers.

## Features

- 🔄 Unified API interface compatible with OpenAI's API format
- 👥 User management and authentication
- 📊 Usage statistics tracking
- 🤖 Support for various LLM providers
- 🐳 Docker support for easy deployment
- 🖥️ CLI-based admin interface for user management and stats


## Installation

Download docker-compose.yaml
```bash
wget -O docker-compose.yaml https://raw.githubusercontent.com/valaises/llm-portal/refs/heads/main/docker-compose.yaml
```

Start docker compose
#### Using Docker Compose
```bash
docker compose up -d
```

## Installation, Development

Clone repository
```sh
git clone https://github.com/valaises/llm-portal.git
```

Start docker compose
```sh
docker compose -f docker-compose-dev.yaml up -d
```

## Example: Make a Chat Request
```bash
curl https://llmproxy.xi.valerii.cc/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin1234" \
  -d '{
    "model": "gemini-2.5-pro",
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

#### Create a User and API KEY Using requests
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

## Accessing UsageStats
You can use DB Viewer to access SQLite DB or use a CLI tool

### CLI Tool Usage

Execute command
```bash
docker exec -it llm-portal bash -c "python -m src.core.scripts.show_usage_stats"
```

| User ID | Requests | Tokens In | Tokens Out | Cost In ($) | Cost Out ($) | Messages | Models Used       |
|---------|----------|-----------|------------|-------------|--------------|-----------|------------------|
| 4       | 4        | 76        | 44         | 0           | 0            | 8         | gpt-4o-2024-11-20 |
| TOTAL   | 4        | 76        | 44         | 0           | 0            | 8         | ALL              |

## License

This project is licensed under a custom license that:
- Allows free use for personal and non-commercial purposes
- Requires explicit permission from the author for any commercial use
- Requires attribution

See the [LICENSE](LICENSE) file for details.
