"""Self-contained HTML sunburst (circular sector) visualization."""

from __future__ import annotations

import html
import json
import webbrowser
from pathlib import Path

from .scanner import ScanResult, build_tree
from .sizes import format_size


def render_html_report(
    result: ScanResult,
    *,
    max_depth: int = 5,
    max_children: int = 48,
) -> str:
    """Return a standalone HTML document with a circular sector layout."""
    tree = build_tree(result, max_depth=max_depth, max_children=max_children)
    payload = {
        "root": str(result.root),
        "total_size": result.total_size,
        "total_size_human": format_size(result.total_size),
        "file_count": result.file_count,
        "dir_count": result.dir_count,
        "disk": {
            "used_human": format_size(result.disk_used or 0) if result.disk_used is not None else None,
            "free_human": format_size(result.disk_free or 0) if result.disk_free is not None else None,
            "total_human": format_size(result.disk_total or 0) if result.disk_total is not None else None,
        },
        "tree": tree.to_dict(),
    }
    data_json = json.dumps(payload, ensure_ascii=False)
    # Prevent </script> breakouts inside JSON strings.
    data_json = data_json.replace("<", "\\u003c").replace(">", "\\u003e")
    title = html.escape(f"Disk-Space-Scanner — {result.root}")
    return _HTML_TEMPLATE.replace("__TITLE__", title).replace("__DATA__", data_json)


def write_html_report(
    result: ScanResult,
    output: Path,
    *,
    max_depth: int = 5,
    max_children: int = 48,
    open_browser: bool = False,
) -> Path:
    """Write the HTML report to ``output`` and optionally open it."""
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_html_report(result, max_depth=max_depth, max_children=max_children),
        encoding="utf-8",
    )
    if open_browser:
        webbrowser.open(output.as_uri())
    return output


# Standalone page: works in any modern browser on Windows, macOS, and Linux.
# No CDN / network required — pure SVG + vanilla JS.
_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>__TITLE__</title>
<style>
  :root {
    --bg0: #0f1714;
    --bg1: #1a2621;
    --ink: #e8f0ec;
    --muted: #9bb0a6;
    --accent: #3dbf8f;
    --accent-2: #e6b35a;
    --panel: rgba(26, 38, 33, 0.92);
    --line: rgba(232, 240, 236, 0.12);
    --font-display: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    --font-mono: "Cascadia Code", "SF Mono", Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    min-height: 100%;
    background:
      radial-gradient(1200px 600px at 12% -10%, #243d34 0%, transparent 55%),
      radial-gradient(900px 500px at 100% 0%, #2a3d34 0%, transparent 50%),
      linear-gradient(160deg, var(--bg0), #121c18 55%, #0c1210);
    color: var(--ink);
    font-family: var(--font-display);
  }
  body { display: grid; grid-template-rows: auto 1fr; min-height: 100vh; }
  header {
    padding: 1.25rem 1.5rem 0.75rem;
    border-bottom: 1px solid var(--line);
  }
  header .brand {
    font-size: 0.75rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--accent);
    margin: 0 0 0.35rem;
  }
  header h1 {
    margin: 0;
    font-size: clamp(1.1rem, 2.4vw, 1.55rem);
    font-weight: 650;
    word-break: break-all;
  }
  header .meta {
    margin-top: 0.55rem;
    color: var(--muted);
    font-size: 0.92rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.25rem;
  }
  main {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(220px, 320px);
    gap: 0;
    min-height: 0;
  }
  @media (max-width: 860px) {
    main { grid-template-columns: 1fr; grid-template-rows: 1fr auto; }
  }
  #chart-wrap {
    position: relative;
    min-height: 420px;
    padding: 0.5rem;
  }
  #chart {
    width: 100%;
    height: min(78vh, 820px);
    display: block;
    cursor: default;
  }
  #chart path.sector {
    stroke: rgba(15, 23, 20, 0.55);
    stroke-width: 1;
    transition: opacity 120ms ease, filter 120ms ease;
  }
  #chart path.sector:hover {
    filter: brightness(1.15);
  }
  #chart path.sector.dim { opacity: 0.28; }
  #chart text.center-label {
    fill: var(--ink);
    text-anchor: middle;
    font-family: var(--font-display);
  }
  aside {
    border-left: 1px solid var(--line);
    background: var(--panel);
    padding: 1rem 1.1rem 1.5rem;
    overflow: auto;
  }
  @media (max-width: 860px) {
    aside { border-left: none; border-top: 1px solid var(--line); }
  }
  aside h2 {
    margin: 0 0 0.65rem;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
  }
  #detail .name {
    font-size: 1.05rem;
    font-weight: 600;
    word-break: break-word;
  }
  #detail .path {
    margin-top: 0.35rem;
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 0.78rem;
    word-break: break-all;
  }
  #detail .size {
    margin-top: 0.85rem;
    font-size: 1.35rem;
    color: var(--accent-2);
    font-variant-numeric: tabular-nums;
  }
  #detail .kind {
    display: inline-block;
    margin-top: 0.55rem;
    padding: 0.15rem 0.45rem;
    border: 1px solid var(--line);
    border-radius: 4px;
    font-size: 0.75rem;
    color: var(--muted);
  }
  #legend {
    margin-top: 1.4rem;
    display: grid;
    gap: 0.4rem;
  }
  .swatch {
    display: grid;
    grid-template-columns: 14px 1fr auto;
    gap: 0.55rem;
    align-items: center;
    font-size: 0.85rem;
  }
  .swatch i {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    display: block;
  }
  .swatch .sz {
    color: var(--muted);
    font-variant-numeric: tabular-nums;
    font-family: var(--font-mono);
    font-size: 0.78rem;
  }
  .hint {
    margin-top: 1.25rem;
    color: var(--muted);
    font-size: 0.8rem;
    line-height: 1.45;
  }
