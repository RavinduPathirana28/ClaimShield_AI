const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT_DIR = __dirname;
const isWin = process.platform === 'win32';
const pyPath = isWin
  ? path.join(ROOT_DIR, '.venv', 'Scripts', 'python.exe')
  : path.join(ROOT_DIR, '.venv', 'bin', 'python');
const pipPath = isWin
  ? path.join(ROOT_DIR, '.venv', 'Scripts', 'pip.exe')
  : path.join(ROOT_DIR, '.venv', 'bin', 'pip');

function log(msg) {
  console.log(`\x1b[36m[ClaimShield]\x1b[0m ${msg}`);
}

function ensureVenv() {
  if (!fs.existsSync(pyPath)) {
    log('Python virtual environment (.venv) not found. Initializing...');
    const pythonCmd = isWin ? 'python' : 'python3';
    execSync(`${pythonCmd} -m venv .venv`, { cwd: ROOT_DIR, stdio: 'inherit', shell: true });

    log('Installing Python requirements from requirements.txt...');
    execSync(`"${pipPath}" install -r requirements.txt`, { cwd: ROOT_DIR, stdio: 'inherit', shell: true });
  }

  // Check if spaCy en_core_web_sm model is downloaded
  try {
    execSync(`"${pyPath}" -c "import spacy; spacy.load('en_core_web_sm')"`, { cwd: ROOT_DIR, stdio: 'ignore', shell: true });
  } catch {
    log('Downloading missing spaCy language model (en_core_web_sm)...');
    execSync(`"${pyPath}" -m spacy download en_core_web_sm`, { cwd: ROOT_DIR, stdio: 'inherit', shell: true });
  }
}

function ensureNodeModules() {
  const rootModules = path.join(ROOT_DIR, 'node_modules');
  const frontendModules = path.join(ROOT_DIR, 'frontend', 'node_modules');

  if (!fs.existsSync(rootModules) || !fs.existsSync(frontendModules)) {
    log('Installing missing npm dependencies...');
    execSync('npm install', { cwd: ROOT_DIR, stdio: 'inherit', shell: true });
  }
}

function start() {
  log('Starting fullstack application (Backend: 8000, Frontend: 5173)...');
  const apiCmd = 'node run-py.js -m uvicorn app.api:app --port 8000 --reload --reload-dir app';
  const webCmd = 'npm run dev --workspace frontend';
  
  execSync(
    `npx concurrently -k -n api,web -c blue,magenta "${apiCmd}" "${webCmd}"`,
    { cwd: ROOT_DIR, stdio: 'inherit', shell: true }
  );
}

try {
  ensureVenv();
  ensureNodeModules();
  start();
} catch (err) {
  // If user hits Ctrl+C, exit gracefully
  process.exit(0);
}
