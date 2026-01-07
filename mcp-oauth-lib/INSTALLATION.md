# Installation Guide - MCP OAuth Library

## Prerequisites

- Python 3.11 or higher
- pip or pip3
- Redis server (for state management features)

## Installation Methods

### Development Installation (Recommended)

Install in editable mode for development:

```bash
cd mcp-oauth-lib
pip install -e .
```

### With Development Dependencies

For running tests and development tools:

```bash
pip install -e ".[dev]"
```

### Production Installation

```bash
pip install .
```

### As Dependency in Other Services

Add to your `requirements.txt`:

```
-e ../mcp-oauth-lib
```

Or in `pyproject.toml`:

```toml
[project]
dependencies = [
    "mcp-oauth @ file:///${PROJECT_ROOT}/../mcp-oauth-lib",
]
```

## Verification

Verify the installation:

```python
python -c "from mcp_oauth import PKCEFlow; print('Installation successful')"
```

## Redis Setup

The state management module requires Redis:

### Local Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Verify Redis Connection

```python
import redis
r = redis.from_url("redis://localhost:6379")
r.ping()  # Should return True
```

## Running Tests

```bash
cd mcp-oauth-lib
pip install -e ".[dev]"
pytest
```

### With Coverage

```bash
pytest --cov=mcp_oauth --cov-report=html
```

## Troubleshooting

### Import Errors

If you encounter import errors, ensure:

1. You're using Python 3.11+: `python --version`
2. The package is installed: `pip show mcp-oauth`
3. Virtual environment is activated

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Check connectivity
python -c "import redis; r=redis.from_url('redis://localhost:6379'); print(r.ping())"
```

### Dependency Conflicts

Create a fresh virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e .
```
