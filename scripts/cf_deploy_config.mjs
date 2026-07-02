#!/usr/bin/env node
// cf_deploy_config.mjs - config-only live deploy of the imagine-mcp CF
// Worker + Container, driven by the committed wrangler.jsonc.
//
// The committed wrangler.jsonc carries three deploy-time placeholders that are
// NOT checked in as live values (so the public repo never pins account/KV ids
// or the maintainer's own domain):
//   <YOUR_ACCOUNT_ID>          -> the CF account id     (env CLOUDFLARE_ACCOUNT_ID)
//   <imagine-kv-namespace-id>  -> the live KV id         (env IMAGINE_KV_NAMESPACE_ID)
//   <YOUR_PUBLIC_URL>          -> the public origin URL  (env PUBLIC_URL)
// This script substitutes all three into a temp config and runs `wrangler deploy`
// against it, so the committed wrangler.jsonc stays placeholder-clean. The
// <YOUR_WORKER_DOMAIN> routes placeholder needs no value -- the routes block is
// stripped below (the config-only token can't reconcile zone Workers Routes).
// Pass --dry-run to print the substituted config and exit without deploying.
//
// It is config-only: it does NOT rebuild or push the container image. It reuses
// the image tag already pushed to the CF managed registry (default `beta`,
// override with IMAGINE_IMAGE_TAG) and preserves existing `wrangler secret`
// values. Use it to roll out wrangler.jsonc changes such as the container
// instance_type / max_instances and the ImagineContainer.sleepAfter in
// src/worker.ts (the dominant GiB-second cost knobs).
//
// Usage (token + ids injected by skret; never commit them):
//   MSYS_NO_PATHCONV=1 skret run -e dev --path=/n24q02m/dev -- \
//     bash -c 'export CLOUDFLARE_API_TOKEN=$CF_DEV_TOKEN \
//       CLOUDFLARE_ACCOUNT_ID=<account> IMAGINE_KV_NAMESPACE_ID=<kv> \
//       PUBLIC_URL=<https://your.domain> \
//       && npm run cf:deploy'
//
// To build + push a fresh image first (and run the canary gate), use the fuller
// scripts/deploy_cf.py instead; this script is the lightweight config-only path.

import { readFileSync, writeFileSync, rmSync } from 'fs';
import { join } from 'path';
import { spawnSync } from 'child_process';

const root = process.cwd();
const srcConfig = join(root, 'wrangler.jsonc');
const tmpConfig = join(root, 'wrangler.deploy-tmp.jsonc');

// --dry-run substitutes + prints the temp config without deploying (no CF token
// needed); account/KV fall back to obvious dummies so a quick PUBLIC_URL check
// works with only PUBLIC_URL set.
const dryRun = process.argv.includes('--dry-run');

const accountId = process.env.CLOUDFLARE_ACCOUNT_ID || (dryRun ? 'DRYRUN_ACCOUNT' : undefined);
const kvId = process.env.IMAGINE_KV_NAMESPACE_ID || (dryRun ? 'DRYRUN_KV_ID' : undefined);
const publicUrl = process.env.PUBLIC_URL;
const imageTag = process.env.IMAGINE_IMAGE_TAG || 'beta';

if (!dryRun && !process.env.CLOUDFLARE_API_TOKEN) {
  console.error('CLOUDFLARE_API_TOKEN is required (skret /n24q02m/dev CF_DEV_TOKEN).');
  process.exit(1);
}
if (!accountId) {
  console.error('CLOUDFLARE_ACCOUNT_ID is required (substitutes <YOUR_ACCOUNT_ID>).');
  process.exit(1);
}
if (!kvId) {
  console.error('IMAGINE_KV_NAMESPACE_ID is required (substitutes <imagine-kv-namespace-id>).');
  process.exit(1);
}
if (!publicUrl) {
  console.error('PUBLIC_URL is required (substitutes <YOUR_PUBLIC_URL>).');
  process.exit(1);
}

let config = readFileSync(srcConfig, 'utf8');
config = config
  .replaceAll('<YOUR_ACCOUNT_ID>', accountId)
  .replaceAll('<imagine-kv-namespace-id>', kvId)
  .replaceAll('<YOUR_PUBLIC_URL>', publicUrl)
  .replace(/(registry\.cloudflare\.com\/[^/]+\/imagine-mcp):[^"]+/, `$1:${imageTag}`)
  // Drop the routes block: imagine.n24q02m.com is already attached as a custom
  // domain, and editing zone Workers Routes needs a zone-scoped token the
  // config-only CF_DEV_TOKEN does not carry. Re-asserting it fails with API
  // error 10000 AFTER the (successful) Worker + container update, so strip it.
  .replace(/^\s*"routes":\s*\[[^\]]*\],?\s*$\n?/m, '')
  // ...but stripping routes makes wrangler default workers_dev=true, exposing a
  // *.workers.dev URL + Preview URLs. Pin them off so the only public surface
  // stays the already-attached custom domain.
  .replace(/^(\s*)"name":\s*"imagine-mcp-worker",\s*$/m, '$1"name": "imagine-mcp-worker",\n$1"workers_dev": false,\n$1"preview_urls": false,');

writeFileSync(tmpConfig, config, 'utf8');

if (dryRun) {
  // Print the fully-substituted config and flag any placeholder still left, then
  // exit without touching Cloudflare (the temp config is not deployed).
  const leftover = [...new Set(config.match(/<[A-Za-z0-9_-]+>/g) || [])];
  console.log('cf:deploy --dry-run - substituted config (not deploying):\n');
  console.log(config);
  rmSync(tmpConfig, { force: true });
  if (leftover.length) {
    console.error(`\nFAIL: unsubstituted placeholder(s) remain: ${leftover.join(', ')}`);
    process.exit(1);
  }
  console.log('\nOK: no unsubstituted <...> placeholders remain.');
  process.exit(0);
}

console.log('cf:deploy - deploying config-only Worker + Container update');

try {
  // shell:true so the local wrangler bin resolves on every platform — direct
  // spawn of npx.cmd is rejected with EINVAL on Windows (Node .cmd hardening).
  const res = spawnSync('npx', ['wrangler', 'deploy', '--config', tmpConfig], {
    stdio: 'inherit',
    shell: true,
  });
  process.exitCode = res.status ?? 1;
} finally {
  rmSync(tmpConfig, { force: true });
}
