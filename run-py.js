const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const py = process.platform === 'win32'
  ? path.join(__dirname, '.venv', 'Scripts', 'python.exe')
  : path.join(__dirname, '.venv', 'bin', 'python');

if (!fs.existsSync(py)) {
  console.error(`\n[ClaimShield] Virtual environment not found at: ${py}\nPlease run setup first.\n`);
  process.exit(1);
}

const args = process.argv.slice(2);
const child = spawn(py, args, { stdio: 'inherit' });
child.on('exit', (code) => process.exit(code ?? 0));
