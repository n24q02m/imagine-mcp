import sys
import re

with open('src/imagine_mcp/server.py', 'r') as f:
    content = f.read()

# Define helpers
helpers = """
def _config_open_relay() -> dict[str, Any]:
    from imagine_mcp import relay_setup
    import asyncio

    result = asyncio.run(relay_setup.ensure_config(force=True))
    if result is None:
        return {
            "status": "degraded",
            "message": (
                "No credentials loaded. Set MCP_RELAY_URL and retry, "
                "or run the server in `http local relay mode` (default)."
            ),
        }
    return {
        "status": "saved",
        "providers_configured": _providers_configured(),
    }


def _config_relay_status() -> dict[str, Any]:
    # Derive providers from live PerPluginStore + env so status
    # is accurate even when env vars were not populated at startup.
    _live_providers = _providers_configured_live()
    return {
        "status": "configured" if _live_providers else "pending",
        "providers_configured": _live_providers,
    }


def _config_relay_complete() -> dict[str, Any]:
    _live_providers = _providers_configured_live()
    return {
        "status": "saved" if _live_providers else "no_credentials",
        "providers_configured": _live_providers,
    }


def _config_relay_skip() -> dict[str, Any]:
    # Only claim "using env vars" when env vars are actually set.
    _env_providers = _providers_configured()
    if not _env_providers:
        return {
            "status": "needs_setup",
            "message": "No env vars set. Run config(action='open_relay') to configure via browser.",
        }
    return {
        "status": "using_env",
        "providers": _env_providers,
    }


def _config_relay_reset() -> dict[str, Any]:
    from imagine_mcp import relay_setup

    return relay_setup.reset_credentials()


def _config_warmup() -> dict[str, Any]:
    return {
        "status": "ok",
        "message": "No heavy resources to warm up in v1.",
    }


def _config_status() -> dict[str, Any]:
    return {
        "version": _get_version(),
        "credentials_state": _creds_state(),
        "providers_configured": _providers_configured(),
        "default_provider": settings.default_provider,
        "default_tier": settings.default_tier,
        "cache_ttl_seconds": settings.cache_ttl_seconds,
    }


def _config_cache_clear() -> dict[str, Any]:
    from imagine_mcp.cache import ResponseCache

    cache = ResponseCache(
        path=Path(platformdirs.user_cache_dir("imagine-mcp")) / "cache",
        default_ttl=settings.cache_ttl_seconds,
    )
    cache.clear()
    return {"status": "ok", "message": "Cache cleared."}
"""

# Insert helpers after _set_runtime
set_runtime_end = '    return {\n        "status": "ok",\n        "message": f"Set {key}={value} (runtime only; persistent via mcp-core).",\n    }'
content = content.replace(set_runtime_end, set_runtime_end + "\n" + helpers)

# Update config tool
new_config_body = """        match action:
            case "open_relay":
                return _config_open_relay()
            case "relay_status":
                return _config_relay_status()
            case "relay_complete":
                return _config_relay_complete()
            case "relay_skip":
                return _config_relay_skip()
            case "relay_reset":
                return _config_relay_reset()
            case "warmup":
                return _config_warmup()
            case "status":
                return _config_status()
            case "set":
                return _set_runtime(key, value)
            case "cache_clear":
                return _config_cache_clear()
            case _:
                return {
                    "status": "error",
                    "message": (
                        f"Unknown action {action!r}. Valid: open_relay|relay_status|"
                        "relay_skip|relay_reset|relay_complete|warmup|"
                        "status|set|cache_clear"
                    ),
                }"""

# Use regex to replace the config tool body
pattern = re.compile(r'(def config\(.*?\) -> dict\[str, Any\]:).*?(    @app\.tool)', re.DOTALL)

# Let's be more specific with the replacement to avoid matching other things
config_tool_start = '    def config(\n        action: str,\n        key: str | None = None,\n        value: str | None = None,\n    ) -> dict[str, Any]:\n        """Server config and credential management."""'
config_tool_end = '                    "status|set|cache_clear"\n                    ),\n                }'

# Find the start and end of the config function body
start_idx = content.find(config_tool_start)
if start_idx != -1:
    body_start = start_idx + len(config_tool_start)
    end_idx = content.find(config_tool_end, body_start)
    if end_idx != -1:
        body_end = end_idx + len(config_tool_end)
        content = content[:body_start] + "\n" + new_config_body + "\n" + content[body_end:]

with open('src/imagine_mcp/server.py', 'w') as f:
    f.write(content)
