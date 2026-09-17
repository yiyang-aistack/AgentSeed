# Security Policy

## Supported Versions

We actively maintain the following versions of AgentSeed:

| Version | Supported          | Notes                              |
| ------- | ------------------ | ---------------------------------- |
| 0.1.x   | ✅ Yes             | Current development branch         |
| < 0.1   | ❌ No              | Pre-release, no security support   |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, report them privately via one of the following channels:

- **Email**: [titanai@qq.com](mailto:titanai@qq.com) — please include "AgentSeed Security" in the subject line
- **GitHub Private Vulnerability Reporting**: If enabled on the repository, use the "Report a vulnerability" button on the Security tab

### What to include in your report

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any possible mitigations you've identified

### Expected response time

- We will acknowledge your report within **48 hours**
- We will aim to provide a triage status within **7 days**
- We take security seriously and will make every effort to resolve critical issues promptly

## Security Considerations for AgentSeed

AgentSeed is an AI Agent framework that handles API keys, external service credentials, and runs a local HTTP server. Please be aware of the following:

### API Key Management

- **Never commit real API keys** — `.env` is excluded from git via `.gitignore`, but always double-check before committing
- Keys live in `.env` → never paste them into issues, commit messages, or chat UI screenshots
- If you suspect a key has been exposed, **rotate it immediately** in the provider's dashboard
- `servers.yaml` uses `${VAR}` placeholders — this is intentional and correct practice

### Server Exposure

- Default `HOST=localhost` keeps the LangGraph API server local-only
- Setting `HOST=0.0.0.0` exposes it on your network — anyone reachable can call your graphs
- For production behind Docker, always put a reverse proxy (Nginx, Caddy) with auth/TLS in front
- The server currently has **no built-in authentication** — do not expose directly to the public internet

### Hermes Agent Bridge

- `API_SERVER_KEY` is a bearer token between AgentSeed and a local Hermes Agent
- This is **not a user-facing auth mechanism** — do not reuse it for anything else
- Keep `HERMES_BASE_URL` pointing to `127.0.0.1` unless you know what you're doing

### Docker & Deployment

- `Dockerfile` intentionally does **not** bake `.env` into the image — secrets must be injected at runtime
- `docker-compose.yml` ships only placeholder keys — replace via `env_file` with a real `.env`
- The in-memory LangGraph runtime (`LANGGRAPH_RUNTIME_EDITION=inmem`) does not persist data to disk — this is safe for demos but not for production

### Dependencies

- AgentSeed pins Python deps via `uv.lock` and frontend deps via `yarn.lock`
- CI runs on every push to catch lint/type issues before they land
- We do not yet have automated dependency update (Dependabot) — this is planned

## Best Practices for Users

1. Always run behind a firewall in production
2. Use `.env.example` as your template — never start from scratch
3. Keep `LOG_LEVEL=DEBUG` only during development
4. Run `uv sync && uv run ruff check` regularly to catch issues early
5. Monitor LangGraph API usage if pointing at paid LLM endpoints

## Security Updates

This policy may be updated from time to time. Significant changes will be noted in the repository's release notes and CHANGELOG (if any).
