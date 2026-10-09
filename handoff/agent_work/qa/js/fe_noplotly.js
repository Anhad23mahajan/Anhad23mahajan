// What does the page do when cdn.plot.ly is unreachable (venue Wi-Fi, corporate proxy)? Plotly undefined.
const { JSDOM } = require('jsdom'); const fs = require('fs'); const BASE = process.argv[2];
const HTML = fs.readFileSync('/home/user/Anhad23mahajan/lumen/static/index.html', 'utf8'); const errors = [];
const dom = new JSDOM(HTML, { runScripts: 'dangerously', pretendToBeVisual: true, url: BASE + '/', beforeParse(w) { w.fetch = (p, o) => fetch(BASE + p, o); w.addEventListener('error', e => errors.push(e.message)); } });
(async () => {
  const w = dom.window; console.log('typeof Plotly =', typeof w.Plotly);
  const demo = await (await fetch(BASE + '/api/demo', { method: 'POST' })).json(); w.render(demo);
  await new Promise(r => setTimeout(r, 1500));
  const d = w.document; console.log('KPIs rendered:', d.querySelectorAll('.kpi').length, '| insights rendered:', d.querySelectorAll('.ins').length, '| chart containers:', d.querySelectorAll('#charts .chart').length, '| #ferr:', JSON.stringify(d.querySelector('#ferr').textContent), '| visible error banner:', JSON.stringify(d.querySelector('#uerr').textContent));
  console.log('uncaught JS errors:', errors);
  console.log('new Error([{type:..}]).message =', new Error([{ type: 'missing', loc: ['body', 'x'] }]).message);
  process.exit(0);
})();
