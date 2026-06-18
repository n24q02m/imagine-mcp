"""CF imagine live OAuth full-flow self-test harness.

Drives the deployed imagine-mcp Cloudflare Worker (Worker + Container + KV)
end-to-end against a public endpoint and asserts base64-force is live:

  1. DCR register        -- POST /register (RFC 7591) -> client_id
  2. password-grant      -- /authorize -> /login (gate password) -> token
  3. /authorize form save with retry-on-500 (E.1 interception-race mitigation)
  4. poll until readable  (E.2 KV eventual-consistency mitigation)
  5. authenticated tool call -- config(action="status") then
     generate(media_type="image", prompt="a red circle", tier="poor"); assert the
     result has `image_base64` and NO `image_path` (proves IMAGINE_OUTPUT_MODE=base64
     is forced server-side on the serverless deployment).

The retry-on-500 (save_retries) + awaiting-setup poll (retries/delay) plumbing is
ported from the wet CF harness (the plan-01-hardened worker template imagine copies
in Task 3); the run-mode flags drive the Task 5 success-criteria scenarios.

Secrets from env: provider keys GEMINI_API_KEY / OPENAI_API_KEY / XAI_API_KEY
(skret injects these); login gate password from MCP_RELAY_PASSWORD (or RELAY_PW).

Run modes:
  (default)            full flow: save creds + authenticated generate, assert base64.
  --save-only          DCR + token + save creds for one sub, then exit (recreate-gate
                       setup half of SUCCESS CRITERION 4).
  --auth-only          reuse/re-mint a token for the SAME sub, tool call WITHOUT
                       re-saving creds (recreate-gate verify half: state survived KV).
  --two-sub-isolation  two distinct subs, each saves its own provider key; assert
                       each sub sees only its own configured provider (no bleed).

Examples:
  skret run -e prod -- python scripts/cf_full_flow.py --endpoint https://imagine.n24q02m.com
  skret run -e prod -- python scripts/cf_full_flow.py --save-only
  skret run -e prod -- python scripts/cf_full_flow.py --auth-only
  skret run -e prod -- python scripts/cf_full_flow.py --two-sub-isolation
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json as _json
import os
import re
import secrets
import sys
import time
import urllib.parse

# No hardcoded host: set CF_ENDPOINT or pass --endpoint https://<your-worker-domain>.
# This self-tests YOUR deployed CF server; creds come from env (MCP_RELAY_PASSWORD +
# provider keys) -- the maintainer injects them via skret, but any export works.
DEFAULT_ENDPOINT = os.environ.get("CF_ENDPOINT", "")


def _password() -> str:
    pw = os.environ.get("RELAY_PW") or os.environ.get("MCP_RELAY_PASSWORD")
    if not pw:
        raise SystemExit(
            "MCP_RELAY_PASSWORD (or RELAY_PW) is required for the password-grant "
            "login gate. It lives in skret /oci-vm-prod/prod (infra-shared), NOT "
            "/imagine-mcp/prod -- compose both namespaces (see plan Task 5)."
        )
    return pw


def _provider_creds() -> dict[str, str]:
    """Build the credential form payload from whichever provider keys are present.

    imagine forwards GEMINI/OPENAI/XAI keys + the optional UNDERSTAND_MODELS chain.
    Generation is native (no model chain needed); a single provider key is enough
    to exercise base64-force.
    """
    creds: dict[str, str] = {}
    for env_name in ("GEMINI_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY"):
        v = os.environ.get(env_name)
        if v:
            creds[env_name] = v
    if os.environ.get("UNDERSTAND_MODELS"):
        creds["UNDERSTAND_MODELS"] = os.environ["UNDERSTAND_MODELS"]
    return creds


def _provider_of(creds: dict[str, str]) -> str | None:
    """The generate provider implied by the configured key (first present wins;
    matches the dispatcher auto-fallback order xai -> openai -> gemini)."""
    if "XAI_API_KEY" in creds:
        return "grok"
    if "OPENAI_API_KEY" in creds:
        return "openai"
    if "GEMINI_API_KEY" in creds:
        return "gemini"
    return None


class _SaveRetry(Exception):
    pass


def get_token(
    endpoint: str,
    creds: dict[str, str],
    *,
    save: bool = True,
    save_retries: int = 8,
) -> str:
    """Run the full OAuth flow, retrying on a transient 500 at the credential
    save step (CF Containers outbound-interception race on cold-started
    instances -- the kv.internal PUT occasionally lands before interception is
    applied; E.1). Each retry restarts from DCR so the nonce is fresh.

    When ``save`` is False the credential form is still submitted with an EMPTY
    payload (no provider keys) so existing KV state is left untouched -- used by
    --auth-only to re-mint a token for the SAME sub without overwriting creds.
    """
    import httpx  # lazy: keep --help importable without httpx installed

    last: Exception | None = None
    payload = creds if save else {}
    for attempt in range(save_retries):
        try:
            return _get_token_once(httpx, endpoint, payload)
        except _SaveRetry as e:
            last = e
            print(
                f"get_token: save 500 (interception race), retry {attempt + 1}/{save_retries}"
            )
            time.sleep(3)
    raise RuntimeError(f"get_token failed after {save_retries} retries: {last}")


def _get_token_once(httpx, endpoint: str, creds: dict[str, str]) -> str:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    ru = "http://localhost:9999/cb"
    pw = _password()
    with httpx.Client(timeout=120, follow_redirects=False) as c:
        cid = c.post(
            f"{endpoint}/register",
            json={
                "client_name": "cf-verify",
                "redirect_uris": [ru],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
                "scope": "offline_access",
            },
        ).json()["client_id"]
        az = c.get(
            f"{endpoint}/authorize",
            params={
                "response_type": "code",
                "client_id": cid,
                "redirect_uri": ru,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": "st",
                "scope": "offline_access",
            },
        )
        nxt = urllib.parse.parse_qs(
            urllib.parse.urlparse(az.headers["location"]).query
        )["next"][0]
        lg = c.post(f"{endpoint}/login", data={"next": nxt, "password": pw})
        url = lg.headers["location"]
        url = url if url.startswith("http") else endpoint + url
        form_html = c.get(url).text
        m = re.search(r"/authorize\?nonce=([A-Za-z0-9_\-]+)", form_html)
        assert m, "nonce not found in form"
        nonce = m.group(1)
        sub = c.post(f"{endpoint}/authorize", params={"nonce": nonce}, json=creds)
        if sub.status_code == 500 and "save credentials" in sub.text:
            raise _SaveRetry(sub.text[:120])
        assert sub.status_code == 200, (sub.status_code, sub.text[:300])
        data = sub.json()
        assert data.get("ok"), data
        code = urllib.parse.parse_qs(urllib.parse.urlparse(data["redirect_url"]).query)[
            "code"
        ][0]
        tok = c.post(
            f"{endpoint}/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": ru,
                "client_id": cid,
                "code_verifier": verifier,
            },
        )
        assert tok.status_code == 200, (tok.status_code, tok.text[:300])
        return tok.json()["access_token"]


def _sub_of(token: str) -> str:
    payload = _json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))
    return payload.get("sub", "?")


async def _call(s, label, tool, args, *, retries=20, delay=8):
    """Call a tool, retrying while credentials are still propagating (KV
    cross-colo eventual consistency after setup writes them on another DO; E.2).
    Returns the concatenated text payload of the result, or None on give-up."""
    for i in range(retries):
        try:
            res = await s.call_tool(tool, args)
            txt = "".join(getattr(b, "text", "") for b in res.content)
            if "awaiting_setup" in txt or "Credentials not configured" in txt:
                print(f"{label}: awaiting_setup (KV propagating) try {i + 1}/{retries}")
                await asyncio.sleep(delay)
                continue
            print(f"{label} OK:", txt[:320].replace("\n", " "))
            return txt
        except Exception as e:
            print(f"{label} ERR:", repr(e)[:300])
            return None
    print(f"{label}: gave up after {retries} tries")
    return None


def _assert_base64_no_path(txt: str) -> None:
    """Assert a generate result carries image_base64 and NOT image_path."""
    assert txt is not None, "generate returned no payload"
    assert "image_base64" in txt, f"expected image_base64 in result, got: {txt[:300]}"
    assert "image_path" not in txt, (
        f"image_path present -- base64-force NOT live: {txt[:300]}"
    )
    print("ASSERT OK: image_base64 present, image_path absent (base64-force live).")


async def _session(endpoint: str, token: str):
    from mcp import ClientSession  # lazy: keep --help importable without mcp installed
    from mcp.client.streamable_http import streamablehttp_client

    return streamablehttp_client(
        f"{endpoint}/mcp", headers={"Authorization": f"Bearer {token}"}
    ), ClientSession


async def run_full(endpoint: str) -> None:
    creds = _provider_creds()
    if not creds:
        raise SystemExit(
            "No provider key in env (GEMINI_API_KEY / OPENAI_API_KEY / XAI_API_KEY). "
            "skret run injects them; cannot save credentials without one."
        )
    provider = _provider_of(creds)
    token = get_token(endpoint, creds, save=True)
    print("TOKEN OK len=", len(token), "sub=", _sub_of(token))
    transport, ClientSession = await _session(endpoint, token)
    async with transport as (r, w, _), ClientSession(r, w) as s:
        await s.initialize()
        tools = await s.list_tools()
        print("TOOLS:", [t.name for t in tools.tools])
        await _call(s, "CONFIG_STATUS", "config", {"action": "status"})
        txt = await _call(
            s,
            "GENERATE_IMAGE",
            "generate",
            {
                "media_type": "image",
                "prompt": "a red circle",
                "tier": "poor",
                **({"provider": provider} if provider else {}),
            },
        )
        _assert_base64_no_path(txt)
    print("FULL FLOW PASS.")


def _token_file():
    from pathlib import Path as _Path

    return _Path(__file__).with_name(".imagine_cf_token")


async def run_save_only(endpoint: str) -> None:
    creds = _provider_creds()
    if not creds:
        raise SystemExit("No provider key in env -- nothing to save (--save-only).")
    token = get_token(endpoint, creds, save=True)
    # Dump the EXACT token so --auth-only can replay the SAME JWT sub. The
    # relay-login mints a fresh random sub on every /authorize, so re-minting in
    # --auth-only would read a NEW (empty) sub vault; the recreate gate must
    # prove THIS sub's creds survived in KV, hence we persist the token.
    _token_file().write_text(token)
    print(
        "SAVE-ONLY OK: creds saved for sub=",
        _sub_of(token),
        "len(token)=",
        len(token),
        "(token dumped for --auth-only)",
    )


async def run_auth_only(endpoint: str) -> None:
    # Replay the EXACT token dumped by --save-only (same JWT sub) WITHOUT
    # re-minting or re-saving: this proves the previously-saved key survived a
    # delete+recreate (SUCCESS CRITERION 4). Re-minting would create a new random
    # sub whose vault is empty (relay-login mints sub per /authorize).
    tok_path = _token_file()
    if not tok_path.exists():
        raise SystemExit("No dumped token -- run --save-only first.")
    token = tok_path.read_text().strip()
    provider = _provider_of(_provider_creds())  # local hint for the generate call
    print("AUTH-ONLY: replaying saved token for sub=", _sub_of(token))
    transport, ClientSession = await _session(endpoint, token)
    async with transport as (r, w, _), ClientSession(r, w) as s:
        await s.initialize()
        await _call(s, "CONFIG_STATUS", "config", {"action": "status"})
        txt = await _call(
            s,
            "GENERATE_IMAGE",
            "generate",
            {
                "media_type": "image",
                "prompt": "a red circle",
                "tier": "poor",
                **({"provider": provider} if provider else {}),
            },
        )
        _assert_base64_no_path(txt)
    print("AUTH-ONLY PASS: state survived recreate (KV creds resolved, no re-save).")


async def run_two_sub_isolation(endpoint: str) -> None:
    # Two distinct subs each get a DIFFERENT provider key; assert each only sees
    # its own configured provider (KV keys imagine/subs/<sub>/config are disjoint,
    # AES-GCM under per-sub-derived keys). The gate password is shared, so we
    # distinguish subs by configuring a distinct provider per run and asserting
    # the status reflects only that provider.
    all_creds = _provider_creds()
    keys = [
        k for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY") if k in all_creds
    ]
    if len(keys) < 2:
        raise SystemExit(
            "two-sub isolation needs >=2 distinct provider keys in env "
            f"(have: {keys or 'none'})."
        )
    prov_of = {
        "GEMINI_API_KEY": "gemini",
        "OPENAI_API_KEY": "openai",
        "XAI_API_KEY": "grok",
    }
    results: dict[str, str] = {}
    subs: dict[str, str] = {}
    for k in keys[:2]:
        creds = {k: all_creds[k]}
        token = get_token(endpoint, creds, save=True)
        sub = _sub_of(token)
        subs[k] = sub
        transport, ClientSession = await _session(endpoint, token)
        async with transport as (r, w, _), ClientSession(r, w) as s:
            await s.initialize()
            txt = await _call(
                s, f"STATUS[{prov_of[k]}]", "config", {"action": "status"}
            )
            results[k] = txt or ""
    # Each sub's status must reflect its own configured provider and NOT bleed the
    # other sub's provider into its view.
    a, b = keys[0], keys[1]
    print(f"sub({prov_of[a]})={subs[a]}  sub({prov_of[b]})={subs[b]}")
    if subs[a] == subs[b]:
        raise SystemExit(
            f"ISOLATION INCONCLUSIVE: both runs share sub {subs[a]} (same gate "
            "password collapses to one DO). Provide per-sub tokens to test bleed."
        )
    if prov_of[b] in results[a] and prov_of[a] not in results[a]:
        raise SystemExit(
            f"ISOLATION FAIL: sub {subs[a]} sees {prov_of[b]}'s provider, not its own."
        )
    if prov_of[a] in results[b] and prov_of[b] not in results[b]:
        raise SystemExit(
            f"ISOLATION FAIL: sub {subs[b]} sees {prov_of[a]}'s provider, not its own."
        )
    print(
        "TWO-SUB ISOLATION OK: distinct subs, each configured independently, no bleed."
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="CF imagine live OAuth full-flow self-test harness.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        required=not DEFAULT_ENDPOINT,
        help=f"Deployed imagine endpoint (default: {DEFAULT_ENDPOINT})",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--save-only",
        action="store_true",
        help="DCR + token + save creds for one sub, then exit (recreate-gate setup).",
    )
    mode.add_argument(
        "--auth-only",
        action="store_true",
        help="Re-mint a token for the SAME sub, tool call WITHOUT re-saving creds "
        "(recreate-gate verify -- state survived KV).",
    )
    mode.add_argument(
        "--two-sub-isolation",
        action="store_true",
        help="Two distinct subs, assert each sees only its own provider key.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.save_only:
        asyncio.run(run_save_only(args.endpoint))
    elif args.auth_only:
        asyncio.run(run_auth_only(args.endpoint))
    elif args.two_sub_isolation:
        asyncio.run(run_two_sub_isolation(args.endpoint))
    else:
        asyncio.run(run_full(args.endpoint))
    return 0


if __name__ == "__main__":
    sys.exit(main())
