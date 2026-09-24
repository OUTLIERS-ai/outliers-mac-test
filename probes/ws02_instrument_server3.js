'use strict';
// Probe for FleetView (wave 1 fix round 2), measurement only: rewrites tests/server3.test.js in a
// downloaded copy so that, when "the page keeps answering while 1 big log file is read" fails,
// its message also says which FleetView answered (its log folder and process number, from
// /api/meta), whether the FleetView this test started is still running (its exit code) and what
// it printed on its error output. Never used in a member repo.
//
//   node ../_mactest/probes/ws02_instrument_server3.js      (run in a FleetView folder)
const fs = require('fs');
const f = 'tests/server3.test.js';
const raw = fs.readFileSync(f, 'utf8');
const crlf = raw.includes('\r\n');
let s = raw.replace(/\r\n/g, '\n');
const n0 = s.length;
function swap(a, b) {
  if (!s.includes(a)) { console.error('instrument: text not found: ' + a.slice(0, 80)); process.exit(1); }
  s = s.replace(a, b);
}
swap("const child = spawn(process.execPath, [WATCHER], { env, windowsHide: true, stdio: 'ignore' });\n  t.after(() => { try { child.kill(); } catch { /* gone */ } });\n  const base = `http://127.0.0.1:${port}`;\n  await waitFor(base + '/api/meta');\n  return { root, projects, port, base, cfgFile };",
  "const child = spawn(process.execPath, [WATCHER], { env, windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'] });\n" +
  "  let said = '', exitCode = 'still running';\n" +
  "  child.stderr.on('data', (d) => { said += d; });\n" +
  "  child.on('exit', (c) => { exitCode = String(c); });\n" +
  "  t.after(() => { try { child.kill(); } catch { /* gone */ } });\n" +
  "  const base = `http://127.0.0.1:${port}`;\n  await waitFor(base + '/api/meta');\n" +
  "  const info = async () => { let m = {}; try { m = await (await fetch(base + '/api/meta')).json(); } catch (e) { m = { error: String(e) }; }\n" +
  "    return 'PROBE port ' + port + '; answered by pid ' + m.pid + ' reading ' + m.logsFolder + '; this test\\'s FleetView pid ' + child.pid +\n" +
  "      ' reading ' + projects + ', exit ' + exitCode + '; it said: ' + said.slice(0, 2000) +\n" +
  "      '; its record: ' + await fetch(base + '/api/probe').then((r) => r.text()).catch((e) => String(e)); };\n" +
  "  return { root, projects, port, base, cfgFile, info };");
swap("  assert.equal(tokens, 100000, 'the whole file was read (' + (size / 1048576).toFixed(1) + ' MB)');",
  "  if (tokens !== 100000) console.log(await s.info());\n" +
  "  assert.equal(tokens, 100000, 'the whole file was read (' + (size / 1048576).toFixed(1) + ' MB)');");
fs.writeFileSync(f, crlf ? s.replace(/\n/g, '\r\n') : s);
console.log('instrumented ' + f + ' (' + n0 + ' -> ' + s.length + ' characters)');

// Part 2: FleetView itself (the downloaded copy only) tells its error output what chokidar
// reported and what its reading line did, with times, so the failure message above shows them.
const w = 'watcher.js';
const wraw = fs.readFileSync(w, 'utf8');
const wcrlf = wraw.includes('\r\n');
let ws = wraw.replace(/\r\n/g, '\n');
function wswap(a, b) {
  if (!ws.includes(a)) { console.error('instrument: watcher text not found: ' + a.slice(0, 80)); process.exit(1); }
  ws = ws.replace(a, b);
}
wswap("function readNext() {\n  if (reading) return;",
  "const T0 = Date.now();\nconst PROBE = [];\nconst say = (s) => { if (PROBE.length < 400) PROBE.push('+' + (Date.now() - T0) + 'ms ' + s); };\n" +
  "app.get('/api/probe', (req, res) => res.json(PROBE));\n" +
  "function readNext() {\n  say('readNext reading=' + reading + ' line=' + readLine.length);\n  if (reading) return;");
wswap("  const next = () => { reading = false; setImmediate(readNext); };",
  "  say('start ' + path.basename(f));\n  const next = () => { say('done ' + path.basename(f)); reading = false; setImmediate(readNext); };");
wswap("  watcher.on('add', f => { if (want(f)) readSafely(f); });",
  "  watcher.on('all', (ev, p) => say('chokidar ' + ev + ' ' + p));\n  watcher.on('ready', () => say('chokidar ready'));\n" +
  "  watcher.on('add', f => { if (want(f)) readSafely(f); });");
fs.writeFileSync(w, wcrlf ? ws.replace(/\n/g, '\r\n') : ws);
console.log('instrumented ' + w);