</style>
</head>
<body>
<header>
  <p class="brand">Disk-Space-Scanner</p>
  <h1 id="root-title"></h1>
  <div class="meta" id="meta"></div>
</header>
<main>
  <div id="chart-wrap">
    <svg id="chart" viewBox="0 0 800 800" role="img" aria-label="Circular sector disk usage chart"></svg>
  </div>
  <aside>
    <h2>Selection</h2>
    <div id="detail">
      <div class="name">—</div>
      <div class="path"></div>
      <div class="size"></div>
      <div class="kind"></div>
    </div>
    <h2 style="margin-top:1.5rem">Top sectors (ring 1)</h2>
    <div id="legend"></div>
    <p class="hint">
      Folders are annular sectors; each file is its own sector.
      Hover a sector for details. Click a folder to zoom; click the center to zoom out.
      Works offline in any modern browser (Windows, macOS, Linux).
    </p>
  </aside>
</main>
<script id="payload" type="application/json">__DATA__</script>
<script>
(function () {
  const DATA = JSON.parse(document.getElementById("payload").textContent);
  const COLORS = [
    "#3dbf8f", "#e6b35a", "#5aa7d6", "#d67a8a", "#7bc96f",
    "#c4a35a", "#6ec6c0", "#e08e6d", "#8fb3a5", "#b7d14a",
    "#4f8f7a", "#db9e3a", "#6b9bb8", "#c96b7c", "#9ac27a"
  ];

  function formatSize(bytes) {
    const units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"];
    let v = Math.max(0, Number(bytes) || 0);
    let i = 0;
    while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
    if (i === 0) return Math.round(v) + " B";
    return v.toFixed(1) + " " + units[i];
  }

  document.getElementById("root-title").textContent = DATA.root;
  const meta = document.getElementById("meta");
  meta.innerHTML = [
    "<span>Total scanned: <strong>" + DATA.total_size_human + "</strong></span>",
    "<span>" + DATA.file_count + " files · " + DATA.dir_count + " dirs</span>",
    DATA.disk && DATA.disk.total_human
      ? "<span>Mount: " + DATA.disk.used_human + " used / " + DATA.disk.free_human + " free</span>"
      : ""
  ].filter(Boolean).join("");

  const svg = document.getElementById("chart");
  const cx = 400, cy = 400;
  const INNER = 70;
  const RING = 52;
  let focus = DATA.tree;
  let focusStack = [];

  function colorFor(path, depth, index) {
    if (!path) return "#5a6b63";
    let h = 0;
    for (let i = 0; i < path.length; i++) h = (h * 31 + path.charCodeAt(i)) >>> 0;
    return COLORS[(h + depth * 3 + index) % COLORS.length];
  }

  function polar(r, a) {
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  }

  function arcPath(r0, r1, a0, a1) {
    const large = (a1 - a0) > Math.PI ? 1 : 0;
    const p0 = polar(r1, a0), p1 = polar(r1, a1);
    const p2 = polar(r0, a1), p3 = polar(r0, a0);
    if (a1 - a0 >= 2 * Math.PI - 1e-9) {
      // Full ring — split into two arcs for valid SVG.
      const mid = a0 + Math.PI;
      const m1 = polar(r1, mid), m0 = polar(r0, mid);
      return [
        "M", p0[0], p0[1],
        "A", r1, r1, 0, 1, 1, m1[0], m1[1],
        "A", r1, r1, 0, 1, 1, p0[0], p0[1],
        "L", p3[0], p3[1],
        "A", r0, r0, 0, 1, 0, m0[0], m0[1],
        "A", r0, r0, 0, 1, 0, p3[0], p3[1],
        "Z"
      ].join(" ");
    }
    return [
      "M", p0[0], p0[1],
      "A", r1, r1, 0, large, 1, p1[0], p1[1],
      "L", p2[0], p2[1],
      "A", r0, r0, 0, large, 0, p3[0], p3[1],
      "Z"
    ].join(" ");
  }

  function layout(node, depth, a0, a1, out) {
    if (!node || node.size <= 0) return;
    out.push({ node, depth, a0, a1 });
    const kids = (node.children || []).filter(c => c.size > 0);
    if (!kids.length) return;
    const total = kids.reduce((s, c) => s + c.size, 0) || 1;
    let angle = a0;
    const span = a1 - a0;
    kids.forEach((child) => {
      const next = angle + span * (child.size / total);
      layout(child, depth + 1, angle, next, out);
      angle = next;
    });
  }

  function setDetail(node) {
    const el = document.getElementById("detail");
    el.querySelector(".name").textContent = node.name || node.path || "(root)";
    el.querySelector(".path").textContent = node.path || "";
    el.querySelector(".size").textContent = formatSize(node.size);
    el.querySelector(".kind").textContent =
      node.kind === "file" ? "file sector" :
      node.kind === "dir" ? "folder sector" : "grouped sector";
  }

  function renderLegend(node) {
    const box = document.getElementById("legend");
    const kids = (node.children || []).slice().sort((a, b) => b.size - a.size).slice(0, 12);
    box.innerHTML = kids.map((c, i) => {
      const col = colorFor(c.path || c.name, 1, i);
      return '<div class="swatch"><i style="background:' + col + '"></i><span>' +
        (c.name || "").replace(/[<>&]/g, s => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[s])) +
        '</span><span class="sz">' + formatSize(c.size) + '</span></div>';
    }).join("") || "<div class='hint'>No child sectors</div>";
  }

  function draw() {
    const segments = [];
    layout(focus, 0, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI, segments);
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Center disk
    const center = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    center.setAttribute("cx", cx);
    center.setAttribute("cy", cy);
    center.setAttribute("r", INNER - 8);
    center.setAttribute("fill", "#15201b");
    center.setAttribute("stroke", "rgba(232,240,236,0.15)");
    center.style.cursor = focusStack.length ? "pointer" : "default";
    center.addEventListener("click", () => {
      if (!focusStack.length) return;
      focus = focusStack.pop();
      draw();
    });
    svg.appendChild(center);

    const label1 = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label1.setAttribute("x", cx);
    label1.setAttribute("y", cy - 6);
    label1.setAttribute("class", "center-label");
    label1.setAttribute("font-size", "13");
    label1.textContent = focusStack.length ? "zoom out" : "root";
    svg.appendChild(label1);

    const label2 = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label2.setAttribute("x", cx);
    label2.setAttribute("y", cy + 14);
    label2.setAttribute("class", "center-label");
    label2.setAttribute("font-size", "12");
    label2.setAttribute("fill", "#9bb0a6");
    label2.textContent = formatSize(focus.size);
    svg.appendChild(label2);

    const maxDepth = Math.max(1, ...segments.map(s => s.depth));
    segments.filter(s => s.depth > 0).forEach((seg, idx) => {
      const r0 = INNER + (seg.depth - 1) * RING;
      const r1 = INNER + seg.depth * RING;
      if (r1 > 390) return;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", arcPath(r0, r1, seg.a0, seg.a1));
      path.setAttribute("fill", colorFor(seg.node.path || seg.node.name, seg.depth, idx));
      path.setAttribute("class", "sector");
      path.style.cursor = seg.node.kind === "dir" && (seg.node.children || []).length ? "pointer" : "default";
      path.addEventListener("mouseenter", () => {
        svg.querySelectorAll("path.sector").forEach(p => p.classList.add("dim"));
        path.classList.remove("dim");
        setDetail(seg.node);
      });
      path.addEventListener("mouseleave", () => {
        svg.querySelectorAll("path.sector").forEach(p => p.classList.remove("dim"));
        setDetail(focus);
      });
      path.addEventListener("click", (ev) => {
        ev.stopPropagation();
        if (seg.node.kind === "dir" && (seg.node.children || []).length) {
          focusStack.push(focus);
          focus = seg.node;
          draw();
        } else {
          setDetail(seg.node);
        }
      });
      svg.appendChild(path);
    });

    setDetail(focus);
    renderLegend(focus);
  }

  draw();
})();
</script>
</body>
</html>
"""
