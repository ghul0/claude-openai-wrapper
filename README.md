# Claude OpenAI API

OpenAI-compatible API server for Claude Code SDK - Run Claude locally with OpenAI client libraries.

## Features

- **OpenAI Chat Completions API** compatible endpoints
- **Local Claude execution** via Claude Code SDK
- **Multiple model support** (Sonnet, Haiku)
- **Docker-based deployment** for easy setup
- **API key authentication** for secure access
- **JSON response format** support

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Claude CLI authenticated on your system

### Installation

1. Clone the repository:
```bash
git clone git@github.com:ghul0/claude-openai-wrapper.git
cd claude-openai-wrapper
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Edit `.env` to set your API key:
```bash
API_KEY=your-secure-api-key
```

4. Start the server:
```bash
docker-compose up -d
```

The API will be available at `http://localhost:8100`

### Claude Authentication (One-time Setup)

Authenticate Claude CLI inside the container (only needed once, persists across restarts):

```bash
docker exec -it claude-code-openai-api bash
claude --version  # Follow authentication prompts
exit
```

## API Usage

### Chat Completion

```bash
curl -X POST http://localhost:8100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secure-api-key" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100
  }'
```

### Available Models

- `claude-3-5-sonnet-20241022` - Most capable model
- `claude-3-5-haiku-20241022` - Faster, lighter model
- `gpt-4` - Alias for claude-3-5-sonnet
- `gpt-3.5-turbo` - Alias for claude-3-5-haiku

### Python Client Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8100/v1",
    api_key="your-secure-api-key"
)

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "What is 2+2?"}
    ]
)

print(response.choices[0].message.content)
```

## Configuration

### Environment Variables

- `API_KEY` - API key for authentication (required)
- `CLAUDE_CODE_PATH` - Path to Claude CLI (default: /usr/bin/claude)
- `LOG_LEVEL` - Logging level (default: INFO)
- `PORT` - External port (default: 8100, internal: 8000)

### Claude SDK Options

Configure Claude's behavior via environment variables:

- `CLAUDE_ALLOWED_TOOLS` - Tools Claude can use (default: Read,Grep,Glob,LS)
- `CLAUDE_MAX_THINKING_TOKENS` - Max thinking tokens (default: 8000)
- `CLAUDE_PERMISSION_MODE` - Permission mode (default: bypassPermissions)
- `CLAUDE_DEFAULT_MODEL` - Default model if not specified

## API Endpoints

- `GET /health` - Health check
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Create chat completion

## Limitations

- Streaming responses not yet supported
- Single completion per request (n=1)
- Token counting is approximate

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

### Docker Build

```bash
docker build -t claude-openai-api .
docker run -p 8000:8000 --env-file .env claude-openai-api
```

## License

MIT License - Copyright (c) 2025 Tomasz Młynek

## Support

For issues and feature requests, please visit: https://github.com/ghul0/claude-openai-wrapper/issues