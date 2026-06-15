# config tool

Credential setup and runtime configuration -- merged into one tool per 2026-04-18 standard.

## Signature

```python
config(
    action: str,
    key: str | None = None,
    value: str | None = None,
) -> dict
```

## Actions

### Credential / relay

| Action | Purpose |
|--------|---------|
| `open_relay` | Start relay session; server opens browser with credential form |
| `relay_status` | Poll current relay session status |
| `relay_complete` | Persist relay submission to the encrypted per-plugin store (`~/.imagine-mcp/config.json`) |
| `relay_skip` | Skip relay; rely on env vars only |
| `relay_reset` | Delete stored credentials (forces re-setup) |
| `warmup` | Pre-load heavy resources (no-op in v1) |

### Runtime

| Action | Purpose |
|--------|---------|
| `status` | Show current config + credential state + model versions |
| `set` | Update setting (requires `key` and `value`) |
| `cache_clear` | Wipe response cache |

## Example flow

```python
# First-time setup
config(action="open_relay")
# -> {"status": "saved", "providers_configured": [...]} or {"status": "degraded", "message": "..."}

config(action="relay_status")
# -> {"status": "pending", "providers_configured": []} or {"status": "configured", "providers_configured": [...]}

config(action="relay_complete")
# -> {"status": "saved", "providers_configured": ["gemini", "openai", "grok"]} or {"status": "no_credentials", "providers_configured": []}

config(action="status")
# -> {"credentials_state": "CONFIGURED", "providers_configured": [...], ...}
```

## Settable keys

- `log_level`: DEBUG | INFO | WARNING | ERROR
- `default_provider`: gemini | openai | grok
- `default_tier`: poor | rich
- `cache_ttl_seconds`: integer (0 = disable cache)

## Security

- Credentials stored in `~/.imagine-mcp/config.json` via mcp-core (AES-256-GCM, machine-bound key); multi-user HTTP mode scopes them per JWT subject under `~/.imagine-mcp/subs/<sub>/config.json` (AES-256-GCM, PBKDF2 key from `CREDENTIAL_SECRET`).
- Setup transport: in HTTP mode credentials are entered through the browser credential form served by the mcp-core OAuth Authorization Server (`/authorize`).
- API keys **never** appear in logs or error messages.
