# CHANGELOG

<!-- version list -->

## v1.8.1 (2026-07-05)


## v1.8.1-beta.1 (2026-07-05)

### Bug Fixes

- Add BYO Deploy to Cloudflare section to README
  ([#413](https://github.com/n24q02m/imagine-mcp/pull/413),
  [`4e81ac3`](https://github.com/n24q02m/imagine-mcp/commit/4e81ac35ca49925946d9929ed33bfd8e1fe6b499))

- Clarify Workers Paid plan is required for Containers in README
  ([#413](https://github.com/n24q02m/imagine-mcp/pull/413),
  [`4e81ac3`](https://github.com/n24q02m/imagine-mcp/commit/4e81ac35ca49925946d9929ed33bfd8e1fe6b499))

- Do not log substituted CF config in cf_deploy dry-run
  ([#413](https://github.com/n24q02m/imagine-mcp/pull/413),
  [`4e81ac3`](https://github.com/n24q02m/imagine-mcp/commit/4e81ac35ca49925946d9929ed33bfd8e1fe6b499))

- Guard PUBLIC_URL substitution on placeholder presence in cf_deploy_config.mjs
  ([#413](https://github.com/n24q02m/imagine-mcp/pull/413),
  [`4e81ac3`](https://github.com/n24q02m/imagine-mcp/commit/4e81ac35ca49925946d9929ed33bfd8e1fe6b499))

- Pipeline URL validation and fetching to remove barrier sync
  ([`b9071ea`](https://github.com/n24q02m/imagine-mcp/commit/b9071eac389f07c1ec214264b8b840a0f2bac233))

- Substitute PUBLIC_URL in cf_deploy_config.mjs (BYO-generic base wrangler.jsonc)
  ([#413](https://github.com/n24q02m/imagine-mcp/pull/413),
  [`4e81ac3`](https://github.com/n24q02m/imagine-mcp/commit/4e81ac35ca49925946d9929ed33bfd8e1fe6b499))

- Use placeholders for PUBLIC_URL and routes in wrangler.jsonc (BYO-generic)
  ([#413](https://github.com/n24q02m/imagine-mcp/pull/413),
  [`4e81ac3`](https://github.com/n24q02m/imagine-mcp/commit/4e81ac35ca49925946d9929ed33bfd8e1fe6b499))

- Validate MCP_PORT and MCP_HOST configuration at startup
  ([`2aee318`](https://github.com/n24q02m/imagine-mcp/commit/2aee3180c7a33458291304311c5700067f3dea14))

- **deps**: Lock file maintenance
  ([`6a689dd`](https://github.com/n24q02m/imagine-mcp/commit/6a689dd878214cda843ef83e3d50491c64fee7e4))

- **deps**: Update docker/build-push-action digest
  ([`5226ad1`](https://github.com/n24q02m/imagine-mcp/commit/5226ad1d39a50ce4bce8d7bba721f4a771a67a6e))

- **deps**: Update docker/login-action digest to af1e73f
  ([`5d6e7b8`](https://github.com/n24q02m/imagine-mcp/commit/5d6e7b89106cf3c94b002a44eb8a310f6115fcc3))

- **deps**: Update docker/setup-buildx-action digest
  ([`201fa7f`](https://github.com/n24q02m/imagine-mcp/commit/201fa7f6b1f25324a7fb4df27524b8ee336c77bc))

- **deps**: Update non-major dependencies
  ([`b322ceb`](https://github.com/n24q02m/imagine-mcp/commit/b322ceb863cc7313ce66c8dc01f5b102801bc4dc))


## v1.8.0 (2026-07-02)

### Bug Fixes

- Bump mcp-core to 1.18.1 ([#412](https://github.com/n24q02m/imagine-mcp/pull/412),
  [`707a88f`](https://github.com/n24q02m/imagine-mcp/commit/707a88fa1e7c210197e8edb913fa890ee1da60f2))

### Features

- Document vertex_express provider option ([#410](https://github.com/n24q02m/imagine-mcp/pull/410),
  [`329ba24`](https://github.com/n24q02m/imagine-mcp/commit/329ba24deb513a6d56f7b390e432c952dbacbecd))


## v1.8.0-beta.1 (2026-07-02)

### Features

- Deploy CF Worker+Container on release from cd.yml
  ([#409](https://github.com/n24q02m/imagine-mcp/pull/409),
  [`81f8caf`](https://github.com/n24q02m/imagine-mcp/commit/81f8caff77994f1576af86e6cbde6a466b65e4f5))


## v1.7.1-beta.1 (2026-07-01)

### Bug Fixes

- Add Vertex AI (Express) support to relay form and credential state
  ([#402](https://github.com/n24q02m/imagine-mcp/pull/402),
  [`18ef291`](https://github.com/n24q02m/imagine-mcp/commit/18ef291980a1c376163f7b34ac34d367bc924c35))

- Bump mcp-core to 1.18.1b1 for the vertex relay dropdown fix
  ([#403](https://github.com/n24q02m/imagine-mcp/pull/403),
  [`5454d49`](https://github.com/n24q02m/imagine-mcp/commit/5454d497ea791fff11a2bc85f18692da964e3160))


## v1.7.0 (2026-07-01)


## v1.7.0-beta.14 (2026-06-30)

### Bug Fixes

- Add dispatcher validation tests
  ([`ce19684`](https://github.com/n24q02m/imagine-mcp/commit/ce19684659260f04e9b99d550ed1193275d65b46))

- Add grok generate_video provider tests
  ([`b0a20ae`](https://github.com/n24q02m/imagine-mcp/commit/b0a20ae1bf3a57f26da4ac62f36eca2172b889db))

- Bound download read size with pre-flight Content-Length check
  ([`6fce026`](https://github.com/n24q02m/imagine-mcp/commit/6fce026f12cc730957f9460f4670da7668feac46))

- Canary Gate-A/B settle-retry to avoid false-fail on slow container startup
  ([#392](https://github.com/n24q02m/imagine-mcp/pull/392),
  [`26b7626`](https://github.com/n24q02m/imagine-mcp/commit/26b7626e8cdcbcc4c3a806ad1197d39a821a0669))

- Collapse OAuth + per-sub routing to one DO (resolve max_instances=1 deadlock)
  ([#397](https://github.com/n24q02m/imagine-mcp/pull/397),
  [`f77066a`](https://github.com/n24q02m/imagine-mcp/commit/f77066a7ef47f16448154923732c7e44fb13bbd9))

- Route OAuth /token refresh to the sub's DO to avoid max_instances=1 deadlock
  ([#393](https://github.com/n24q02m/imagine-mcp/pull/393),
  [`aefdf15`](https://github.com/n24q02m/imagine-mcp/commit/aefdf15ac0b4b1f1f4afcbd3a997d17021123a20))

- Use urlparse + posixpath.splitext for platform-independent URL extension
  ([`209de15`](https://github.com/n24q02m/imagine-mcp/commit/209de156e40578812f84875f06d6c4d18cf97550))


## v1.7.0-beta.13 (2026-06-29)

### Bug Fixes

- Add coverage for default provider fallback and models.py
  ([`89042ff`](https://github.com/n24q02m/imagine-mcp/commit/89042ffee487894281743d38685efb207a8bc6fd))

- Add test coverage for openai generate_image logic
  ([`7f64b0b`](https://github.com/n24q02m/imagine-mcp/commit/7f64b0bf77c174fb1586002368e4ddcbcf4d6cd1))

- Cap max_instances=1 for CF container cost (solo dev default)
  ([`f4589a1`](https://github.com/n24q02m/imagine-mcp/commit/f4589a1a82e6805e40c94980184b3734014cde03))

- Cover default-provider fallback
  ([`89042ff`](https://github.com/n24q02m/imagine-mcp/commit/89042ffee487894281743d38685efb207a8bc6fd))

- Cover dispatcher _validate_url edge cases
  ([`16ae754`](https://github.com/n24q02m/imagine-mcp/commit/16ae7547f9e86be55df7302d1c1f2f5daa9a88be))

- Cover Grok generate_image
  ([`922b41a`](https://github.com/n24q02m/imagine-mcp/commit/922b41a31188139c5b58b707313a29f07706cc54))

- Cover OpenAI generate_image
  ([`7f64b0b`](https://github.com/n24q02m/imagine-mcp/commit/7f64b0bf77c174fb1586002368e4ddcbcf4d6cd1))

- Cover relay_complete live-state path
  ([`90e3dd0`](https://github.com/n24q02m/imagine-mcp/commit/90e3dd0f7e007dfbf93f8ab4d0fdc546d28be494))

- Cover Settings defaults/constraints
  ([`15e9184`](https://github.com/n24q02m/imagine-mcp/commit/15e91844d063cecc1516e6331b2943ee4b923db1))

- Enforce Content-Length pre-flight cap on download streams
  ([`170434c`](https://github.com/n24q02m/imagine-mcp/commit/170434cd8e6d4936fc6242dca30fd675361c6de9))

- Harden file-extension extraction against bypass
  ([`9d840f3`](https://github.com/n24q02m/imagine-mcp/commit/9d840f3518fb0f6fe5ec6dd9822fbd0adbc89039))

- Lock file maintenance
  ([`95629de`](https://github.com/n24q02m/imagine-mcp/commit/95629de6bd2c7f95c7d8ef89b0dc65352d122af9))

- Order-preserving provider dedup via set op
  ([`7df5385`](https://github.com/n24q02m/imagine-mcp/commit/7df5385c5d43a0bbb2d1b807eb29112315499c34))

- Update actions/setup-python digest
  ([`e528e48`](https://github.com/n24q02m/imagine-mcp/commit/e528e48c6802936e9df726d027513b8dec885f87))

- Update dawidd6/action-send-mail action
  ([`a152f07`](https://github.com/n24q02m/imagine-mcp/commit/a152f07060a21b073bee412a7e42373bce3ef91c))

- Validate PUBLIC_URL scheme and hostname at startup
  ([`65b012e`](https://github.com/n24q02m/imagine-mcp/commit/65b012e9e8a38edd3497b8667cf26db9712f46f6))

- **deps**: Update non-major dependencies ([#364](https://github.com/n24q02m/imagine-mcp/pull/364),
  [`faaf0fd`](https://github.com/n24q02m/imagine-mcp/commit/faaf0fd1de1e1bbe1c71e54e91b64cec32a5ee24))


## v1.7.0-beta.12 (2026-06-23)

### Bug Fixes

- Bump mcp-core to 1.18.0b20 (relay catalog Jina/normalize + keyword)
  ([#347](https://github.com/n24q02m/imagine-mcp/pull/347),
  [`5ffc664`](https://github.com/n24q02m/imagine-mcp/commit/5ffc6647902252375bfc8049ff64e582c1bf1c6b))

- Bump mcp-core to 1.18.0b20 for relay catalog + drop hardcoded suggestions
  ([#347](https://github.com/n24q02m/imagine-mcp/pull/347),
  [`5ffc664`](https://github.com/n24q02m/imagine-mcp/commit/5ffc6647902252375bfc8049ff64e582c1bf1c6b))

### Features

- Catalog-driven understand models; keep minimal grok generate supplement
  ([#347](https://github.com/n24q02m/imagine-mcp/pull/347),
  [`5ffc664`](https://github.com/n24q02m/imagine-mcp/commit/5ffc6647902252375bfc8049ff64e582c1bf1c6b))


## v1.7.0-beta.11 (2026-06-22)

### Bug Fixes

- Bump mcp-core to 1.18.0b19 (relay model-search catalog + OAuth refresh-TTL)
  ([#344](https://github.com/n24q02m/imagine-mcp/pull/344),
  [`7b539ab`](https://github.com/n24q02m/imagine-mcp/commit/7b539ab6bffcc99d1be39a1e87824544e89a8044))


## v1.7.0-beta.10 (2026-06-22)

### Bug Fixes

- Pin CF max_instances to 3 ([#343](https://github.com/n24q02m/imagine-mcp/pull/343),
  [`02f4ad9`](https://github.com/n24q02m/imagine-mcp/commit/02f4ad9fe1a3ee6eb7024741c34d9020fe82a3da))

- Rewrite README install + configuration sections to match current code
  ([#340](https://github.com/n24q02m/imagine-mcp/pull/340),
  [`e512742`](https://github.com/n24q02m/imagine-mcp/commit/e512742084ccf6dc671af8e0f6b757cee7d67f10))


## v1.7.0-beta.9 (2026-06-21)

### Bug Fixes

- Add cf:deploy script for live wrangler deploy
  ([#339](https://github.com/n24q02m/imagine-mcp/pull/339),
  [`203c6e1`](https://github.com/n24q02m/imagine-mcp/commit/203c6e1a731cf6227cc841bb2f5ccaada78c185d))

- Drop env-derived value from cf_deploy log (CodeQL js/clear-text-logging)
  ([#339](https://github.com/n24q02m/imagine-mcp/pull/339),
  [`203c6e1`](https://github.com/n24q02m/imagine-mcp/commit/203c6e1a731cf6227cc841bb2f5ccaada78c185d))

- Lock file maintenance ([#332](https://github.com/n24q02m/imagine-mcp/pull/332),
  [`dd1f374`](https://github.com/n24q02m/imagine-mcp/commit/dd1f374b54eddd0f8f8c3f2c998eeb92810b4f4f))

- Note headless constraints in journal ([#335](https://github.com/n24q02m/imagine-mcp/pull/335),
  [`044ab9f`](https://github.com/n24q02m/imagine-mcp/commit/044ab9f69409a585e15b19527d481a40b4e6a364))

- Note headless constraints in journal for palette
  ([#335](https://github.com/n24q02m/imagine-mcp/pull/335),
  [`044ab9f`](https://github.com/n24q02m/imagine-mcp/commit/044ab9f69409a585e15b19527d481a40b4e6a364))

- Note headless constraints in palette journal
  ([#335](https://github.com/n24q02m/imagine-mcp/pull/335),
  [`044ab9f`](https://github.com/n24q02m/imagine-mcp/commit/044ab9f69409a585e15b19527d481a40b4e6a364))

- Right-size CF container instance_type and sleepAfter to cut GiB-second cost
  ([#338](https://github.com/n24q02m/imagine-mcp/pull/338),
  [`6f60c54`](https://github.com/n24q02m/imagine-mcp/commit/6f60c540a8a67570c468ab8175b05e6e38ac4ed3))

- Sub-aware understand/generate model selection + relay re-submit overwrite
  ([#337](https://github.com/n24q02m/imagine-mcp/pull/337),
  [`2a0f6ca`](https://github.com/n24q02m/imagine-mcp/commit/2a0f6ca747422dfeb2b37811e34ab3b26c4f75fe))

- Update actions/checkout action to v7 ([#331](https://github.com/n24q02m/imagine-mcp/pull/331),
  [`9df8ba5`](https://github.com/n24q02m/imagine-mcp/commit/9df8ba55a2a62790df45312bd5939c4c1729c7e5))

- 🎨 Palette: note headless constraints in journal
  ([#335](https://github.com/n24q02m/imagine-mcp/pull/335),
  [`044ab9f`](https://github.com/n24q02m/imagine-mcp/commit/044ab9f69409a585e15b19527d481a40b4e6a364))

- **deps**: Update non-major dependencies ([#330](https://github.com/n24q02m/imagine-mcp/pull/330),
  [`17013e4`](https://github.com/n24q02m/imagine-mcp/commit/17013e491e7f9ec6a02e3ec779fa1ce9e7348acc))


## v1.7.0-beta.8 (2026-06-19)

### Bug Fixes

- Bump mcp-core floor to 1.18.0b14 for the key-rotation primitive
  ([`77aeca2`](https://github.com/n24q02m/imagine-mcp/commit/77aeca2ae210282260d7b82b1f5796b0a1b30ed4))

- Make canary gate utf-8-safe (decode+encode) and Cloudflare-UA-aware
  ([`a07708e`](https://github.com/n24q02m/imagine-mcp/commit/a07708e687a81d49d4b22c13f4f6466f3cbec214))

- Make canary gate utf-8-safe and Cloudflare-UA-aware
  ([`a07708e`](https://github.com/n24q02m/imagine-mcp/commit/a07708e687a81d49d4b22c13f4f6466f3cbec214))

- Neutral default endpoint + env-first secrets in CF self-host scripts
  ([`6e39d12`](https://github.com/n24q02m/imagine-mcp/commit/6e39d12c6b36b1735966f2520bae6ffc6ff79421))

- Use contextlib.suppress for stdout reconfigure (SIM105)
  ([`a07708e`](https://github.com/n24q02m/imagine-mcp/commit/a07708e687a81d49d4b22c13f4f6466f3cbec214))


## v1.7.0-beta.7 (2026-06-18)

### Bug Fixes

- Add post-deploy canary gate with auto-rollback to deploy_cf.py
  ([`ddace9c`](https://github.com/n24q02m/imagine-mcp/commit/ddace9ca513dcf25eeff521a23adf1cbb986badd))

- Apply ruff format to cf_full_flow harness
  ([#318](https://github.com/n24q02m/imagine-mcp/pull/318),
  [`05800e9`](https://github.com/n24q02m/imagine-mcp/commit/05800e94f2bf5c249e64e197b6d32f205cf575fa))

- Forward MCP_RELAY_PASSWORD into container + replay token for recreate gate
  ([#317](https://github.com/n24q02m/imagine-mcp/pull/317),
  [`57954ef`](https://github.com/n24q02m/imagine-mcp/commit/57954ef72841eaffb680b1113929eb77b2cd6c1a))

- Prefix unused account var to satisfy RUF059
  ([`ddace9c`](https://github.com/n24q02m/imagine-mcp/commit/ddace9ca513dcf25eeff521a23adf1cbb986badd))

- Refresh lockfile (renovate maintenance)
  ([`751d302`](https://github.com/n24q02m/imagine-mcp/commit/751d3024c49af7005f1e853b1c09a61757ae7ce9))

- Refresh lockfile (renovate maintenance)
  ([`dd86d8a`](https://github.com/n24q02m/imagine-mcp/commit/dd86d8a6b9eec712963c87e5a8a57bd11fbfe8cf))

- Update non-major dependencies
  ([`969646b`](https://github.com/n24q02m/imagine-mcp/commit/969646b2db5d8c36ef8c0c9c04a355551dc18079))

- Update non-major dependencies
  ([`b7b3192`](https://github.com/n24q02m/imagine-mcp/commit/b7b31922c15cf4f8bbdd1bccbe55121fa72b30bf))

- Update typescript to v6
  ([`7c280ba`](https://github.com/n24q02m/imagine-mcp/commit/7c280ba903a273e347f3dce9efbc243d050a75b8))

### Features

- Add post-deploy canary gate with auto-rollback to deploy_cf.py
  ([`ddace9c`](https://github.com/n24q02m/imagine-mcp/commit/ddace9ca513dcf25eeff521a23adf1cbb986badd))


## v1.7.0-beta.6 (2026-06-15)

### Bug Fixes

- Add thread-safe client manager and extract download helpers
  ([#312](https://github.com/n24q02m/imagine-mcp/pull/312),
  [`0a82c48`](https://github.com/n24q02m/imagine-mcp/commit/0a82c487642455f8557cf25092dc45a2548f5b06))

- Centralize client initialization and credential resolution logic
  ([#302](https://github.com/n24q02m/imagine-mcp/pull/302),
  [`ac1e019`](https://github.com/n24q02m/imagine-mcp/commit/ac1e01924937b465c19afd6b962da6ef6d301050))

- Import Callable from collections.abc (ruff UP035)
  ([#302](https://github.com/n24q02m/imagine-mcp/pull/302),
  [`ac1e019`](https://github.com/n24q02m/imagine-mcp/commit/ac1e01924937b465c19afd6b962da6ef6d301050))

- Offload blocking provider/config i/o off the event loop
  ([#304](https://github.com/n24q02m/imagine-mcp/pull/304),
  [`83881c4`](https://github.com/n24q02m/imagine-mcp/commit/83881c4ccd1252664dc36932935d8de785e6782c))

- Optimize url processing with native async i/o
  ([#309](https://github.com/n24q02m/imagine-mcp/pull/309),
  [`6e3a1cf`](https://github.com/n24q02m/imagine-mcp/commit/6e3a1cf4ae50db25dfe0e04b0273bceec78e8839))

- Report relay_skip via canonical CREDENTIAL_KEYS
  ([#308](https://github.com/n24q02m/imagine-mcp/pull/308),
  [`34d45e6`](https://github.com/n24q02m/imagine-mcp/commit/34d45e62c7383dc189bf9c0e8bf0bd24a7d5a3bc))

- **deps**: Update non-major dependencies ([#310](https://github.com/n24q02m/imagine-mcp/pull/310),
  [`fb1497d`](https://github.com/n24q02m/imagine-mcp/commit/fb1497d7cb650c791a62f946a08b1e9624d4ef45))

### Features

- Cloudflare serverless migration (Worker + Container + KV-only, base64 output)
  ([#316](https://github.com/n24q02m/imagine-mcp/pull/316),
  [`44af98b`](https://github.com/n24q02m/imagine-mcp/commit/44af98befe776467488c321fd3b6cdc60ea25f34))


## v1.7.0-beta.5 (2026-06-15)

### Bug Fixes

- Bump mcp-core to 1.18.0b5 for vertex_express support
  ([#315](https://github.com/n24q02m/imagine-mcp/pull/315),
  [`4386dd4`](https://github.com/n24q02m/imagine-mcp/commit/4386dd4e934425e12a3164d66cbacec066438a8a))


## v1.7.0-beta.4 (2026-06-15)

### Bug Fixes

- Correct credential storage and setup-transport docs
  ([`435900f`](https://github.com/n24q02m/imagine-mcp/commit/435900f18acbec9af37e6329e773f3dbe4f9c6df))

- Fetch understand-flow media concurrently via asyncio.gather
  ([#291](https://github.com/n24q02m/imagine-mcp/pull/291),
  [`1e58248`](https://github.com/n24q02m/imagine-mcp/commit/1e58248369ad7757b16f7317df6d4ae11e8f5550))

- Narrow gather results on BaseException for ty check
  ([#291](https://github.com/n24q02m/imagine-mcp/pull/291),
  [`1e58248`](https://github.com/n24q02m/imagine-mcp/commit/1e58248369ad7757b16f7317df6d4ae11e8f5550))

- Remove literal v<auto> placeholder from stabilization note
  ([#293](https://github.com/n24q02m/imagine-mcp/pull/293),
  [`0aeddcf`](https://github.com/n24q02m/imagine-mcp/commit/0aeddcf8f75e8a270f04bb42a2e359c8747fa7d1))

- Remove orphaned Qodo pr-agent config ([#289](https://github.com/n24q02m/imagine-mcp/pull/289),
  [`567f7b8`](https://github.com/n24q02m/imagine-mcp/commit/567f7b8fa64f74fc90e86a355869ff6ef396ec77))

- Resolve memory exhaustion and disk DoS in media download
  ([#283](https://github.com/n24q02m/imagine-mcp/pull/283),
  [`171d38f`](https://github.com/n24q02m/imagine-mcp/commit/171d38f9d983c5efdb22f025a559229676c29a33))

- Ruff-format media download + resolve ty binary-write type error
  ([#283](https://github.com/n24q02m/imagine-mcp/pull/283),
  [`171d38f`](https://github.com/n24q02m/imagine-mcp/commit/171d38f9d983c5efdb22f025a559229676c29a33))

- Sentinel: add html parsing security enhancements to leaderboard script
  ([#290](https://github.com/n24q02m/imagine-mcp/pull/290),
  [`b57e80a`](https://github.com/n24q02m/imagine-mcp/commit/b57e80a7b8841e556e0ecf61ee09ea1514383f10))

- Sync imagine docs with code (drop removed config models action)
  ([#292](https://github.com/n24q02m/imagine-mcp/pull/292),
  [`d83be35`](https://github.com/n24q02m/imagine-mcp/commit/d83be35e47778c065a1d7e2aa45bf30264fe659d))

- Sync README tagline to current capability description
  ([#295](https://github.com/n24q02m/imagine-mcp/pull/295),
  [`d456b1a`](https://github.com/n24q02m/imagine-mcp/commit/d456b1a6110a23dcf626fcc66fcee1a559d2f2b2))

- 🛡️ sentinel: [MEDIUM] add html parsing security enhancements to leaderboard script
  ([#290](https://github.com/n24q02m/imagine-mcp/pull/290),
  [`b57e80a`](https://github.com/n24q02m/imagine-mcp/commit/b57e80a7b8841e556e0ecf61ee09ea1514383f10))

- **deps**: Update non-major dependencies ([#298](https://github.com/n24q02m/imagine-mcp/pull/298),
  [`e9edca8`](https://github.com/n24q02m/imagine-mcp/commit/e9edca87a39ab54661ba16053bfc1df0e288e8fe))

- **deps**: Update step-security/harden-runner digest to 9af89fc
  ([#297](https://github.com/n24q02m/imagine-mcp/pull/297),
  [`543c30f`](https://github.com/n24q02m/imagine-mcp/commit/543c30fa6c7c332898b5c2b153c16995c4f7e7f8))

### Features

- Sync cross-promo section ([#296](https://github.com/n24q02m/imagine-mcp/pull/296),
  [`732e07e`](https://github.com/n24q02m/imagine-mcp/commit/732e07e06a6568f4539c2379fba76d59d83014b0))


## v1.7.0-beta.3 (2026-06-11)

### Bug Fixes

- Document per-task model chains + provider->key table (drop priority-router docs)
  ([#287](https://github.com/n24q02m/imagine-mcp/pull/287),
  [`b2f7595`](https://github.com/n24q02m/imagine-mcp/commit/b2f7595d18a735e584452438dc427bd126d7664e))

### Features

- Drop config(action="models") catalog-listing tool action
  ([#288](https://github.com/n24q02m/imagine-mcp/pull/288),
  [`4a63b79`](https://github.com/n24q02m/imagine-mcp/commit/4a63b798ea7bc1526e7dc2b15c8e368ffda51683))

- Drop config(action="models") mention from CLAUDE.md
  ([#288](https://github.com/n24q02m/imagine-mcp/pull/288),
  [`4a63b79`](https://github.com/n24q02m/imagine-mcp/commit/4a63b798ea7bc1526e7dc2b15c8e368ffda51683))


## v1.7.0-beta.2 (2026-06-11)

### Bug Fixes

- Document litellm passthrough + model param in CLAUDE.md/AGENTS.md
  ([#285](https://github.com/n24q02m/imagine-mcp/pull/285),
  [`aec7752`](https://github.com/n24q02m/imagine-mcp/commit/aec7752017ec4b5004ea70090fa316ccdc834a29))

### Features

- Imagine understand model-chain + relay widget (generate stays native)
  ([#286](https://github.com/n24q02m/imagine-mcp/pull/286),
  [`940abed`](https://github.com/n24q02m/imagine-mcp/commit/940abed90195f6c03c06ad96edcaa971ec16ce88))


## v1.7.0-beta.1 (2026-06-11)

### Bug Fixes

- Drop private registry import + cover capability re-raise
  ([#284](https://github.com/n24q02m/imagine-mcp/pull/284),
  [`e368d52`](https://github.com/n24q02m/imagine-mcp/commit/e368d525ee17f1aa202a704121d2b128d4e8acd3))

### Features

- Migrate understand to litellm passthrough + open model surface
  ([#284](https://github.com/n24q02m/imagine-mcp/pull/284),
  [`e368d52`](https://github.com/n24q02m/imagine-mcp/commit/e368d525ee17f1aa202a704121d2b128d4e8acd3))

- Migrate understand to litellm passthrough + open model surface via mcp-core[llm]
  ([#284](https://github.com/n24q02m/imagine-mcp/pull/284),
  [`e368d52`](https://github.com/n24q02m/imagine-mcp/commit/e368d525ee17f1aa202a704121d2b128d4e8acd3))


## v1.6.2-beta.2 (2026-06-10)

### Bug Fixes

- Add missing DNS error path tests for validate_url_and_get_ip
  ([#274](https://github.com/n24q02m/imagine-mcp/pull/274),
  [`608e4e1`](https://github.com/n24q02m/imagine-mcp/commit/608e4e1b53ca3b03918c719975f6da4d2cf3a0d7))

- Add missing error path tests for detect_media_type
  ([#276](https://github.com/n24q02m/imagine-mcp/pull/276),
  [`b483e71`](https://github.com/n24q02m/imagine-mcp/commit/b483e71ad514f57bf987da49d8fc0edc56076db5))

- Default MCP_HOST to 127.0.0.1, opt into 0.0.0.0 via Docker
  ([`b7919b3`](https://github.com/n24q02m/imagine-mcp/commit/b7919b3595e2a0940d60c9e4954272669289a8c4))

- Resolve stale state in relay_status/relay_complete
  ([#280](https://github.com/n24q02m/imagine-mcp/pull/280),
  [`1844f18`](https://github.com/n24q02m/imagine-mcp/commit/1844f184d7839680dba1752aee423d9d75e83e8d))


## v1.6.2-beta.1 (2026-06-10)

### Bug Fixes

- Add Comparison capability matrix to README
  ([#271](https://github.com/n24q02m/imagine-mcp/pull/271),
  [`563adfc`](https://github.com/n24q02m/imagine-mcp/commit/563adfcd5602dedbc3ab1a1317febaa07e6935b0))

- Correct stale env var, CLI flag, docs-site links and tool inventory in docs
  ([#270](https://github.com/n24q02m/imagine-mcp/pull/270),
  [`91cfae2`](https://github.com/n24q02m/imagine-mcp/commit/91cfae2812ac97ae7639a0adb75d1935f50fcf16))


## v1.6.1 (2026-06-09)


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
