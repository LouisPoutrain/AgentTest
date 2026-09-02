const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const treeKill = require('tree-kill');

let mainWindow;
let backendProcess;
let frontendProcess;

function startBackend() {
  const venvPath = path.join(__dirname, '../.venv/bin/uvicorn');
  const backendDir = path.join(__dirname, '../backend');
  
  console.log('Starting Python backend...');
  backendProcess = spawn(venvPath, ['app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: backendDir,
    stdio: 'inherit'
  });

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend process:', err);
  });
}

function startFrontend() {
  const servePath = path.join(__dirname, 'node_modules', '.bin', 'serve');
  const outDir = path.join(__dirname, '../frontend/out');
  
  console.log('Starting Frontend server...');
  frontendProcess = spawn(servePath, ['-s', outDir, '-l', 'tcp://127.0.0.1:3000'], {
    stdio: 'inherit'
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    titleBarStyle: 'hiddenInset',
    title: 'Agent Zouglou',
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`[Browser Console]: ${message}`);
  });

  // Clear cache to prevent aggressive Next.js/Serve caching during dev
  await mainWindow.webContents.session.clearCache();

  // Load the next.js app from the local frontend server
  mainWindow.loadURL('http://127.0.0.1:3000');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  if (process.platform === 'darwin') {
    app.dock.setIcon(path.join(__dirname, 'icon.png'));
  }

  startBackend();
  startFrontend();
  
  // Poll backend health before opening window
  const checkBackend = () => {
    return new Promise((resolve) => {
      const http = require('http');
      const req = http.get('http://127.0.0.1:8000/api/health', (res) => {
        if (res.statusCode === 200) resolve(true);
        else resolve(false);
      });
      req.on('error', () => resolve(false));
      req.end();
    });
  };

  console.log("Waiting for backend to be ready...");
  while (!(await checkBackend())) {
    await new Promise(r => setTimeout(r, 500));
  }
  console.log("Backend is ready. Opening window.");
  await createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    console.log('Killing backend process...');
    treeKill(backendProcess.pid);
  }
  if (frontendProcess) {
    console.log('Killing frontend process...');
    treeKill(frontendProcess.pid);
  }
});
