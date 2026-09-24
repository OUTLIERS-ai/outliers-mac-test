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
  "      ' reading ' + projects + ', exit ' + exitCode + '; it said: ' + said.slice(0, 600); };\n" +
  "  return { root, projects, port, base, cfgFile, info };");
swap("  assert.equal(tokens, 100000, 'the whole file was read (' + (size / 1048576).toFixed(1) + ' MB)');",
  "  if (tokens !== 100000) console.log(await s.info());\n" +
  "  assert.equal(tokens, 100000, 'the whole file was read (' + (size / 1048576).toFixed(1) + ' MB)');");
fs.writeFileSync(f, crlf ? s.replace(/\n/g, '\r\n') : s);
console.log('instrumented ' + f + ' (' + n0 + ' -> ' + s.length + ' characters)');
