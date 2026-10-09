const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const payloads = [
  "<script>alert(1)</script>",
  "<img src=x onerror=alert(1)>",
  "\" onmouseover=\"alert(1)",
  "'><svg onload=alert(1)>",
  "javascript:alert(1)",
  "Normal product name",
  "<a href=\"javascript:alert(1)\">click</a>",
];

for (const p of payloads) {
  const out = esc(p);
  console.log(JSON.stringify(p), "->", JSON.stringify(out));
  // Simulate the title="..." attribute sink exactly as index.html builds it:
  const attrHtml = `<td title="${out}">${out}</td>`;
  console.log("  as attribute context:", attrHtml);
}

// Specifically check: does esc() leave a raw single-quote that could matter
// if some OTHER part of the code used single-quoted attributes anywhere?
console.log("\nsingle-quote handling:", JSON.stringify(esc("'quoted'")));
