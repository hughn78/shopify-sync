const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

let mainWindow;
let backendProcess;

const isDev = !app.isPackaged;

function resolveBackendRoot() {
  if (isDev) {
    return path.join(__dirname, '..', 'backend');
  }

  const candidates = [
    path.join(process.resourcesPath, 'backend'),
    path.join(process.resourcesPath, '..', 'backend'),
    path.join(process.resourcesPath, '..', '..', 'backend'),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  return candidates[0];
}

function resolvePythonCommand(backendRoot) {
  if (isDev) {
    return {
      command: path.join(backendRoot, '.venv', 'bin', 'python'),
      args: ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
      env: { ...process.env, PYTHONPATH: backendRoot },
    };
  }

  return {
    command: '/usr/bin/python3',
    args: ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
    env: { ...process.env, PYTHONPATH: backendRoot },
  };
}

async function waitForServer(url, timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return true;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  return false;
}

async function startBackend() {
  const backendRoot = resolveBackendRoot();
  const entry = resolvePythonCommand(backendRoot);

  if (!fs.existsSync(backendRoot)) {
    throw new Error(`Backend directory not found: ${backendRoot}`);
  }

  backendProcess = spawn(entry.command, entry.args, {
    cwd: backendRoot,
    env: entry.env,
    stdio: 'pipe',
  });

  backendProcess.stdout.on('data', (data) => {
    process.stdout.write(`[backend] ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    process.stderr.write(`[backend] ${data}`);
  });

  backendProcess.on('exit', (code) => {
    if (code !== 0) {
      dialog.showErrorBox('Backend stopped', `The backend process exited with code ${code}.`);
    }
  });

  const ok = await waitForServer('http://127.0.0.1:8000/api/health');
  if (!ok) {
    throw new Error('Backend did not become ready in time.');
  }
}

async function createWindow() {
  await startBackend();

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1100,
    minHeight: 760,
    title: 'Pharmacy Stock Sync',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      sandbox: true,
    },
  });

  await mainWindow.loadURL('http://127.0.0.1:8000');
}

app.whenReady().then(async () => {
  try {
    await createWindow();
  } catch (error) {
    dialog.showErrorBox('Unable to start Pharmacy Stock Sync', error instanceof Error ? error.message : String(error));
    app.quit();
  }

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill('SIGTERM');
  }
});
