import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const scriptsDir = path.dirname(__filename);
const frontendDir = path.resolve(scriptsDir, '..');
const localBin = path.join(frontendDir, 'node_modules', '.bin');

const env = {
  ...process.env,
  npm_config_prefix: frontendDir,
  npm_config_userconfig: path.join(frontendDir, '.npmrc.local-build'),
  NODE_PATH: path.join(frontendDir, 'node_modules'),
  PATH: `${localBin}:${process.env.PATH ?? ''}`,
};

delete env.npm_config_workspace;
delete env.npm_config_workspaces;
delete env.INIT_CWD;

for (const [cmd, args] of [
  ['node', [path.join(frontendDir, 'node_modules', 'typescript', 'bin', 'tsc'), '-p', 'tsconfig.json']],
  ['node', [path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js'), 'build']],
]) {
  const result = spawnSync(cmd, args, {
    cwd: frontendDir,
    env,
    stdio: 'inherit',
  });

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
