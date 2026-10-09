#!/usr/bin/env bash
# Vendor Plotly + fonts into static/ so the app makes ZERO third-party requests (and works offline / on conference wifi).
# Run from the repo root.  Versions are pinned; licences: plotly.js MIT, Figtree + Bricolage Grotesque SIL OFL 1.1.
set -euo pipefail
mkdir -p static/vendor/fonts && tmp=$(mktemp -d) && cd "$tmp"
npm pack plotly.js-basic-dist-min@2.35.2 @fontsource-variable/figtree@5.3.0 @fontsource-variable/bricolage-grotesque@5.3.0 >/dev/null
for t in *.tgz; do mkdir "x_${t%.tgz}" && tar xzf "$t" -C "x_${t%.tgz}"; done
cd - >/dev/null
cp "$tmp"/x_plotly*/package/plotly-basic.min.js static/vendor/plotly-basic-2.35.2.min.js
cp "$tmp"/x_fontsource-variable-figtree*/package/files/figtree-latin-{,ext-}wght-normal.woff2 static/vendor/fonts/
cp "$tmp"/x_fontsource-variable-bricolage*/package/files/bricolage-grotesque-latin-{,ext-}opsz-normal.woff2 static/vendor/fonts/
cp /path/to/snippets/01-vendor-assets/fonts.css static/vendor/fonts.css      # <- adjust path
cp "$tmp"/x_plotly*/package/LICENSE static/vendor/PLOTLY-LICENSE.txt
cp "$tmp"/x_fontsource-variable-figtree*/package/LICENSE static/vendor/fonts/FIGTREE-OFL.txt
cp "$tmp"/x_fontsource-variable-bricolage*/package/LICENSE static/vendor/fonts/BRICOLAGE-OFL.txt
ls -la static/vendor static/vendor/fonts
# then in static/index.html replace the 4 head lines (preconnect, google fonts <link>, cdn.plot.ly <script>) with:
#   <link rel="preload" href="/assets/vendor/fonts/figtree-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
#   <link rel="preload" href="/assets/vendor/fonts/bricolage-grotesque-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>
#   <link rel="stylesheet" href="/assets/vendor/fonts.css">
#   <script src="/assets/vendor/plotly-basic-2.35.2.min.js" defer></script>
