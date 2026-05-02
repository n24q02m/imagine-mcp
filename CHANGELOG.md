# CHANGELOG

<!-- version list -->

## v1.2.0-beta.5 (2026-05-02)

### Bug Fixes

- Imagine auto-fallback provider when default API key missing
  ([#58](https://github.com/n24q02m/imagine-mcp/pull/58),
  [`86a0b51`](https://github.com/n24q02m/imagine-mcp/commit/86a0b517029002f880294f282ab0ee1471e96029))


## v1.2.0-beta.4 (2026-05-02)

### Bug Fixes

- Gate PerPluginStore reads behind HTTP mode (stdio = env-only)
  ([#57](https://github.com/n24q02m/imagine-mcp/pull/57),
  [`015faaa`](https://github.com/n24q02m/imagine-mcp/commit/015faaad32fa1563f174981e6b30b75fb81013fa))


## v1.2.0-beta.3 (2026-05-02)

### Bug Fixes

- Register_open_relay_tool signature for mcp-core 1.13
  ([#55](https://github.com/n24q02m/imagine-mcp/pull/55),
  [`4455b1b`](https://github.com/n24q02m/imagine-mcp/commit/4455b1b78f0444f29f1db287172695100af76270))

- Setup docs + README reflect stdio-pure architecture
  ([#56](https://github.com/n24q02m/imagine-mcp/pull/56),
  [`0002916`](https://github.com/n24q02m/imagine-mcp/commit/0002916293855a4bd0af97e72204f1413da84544))

### Features

- Stdio-pure + http-multi-user (drop daemon-bridge)
  ([#55](https://github.com/n24q02m/imagine-mcp/pull/55),
  [`4455b1b`](https://github.com/n24q02m/imagine-mcp/commit/4455b1b78f0444f29f1db287172695100af76270))


## v1.2.0-beta.2 (2026-04-30)

### Bug Fixes

- G6 UX relay_status accuracy and relay_skip honesty
  ([#47](https://github.com/n24q02m/imagine-mcp/pull/47),
  [`f87d462`](https://github.com/n24q02m/imagine-mcp/commit/f87d4629d4172618c1dc14a747be52ed4d5b82fa))

- **lint**: Use X | None syntax, remove unused import per ruff UP045/F401
  ([#45](https://github.com/n24q02m/imagine-mcp/pull/45),
  [`80d9fc2`](https://github.com/n24q02m/imagine-mcp/commit/80d9fc2ea4d8ae0d759f15bac79e98587bdeff78))

### Features

- **docs**: Add trust model section to README
  ([#46](https://github.com/n24q02m/imagine-mcp/pull/46),
  [`68882d4`](https://github.com/n24q02m/imagine-mcp/commit/68882d48f822fb5bff4b9d9a4d3c85166ea83c69))

- **storage**: Migrate to PerPluginStore from mcp-core 1.13.0b1+
  ([#45](https://github.com/n24q02m/imagine-mcp/pull/45),
  [`80d9fc2`](https://github.com/n24q02m/imagine-mcp/commit/80d9fc2ea4d8ae0d759f15bac79e98587bdeff78))


## v1.2.0-beta.1 (2026-04-30)

### Features

- Route stdio mode to FastMCP direct + multi-target Dockerfile
  ([#43](https://github.com/n24q02m/imagine-mcp/pull/43),
  [`f524ef2`](https://github.com/n24q02m/imagine-mcp/commit/f524ef2111e5f317ec9ff5bbec465e3e9401032f))


## v1.1.4 (2026-04-29)

### Bug Fixes

- Bump n24q02m-mcp-core to 1.11.3 for D17 tools cache refresh
  ([#38](https://github.com/n24q02m/imagine-mcp/pull/38),
  [`8b84cf1`](https://github.com/n24q02m/imagine-mcp/commit/8b84cf15077e9ac32dbea9c458aa951af826c779))


## v1.1.3 (2026-04-29)

### Bug Fixes

- Pin Python to ==3.13.* for pin parity (D13)
  ([#32](https://github.com/n24q02m/imagine-mcp/pull/32),
  [`5842c73`](https://github.com/n24q02m/imagine-mcp/commit/5842c735a24dc2821ec033724e91f2e3bbe87717))

- Register config__open_relay tool (Transparent Bridge Wave 3)
  ([#34](https://github.com/n24q02m/imagine-mcp/pull/34),
  [`c5be7ae`](https://github.com/n24q02m/imagine-mcp/commit/c5be7ae6c3717926c3b30ba8d141a9eec747b8f7))


## v1.1.2 (2026-04-28)

### Bug Fixes

- Align setup-manual env example with GEMINI_API_KEY rename
  ([#28](https://github.com/n24q02m/imagine-mcp/pull/28),
  [`70ffa3b`](https://github.com/n24q02m/imagine-mcp/commit/70ffa3baddcb50a722f17561b1422fb828b78173))

- Pass MCP_TRANSPORT=stdio in plugin.json ([#29](https://github.com/n24q02m/imagine-mcp/pull/29),
  [`2f90a96`](https://github.com/n24q02m/imagine-mcp/commit/2f90a96cc0431f7f32fc62ac86a728e21b05f356))

- **deps**: Bump n24q02m-mcp-core to 1.10.0 — Transparent Bridge waves 1-3
  ([#31](https://github.com/n24q02m/imagine-mcp/pull/31),
  [`a8fe1ec`](https://github.com/n24q02m/imagine-mcp/commit/a8fe1ec7ca28abc8813f1384a967a16809b0d02d))


## v1.1.1 (2026-04-28)

### Bug Fixes

- Bump n24q02m-mcp-core to 1.9.0 ([#27](https://github.com/n24q02m/imagine-mcp/pull/27),
  [`2f619f2`](https://github.com/n24q02m/imagine-mcp/commit/2f619f216fb6b859084f6241e7db555161f51217))


## v1.1.0 (2026-04-27)

### Bug Fixes

- Bump n24q02m-mcp-core to 1.8.0 ([#21](https://github.com/n24q02m/imagine-mcp/pull/21),
  [`aa78edf`](https://github.com/n24q02m/imagine-mcp/commit/aa78edf556ca7232a6f80e50f781795dfa057dfe))

### Features

- Add ## E2E section to CLAUDE.md per Task 21 docs rollout
  ([#21](https://github.com/n24q02m/imagine-mcp/pull/21),
  [`aa78edf`](https://github.com/n24q02m/imagine-mcp/commit/aa78edf556ca7232a6f80e50f781795dfa057dfe))

- Add ## E2E section to CLAUDE.md per Task 21 docs rollout
  ([#19](https://github.com/n24q02m/imagine-mcp/pull/19),
  [`c64f07c`](https://github.com/n24q02m/imagine-mcp/commit/c64f07c3edbce5b88e5413302c1dec871ebc0c32))


## v1.1.0-beta.1 (2026-04-27)

### Features

- GEMINI_API_KEY rename + per-JWT-sub LLM keys
  ([#18](https://github.com/n24q02m/imagine-mcp/pull/18),
  [`62ae0b7`](https://github.com/n24q02m/imagine-mcp/commit/62ae0b789cb46d3087c7871cea883bb32f9b5ffe))

- Imagine-mcp per-JWT-sub LLM keys for multi-user remote mode
  ([#18](https://github.com/n24q02m/imagine-mcp/pull/18),
  [`62ae0b7`](https://github.com/n24q02m/imagine-mcp/commit/62ae0b789cb46d3087c7871cea883bb32f9b5ffe))

- Rename GOOGLE_AI_STUDIO_API_KEY to GEMINI_API_KEY for parity with wet/mnemo/crg
  ([#18](https://github.com/n24q02m/imagine-mcp/pull/18),
  [`62ae0b7`](https://github.com/n24q02m/imagine-mcp/commit/62ae0b789cb46d3087c7871cea883bb32f9b5ffe))


## v1.0.2 (2026-04-24)

### Bug Fixes

- Wire on_credentials_saved into run_local_server
  ([#11](https://github.com/n24q02m/imagine-mcp/pull/11),
  [`031ae63`](https://github.com/n24q02m/imagine-mcp/commit/031ae63c4b1d3f170264b57884cf554025ebd45f))


## v1.0.1 (2026-04-24)

### Bug Fixes

- Add http remote relay self-host mode + properly await run_local_server
  ([`f7a1645`](https://github.com/n24q02m/imagine-mcp/commit/f7a1645128d5b6ba6af3843c633f2e8ca1321684))

- Align repo manifests with wet-mcp Tier 1 Flagship parity
  ([`2314387`](https://github.com/n24q02m/imagine-mcp/commit/2314387255fa00ad001f19b23eae391df6a8794d))

- Align stdio mode with mcp-core run_smart_stdio_proxy for sibling parity
  ([`f8037dc`](https://github.com/n24q02m/imagine-mcp/commit/f8037dc5884063c4ea2703fdcebec27b5498821f))

- Bump n24q02m-mcp-core to 1.7.6 ([#10](https://github.com/n24q02m/imagine-mcp/pull/10),
  [`3785b58`](https://github.com/n24q02m/imagine-mcp/commit/3785b58bdcc21b35c77087ff703d43759759342b))

- Harden .pre-commit-config.yaml to wet-mcp baseline
  ([`679fbce`](https://github.com/n24q02m/imagine-mcp/commit/679fbce08f85a60f9fba09cfd29da07068d30e7c))

- Rewrite README + CONTRIBUTING to Tier 1 Flagship MCP baseline
  ([`6104c8f`](https://github.com/n24q02m/imagine-mcp/commit/6104c8f043d0e12f3ee715f5ee9623f43d055b88))


## v1.0.0 (2026-04-24)


## v1.0.0-beta.3 (2026-04-24)

### Bug Fixes

- Remove wheel force-include and whitelist README.md in .dockerignore
  ([`8af6f76`](https://github.com/n24q02m/imagine-mcp/commit/8af6f7613f331a1903b37b8b9115cbeaee10c15b))


## v1.0.0-beta.2 (2026-04-24)

### Bug Fixes

- Rewrite Dockerfile with COPY-first pattern so hatchling finds README.md
  ([`32456c5`](https://github.com/n24q02m/imagine-mcp/commit/32456c5a420282396bc0976f650e784c5cbf405f))


## v1.0.0-beta.1 (2026-04-24)

- Initial Release
