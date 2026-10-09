/* 08-a11y-enhancer.js : accessibility layer that needs NO edits to index.html's own script (effort S, risk low).
   load it with: script tag, src=/assets/a11y-enhancer.js, defer
   Everything is derived from the DOM with MutationObservers, so it survives a restyle.  Adds:
   - role=tablist/tab/tabpanel + aria-selected (+ arrow-key navigation) for "Raw Input / Cleaned Output"
   - aria-live="polite" on the answer area and the summary (answers/spinner were never announced)
   - role="img" + aria-label on every chart container (Plotly SVGs otherwise read out as a string of tick labels)
   - aria-busy mirrored from the .busy class, and real `disabled` on busy buttons (pointer-events:none alone did not stop Enter/Space)
   - moves focus to the summary heading when the dashboard appears (focus used to be lost to <body> when the hero was hidden)
   - Enter during IME composition no longer submits a question
   NOT done here (needs the app's own JS): chart-level text summaries are generic ("chart: <title>"). The diff 03 does better. */
(function () {
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  function tabs() {
    const raw = $('#tab-raw'), proc = $('#tab-processed'), box = $('#preview-box'); if (!raw || !proc) return;
    raw.parentElement.setAttribute('role', 'tablist'); raw.parentElement.setAttribute('aria-label', 'Data preview');
    [raw, proc].forEach(t => { t.setAttribute('role', 'tab'); t.setAttribute('aria-controls', 'preview-box'); const on = t.classList.contains('active'); t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1 });
    if (box) { box.setAttribute('role', 'tabpanel'); box.setAttribute('aria-labelledby', raw.classList.contains('active') ? 'tab-raw' : 'tab-processed') }
  }
  function live() {
    const ans = $('#ans'); if (ans) ans.setAttribute('aria-live', 'polite');
    const q = $('#q'); if (q) { q.maxLength = 500; q.autocomplete = 'off' }
  }
  function charts() {
    $$('.chart, #fchart').forEach(c => {
      if (c.getAttribute('role')) return;
      const cap = c.previousElementSibling && c.previousElementSibling.matches('p.note,figcaption') ? c.previousElementSibling.textContent : '';
      const label = c.id === 'fchart' ? 'Forecast chart: ' + (($('#fnote') || {}).textContent || 'actual values and forecast with a likely range')
        : c.id === 'rc' ? 'Chart of the answer: ' + (($('#ans .a') || {}).textContent || '') : (cap ? 'Chart: ' + cap : 'Chart');
      c.setAttribute('role', 'img'); c.setAttribute('aria-label', label.slice(0, 300));
    });
  }
  function busy() {
    $$('.busy').forEach(el => { el.setAttribute('aria-busy', 'true'); if ('disabled' in el && !el.disabled) { el.disabled = true; el.dataset.busyDisabled = '1' } });
    $$('[aria-busy="true"]:not(.busy)').forEach(el => { el.setAttribute('aria-busy', 'false'); if (el.dataset.busyDisabled) { el.disabled = false; delete el.dataset.busyDisabled } });   // only undo what WE disabled
  }
  function focusSummary() {
    const app = $('#app'), h = $('.summary h3'); if (!app || !h) return;
    if (getComputedStyle(app).display !== 'none') { h.tabIndex = -1; h.focus({ preventScroll: true }) }
  }
  function all() { tabs(); live(); charts(); busy() }
  const mo = new MutationObserver(all); mo.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  new MutationObserver(focusSummary).observe($('#app'), { attributes: true, attributeFilter: ['style'] });
  document.addEventListener('click', e => { if (e.target.matches('#tab-raw,#tab-processed')) setTimeout(tabs, 0) });
  document.addEventListener('keydown', e => {
    if (e.target.matches('#q') && e.key === 'Enter' && e.isComposing) { e.stopImmediatePropagation(); e.preventDefault() }
    if (e.target.matches('#tab-raw,#tab-processed') && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) { const t = $(e.key === 'ArrowLeft' ? '#tab-raw' : '#tab-processed'); t.click(); t.focus() }
  }, true);
  all();
})();
