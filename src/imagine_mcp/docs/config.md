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
| `relay_complete` | Persist relay submission to encrypted config.enc |
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
# -> {"session_id": "...", "url": "http://localhost:8001/...", "expires_in_seconds": 300}

config(action="relay_status")
# -> {"status": "pending"} or {"status": "done"}

config(action="relay_complete")
# -> {"status": "saved", "providers_configured": ["gemini", "openai", "grok"]}

config(action="status")
# -> {"credentials_state": "CONFIGURED", "providers_configured": [...], ...}
```

## Settable keys

- `log_level`: DEBUG | INFO | WARNING | ERROR
- `default_provider`: gemini | openai | grok
- `default_tier`: poor | rich
- `cache_ttl_seconds`: integer (0 = disable cache)

## Security

- Credentials stored in `config.enc` via mcp-core (AES-256-GCM, machine-bound key).
- Relay transport: ECDH P-256 key exchange + AES-256-GCM.
- API keys **never** appear in logs or error messages.
