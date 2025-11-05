# Starting the PineScript RAG Server

This file documents quick ways to run the server locally (development), run a production-like process locally, and build/run with Docker. It also lists alternatives when `docker` is not available on your machine.

## Quick dev run (recommended while developing)

1. Activate your virtualenv and install dependencies (if not already):

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run with `uvicorn` (auto-reload, development):

```bash
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

3. Open the status endpoint:

```bash
curl http://localhost:8000/status
```

## Production-like local run (Gunicorn + Uvicorn workers)

Use this to approximate the production environment used by the Docker image.

```bash
# inside the activated venv
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 server.app:app --log-level info
```

Adjust `-w 4` for the CPU cores available.

## Docker: build & run (local)

The repo includes a `Dockerfile` that runs Gunicorn with Uvicorn workers.

Build the image:

```bash
# from project root
docker build -t pinescript-rag-server:latest .
```

Run the container (example using environment variables):

```bash
# recommended: use an env file containing your secrets
# create a file named `.env` at project root with required env vars

# run container with env file and port mapping
docker run --rm -p 8000:8000 --env-file .env pinescript-rag-server:latest
```

Example of required env vars (place in `.env` or pass individually):

```
SUPABASE_URL=https://your.supabase.url
SUPABASE_SERVICE_ROLE_KEY=eyJ...
OPENAI_API_KEY=sk-...
JWT_SECRET=some-secret
ADMIN_API_KEY=admin-secret
```

### Docker CLI not found (`zsh: command not found: docker`)

If you see `zsh: command not found: docker` it means the Docker CLI is not installed or not on your PATH. Options on macOS:

- Install Docker Desktop (recommended):
  - Download from https://www.docker.com/products/docker-desktop and follow install steps.
  - After installation, make sure Docker Desktop is running (the whale icon in the macOS menu bar). The `docker` CLI will be available in your shell.

- Use Homebrew to install `docker` client and `colima` as a lightweight VM (works well on Apple Silicon):

```bash
# install colima and docker CLI
brew install colima docker
colima start --cpu 4 --memory 8
# now docker build/run will use Colima VM
```

- Use Podman (drop-in replacement in many cases):

```bash
brew install podman
podman build -t pinescript-rag-server:latest .
podman run -p 8000:8000 --env-file .env pinescript-rag-server:latest
```

- If you don't want to install Docker locally, you can build images in CI (GitHub Actions) and push them to a registry (GitHub Container Registry, Docker Hub). See `.github/workflows/ci.yml` for a simple example.

## Alternative: run without Docker (recommended for quick local testing)

If installing Docker isn't convenient, use the `uvicorn` or `gunicorn` commands above to run the app directly in your venv.

## Health check & common operations

- Status: `GET /status`
- Trigger background indexing:

```bash
curl -X POST "http://localhost:8000/internal/index?background=true" -H "X-Admin-Key: $ADMIN_API_KEY"
```

- Chat call (requires JWT):

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"How do I create a SMA?","max_context_docs":4,"temperature":0.1}'
```

## Notes

- Ensure secrets (`SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, etc.) are stored securely and not committed to source control.
- For macOS Apple Silicon (M1/M2), prefer Docker Desktop or Colima; some images or dependencies may require platform args (e.g., `--platform linux/amd64`) though the base `python:3.11-slim` image used should work on `linux/arm64` as well.

If you want, I can create a `scripts/run.sh` to wrap common run commands, or add a `docker-compose.yml` for local development (with optional local Postgres for testing). Let me know which you prefer.
