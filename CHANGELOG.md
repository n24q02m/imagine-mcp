# CHANGELOG

<!-- version list -->

## v1.6.1-beta.1 (2026-06-09)

### Bug Fixes

- Fix ssl validation failure during dns pinning
  ([#262](https://github.com/n24q02m/imagine-mcp/pull/262),
  [`69b6a09`](https://github.com/n24q02m/imagine-mcp/commit/69b6a098a3b79e5e65204fee91ab0848e527f604))

- Gitignore bot/merge junk artifacts (*.orig/*.rej/*.patch/*.diff/*.cover/*.bak)
  ([#246](https://github.com/n24q02m/imagine-mcp/pull/246),
  [`b4ff03d`](https://github.com/n24q02m/imagine-mcp/commit/b4ff03de07f424bc5252b4601d502f97d6a57e3b))

- 🔒 [SECURITY] fix ssl validation when rewriting requests to ips
  ([#262](https://github.com/n24q02m/imagine-mcp/pull/262),
  [`69b6a09`](https://github.com/n24q02m/imagine-mcp/commit/69b6a098a3b79e5e65204fee91ab0848e527f604))

- **deps**: Update non-major dependencies ([#248](https://github.com/n24q02m/imagine-mcp/pull/248),
  [`037beae`](https://github.com/n24q02m/imagine-mcp/commit/037beaed05a7fe7f8f2e43c67c43832d493cdffd))


## v1.6.0 (2026-06-07)

### Bug Fixes

- Apply ruff format to SSRF regression tests
  ([#244](https://github.com/n24q02m/imagine-mcp/pull/244),
  [`23bd17d`](https://github.com/n24q02m/imagine-mcp/commit/23bd17daf342eff9d26b152bd042c723a36597c7))

- Pin httpx <1 to lock SSRFSafeTransport sni_hostname behavior + add SSRF regression tests
  ([#244](https://github.com/n24q02m/imagine-mcp/pull/244),
  [`23bd17d`](https://github.com/n24q02m/imagine-mcp/commit/23bd17daf342eff9d26b152bd042c723a36597c7))

- Report real package version in serverInfo.version
  ([#244](https://github.com/n24q02m/imagine-mcp/pull/244),
  [`23bd17d`](https://github.com/n24q02m/imagine-mcp/commit/23bd17daf342eff9d26b152bd042c723a36597c7))


## v1.6.0-beta.2 (2026-06-07)

### Bug Fixes

- Apply ruff format to SSRF regression tests
  ([#243](https://github.com/n24q02m/imagine-mcp/pull/243),
  [`3fefe6c`](https://github.com/n24q02m/imagine-mcp/commit/3fefe6cfb4789fdeacb34c50117c4e5e57c460bc))

- Pin httpx <1 + SSRF regression tests for SSRFSafeTransport
  ([#243](https://github.com/n24q02m/imagine-mcp/pull/243),
  [`3fefe6c`](https://github.com/n24q02m/imagine-mcp/commit/3fefe6cfb4789fdeacb34c50117c4e5e57c460bc))

- Pin httpx <1 to lock SSRFSafeTransport sni_hostname behavior + add SSRF regression tests
  ([#243](https://github.com/n24q02m/imagine-mcp/pull/243),
  [`3fefe6c`](https://github.com/n24q02m/imagine-mcp/commit/3fefe6cfb4789fdeacb34c50117c4e5e57c460bc))


## v1.6.0-beta.1 (2026-06-07)

### Bug Fixes

- Add tests for credentials_for_current_request
  ([`d712f0c`](https://github.com/n24q02m/imagine-mcp/commit/d712f0cb84839fe9bb5ed54b0d2ec6a77bbf32bd))

- Add tests for download_to_path
  ([`fadcf15`](https://github.com/n24q02m/imagine-mcp/commit/fadcf1538282f87f22205f293eee708d439bd0fa))

- Cache static help markdown reads
  ([`a79cd90`](https://github.com/n24q02m/imagine-mcp/commit/a79cd900561d12c863b2bc2ffb31b4ac1e310155))

- Clear help-content cache after test to prevent cross-test pollution
  ([`05ddf94`](https://github.com/n24q02m/imagine-mcp/commit/05ddf94fd722d139d2db7de91d4eb036e380bb46))

- Update actions/checkout digest to df4cb1c (Renovate)
  ([`b2041ab`](https://github.com/n24q02m/imagine-mcp/commit/b2041ab3f4dae2508f87ca0e1682a678483b97ba))

- Update non-major dependencies (Renovate)
  ([`3929f0f`](https://github.com/n24q02m/imagine-mcp/commit/3929f0f49c267b02407ef641bc50b8a8c19b593d))

### Features

- Add comprehensive server.py test coverage
  ([`0e266df`](https://github.com/n24q02m/imagine-mcp/commit/0e266df1698513a845e9b711349d8079b8cbfac5))


## v1.5.4 (2026-06-01)

### Bug Fixes

- Pin mcp-core 1.17.2 (stable)
  ([`f88d7e8`](https://github.com/n24q02m/imagine-mcp/commit/f88d7e88284eafea016bf5c74a05cbad99fe817b))


## v1.5.4-beta.2 (2026-06-01)

### Bug Fixes

- Detect real image mime type for Gemini vision instead of hardcoding image/png
  ([#202](https://github.com/n24q02m/imagine-mcp/pull/202),
  [`84c05f0`](https://github.com/n24q02m/imagine-mcp/commit/84c05f0cafc204f5fbe2a6bbd5e0a97b7233d9a5))


## v1.5.4-beta.1 (2026-06-01)

### Bug Fixes

- Bump mcp-core to 1.17.2-beta.1 for beta testing
  ([`8499066`](https://github.com/n24q02m/imagine-mcp/commit/84990669202cf5a10ee23b4d216d994366c80efd))

- Correct stale transport-mode docs and degraded-mode warning
  ([#201](https://github.com/n24q02m/imagine-mcp/pull/201),
  [`661ca85`](https://github.com/n24q02m/imagine-mcp/commit/661ca8547dfeed4a41fa11904fedef265073f49a))

- Sync docs to code (provider default None, GEMINI_API_KEY env name, drop dead setup-manual link)
  ([#200](https://github.com/n24q02m/imagine-mcp/pull/200),
  [`0c62573`](https://github.com/n24q02m/imagine-mcp/commit/0c625738736f06dc4da036fbce5f0caa5c7a3e62))

- Update non-major dependencies ([#191](https://github.com/n24q02m/imagine-mcp/pull/191),
  [`07f5d22`](https://github.com/n24q02m/imagine-mcp/commit/07f5d220e290b15fb4ae0f656933b2b96e95f2f3))


## v1.5.3 (2026-05-29)

### Bug Fixes

- Pin mcp-core 1.17.1 (BearerMCPApp resource_metadata #260)
  ([`1329edc`](https://github.com/n24q02m/imagine-mcp/commit/1329edc4071ad3d58a97e5996376ddb86c6223fc))


## v1.5.2 (2026-05-29)

### Bug Fixes

- Pin mcp-core 1.17.0 (stable OAuth refresh_token)
  ([`cbaf210`](https://github.com/n24q02m/imagine-mcp/commit/cbaf2106eba2a8372454686d14c9563c08a2a635))


## v1.5.2-beta.1 (2026-05-29)

### Bug Fixes

- Add gemini generate_image missing-data error tests
  ([#163](https://github.com/n24q02m/imagine-mcp/pull/163),
  [`8133615`](https://github.com/n24q02m/imagine-mcp/commit/813361535637947bf5b9f2818e3e0313551db747))

- Add SSRF protection to grok provider API client
  ([#186](https://github.com/n24q02m/imagine-mcp/pull/186),
  [`3e00e01`](https://github.com/n24q02m/imagine-mcp/commit/3e00e01aee9b145ece1853846f71784642f794dd))

- Add understand_multimodal mocked tests ([#169](https://github.com/n24q02m/imagine-mcp/pull/169),
  [`a5e6460`](https://github.com/n24q02m/imagine-mcp/commit/a5e6460d3afd9fafba39c94e71abcaf480f77674))

- Bump mcp-core to 1.17.0-beta.1 for OAuth refresh_token
  ([`8f68137`](https://github.com/n24q02m/imagine-mcp/commit/8f681377132085f14f667af2440bce17414763ec))


## v1.5.1 (2026-05-28)


## v1.5.1-beta.1 (2026-05-28)

### Bug Fixes

- 🛡️ sentinel: fix path traversal vulnerability in grok provider
  ([#156](https://github.com/n24q02m/imagine-mcp/pull/156),
  [`553bacc`](https://github.com/n24q02m/imagine-mcp/commit/553bacc85398af5a54cff216ca9baa030e056ccd))

- **deps**: Pin pydantic to <2.13 to match mcp-core 1.15.0 transitive cap
  ([`62cba02`](https://github.com/n24q02m/imagine-mcp/commit/62cba023bc6aa4947bce224a316d857895d15d4c))

- **deps**: Update non-major dependencies ([#157](https://github.com/n24q02m/imagine-mcp/pull/157),
  [`60b9eb3`](https://github.com/n24q02m/imagine-mcp/commit/60b9eb33c6e8dde6b50d02ed3d835394aad29b87))


## v1.5.0 (2026-05-26)


## v1.5.0-beta.3 (2026-05-26)

### Features

- Wire MCP_AUTH_DISABLE env to run_http_server(auth_disabled=)
  ([`79ae89d`](https://github.com/n24q02m/imagine-mcp/commit/79ae89d22a3f406c8d9eab37d0db258542e54828))


## v1.5.0-beta.2 (2026-05-26)

### Features

- Add MCP_AUTH_DISABLE env flag for external auth boundary
  ([`053ab6e`](https://github.com/n24q02m/imagine-mcp/commit/053ab6e0a32f41dd0e65b0a5ada7e3af60fbfa5e))


## v1.5.0-beta.1 (2026-05-24)

### Bug Fixes

- Add uv.lock security-floor guard test ([#139](https://github.com/n24q02m/imagine-mcp/pull/139),
  [`8e6fb7b`](https://github.com/n24q02m/imagine-mcp/commit/8e6fb7ba58e1c903de0742b455153c335a1bb245))

- Bump pinned CI action digests and add relay/entrypoint tests
  ([#139](https://github.com/n24q02m/imagine-mcp/pull/139),
  [`8e6fb7b`](https://github.com/n24q02m/imagine-mcp/commit/8e6fb7ba58e1c903de0742b455153c335a1bb245))

- Patch dependency CVEs, bump CI action digests, add test coverage
  ([#139](https://github.com/n24q02m/imagine-mcp/pull/139),
  [`8e6fb7b`](https://github.com/n24q02m/imagine-mcp/commit/8e6fb7ba58e1c903de0742b455153c335a1bb245))

- Pin urllib3 and idna floors to patch dependency CVEs
  ([#139](https://github.com/n24q02m/imagine-mcp/pull/139),
  [`8e6fb7b`](https://github.com/n24q02m/imagine-mcp/commit/8e6fb7ba58e1c903de0742b455153c335a1bb245))

- Resolve SSRF vulnerability in Grok provider by using SSRFSafeTransport
  ([#132](https://github.com/n24q02m/imagine-mcp/pull/132),
  [`6288edc`](https://github.com/n24q02m/imagine-mcp/commit/6288edca4c2cd41cb7391a20a69f06389efdd3ba))

- 🛡️ sentinel: support ipv6 resolution in ssrf filter
  ([#147](https://github.com/n24q02m/imagine-mcp/pull/147),
  [`b81b5cc`](https://github.com/n24q02m/imagine-mcp/commit/b81b5cca0b8b0258f52a95c6152b4983a0f8dda7))

- **ci**: Add PR title check via amannn/action-semantic-pull-request
  ([#108](https://github.com/n24q02m/imagine-mcp/pull/108),
  [`3d0983f`](https://github.com/n24q02m/imagine-mcp/commit/3d0983f8c895b2a9531698e27a84254c439f72ef))

- **deps**: Pin pydantic <2.13 for mcp-core 1.14.0 compatibility
  ([#118](https://github.com/n24q02m/imagine-mcp/pull/118),
  [`de818a7`](https://github.com/n24q02m/imagine-mcp/commit/de818a74e7221ed57cecaf87b81944185016b822))

- **deps**: Update non-major dependencies ([#118](https://github.com/n24q02m/imagine-mcp/pull/118),
  [`de818a7`](https://github.com/n24q02m/imagine-mcp/commit/de818a74e7221ed57cecaf87b81944185016b822))

- **security**: Route Grok provider calls through SSRF-safe client and gate bind host
  ([#132](https://github.com/n24q02m/imagine-mcp/pull/132),
  [`6288edc`](https://github.com/n24q02m/imagine-mcp/commit/6288edca4c2cd41cb7391a20a69f06389efdd3ba))

### Features

- ⚡ bolt: optimize media type detection concurrency
  ([`30ff068`](https://github.com/n24q02m/imagine-mcp/commit/30ff0688fd26ebf1c3b2ea61a9e3b0bfda3b0698))


## v1.4.0 (2026-05-09)


## v1.4.0-beta.1 (2026-05-08)

### Bug Fixes

- Resolve TOCTOU SSRF via DNS pinning and secure media fetching
  ([#96](https://github.com/n24q02m/imagine-mcp/pull/96),
  [`2bc6657`](https://github.com/n24q02m/imagine-mcp/commit/2bc6657a57cc158adb667bddffa7c4d8f1ce316f))

- Resolve TOCTOU SSRF via DNS pinning and secure media fetching (fix lint)
  ([#96](https://github.com/n24q02m/imagine-mcp/pull/96),
  [`2bc6657`](https://github.com/n24q02m/imagine-mcp/commit/2bc6657a57cc158adb667bddffa7c4d8f1ce316f))

- Resolve TOCTOU SSRF via DNS pinning and secure media fetching (fix type hinting)
  ([#96](https://github.com/n24q02m/imagine-mcp/pull/96),
  [`2bc6657`](https://github.com/n24q02m/imagine-mcp/commit/2bc6657a57cc158adb667bddffa7c4d8f1ce316f))

- Resolve TOCTOU SSRF via DNS pinning and secure media fetching (fix types & mocks)
  ([#96](https://github.com/n24q02m/imagine-mcp/pull/96),
  [`2bc6657`](https://github.com/n24q02m/imagine-mcp/commit/2bc6657a57cc158adb667bddffa7c4d8f1ce316f))

- Restore docs/models.md (Spec F Phase 4 mistakenly deleted)
  ([`e0cd077`](https://github.com/n24q02m/imagine-mcp/commit/e0cd0778f8eaaa71971f28b59885c3f42db2b1c6))

- Update setup-manual.md refs in error messages to mcp.n24q02m.com
  ([`9712b73`](https://github.com/n24q02m/imagine-mcp/commit/9712b73a264697bd0fb7ac26d9af565f24f29d18))

- **deps**: Bump n24q02m-mcp-core to 1.14.0
  ([`733d87c`](https://github.com/n24q02m/imagine-mcp/commit/733d87cacfd657759fdbb31df37fa8ece4948fbb))

- **deps**: Bump python-multipart from 0.0.26 to 0.0.27
  ([`1f6fe67`](https://github.com/n24q02m/imagine-mcp/commit/1f6fe6789f495ffe3c5cc8d0ad90b4451c80cb46))

### Features

- Add MediaDetectError tests for detect_media_type
  ([`7a9b333`](https://github.com/n24q02m/imagine-mcp/commit/7a9b3336d66d4c8d34a4c92dbbe61bd1f8aeea43))

- Add Table of contents heading + auto-generated link list (Spec E Wave 2)
  ([`d1d069d`](https://github.com/n24q02m/imagine-mcp/commit/d1d069d795a4eeca2aec7d2cc361b905d532f82b))

- Link to mcp.n24q02m.com unified docs site (Spec F Phase 4)
  ([`6f1f748`](https://github.com/n24q02m/imagine-mcp/commit/6f1f748645629e04f81a31c545294249c07a8c12))

- Sync cross-promo section ([#102](https://github.com/n24q02m/imagine-mcp/pull/102),
  [`a493183`](https://github.com/n24q02m/imagine-mcp/commit/a493183e65f3a104642103a5ef8b0096305f813c))


## v1.3.0 (2026-05-06)


## v1.3.0-beta.1 (2026-05-06)

### Bug Fixes

- Consolidate setup docs body to 3 methods (drop legacy Method 4/5)
  ([#70](https://github.com/n24q02m/imagine-mcp/pull/70),
  [`b667ea7`](https://github.com/n24q02m/imagine-mcp/commit/b667ea784466f7bd69d0dc7bfadac001c2ccaa41))

### Features

- Add explicit Method overview section to setup docs
  ([#69](https://github.com/n24q02m/imagine-mcp/pull/69),
  [`73bc4d9`](https://github.com/n24q02m/imagine-mcp/commit/73bc4d9d1142bb6e35d1499c548262f39db7cedc))

- Clarify Method 1/2/3 mutually exclusive (CC scope-by-endpoint)
  ([#75](https://github.com/n24q02m/imagine-mcp/pull/75),
  [`8fda3d5`](https://github.com/n24q02m/imagine-mcp/commit/8fda3d5da6228e9687b08c8e1f29fb01086fde01))

- Declare userConfig schema and document install prompt
  ([#71](https://github.com/n24q02m/imagine-mcp/pull/71),
  [`f2285df`](https://github.com/n24q02m/imagine-mcp/commit/f2285df53a40be80ba3023a3fd6183810178685b))

- Document userConfig credential prompts per plugin
  ([#74](https://github.com/n24q02m/imagine-mcp/pull/74),
  [`e8bf3d1`](https://github.com/n24q02m/imagine-mcp/commit/e8bf3d1e6bfc3efbdb921d99c844dcb537fcbace))


## v1.2.0 (2026-05-04)

### Bug Fixes

- Bump mcp-core to 1.13.0 (STABLE) ([#68](https://github.com/n24q02m/imagine-mcp/pull/68),
  [`7ecd780`](https://github.com/n24q02m/imagine-mcp/commit/7ecd78000c415006b3f15237f719511a29232286))


## v1.2.0-beta.8 (2026-05-03)

### Bug Fixes

- Bump mcp-core to 1.13.0-beta.9 for /login form shell refactor
  ([#64](https://github.com/n24q02m/imagine-mcp/pull/64),
  [`ba381d4`](https://github.com/n24q02m/imagine-mcp/commit/ba381d4b034463e8f5c6d4e69838fadb7ce9f830))


## v1.2.0-beta.7 (2026-05-03)

### Features

- Bump mcp-core to 1.13.0-beta.7 ([#62](https://github.com/n24q02m/imagine-mcp/pull/62),
  [`b352dcf`](https://github.com/n24q02m/imagine-mcp/commit/b352dcf202645cf50c7aa775938b28afde8f07e8))

- Document MCP_RELAY_PASSWORD edge auth gate ([#63](https://github.com/n24q02m/imagine-mcp/pull/63),
  [`04fc99e`](https://github.com/n24q02m/imagine-mcp/commit/04fc99ee8f6b5422f102b5768b1f01d90d966b1b))

- Pass MCP_RELAY_PASSWORD env to HTTP container
  ([#61](https://github.com/n24q02m/imagine-mcp/pull/61),
  [`ea5fc1b`](https://github.com/n24q02m/imagine-mcp/commit/ea5fc1b656baacbf492c250ab74812dc3caa2414))


## v1.2.0-beta.6 (2026-05-03)

### Bug Fixes

- HTTP multi-user credential wiring (per-sub contextvar)
  ([#60](https://github.com/n24q02m/imagine-mcp/pull/60),
  [`0cd142f`](https://github.com/n24q02m/imagine-mcp/commit/0cd142f43d58e9fa004d3f14aaa92381cce816bd))


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
