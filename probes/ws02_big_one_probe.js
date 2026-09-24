'use strict';
// Probe for FleetView (wave 1 fix round 2): why does "the page keeps answering while 1 big log
// file is read" (tests/server3.test.js) sometimes read nothing at all in 25 seconds on
// windows-latest (3 of 10 runs of npm test, run 36060772079)?
//
// Repeats that test's exact scene N times. FleetView (watcher.js) is started with a preload that
// timestamps every chokidar event (add, addDir, change, ready, error, raw) to its error output,
// and the probe timestamps its own steps (server answering, folder made, file finished). A failed
// round prints the whole record, so it shows whether chokidar never reported the file, or reported
// it and FleetView did not read it.
//
//   node ../_mactest/probes/ws02_big_one_probe.js [rounds]     (run in a FleetView folder)
const fs = require('fs');
const os = require('os');
const net = require('net');
const path = require('path');
const { spawn } = require('child_process');

const ROUNDS = Number(process.argv[2] || 10);
const MEMBER = process.cwd();
const WATCHER = path.join(MEMBER, 'watcher.js');
const HOOK = path.join(os.tmpdir(), 'fv-chokidar-hook-' + process.pid + '.js');
fs.writeFileSync(HOOK, `
const t0 = Date.now();
const { FSWatcher } = require(require.resolve('chokidar', { paths: [${JSON.stringify(MEMBER)}] }));
const emit = FSWatcher.prototype.emit;
FSWatcher.prototype.emit = function (ev, ...rest) {
  if (ev !== 'all') process.stderr.write('[chokidar +' + (Date.now() - t0) + 'ms] ' + ev + ' ' + rest.map(String).join(' ').slice(0, 160) + '\\n');
  return emit.call(this, ev, ...rest);
};
`);

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
function freePort() {
  return new Promise((resolve) => {
    const s = net.createServer();
    s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => resolve(p)); });
  });
}

async function round(n) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fleetview-probe-'));
  const projects = path.join(root, '.claude', 'projects');
  fs.mkdirSync(projects, { recursive: true });
  const port = await freePort();
  const cfgFile = path.join(root, 'config.json');
  fs.writeFileSync(cfgFile, JSON.stringify({ folders: [], usage: { enabled: false } }));
  const env = { ...process.env, HOME: root, USERPROFILE: root, CLAUDE_CONFIG_DIR: path.join(root, '.claude'),
    FLEETVIEW_CONFIG: cfgFile, PORT: String(port), FLEETVIEW_NO_CCUSAGE: '1' };
  const t0 = Date.now();
  const log = [];
  const note = (s) => log.push('[probe +' + (Date.now() - t0) + 'ms] ' + s);
  const child = spawn(process.execPath, ['--require', HOOK, WATCHER], { env, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  child.stdout.on('data', d => log.push('[out] ' + String(d).trim()));
  child.stderr.on('data', d => log.push(String(d).trim()));
  const base = `http://127.0.0.1:${port}`;
  const end0 = Date.now() + 20000;
  while (Date.now() < end0) {
    try { const r = await fetch(base + '/api/meta'); if (r.ok) break; } catch { /* not up */ }
    await sleep(200);
  }
  note('server answered /api/meta');
  const dir = path.join(projects, 'C--Demo--Big');
  fs.mkdirSync(dir, { recursive: true });
  note('folder made');
  const now = new Date().toISOString();
  const lineFor = (k) => JSON.stringify({ type: 'assistant', sessionId: 'big-one', cwd: 'C:\\Demo\\Big', timestamp: now,
    message: { id: 'm' + k, model: 'claude-opus-5', role: 'assistant', stop_reason: null,
      content: [{ type: 'text', text: 'w'.repeat(300) }], usage: { output_tokens: 1 } } });
  const f = path.join(dir, 'big-one.jsonl');
  const fd = fs.openSync(f, 'w');
  note('file opened');
  for (let i = 0; i < 50; i++) {
    const chunk = [];
    for (let j = 0; j < 2000; j++) chunk.push(lineFor(i * 2000 + j));
    fs.writeSync(fd, chunk.join('\n') + '\n');
  }
  fs.closeSync(fd);
  note('file finished');
  let tokens = 0;
  const end = Date.now() + 25000;
  while (Date.now() < end) {
    try { tokens = (await (await fetch(base + '/api/graph', { cache: 'no-store' })).json()).totals.outputTokens; } catch { /* busy */ }
    if (tokens >= 100000) break;
    await sleep(50);
  }
  note('tokens ' + tokens);
  child.kill();
  await sleep(300);
  const ok = tokens === 100000;
  console.log('round ' + n + ': ' + (ok ? 'READ' : 'NOT READ (' + tokens + ' tokens)') + ' in ' + (Date.now() - t0) + ' ms');
  if (!ok) console.log(log.join('\n'));
  return ok;
}

(async () => {
  let failed = 0;
  for (let n = 1; n <= ROUNDS; n++) if (!(await round(n))) failed++;
  console.log('PROBE: ' + failed + ' of ' + ROUNDS + ' rounds read nothing or too little');
  try { fs.unlinkSync(HOOK); } catch { /* gone */ }
})();
