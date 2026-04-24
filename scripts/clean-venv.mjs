#!/usr/bin/env node
import { rmSync, existsSync } from 'fs';
import { join } from 'path';

const venvPath = join(process.cwd(), '.venv');
if (existsSync(venvPath)) {
  console.log(`Removing stale .venv at ${venvPath}`);
  rmSync(venvPath, { recursive: true, force: true });
}
