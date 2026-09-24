// Wave 1 leftover, FleetView (ws-02): why did "reading a big log hands control back between
// pieces" see a 619 ms gap once in 10 runs on the Intel test Mac (review/wave1-workspace.md)?
//
// Rebuilds the test's scene exactly (20,000 log lines, 256 KB pieces, a 5 ms timer) and prints,
// for 1 run: every piece's own time (the work between 2 hand-backs), every timer gap over 50 ms,
// and the heap size, so a slow piece (the work itself), a garbage-collection pause (run with
// --trace-gc, whose lines land between the gaps) and a machine stall (a gap with no slow piece
// and no collection) can be told apart. Run from the FleetView repo:
//     node --trace-gc ../_mactest/probes/ws02_big_log_gaps.js
// Prints only; writes nothing outside a throwaway folder.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const repo = process.cwd();
const { createStore } = require(path.join(repo, 'lib', 'sessions'));

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ws02-gaps-'));
const f = path.join(dir, 'chunky.jsonl');
const lines = [];
for (let i = 0; i < 20000; i++) lines.push(JSON.stringify({ type: 'assistant', sessionId: 'chunky', timestamp: new Date().toISOString(),
  message: { id: 'c' + i, model: 'claude-opus-5', stop_reason: 'end_turn', content: [{ type: 'text', text: 'x'.repeat(200) }], usage: { output_tokens: 1 } } }));
fs.writeFileSync(f, lines.join('\n') + '\n');

const store = createStore({ chunkBytes: 256 * 1024 });
const t0 = Date.now();
// Time each piece: wrap setImmediate while the read runs, so the time from 1 step starting to
// the next step being queued is the piece's own work.
const realSetImmediate = global.setImmediate;
const pieces = [];
const cpu = [];   // the CPU time the piece actually used (user + system), in ms
global.setImmediate = (fn, ...a) => realSetImmediate(() => {
  const s = process.hrtime.bigint(), c = process.cpuUsage();
  try { return fn(...a); } finally {
    pieces.push(Number(process.hrtime.bigint() - s) / 1e6);
    const d = process.cpuUsage(c); cpu.push((d.user + d.system) / 1000);
  }
}, ...a);
let last = Date.now(), worst = 0, ticks = 0;
const gaps = [];
const timer = setInterval(() => {
  const t = Date.now(), g = t - last;
  if (g > 50) gaps.push({ at: t - t0, gap: g, heapMB: Math.round(process.memoryUsage().heapUsed / 1048576) });
  worst = Math.max(worst, g); last = t; ticks++;
}, 5);
store.processFileAsync(f, () => {
  clearInterval(timer);
  global.setImmediate = realSetImmediate;
  const sorted = pieces.slice().sort((a, b) => b - a);
  console.log('RESULT pieces=%d total_ms=%d ticks=%d worst_gap_ms=%d', pieces.length, Date.now() - t0, ticks, worst);
  console.log('RESULT slowest pieces ms: %s', sorted.slice(0, 5).map((x) => x.toFixed(1)).join(' '));
  console.log('RESULT median piece ms: %s', sorted[Math.floor(sorted.length / 2)].toFixed(1));
  console.log('RESULT piece ms in order: %s', pieces.map((x) => x.toFixed(0)).join(' '));
  console.log('RESULT piece cpu ms in order: %s', cpu.map((x) => x.toFixed(0)).join(' '));
  const w = pieces.indexOf(sorted[0]);
  console.log('RESULT slowest piece: #%d wall %s ms, cpu %s ms', w + 1, pieces[w].toFixed(1), cpu[w].toFixed(1));
  for (const g of gaps) console.log('GAP at %d ms: %d ms, heap %d MB', g.at, g.gap, g.heapMB);
  console.log('RESULT tokensOut=%d', store.view(store.sessions.get('chunky')).tokensOut);
  fs.rmSync(dir, { recursive: true, force: true });
});
