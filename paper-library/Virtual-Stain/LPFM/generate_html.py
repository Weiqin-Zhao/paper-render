#!/usr/bin/env python3
"""Generate LPFM presentation HTML file in PixCell design style."""

import os

OUTPUT = os.path.join(os.path.dirname(__file__), "LPFM_presentation.html")


def build_html() -> str:
    """Build the complete HTML string for the LPFM presentation."""

    # ────────────────────────────────────────────
    # CSS (adapted from PixCell, hero gradient → teal theme)
    # ────────────────────────────────────────────
    CSS = r"""
  /* ===== CSS Reset & Base ===== */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #fafbfc;
    --card-bg: #ffffff;
    --text: #1a1a2e;
    --text-secondary: #5a5a7a;
    --accent: #0d9488;
    --accent-light: #f0fdfa;
    --accent-dark: #134e4a;
    --border: #e2e8f0;
    --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04);
    --shadow-lg: 0 10px 25px -3px rgba(0,0,0,0.08), 0 4px 6px -2px rgba(0,0,0,0.03);
    --radius: 12px;
    --radius-sm: 8px;
    --teal: #0d9488;
    --teal-light: #f0fdfa;
    --amber: #d97706;
    --amber-light: #fffbeb;
    --rose: #e11d48;
    --rose-light: #fff1f2;
    --emerald: #059669;
    --emerald-light: #ecfdf5;
    --blue: #2563eb;
    --blue-light: #eff6ff;
    --purple: #7c3aed;
    --purple-light: #f5f3ff;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    transition: background 0.35s ease, color 0.35s ease;
  }

  /* ===== Dark Theme ===== */
  body.dark {
    --bg: #0d1017;
    --card-bg: #161b22;
    --text: #e6edf3;
    --text-secondary: #8b949e;
    --accent: #5eead4;
    --accent-light: #0f2a2a;
    --accent-dark: #99f6e4;
    --border: #30363d;
    --shadow: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -1px rgba(0,0,0,0.25);
    --shadow-lg: 0 10px 25px -3px rgba(0,0,0,0.5), 0 4px 6px -2px rgba(0,0,0,0.3);
    --teal: #5eead4;
    --teal-light: #0f2a2a;
    --amber: #fbbf24;
    --amber-light: #2a2000;
    --rose: #fb7185;
    --rose-light: #2a0f14;
    --emerald: #34d399;
    --emerald-light: #0f2a1e;
    --blue: #60a5fa;
    --blue-light: #0f1a2a;
    --purple: #a78bfa;
    --purple-light: #1a0f2a;
  }
  body.dark .hero {
    background: linear-gradient(135deg, #064e3b 0%, #0d4f6e 50%, #0f766e 100%);
  }
  body.dark .hero::before {
    background: radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%);
  }
  body.dark .hero::after {
    background: radial-gradient(circle, rgba(255,255,255,0.03) 0%, transparent 70%);
  }
  body.dark .hero .tag {
    background: rgba(255,255,255,0.1);
    border-color: rgba(255,255,255,0.08);
  }
  body.dark .toc-sidebar {
    box-shadow: 2px 0 12px rgba(0,0,0,0.3);
  }
  body.dark .toc-sidebar a:hover { background: var(--accent-light); }
  body.dark .toc-sidebar a.active { background: var(--accent-light); }
  body.dark .menu-toggle { color: var(--text); }
  /* Box overrides */
  body.dark .box-insight {
    background: #1a1840;
    border-color: #312e81;
    color: #c7d2fe;
  }
  body.dark .box-warn {
    background: #2a2000;
    border-color: #854d0e;
    color: #fde68a;
  }
  body.dark .box-note {
    background: #0f2a2a;
    border-color: #115e59;
    color: #99f6e4;
  }
  body.dark .box-key {
    background: #2a0f14;
    border-color: #9f1239;
    color: #fecdd3;
  }
  /* Table overrides */
  body.dark thead th {
    background: #1c2128;
  }
  body.dark tbody td {
    border-bottom-color: #21262d;
  }
  body.dark tbody tr:hover { background: #1c2128; }
  /* Flow diagram */
  body.dark .flow {
    background: #111820;
  }
  body.dark .flow-box.highlight {
    background: #0f2a2a;
    border-color: #115e59;
    color: #99f6e4;
  }
  body.dark .flow-box.green {
    background: #0f2a1e;
    border-color: #065f46;
    color: #6ee7b7;
  }
  body.dark .flow-box.amber {
    background: #2a2000;
    border-color: #92400e;
    color: #fde68a;
  }
  body.dark .flow-box.purple {
    background: #1a0f2a;
    border-color: #5b21b6;
    color: #c4b5fd;
  }
  /* Bar chart */
  body.dark .bar-track {
    background: #1c2128;
  }
  /* Image placeholder */
  body.dark .img-placeholder {
    background: linear-gradient(135deg, #111820 0%, #1c2128 100%);
    border-color: #30363d;
  }
  body.dark .img-placeholder:hover {
    border-color: var(--accent);
    background: linear-gradient(135deg, #0f2a2a 0%, #0f2a2a 100%);
  }
  body.dark .img-placeholder .ph-caption { color: #6e7681; }
  body.dark .img-placeholder .ph-filename {
    color: var(--accent);
    background: rgba(94,234,212,0.1);
  }
  /* Formula / code blocks */
  body.dark .formula {
    background: #111820;
  }
  /* Timeline */
  body.dark .timeline-tag {
    background: #1c2128;
  }
  body.dark .timeline-item::before {
    border-color: var(--card-bg);
  }
  /* Discussion cards */
  body.dark .discussion-card summary:hover { background: #1c2128; }
  /* Footer */
  body.dark footer { border-top-color: var(--border); }
  /* Scrollbar for dark mode */
  body.dark ::-webkit-scrollbar { width: 8px; }
  body.dark ::-webkit-scrollbar-track { background: var(--bg); }
  body.dark ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
  body.dark ::-webkit-scrollbar-thumb:hover { background: #484f58; }

  /* ===== Top Controls Bar ===== */
  .top-controls {
    position: fixed;
    top: 20px;
    right: 24px;
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .ctrl-group {
    display: flex;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 3px;
    box-shadow: var(--shadow-md);
    backdrop-filter: blur(12px);
    transition: background 0.35s ease, border-color 0.35s ease;
  }
  .ctrl-btn {
    padding: 6px 18px;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    background: transparent;
    color: var(--text-secondary);
    transition: all 0.25s ease;
    letter-spacing: 0.5px;
    line-height: 1.4;
  }
  .ctrl-btn.active {
    background: var(--accent);
    color: #fff;
    box-shadow: 0 2px 8px rgba(13,148,136,0.3);
  }
  .theme-btn {
    padding: 6px 14px;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    font-size: 16px;
    background: transparent;
    color: var(--text-secondary);
    transition: all 0.25s ease;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .theme-btn:hover { color: var(--accent); }
  .theme-icon-light, .theme-icon-dark { transition: opacity 0.3s ease; }
  .theme-icon-dark { display: none; }
  body.dark .theme-icon-light { display: none; }
  body.dark .theme-icon-dark { display: inline; }

  /* ===== TOC / Nav ===== */
  .toc-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 280px;
    height: 100vh;
    background: var(--card-bg);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    z-index: 900;
    padding: 24px 16px;
    box-shadow: 2px 0 8px rgba(0,0,0,0.03);
    transition: transform 0.3s ease, background 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease;
  }
  .toc-sidebar .toc-title {
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--accent);
    margin-bottom: 16px;
    padding-left: 8px;
  }
  .toc-sidebar a {
    display: block;
    padding: 8px 12px;
    font-size: 13.5px;
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--radius-sm);
    transition: all 0.2s ease;
    line-height: 1.5;
    margin-bottom: 2px;
  }
  .toc-sidebar a:hover { background: var(--accent-light); color: var(--accent); }
  .toc-sidebar a.active { background: var(--accent-light); color: var(--accent); font-weight: 600; }
  .toc-sidebar a.sub { padding-left: 28px; font-size: 12.5px; }

  /* Mobile menu */
  .menu-toggle {
    display: none;
    position: fixed;
    top: 20px;
    left: 16px;
    z-index: 1001;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 12px;
    cursor: pointer;
    box-shadow: var(--shadow-md);
    font-size: 18px;
    line-height: 1;
  }

  /* ===== Main Content ===== */
  .main-content {
    margin-left: 280px;
    max-width: 900px;
    padding: 40px 48px 80px;
  }

  /* ===== Hero Header ===== */
  .hero {
    background: linear-gradient(135deg, #0d4f6e 0%, #0d9488 50%, #14b8a6 100%);
    border-radius: var(--radius);
    padding: 48px 44px;
    margin-bottom: 40px;
    color: #fff;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -60%;
    right: -20%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero::after {
    content: '';
    position: absolute;
    bottom: -40%;
    left: -10%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero h1 {
    font-size: 32px;
    font-weight: 800;
    line-height: 1.3;
    margin-bottom: 16px;
    position: relative;
    z-index: 1;
  }
  .hero .subtitle {
    font-size: 15px;
    opacity: 0.9;
    position: relative;
    z-index: 1;
    line-height: 1.7;
  }
  .hero .tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 20px;
    position: relative;
    z-index: 1;
  }
  .hero .tag {
    background: rgba(255,255,255,0.18);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255,255,255,0.15);
  }

  /* ===== Section ===== */
  section {
    margin-bottom: 48px;
  }
  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--accent-light);
  }
  .section-num {
    background: var(--accent);
    color: #fff;
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 700;
    flex-shrink: 0;
  }
  .section-header h2 {
    font-size: 24px;
    font-weight: 700;
    color: var(--text);
    line-height: 1.3;
  }

  .subsection h3 {
    font-size: 18px;
    font-weight: 700;
    color: var(--accent-dark);
    margin: 32px 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .subsection h3::before {
    content: '';
    width: 4px;
    height: 20px;
    background: var(--accent);
    border-radius: 2px;
    flex-shrink: 0;
  }

  .subsection h4 {
    font-size: 15px;
    font-weight: 700;
    color: var(--text);
    margin: 24px 0 12px;
  }

  p { margin-bottom: 14px; color: var(--text); }

  /* ===== Cards ===== */
  .card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: var(--shadow);
  }
  .card-accent {
    border-left: 4px solid var(--accent);
  }

  /* ===== Insight / Note / Warning boxes ===== */
  .box {
    border-radius: var(--radius-sm);
    padding: 16px 20px;
    margin: 16px 0;
    font-size: 14.5px;
    line-height: 1.7;
  }
  .box-insight {
    background: var(--purple-light);
    border: 1px solid #ddd6fe;
    color: #5b21b6;
  }
  .box-insight::before { content: '\01F4A1 '; }
  .box-warn {
    background: var(--amber-light);
    border: 1px solid #fde68a;
    color: #92400e;
  }
  .box-warn::before { content: '\026A0\0FE0F '; }
  .box-note {
    background: var(--teal-light);
    border: 1px solid #99f6e4;
    color: #134e4a;
  }
  .box-note::before { content: '\01F4CC '; }
  .box-key {
    background: var(--rose-light);
    border: 1px solid #fecdd3;
    color: #9f1239;
  }
  .box-key::before { content: '\01F511 '; }

  /* ===== Tables ===== */
  .table-wrap {
    overflow-x: auto;
    margin: 16px 0;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  thead th {
    background: #f8fafc;
    font-weight: 700;
    text-align: left;
    padding: 12px 16px;
    border-bottom: 2px solid var(--border);
    color: var(--text);
    white-space: nowrap;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  tbody td {
    padding: 10px 16px;
    border-bottom: 1px solid #f1f5f9;
    color: var(--text-secondary);
  }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:hover { background: #f8fafc; }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
  td strong { color: var(--text); }

  /* ===== Flow Diagrams ===== */
  .flow {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
    margin: 20px 0;
    padding: 24px;
    background: #f8fafc;
    border-radius: var(--radius);
    border: 1px solid var(--border);
  }
  .flow-row {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .flow-box {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 18px;
    font-size: 13.5px;
    font-weight: 600;
    color: var(--text);
    box-shadow: var(--shadow);
    text-align: center;
    max-width: 300px;
  }
  .flow-box.highlight {
    background: var(--accent-light);
    border-color: #99f6e4;
    color: var(--accent-dark);
  }
  .flow-box.green {
    background: var(--emerald-light);
    border-color: #a7f3d0;
    color: #065f46;
  }
  .flow-box.amber {
    background: var(--amber-light);
    border-color: #fde68a;
    color: #92400e;
  }
  .flow-box.purple {
    background: var(--purple-light);
    border-color: #ddd6fe;
    color: #5b21b6;
  }
  .flow-box small {
    display: block;
    font-weight: 400;
    font-size: 11.5px;
    margin-top: 4px;
    opacity: 0.8;
  }
  .flow-arrow {
    color: var(--accent);
    font-size: 20px;
    font-weight: 700;
    line-height: 1;
    flex-shrink: 0;
  }
  .flow-arrow-down { text-align: center; padding: 4px 0; }
  .flow-label {
    font-size: 11.5px;
    color: var(--text-secondary);
    text-align: center;
    padding: 0 8px;
    font-style: italic;
  }

  /* ===== Bar Charts ===== */
  .chart-container {
    margin: 20px 0;
    padding: 24px;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
  }
  .chart-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 4px;
  }
  .chart-source {
    font-size: 11.5px;
    color: var(--text-secondary);
    margin-bottom: 16px;
    font-style: italic;
    opacity: 0.8;
  }
  .bar-chart { display: flex; flex-direction: column; gap: 10px; }
  .bar-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .bar-label {
    width: 100px;
    font-size: 12.5px;
    color: var(--text-secondary);
    text-align: right;
    flex-shrink: 0;
    font-weight: 500;
  }
  .bar-track {
    flex: 1;
    height: 28px;
    background: #f1f5f9;
    border-radius: 6px;
    overflow: hidden;
    position: relative;
  }
  .bar-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 1s ease-out;
    display: flex;
    align-items: center;
    padding-left: 10px;
  }
  .bar-value {
    font-size: 11.5px;
    font-weight: 700;
    color: #fff;
    white-space: nowrap;
    text-shadow: 0 1px 2px rgba(0,0,0,0.15);
  }

  /* ===== Comparison Grid ===== */
  .compare-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 16px;
    margin: 16px 0;
  }
  .compare-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 20px;
    box-shadow: var(--shadow);
  }
  .compare-card h5 {
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 10px;
    color: var(--accent);
  }
  .compare-card p {
    font-size: 13.5px;
    color: var(--text-secondary);
    margin-bottom: 0;
  }

  /* ===== Metric Highlight ===== */
  .metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin: 16px 0;
  }
  .metric-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 16px;
    text-align: center;
    box-shadow: var(--shadow);
  }
  .metric-value {
    font-size: 28px;
    font-weight: 800;
    color: var(--accent);
    line-height: 1.2;
  }
  .metric-label {
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 6px;
    font-weight: 500;
  }
  .metric-card.green .metric-value { color: var(--emerald); }
  .metric-card.amber .metric-value { color: var(--amber); }
  .metric-card.rose .metric-value { color: var(--rose); }

  /* ===== Image Placeholder ===== */
  .img-placeholder {
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    border: 2px dashed #cbd5e1;
    border-radius: var(--radius);
    padding: 40px 24px;
    text-align: center;
    margin: 20px 0;
    position: relative;
    min-height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.3s ease;
  }
  .img-placeholder:hover {
    border-color: var(--accent);
    background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
  }
  .img-placeholder .icon {
    font-size: 36px;
    opacity: 0.5;
  }
  .img-placeholder .ph-label {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-secondary);
  }
  .img-placeholder .ph-caption {
    font-size: 12.5px;
    color: #94a3b8;
    max-width: 500px;
    line-height: 1.5;
  }
  .img-placeholder .ph-filename {
    font-size: 11px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    color: var(--accent);
    background: rgba(13,148,136,0.08);
    padding: 3px 10px;
    border-radius: 4px;
    margin-top: 4px;
  }

  /* Actual figure images */
  .fig-img {
    width: 100%;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-md);
    margin: 20px 0 8px;
  }
  .fig-caption {
    font-size: 13px;
    color: var(--text-secondary);
    text-align: center;
    font-style: italic;
    margin-bottom: 16px;
  }

  /* ===== Lists ===== */
  ul, ol { margin: 12px 0; padding-left: 24px; }
  li {
    margin-bottom: 8px;
    color: var(--text-secondary);
    font-size: 15px;
    line-height: 1.7;
  }
  li strong { color: var(--text); }

  /* ===== Code-like blocks ===== */
  .formula {
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 16px 20px;
    margin: 16px 0;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 14px;
    color: var(--text);
    overflow-x: auto;
    text-align: center;
    line-height: 2;
  }

  /* ===== Loss Hierarchy ===== */
  .loss-hierarchy { display: flex; flex-direction: column; gap: 10px; margin: 20px 0; }
  .loss-item {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 18px;
    border-radius: var(--radius-sm);
    background: var(--card-bg);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    font-size: 14px;
  }
  .loss-icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    color: #fff;
    font-size: 14px;
    flex-shrink: 0;
  }

  /* ===== Discussion Cards ===== */
  .discussion-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 16px;
    overflow: hidden;
    box-shadow: var(--shadow);
  }
  .discussion-card summary {
    padding: 16px 20px;
    cursor: pointer;
    font-weight: 700;
    font-size: 15px;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 10px;
    transition: background 0.2s;
    list-style: none;
  }
  .discussion-card summary::-webkit-details-marker { display: none; }
  .discussion-card summary::before {
    content: '\25B8';
    color: var(--accent);
    font-size: 14px;
    transition: transform 0.2s;
    flex-shrink: 0;
  }
  .discussion-card[open] summary::before { transform: rotate(90deg); }
  .discussion-card summary:hover { background: #f8fafc; }
  .discussion-card .detail-body {
    padding: 0 20px 16px;
    font-size: 14.5px;
    color: var(--text-secondary);
    line-height: 1.7;
  }

  /* ===== Quick Reference Table ===== */
  .ref-table td:first-child {
    font-weight: 700;
    color: var(--accent-dark);
    white-space: nowrap;
    width: 160px;
  }

  /* ===== Responsive ===== */
  @media (max-width: 1024px) {
    .toc-sidebar { transform: translateX(-100%); }
    .toc-sidebar.open { transform: translateX(0); }
    .menu-toggle { display: block; }
    .main-content { margin-left: 0; padding: 24px 20px 60px; }
    .hero { padding: 32px 24px; }
    .hero h1 { font-size: 24px; }
    .top-controls { top: 12px; right: 12px; gap: 6px; }
    .ctrl-btn { padding: 5px 12px; font-size: 13px; }
    .theme-btn { padding: 5px 10px; font-size: 14px; }
  }

  /* ===== Animations ===== */
  .fade-in {
    opacity: 0;
    transform: translateY(16px);
    transition: opacity 0.5s ease, transform 0.5s ease;
  }
  .fade-in.visible {
    opacity: 1;
    transform: translateY(0);
  }

  /* Language — hide/show bilingual spans within TOC */
  .toc-sidebar .zh { display: inline; }
  .toc-sidebar .en { display: none; }
  body.en .toc-sidebar .zh { display: none; }
  body.en .toc-sidebar .en { display: inline; }
  /* Block-level bilingual: full element pairs */
  [lang-en] { display: none; }
  body.en [lang-zh] { display: none; }
  body.en [lang-en] { display: revert; }
  /* Fix revert for elements whose authored display differs from UA default */
  body.en .toc-sidebar a[lang-en] { display: block; }
  body.en .section-header h2[lang-en] { display: block; }
  body.en .subsection h3[lang-en] { display: flex; }

  /* Math */
  .katex { font-size: 1em !important; }
  .math-block { overflow-x: auto; padding: 12px 0; text-align: center; }

  /* Code */
  code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 13px; color: var(--rose); }

  /* Two col */
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 16px 0; }
  @media (max-width: 768px) { .two-col { grid-template-columns: 1fr; } }

  /* Print */
  @media print {
    .toc-sidebar, .top-controls, .menu-toggle { display: none !important; }
    .main-content { margin-left: 0; max-width: 100%; padding: 20px; }
    .hero { break-inside: avoid; }
    section { break-inside: avoid; }
  }
"""

    # ────────────────────────────────────────────
    # Helper: image placeholder (PixCell style)
    # ────────────────────────────────────────────
    # Emoji constants for image placeholders
    ICO_CAMERA = chr(0x1F4F7)
    ICO_BUILD = chr(0x1F3D7) + chr(0xFE0F)
    ICO_RULER = chr(0x1F4D0)
    ICO_CHART = chr(0x1F4CA)
    ICO_MAGNIFY = chr(0x1F50D)
    ICO_PALETTE = chr(0x1F3A8)
    ICO_DNA = chr(0x1F9EC)
    ICO_LOOP = chr(0x1F504)
    ICO_GRAPH = chr(0x1F4C8)
    ICO_BROOM = chr(0x1F9F9)
    ICO_FLASK = chr(0x1F9EA)

    def img_ph(ph_id: str, filename: str, label: str,
               caption_zh: str, caption_en: str, icon: str = ICO_CAMERA) -> str:
        return f'''    <div class="img-placeholder" id="{ph_id}">
      <div class="icon">{icon}</div>
      <div class="ph-label">{label}</div>
      <div class="ph-caption" lang-zh>{caption_zh}</div>
      <div class="ph-caption" lang-en>{caption_en}</div>
      <div class="ph-filename">{filename}</div>
    </div>'''

    # ────────────────────────────────────────────
    # Helper: bar chart (PixCell style)
    # ────────────────────────────────────────────
    def bar_chart(title_zh: str, title_en: str,
                  items: list, max_val: float,
                  source_zh: str = "", source_en: str = "") -> str:
        """items: list of (label, value, unit, gradient). source_zh/en: optional paper reference."""
        bars = ""
        for label, val, unit, gradient in items:
            pct = val / max_val * 100
            bars += f'''        <div class="bar-row">
          <div class="bar-label">{label}</div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct:.1f}%;background:{gradient};">
              <span class="bar-value">{val}{unit}</span>
            </div>
          </div>
        </div>
'''
        source_html = ""
        if source_zh:
            source_html = f'''      <div class="chart-source" lang-zh>{source_zh}</div>
      <div class="chart-source" lang-en>{source_en}</div>
'''
        return f'''    <div class="chart-container">
      <div class="chart-title" lang-zh>{title_zh}</div>
      <div class="chart-title" lang-en>{title_en}</div>
{source_html}      <div class="bar-chart">
{bars}      </div>
    </div>'''

    # ================================================================
    # BUILD HTML
    # ================================================================
    html_parts: list[str] = []

    # ── HEAD ──
    html_parts.append(f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LPFM - Lab Meeting Presentation</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}]}});"></script>
<style>{CSS}</style>
</head>
<body>
''')

    # ── TOP CONTROLS ──
    html_parts.append('''<!-- Top Controls: Theme + Language -->
<div class="top-controls">
  <div class="ctrl-group">
    <button class="theme-btn" id="btn-theme" onclick="toggleTheme()" title="Toggle Dark/Light Mode">
      <span class="theme-icon-light">&#9790;</span>
      <span class="theme-icon-dark">&#9788;</span>
    </button>
  </div>
  <div class="ctrl-group">
    <button class="ctrl-btn active" id="btn-zh" onclick="setLang('zh')">中文</button>
    <button class="ctrl-btn" id="btn-en" onclick="setLang('en')">EN</button>
  </div>
</div>

<!-- Mobile Menu Toggle -->
<button class="menu-toggle" onclick="toggleTOC()">☰</button>
''')

    # ── TOC SIDEBAR ──
    html_parts.append('''<!-- Table of Contents Sidebar -->
<nav class="toc-sidebar" id="toc">
  <div class="toc-title"><span class="zh">目录</span><span class="en">Contents</span></div>

  <a href="#motivation"><span class="zh">1. 动机与问题</span><span class="en">1. Motivation & Problem</span></a>
  <a href="#method"><span class="zh">2. 方法</span><span class="en">2. Method</span></a>
  <a href="#stage1" class="sub"><span class="zh">2.2 对比预训练</span><span class="en">2.2 Contrastive Pre-training</span></a>
  <a href="#stage2" class="sub"><span class="zh">2.3 条件扩散</span><span class="en">2.3 Conditional Diffusion</span></a>
  <a href="#prompt" class="sub"><span class="zh">2.5 Prompt 引导</span><span class="en">2.5 Prompt Guidance</span></a>
  <a href="#data"><span class="zh">3. 数据</span><span class="en">3. Data</span></a>
  <a href="#experiments"><span class="zh">4. 实验结果</span><span class="en">4. Experiments</span></a>
  <a href="#ablation"><span class="zh">5. 消融实验</span><span class="en">5. Ablation</span></a>
  <a href="#discussion"><span class="zh">6. 讨论与思考</span><span class="en">6. Discussion</span></a>
  <a href="#quickref"><span class="zh">7. 技术速查</span><span class="en">7. Quick Reference</span></a>
</nav>
''')

    # ── MAIN CONTENT ──
    html_parts.append('''<div class="main-content">
''')

    # ============================================================
    # HERO
    # ============================================================
    html_parts.append('''  <!-- ======================== HERO ======================== -->
  <header class="hero fade-in">
    <h1 lang-zh>LPFM: 统一的低层级病理基础模型</h1>
    <h1 lang-en>LPFM: A Unified Low-level Foundation Model for Enhancing Pathology Image Quality</h1>
    <div class="subtitle" lang-zh>
      Ziyi Liu, Zhe Xu, Jiabo Ma 等 (HKUST, Hao Chen 组)<br>
      用单一架构同时处理 6 类低层级病理图像增强任务
    </div>
    <div class="subtitle" lang-en>
      Ziyi Liu, Zhe Xu, Jiabo Ma et al. (HKUST, Hao Chen Group)<br>
      A single architecture addressing 6 categories of low-level pathology image enhancement tasks
    </div>
    <div class="tag-row">
      <span class="tag" lang-zh>病理图像增强</span>
      <span class="tag" lang-en>Pathology Enhancement</span>
      <span class="tag">Foundation Model</span>
      <span class="tag" lang-zh>对比学习预训练</span>
      <span class="tag" lang-en>Contrastive Pre-training</span>
      <span class="tag" lang-zh>条件扩散模型</span>
      <span class="tag" lang-en>Conditional Diffusion</span>
      <span class="tag" lang-zh>虚拟染色</span>
      <span class="tag" lang-en>Virtual Staining</span>
    </div>
  </header>
''')

    # ============================================================
    # SECTION 1: MOTIVATION
    # ============================================================
    html_parts.append(f'''  <!-- ======================== 1. MOTIVATION ======================== -->
  <section id="motivation" class="fade-in">
    <div class="section-header">
      <span class="section-num">1</span>
      <h2 lang-zh>动机与问题</h2>
      <h2 lang-en>Motivation &amp; Problem</h2>
    </div>

    <div class="subsection">
      <h3 lang-zh>1.1 病理图像质量问题的根源</h3>
      <h3 lang-en>1.1 Root Causes of Pathology Image Quality Issues</h3>

      <p lang-zh>病理图像的低层级质量问题在临床中普遍存在，贯穿整个成像链路：</p>
      <p lang-en>Low-level quality issues in pathology images are pervasive in clinical practice, spanning the entire imaging pipeline:</p>

      <div class="compare-grid">
        <div class="compare-card" style="border-top: 3px solid var(--rose);">
          <h5 lang-zh>制片端</h5>
          <h5 lang-en>Specimen Preparation</h5>
          <p lang-zh>组织固定、切片制备引入的物理伪影；物理染色（H&amp;E、IHC、PAS 等）成本高、耗时长、批次间不一致</p>
          <p lang-en>Physical artifacts from tissue fixation and sectioning; physical staining (H&amp;E, IHC, PAS, etc.) is costly, time-consuming, and inconsistent across batches</p>
        </div>
        <div class="compare-card" style="border-top: 3px solid var(--amber);">
          <h5 lang-zh>成像端</h5>
          <h5 lang-en>Imaging</h5>
          <p lang-zh>光学系统限制（衍射极限、色差）、对焦偏差（尤其厚切片）、扫描仪振动引入的运动模糊</p>
          <p lang-en>Optical system limitations (diffraction limit, chromatic aberration), focus drift (especially thick sections), motion blur from scanner vibration</p>
        </div>
        <div class="compare-card" style="border-top: 3px solid var(--teal);">
          <h5 lang-zh>数字化端</h5>
          <h5 lang-en>Digitization</h5>
          <p lang-zh>多分辨率金字塔的重采样引入的分辨率损失</p>
          <p lang-en>Resolution loss from multi-resolution pyramid resampling</p>
        </div>
      </div>

      <p lang-zh>这些退化直接影响下游诊断任务的准确性，如肿瘤边缘评估、有丝分裂计数等。</p>
      <p lang-en>These degradations directly impact downstream diagnostic accuracy, such as tumor margin assessment and mitotic counting.</p>
    </div>

    <div class="subsection">
      <h3 lang-zh>1.2 现有方法的碎片化问题</h3>
      <h3 lang-en>1.2 Fragmentation of Existing Methods</h3>

      <div class="box box-warn">
        <span lang-zh><strong>核心痛点</strong>：去噪、超分、去模糊、虚拟染色<strong>各用独立的专用模型</strong>，模型间存在<strong>相互干扰</strong>，临床需要<strong>维护多套不兼容的系统</strong>，缺乏统一生成框架。</span>
        <span lang-en><strong>Core Pain Point</strong>: Denoising, super-resolution, deblurring, and virtual staining each use <strong>separate specialized models</strong>. Models <strong>interfere with each other</strong>, clinics must <strong>maintain multiple incompatible systems</strong>, with no unified generative framework.</span>
      </div>
    </div>

    <div class="subsection">
      <h3 lang-zh>1.3 LPFM 的定位</h3>
      <h3 lang-en>1.3 LPFM Positioning</h3>

      <div class="box box-insight">
        <span lang-zh><strong>核心 Insight</strong>：图像修复和虚拟染色在底层是<strong>相互关联的</strong>——共享的特征表示可以实现协同增益。LPFM 构建<strong>首个统一的低层级病理基础模型</strong>，用单一架构同时处理 6 类任务。</span>
        <span lang-en><strong>Core Insight</strong>: Image restoration and virtual staining are <strong>fundamentally interconnected</strong> at the feature level—shared representations enable synergistic gains. LPFM builds the <strong>first unified low-level pathology foundation model</strong>, handling 6 task categories with a single architecture.</span>
      </div>

      <!-- 6 task categories flow -->
      <div class="flow">
        <div class="flow-row" style="gap:10px;flex-wrap:wrap;">
          <div class="flow-box highlight" lang-zh>超分辨率</div>
          <div class="flow-box highlight" lang-en>Super-Resolution</div>
          <div class="flow-box highlight" lang-zh>去模糊</div>
          <div class="flow-box highlight" lang-en>Deblurring</div>
          <div class="flow-box highlight" lang-zh>去噪</div>
          <div class="flow-box highlight" lang-en>Denoising</div>
        </div>
        <div class="flow-arrow-down"><div class="flow-arrow">&darr;</div></div>
        <div class="flow-row" style="gap:10px;flex-wrap:wrap;">
          <div class="flow-box green" lang-zh>复合退化修复</div>
          <div class="flow-box green" lang-en>Compound Degradation</div>
          <div class="flow-box amber" lang-zh>虚拟染色</div>
          <div class="flow-box amber" lang-en>Virtual Staining</div>
          <div class="flow-box purple" lang-zh>退化图虚拟染色</div>
          <div class="flow-box purple" lang-en>Degraded V. Staining</div>
        </div>
        <div class="flow-arrow-down"><div class="flow-arrow">&darr;</div><div class="flow-label" lang-zh>统一由 LPFM 处理</div><div class="flow-label" lang-en>All handled by LPFM</div></div>
      </div>

{img_ph("ph-fig1b", "fig1b_architecture.png",
        "Figure 1-b: LPFM Architecture Overview",
        "LPFM 整体架构概览图——集成对比预训练和 prompt 引导的条件扩散模型用于任务特定生成",
        "LPFM unified architecture overview integrating contrastive pre-training and prompt-guided conditional diffusion for task-specific generation",
        ICO_BUILD)}
    </div>
  </section>
''')

    # ============================================================
    # SECTION 2: METHOD
    # ============================================================
    html_parts.append(f'''  <!-- ======================== 2. METHOD ======================== -->
  <section id="method" class="fade-in">
    <div class="section-header">
      <span class="section-num">2</span>
      <h2 lang-zh>方法</h2>
      <h2 lang-en>Method</h2>
    </div>

    <div class="subsection">
      <h3 lang-zh>方法总览：两阶段框架</h3>
      <h3 lang-en>Method Overview: Two-Stage Framework</h3>

      <p lang-zh>LPFM 采用<strong>两阶段训练</strong>框架，核心思路是<strong>粗糙修复 &rarr; 精细精炼</strong>。</p>
      <p lang-en>LPFM uses a <strong>two-stage training</strong> framework, with the core idea of <strong>coarse restoration &rarr; fine refinement</strong>.</p>

      <!-- Two-stage pipeline flow -->
      <div class="flow">
        <div class="flow-row">
          <div class="flow-box" lang-zh>退化/源染色图像</div>
          <div class="flow-box" lang-en>Degraded/Source Image</div>
          <div class="flow-arrow">&rarr;</div>
          <div class="flow-box highlight"><strong>Stage 1</strong><small lang-zh>对比预训练 KL-AE</small><small lang-en>Contrastive KL-AE</small></div>
          <div class="flow-arrow">&rarr;</div>
          <div class="flow-box amber" lang-zh>粗糙修复<small>全局结构正确</small></div>
          <div class="flow-box amber" lang-en>Coarse Result<small>Globally correct</small></div>
          <div class="flow-arrow">&rarr;</div>
          <div class="flow-box purple"><strong>Stage 2</strong><small lang-zh>条件扩散精炼</small><small lang-en>Cond. Diffusion</small></div>
          <div class="flow-arrow">&rarr;</div>
          <div class="flow-box green" lang-zh>高质量输出</div>
          <div class="flow-box green" lang-en>High-Quality Output</div>
        </div>
        <div class="flow-arrow-down"><div class="flow-label" lang-zh>+ Text Prompt 控制任务类型</div><div class="flow-label" lang-en>+ Text Prompt controls task type</div></div>
      </div>

{img_ph("ph-fig8", "fig8_training_pipeline.png",
        "Figure 8: LPFM Training Pipeline",
        "LPFM 训练阶段完整 pipeline。(a) 对比预训练框架；(b) 条件扩散模型",
        "LPFM training pipeline. (a) Contrastive pre-training framework; (b) Conditional diffusion model",
        ICO_RULER)}
    </div>

    <div class="subsection">
      <h3 lang-zh>2.1 训练数据构造</h3>
      <h3 lang-en>2.1 Training Data Construction</h3>

      <div class="two-col">
        <div>
          <h4 lang-zh>图像修复：合成退化</h4>
          <h4 lang-en>Restoration: Synthetic Degradation</h4>
          <div class="flow" style="padding:16px;">
            <div class="flow-row"><div class="flow-box" lang-zh>公开数据集 WSI</div><div class="flow-box" lang-en>Public Dataset WSIs</div></div>
            <div class="flow-arrow-down"><div class="flow-arrow">&darr;</div></div>
            <div class="flow-row"><div class="flow-box">Tiling (256&times;256)</div></div>
            <div class="flow-arrow-down"><div class="flow-arrow">&darr;</div></div>
            <div class="flow-row"><div class="flow-box green" lang-zh>"高质量" patches (GT)</div><div class="flow-box green" lang-en>"High-quality" patches (GT)</div></div>
            <div class="flow-arrow-down"><div class="flow-arrow">&darr;</div><div class="flow-label" lang-zh>合成退化模拟</div><div class="flow-label" lang-en>Synthetic degradation</div></div>
            <div class="flow-row"><div class="flow-box amber" lang-zh>"退化" patches (Input)</div><div class="flow-box amber" lang-en>"Degraded" patches (Input)</div></div>
          </div>
        </div>
        <div>
          <h4 lang-zh>虚拟染色：物理配对数据</h4>
          <h4 lang-en>Virtual Staining: Physically Paired Data</h4>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th lang-zh>数据集</th><th lang-en>Dataset</th>
                  <th lang-zh>配对方式</th><th lang-en>Pairing</th>
                  <th lang-zh>规模</th><th lang-en>Scale</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>AF2HE</td><td lang-zh>自体荧光 &rarr; H&amp;E</td><td lang-en>Autofluorescence &rarr; H&amp;E</td><td>50,447 train</td></tr>
                <tr><td>HE2PAS</td><td>H&amp;E &rarr; PAS-AB</td><td>10,727 train</td></tr>
                <tr><td>HEMIT</td><td>H&amp;E &rarr; mIHC</td><td>3,717 train</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="box box-insight">
        <span lang-zh><strong>联合预训练</strong>：修复任务和虚拟染色任务在 Stage 1 中<strong>共享同一个 autoencoder、同一套损失函数，联合训练</strong>。论文认为修复和虚拟染色在底层是<strong>同一类问题</strong>——都是将组织的一种"视角"转换为另一种"视角"。</span>
        <span lang-en><strong>Joint Pre-training</strong>: Restoration and virtual staining tasks in Stage 1 <strong>share the same autoencoder and loss functions, trained jointly</strong>. The paper argues they are <strong>fundamentally the same type of problem</strong>—converting one "view" of tissue into another.</span>
      </div>
    </div>

    <!-- 2.2 Stage 1 -->
    <div class="subsection" id="stage1">
      <h3 lang-zh>2.2 Stage 1: 对比预训练</h3>
      <h3 lang-en>2.2 Stage 1: Contrastive Pre-training</h3>

      <p lang-zh><strong>目标</strong>：学习可迁移的、染色不变的 (stain-invariant) 特征表示，在 latent space 中捕获共享特征，并生成粗糙修复结果。</p>
      <p lang-en><strong>Goal</strong>: Learn transferable, stain-invariant feature representations that capture shared features in latent space and produce coarse restoration results.</p>

      <p lang-zh><strong>架构</strong>：KL-Autoencoder (Encoder $\\mathcal{{E}}$ + Decoder $\\mathcal{{D}}$) + CLIP text encoder + cross-attention 条件注入。处理高质量图像和退化图像的 Encoder <strong>共享权重</strong>。</p>
      <p lang-en><strong>Architecture</strong>: KL-Autoencoder (Encoder $\\mathcal{{E}}$ + Decoder $\\mathcal{{D}}$) + CLIP text encoder + cross-attention conditioning. The Encoder <strong>shares weights</strong> for both high-quality and degraded images.</p>

      <h4 lang-zh>训练损失（5 项联合优化）</h4>
      <h4 lang-en>Training Losses (5 jointly optimized terms)</h4>

      <div class="formula">
        $\\mathcal{{L}} = \\mathcal{{L}}_{{recon}} + \\mathcal{{L}}_{{enhance}} + \\mathcal{{L}}_{{cont}} + \\mathcal{{L}}_{{adv}} + \\mathcal{{L}}_{{perceptual}}$
      </div>

      <div class="loss-hierarchy">
        <div class="loss-item" style="border-left: 4px solid var(--blue);">
          <div class="loss-icon" style="background:var(--blue);">R</div>
          <div>
            <strong>$\\mathcal{{L}}_{{recon}}$</strong> &mdash;
            <span lang-zh>重建损失：保证 latent space 信息完整性 (L1)</span>
            <span lang-en>Reconstruction loss: ensures latent space information integrity (L1)</span>
          </div>
        </div>
        <div class="loss-item" style="border-left: 4px solid var(--emerald);">
          <div class="loss-icon" style="background:var(--emerald);">E</div>
          <div>
            <strong>$\\mathcal{{L}}_{{enhance}}$</strong> &mdash;
            <span lang-zh>增强损失：学习退化&rarr;高质量映射 (L1)</span>
            <span lang-en>Enhancement loss: learns degraded&rarr;high-quality mapping (L1)</span>
          </div>
        </div>
        <div class="loss-item" style="border-left: 4px solid var(--teal);">
          <div class="loss-icon" style="background:var(--teal);">C</div>
          <div>
            <strong>$\\mathcal{{L}}_{{cont}}$</strong> &mdash;
            <span lang-zh>对比损失：跨退化/跨染色的不变性（泛化性的关键）</span>
            <span lang-en>Contrastive loss: cross-degradation/cross-stain invariance (key to generalization)</span>
          </div>
        </div>
        <div class="loss-item" style="border-left: 4px solid var(--purple);">
          <div class="loss-icon" style="background:var(--purple);">P</div>
          <div>
            <strong>$\\mathcal{{L}}_{{perceptual}}$</strong> &mdash;
            <span lang-zh>感知损失：高层语义对齐（避免模糊）</span>
            <span lang-en>Perceptual loss: high-level semantic alignment (avoids blurring)</span>
          </div>
        </div>
        <div class="loss-item" style="border-left: 4px solid var(--amber);">
          <div class="loss-icon" style="background:var(--amber);">A</div>
          <div>
            <strong>$\\mathcal{{L}}_{{adv}}$</strong> &mdash;
            <span lang-zh>对抗损失：分布级真实感（细节质量）</span>
            <span lang-en>Adversarial loss: distribution-level realism (detail quality)</span>
          </div>
        </div>
      </div>

      <div class="box box-note">
        <span lang-zh><strong>三层约束体系</strong>：像素 ($\\mathcal{{L}}_{{recon}}/\\mathcal{{L}}_{{enhance}}$) &rarr; 特征 ($\\mathcal{{L}}_{{perceptual}}$) &rarr; 分布 ($\\mathcal{{L}}_{{adv}}$) 三个层级的逐步约束。</span>
        <span lang-en><strong>Three-Level Constraint System</strong>: Pixel ($\\mathcal{{L}}_{{recon}}/\\mathcal{{L}}_{{enhance}}$) &rarr; Feature ($\\mathcal{{L}}_{{perceptual}}$) &rarr; Distribution ($\\mathcal{{L}}_{{adv}}$) progressive constraints.</span>
      </div>
    </div>

    <!-- 2.3 Stage 2 -->
    <div class="subsection" id="stage2">
      <h3 lang-zh>2.3 Stage 2: 条件扩散模型</h3>
      <h3 lang-en>2.3 Stage 2: Conditional Diffusion</h3>

      <p lang-zh><strong>为什么需要 Stage 2？</strong> Stage 1 产生粗糙修复——全局结构正确但缺乏精细细胞级细节。扩散模型擅长生成高频细节，用于补充 Stage 1 无法恢复的信息。</p>
      <p lang-en><strong>Why Stage 2?</strong> Stage 1 produces coarse restoration—globally correct structure but lacking fine cell-level details. Diffusion models excel at generating high-frequency details to supplement what Stage 1 cannot recover.</p>

      <div class="two-col">
        <div>
          <h4>Phase 2a</h4>
          <p lang-zh>预训练<strong>无条件扩散模型</strong>，建立基础的病理图像去噪能力。</p>
          <p lang-en>Pre-train <strong>unconditional diffusion model</strong> to establish basic pathology image denoising capability.</p>
          <div class="formula">$\\mathcal{{L}}_{{DM}} = \\mathbb{{E}} [ \\| \\varepsilon - \\varepsilon_\\theta(x_t, t) \\|_2^2 ]$</div>
        </div>
        <div>
          <h4>Phase 2b</h4>
          <p lang-zh><strong>冻结扩散模型</strong>，引入 ControlNet 风格的可训练条件模块（zero conv 连接），以粗糙修复结果 + 文本 prompt 为条件。</p>
          <p lang-en><strong>Freeze diffusion model</strong>, add ControlNet-style trainable condition module (zero conv), conditioned on coarse result + text prompt.</p>
          <div class="formula">$\\mathcal{{L}}_{{cond}} = \\mathbb{{E}} [ \\| \\varepsilon - \\varepsilon_\\theta(x_t, t, z, c) \\|_2^2 ]$</div>
        </div>
      </div>

{img_ph("ph-fig9", "fig9_inference_pipeline.png",
        "Figure 9: LPFM Inference Pipeline",
        "LPFM 推理阶段完整 pipeline——退化图像经 Stage 1 编码器生成粗糙结果后，与文本 prompt 一起作为条件输入扩散模型，经迭代去噪生成最终高质量输出",
        "LPFM inference pipeline—degraded image passes through Stage 1 encoder for coarse result, then with text prompt as condition into diffusion model for iterative denoising to produce final high-quality output",
        ICO_LOOP)}
    </div>

    <!-- 2.5 Prompt -->
    <div class="subsection" id="prompt">
      <h3 lang-zh>2.5 Textual Prompt 引导机制</h3>
      <h3 lang-en>2.5 Textual Prompt Guidance</h3>

      <p lang-zh>LPFM 通过<strong>自然语言 prompt</strong> 实现<strong>无架构修改的任务切换</strong>，包含三部分：Task Description + Positive Prompt + Negative Prompt。</p>
      <p lang-en>LPFM achieves <strong>task switching without architecture modification</strong> through <strong>natural language prompts</strong>, comprising: Task Description + Positive Prompt + Negative Prompt.</p>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th lang-zh>任务类型</th><th lang-en>Task</th>
              <th>Task Description</th>
              <th>Positive</th>
              <th>Negative</th>
            </tr>
          </thead>
          <tbody>
            <tr><td lang-zh>超分 x2</td><td lang-en>SR x2</td><td>Restore the low-quality H&amp;E pathology image.</td><td>High quality, upscale x2</td><td>low quality, blurry, noisy...</td></tr>
            <tr><td lang-zh>去噪</td><td lang-en>Denoise</td><td>Remove the noise inside the H&amp;E pathology image.</td><td>High quality, <strong>Blurry</strong></td><td>Noisy</td></tr>
            <tr><td>H&amp;E&rarr;PAS-AB</td><td>Translate the H&amp;E image to PAS-AB image</td><td>PAS-AB image</td><td>H&amp;E image, blurry, noisy...</td></tr>
            <tr><td>AF&rarr;H&amp;E</td><td>Translate the label-free patch to H&amp;E image.</td><td>High quality</td><td>low quality, blurry, noisy...</td></tr>
          </tbody>
        </table>
      </div>

      <div class="box box-insight">
        <span lang-zh><strong>有趣的设计</strong>：去噪任务的 positive prompt 包含 "Blurry"——告诉模型"模糊是可以接受的，但噪声不行"，实现对特定退化类型的<strong>选择性处理</strong>。</span>
        <span lang-en><strong>Interesting Design</strong>: The denoising positive prompt includes "Blurry"—telling the model "blur is acceptable, but noise is not," enabling <strong>selective degradation handling</strong>.</span>
      </div>

{img_ph("ph-fig10", "fig10_prompt_restoration.png",
        "Figure 10: Prompt-Guided Restoration",
        "不同文本 prompt 引导下的 H&E 病理图像修复结果",
        "H&E pathology image restoration results under different text prompts",
        ICO_PALETTE)}

{img_ph("ph-fig11", "fig11_prompt_staining.png",
        "Figure 11: Prompt-Guided Virtual Staining",
        "不同文本 prompt 引导下的虚拟染色结果",
        "Virtual staining results under different text prompts",
        ICO_DNA)}
    </div>

    <div class="subsection">
      <h3 lang-zh>2.7 方法总结对比</h3>
      <h3 lang-en>2.7 Method Comparison Summary</h3>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th lang-zh>维度</th><th lang-en>Dimension</th>
              <th lang-zh>现有方法</th><th lang-en>Existing Methods</th>
              <th>LPFM</th>
            </tr>
          </thead>
          <tbody>
            <tr><td lang-zh>任务覆盖</td><td lang-en>Task Coverage</td><td lang-zh>单一任务</td><td lang-en>Single task</td><td lang-zh>统一处理 6 类任务</td><td lang-en>Unified 6 task categories</td></tr>
            <tr><td lang-zh>架构修改</td><td lang-en>Architecture</td><td lang-zh>每个任务不同模型</td><td lang-en>Different model per task</td><td lang-zh>同一架构，prompt 切换</td><td lang-en>Same architecture, prompt switching</td></tr>
            <tr><td lang-zh>预训练</td><td lang-en>Pre-training</td><td lang-zh>无/ImageNet</td><td lang-en>None/ImageNet</td><td lang-zh>190M 病理 patches 对比预训练</td><td lang-en>190M pathology patches contrastive</td></tr>
            <tr><td lang-zh>特征表示</td><td lang-en>Features</td><td lang-zh>任务特定</td><td lang-en>Task-specific</td><td lang-zh>染色不变、退化不变的共享表示</td><td lang-en>Stain/degradation-invariant shared</td></tr>
            <tr><td lang-zh>生成策略</td><td lang-en>Generation</td><td lang-zh>单阶段</td><td lang-en>Single-stage</td><td lang-zh>两阶段渐进精炼</td><td lang-en>Two-stage progressive refinement</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
''')

    # ============================================================
    # SECTION 3: DATA
    # ============================================================
    html_parts.append(f'''  <!-- ======================== 3. DATA ======================== -->
  <section id="data" class="fade-in">
    <div class="section-header">
      <span class="section-num">3</span>
      <h2 lang-zh>数据</h2>
      <h2 lang-en>Data</h2>
    </div>

    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-value">87,810</div>
        <div class="metric-label">WSIs</div>
      </div>
      <div class="metric-card green">
        <div class="metric-value">190M</div>
        <div class="metric-label">Patches</div>
      </div>
      <div class="metric-card amber">
        <div class="metric-value">37</div>
        <div class="metric-label" lang-zh>数据源</div>
        <div class="metric-label" lang-en>Data Sources</div>
      </div>
      <div class="metric-card rose">
        <div class="metric-value">34</div>
        <div class="metric-label" lang-zh>组织类型</div>
        <div class="metric-label" lang-en>Tissue Types</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">5</div>
        <div class="metric-label" lang-zh>染色协议</div>
        <div class="metric-label" lang-en>Stain Protocols</div>
      </div>
    </div>

{img_ph("ph-fig1c", "fig1c_dataset_distribution.png",
        "Figure 1-c: Dataset Distribution",
        "数据集组织类型分布图——87,810 WSIs 和 190M patches 的组织类型分布",
        "Dataset tissue type distribution—87,810 WSIs and 190M patches across tissue types",
        ICO_CHART)}

    <div class="subsection">
      <h3 lang-zh>主要数据集</h3>
      <h3 lang-en>Main Datasets</h3>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th lang-zh>用途</th><th lang-en>Purpose</th>
              <th lang-zh>数据集</th><th lang-en>Dataset</th>
              <th lang-zh>组织</th><th lang-en>Tissue</th>
              <th lang-zh>规模</th><th lang-en>Scale</th>
            </tr>
          </thead>
          <tbody>
            <tr><td lang-zh>预训练</td><td lang-en>Pre-train</td><td>TCGA</td><td lang-zh>多器官</td><td lang-en>Multi-organ</td><td>30,159 slides, ~120M patches</td></tr>
            <tr><td lang-zh>预训练</td><td lang-en>Pre-train</td><td>GTEx</td><td lang-zh>多器官</td><td lang-en>Multi-organ</td><td>25,711 slides, ~31M patches</td></tr>
            <tr><td lang-zh>预训练</td><td lang-en>Pre-train</td><td>CPTAC</td><td lang-zh>多器官</td><td lang-en>Multi-organ</td><td>7,255 slides</td></tr>
            <tr><td lang-zh>内部测试</td><td lang-en>Internal Test</td><td>CAMELYON16</td><td lang-zh>乳腺淋巴结</td><td lang-en>Breast Lymph</td><td>270 WSIs, 1.7M patches</td></tr>
            <tr><td lang-zh>外部验证</td><td lang-en>External Val</td><td>OCELOT / MIDOG / TIGER</td><td lang-zh>多种</td><td lang-en>Various</td><td lang-zh>完全独立</td><td lang-en>Fully independent</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="subsection">
      <h3 lang-zh>3.2 退化模拟</h3>
      <h3 lang-en>3.2 Degradation Simulation</h3>

      <div class="two-col">
        <div>
          <h4 lang-zh>(1) 低分辨率</h4>
          <h4 lang-en>(1) Low Resolution</h4>
          <p lang-zh>三种插值（Area/Bilinear/Bicubic），缩放 2x/4x/8x。排除 nearest-neighbor 因其产生锯齿状核边界。</p>
          <p lang-en>Three interpolation methods (Area/Bilinear/Bicubic), scales 2x/4x/8x. Excludes nearest-neighbor as it produces jagged nuclear boundaries.</p>
        </div>
        <div>
          <h4 lang-zh>(2) 模糊</h4>
          <h4 lang-en>(2) Blur</h4>
          <p lang-zh>各向异性高斯核模拟光学离焦和扫描仪振动。Kernel size: 7/11/15，$\\sigma \\in [1.5, 3.5]$。</p>
          <p lang-en>Anisotropic Gaussian kernels simulating optical defocus and scanner vibration. Kernel size: 7/11/15, $\\sigma \\in [1.5, 3.5]$.</p>
        </div>
      </div>

      <h4 lang-zh>(3) 复合噪声</h4>
      <h4 lang-en>(3) Compound Noise</h4>
      <p lang-zh>高斯噪声（传感器读出噪声）+ 泊松噪声（光子探测量子限制），$\\sigma \\in \\{{21, 31, 41\\}}$。</p>
      <p lang-en>Gaussian noise (sensor readout) + Poisson noise (photon detection quantum limit), $\\sigma \\in \\{{21, 31, 41\\}}$.</p>
    </div>
  </section>
''')

    # ============================================================
    # SECTION 4: EXPERIMENTS
    # ============================================================
    sr_chart = bar_chart(
        "平均 PSNR (dB) — 超分辨率", "Average PSNR (dB) — Super-Resolution",
        [
            ("LPFM", 30.27, " dB", "linear-gradient(90deg,#0d9488,#14b8a6)"),
            ("SwinIR", 26.13, " dB", "linear-gradient(90deg,#7c3aed,#a855f7)"),
            ("BSRGAN", 25.89, " dB", "linear-gradient(90deg,#8b5cf6,#a78bfa)"),
            ("Pix2Pix", 24.10, " dB", "linear-gradient(90deg,#a78bfa,#c4b5fd)"),
            ("LDM", 23.80, " dB", "linear-gradient(90deg,#94a3b8,#cbd5e1)"),
        ],
        35,
        source_zh="数据来源：原文 Figure 2 &amp; Table 1-6",
        source_en="Source: Paper Figure 2 &amp; Table 1-6"
    )

    vs_chart = bar_chart(
        "SSIM 提升幅度 (vs 次优方法)", "SSIM Improvement (vs Runner-up)",
        [
            ("LPFM", 33.8, "%", "linear-gradient(90deg,#0d9488,#14b8a6)"),
            ("AF2HE", 4.5, "%", "linear-gradient(90deg,#7c3aed,#a855f7)"),
            ("HEMIT", 10.7, "%", "linear-gradient(90deg,#2563eb,#60a5fa)"),
        ],
        40,
        source_zh="数据来源：原文 Figure 1e &amp; Figure 5",
        source_en="Source: Paper Figure 1e &amp; Figure 5"
    )

    html_parts.append(f'''  <!-- ======================== 4. EXPERIMENTS ======================== -->
  <section id="experiments" class="fade-in">
    <div class="section-header">
      <span class="section-num">4</span>
      <h2 lang-zh>实验结果</h2>
      <h2 lang-en>Experimental Results</h2>
    </div>

    <p lang-zh>共 <strong>66 个实验任务</strong>，分为 6 大类。评估策略采用<strong>内部测试 + 外部验证</strong>的两级验证。</p>
    <p lang-en>A total of <strong>66 experimental tasks</strong> across 6 categories. Evaluation uses <strong>internal testing + external validation</strong> two-level verification.</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th lang-zh>指标</th><th lang-en>Metric</th>
            <th lang-zh>衡量维度</th><th lang-en>Measures</th>
            <th lang-zh>方向</th><th lang-en>Direction</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>PSNR</td><td lang-zh>像素级精度</td><td lang-en>Pixel-level accuracy</td><td>&uarr; Higher is better</td></tr>
          <tr><td>SSIM</td><td lang-zh>结构相似性</td><td lang-en>Structural similarity</td><td>&uarr; Higher is better</td></tr>
          <tr><td>LPIPS</td><td lang-zh>感知质量</td><td lang-en>Perceptual quality</td><td>&darr; Lower is better</td></tr>
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 lang-zh>4.1 超分辨率 (18 tasks)</h3>
      <h3 lang-en>4.1 Super-Resolution (18 tasks)</h3>

      <p lang-zh><strong>任务构成</strong>：3 种插值方法 (Area/Bilinear/Bicubic) &times; 3 种缩放因子 (2&times;/4&times;/8&times;) &times; 内部/外部 = 18 tasks。模拟 WSI 多分辨率金字塔的重采样过程。</p>
      <p lang-en><strong>Task Design</strong>: 3 interpolation methods (Area/Bilinear/Bicubic) &times; 3 scale factors (2&times;/4&times;/8&times;) &times; internal/external = 18 tasks. Simulates WSI multi-resolution pyramid resampling.</p>

{sr_chart}

      <div class="box box-note">
        <span lang-zh><strong>核心结果</strong>：LPFM 跨三指标平均排名 <strong>1.33</strong>，15/18 任务同时排名前二。平均 PSNR <strong>30.27 dB</strong>，超过次优 <strong>4.14 dB</strong>；SSIM 超出 <strong>0.12</strong>。</span>
        <span lang-en><strong>Key Results</strong>: LPFM average rank <strong>1.33</strong> across 3 metrics, 15/18 tasks ranked top-2 simultaneously. Average PSNR <strong>30.27 dB</strong>, surpassing runner-up by <strong>4.14 dB</strong>; SSIM margin <strong>+0.12</strong>.</span>
      </div>

      <div class="box box-insight">
        <span lang-zh><strong>Insight &mdash; 极端退化下优势更大</strong>：8&times; 超分（最困难场景）下，LPFM 内部 PSNR 24.63 dB vs 次优 20.93 dB（差距 <strong>3.70 dB</strong>），外部 25.50 vs 22.90 dB。强度曲线分析 (PCC) 与 GT 最高：<strong>0.988</strong> (内部)、<strong>0.943</strong> (外部)——说明 LPFM 在信息损失最严重时的重建能力尤为突出，对比学习预训练使其捕获了其他方法难以恢复的组织结构先验。</span>
        <span lang-en><strong>Insight &mdash; Advantage amplifies under extreme degradation</strong>: At 8&times; SR (hardest scenario), LPFM internal PSNR 24.63 dB vs runner-up 20.93 dB (gap <strong>3.70 dB</strong>), external 25.50 vs 22.90 dB. Intensity profile PCC closest to GT: <strong>0.988</strong> (internal), <strong>0.943</strong> (external)—contrastive pre-training captures tissue structural priors that other methods cannot recover under severe information loss.</span>
      </div>

{img_ph("ph-fig2", "fig2_super_resolution.png",
        "Figure 2: Super-Resolution Results",
        "超分辨率实验结果——18 个任务的平均排名、PSNR/SSIM/LPIPS 分布、强度曲线与 PCC 分析、视觉对比",
        "Super-resolution results—average ranking across 18 tasks, PSNR/SSIM/LPIPS distributions, intensity profile and PCC analysis, visual comparisons",
        ICO_GRAPH)}
    </div>

    <div class="subsection">
      <h3 lang-zh>4.2 去模糊 (18 tasks)</h3>
      <h3 lang-en>4.2 Deblurring (18 tasks)</h3>

      <p lang-zh><strong>任务构成</strong>：3 种 kernel size (7/11/15) &times; 3 种 &sigma; 参数 &times; 内部/外部 = 18 tasks。模拟光学离焦、切片缺陷和扫描仪振动。</p>
      <p lang-en><strong>Task Design</strong>: 3 kernel sizes (7/11/15) &times; 3 &sigma; parameters &times; internal/external = 18 tasks. Simulating optical defocus, sectioning defects, and scanner vibration.</p>

      <p lang-zh>LPFM 在 PSNR、SSIM、LPIPS 上均取得<strong>最优平均排名</strong>。PCC: <strong>0.987</strong> (内部), <strong>0.853</strong> (外部)。</p>
      <p lang-en>LPFM achieves <strong>best average ranking</strong> on all three metrics. PCC: <strong>0.987</strong> (internal), <strong>0.853</strong> (external).</p>

      <div class="box box-insight">
        <span lang-zh><strong>Insight &mdash; 退化越强，优势越大</strong>：15 pixel 高斯核（最强模糊）下优势最为明显。这与超分辨率中 8&times; 场景的趋势一致——LPFM 的对比预训练使其在<strong>信息损失严重时仍能调动组织先验知识</strong>进行重建，而非简单的像素级恢复。外部 PCC 0.853 相对内部 0.987 的下降值得关注，提示跨域去模糊仍有改进空间。</span>
        <span lang-en><strong>Insight &mdash; Stronger degradation, larger advantage</strong>: Most pronounced under 15-pixel Gaussian kernel (strongest blur). Consistent with the 8&times; SR trend—contrastive pre-training enables LPFM to <strong>leverage tissue priors under severe information loss</strong> rather than relying on simple pixel-level recovery. The drop from internal PCC 0.987 to external 0.853 is notable, suggesting room for improvement in cross-domain deblurring.</span>
      </div>

{img_ph("ph-fig3", "fig3_deblurring.png",
        "Figure 3: Deblurring Results",
        "去模糊实验结果",
        "Deblurring results",
        ICO_MAGNIFY)}
    </div>

    <div class="subsection">
      <h3 lang-zh>4.3 去噪 (18 tasks)</h3>
      <h3 lang-en>4.3 Denoising (18 tasks)</h3>

      <p lang-zh><strong>任务构成</strong>：3 种噪声强度 (&sigma;=21/31/41) &times; 内部/外部 = 18 tasks（高斯+泊松复合噪声）。</p>
      <p lang-en><strong>Task Design</strong>: 3 noise levels (&sigma;=21/31/41) &times; internal/external = 18 tasks (Gaussian + Poisson compound noise).</p>

      <div class="box box-note">
        <span lang-zh><strong>定量结果</strong>：LPFM 平均排名 <strong>1.48</strong>，14/18 任务在三指标上排名前二。<strong>PSNR 非最优</strong>：SwinIR 27.02 dB &gt; LPFM。<strong>LPIPS 非最优</strong>：HistoDiff 0.172 &gt; LPFM。<strong>但 SSIM 最优 (0.837)</strong>。外部泛化更优：MAE <strong>8.14</strong> (LPFM) vs 8.52 (SwinIR)。</span>
        <span lang-en><strong>Quantitative Results</strong>: LPFM average rank <strong>1.48</strong>, 14/18 tasks ranked top-2 on all metrics. <strong>PSNR not best</strong>: SwinIR 27.02 dB &gt; LPFM. <strong>LPIPS not best</strong>: HistoDiff 0.172 &gt; LPFM. <strong>But SSIM best (0.837)</strong>. Better external generalization: MAE <strong>8.14</strong> (LPFM) vs 8.52 (SwinIR).</span>
      </div>

      <div class="box box-warn">
        <span lang-zh><strong>关键分析：为什么 PSNR 不是最高？</strong> SwinIR 的高 PSNR 来源于 <strong>over-smoothing（过平滑）</strong>：降低 MSE 提高 PSNR，但<strong>擦除诊断关键的细胞细节和组织纹理</strong>。在病理场景中，核膜边界、染色质纹理等高频细节对诊断至关重要，过平滑的图像可能<strong>误导有丝分裂计数、核分级等下游任务</strong>。LPFM 的 SSIM 最优说明它最好地保留了结构信息，三指标的<strong>最佳平衡</strong>在医学影像中比单一指标最优更有临床价值。</span>
        <span lang-en><strong>Key Analysis: Why PSNR is Not the Highest?</strong> SwinIR's high PSNR comes from <strong>over-smoothing</strong>: reducing MSE improves PSNR but <strong>erases diagnostically critical cellular details and tissue textures</strong>. In pathology, high-frequency details like nuclear membranes and chromatin textures are essential—over-smoothed images may <strong>mislead downstream tasks like mitosis counting and nuclear grading</strong>. LPFM's best SSIM indicates superior structural preservation. In medical imaging, <strong>optimal balance across metrics</strong> is more clinically valuable than being best on a single metric.</span>
      </div>

{img_ph("ph-fig4", "fig4_denoising.png",
        "Figure 4: Denoising Results",
        "去噪实验结果",
        "Denoising results",
        ICO_BROOM)}
    </div>

    <div class="subsection">
      <h3 lang-zh>4.4 复合退化修复 (6 tasks)</h3>
      <h3 lang-en>4.4 Compound Degradation (6 tasks)</h3>

      <p lang-zh><strong>任务设计</strong>：随机组合多种退化（高斯模糊 + 泊松噪声 + 低分辨率），模拟<strong>真实临床场景</strong>中多种伪影同时存在的情况。这是<strong>最贴近实际应用</strong>的实验设置——临床图像很少只有单一退化。</p>
      <p lang-en><strong>Task Design</strong>: Randomly combining multiple degradations (Gaussian blur + Poisson noise + low resolution), simulating <strong>real clinical scenarios</strong> where multiple artifacts coexist. This is the <strong>most practically relevant</strong> experimental setting—clinical images rarely exhibit only a single degradation.</p>

      <p lang-zh>LPFM 均值 PSNR <strong>26.15 dB</strong>，超过次优 SwinIR (24.05) <strong>2.10 dB</strong>。SSIM <strong>0.720</strong> vs Pix2Pix 0.642。在 OCELOT 数据集上达到 <strong>28.20 dB</strong>，展示了对多样组织类型的优异泛化。PCC 在所有测试样本上<strong>持续超过 0.9</strong>。</p>
      <p lang-en>LPFM average PSNR <strong>26.15 dB</strong>, surpassing runner-up SwinIR (24.05) by <strong>2.10 dB</strong>. SSIM <strong>0.720</strong> vs Pix2Pix 0.642. Achieves <strong>28.20 dB</strong> on OCELOT dataset, demonstrating excellent generalization across diverse tissue types. PCC consistently <strong>above 0.9</strong> across all test samples.</p>

      <div class="box box-insight">
        <span lang-zh><strong>Insight &mdash; 统一框架在复合退化中的优势</strong>：复合退化场景是专用模型最弱的环节——去噪模型不擅长处理同时存在的模糊，超分模型无法应对额外的噪声。LPFM 因在预训练阶段<strong>同时学习了多种退化的共享表示</strong>，天然具备处理复合退化的能力，这正是统一框架的核心价值所在。</span>
        <span lang-en><strong>Insight &mdash; Unified framework advantage in compound degradation</strong>: Compound degradation is where task-specific models are weakest—denoising models struggle with simultaneous blur, SR models cannot handle additional noise. Because LPFM <strong>learns shared representations across multiple degradation types</strong> during pre-training, it naturally handles compound degradation—this is the core value proposition of the unified framework.</span>
      </div>

{img_ph("ph-fig6", "fig6_compound_degradation.png",
        "Figure 6: Compound Degradation Results",
        "复合退化修复结果",
        "Compound degradation restoration results",
        ICO_FLASK)}
    </div>

    <div class="subsection">
      <h3 lang-zh>4.5 虚拟染色 (3 tasks)</h3>
      <h3 lang-en>4.5 Virtual Staining (3 tasks)</h3>

{vs_chart}

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th lang-zh>任务</th><th lang-en>Task</th>
              <th lang-zh>源&rarr;目标</th><th lang-en>Source&rarr;Target</th>
              <th lang-zh>临床意义</th><th lang-en>Clinical Significance</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>AF2HE</td><td lang-zh>自体荧光&rarr;H&amp;E</td><td lang-en>Autofluorescence&rarr;H&amp;E</td><td lang-zh>快速诊断，免去物理染色步骤</td><td lang-en>Rapid diagnosis, eliminating physical staining</td></tr>
            <tr><td>HE2PAS</td><td>H&amp;E&rarr;PAS-AB</td><td lang-zh>肾脏病理特殊染色（基底膜、糖原）</td><td lang-en>Renal pathology special stain (basement membrane, glycogen)</td></tr>
            <tr><td>HEMIT</td><td>H&amp;E&rarr;mIHC</td><td lang-zh>多重免疫组化（DAPI/panCK/CD3）</td><td lang-en>Multiplex IHC (DAPI/panCK/CD3)</td></tr>
          </tbody>
        </table>
      </div>

      <p lang-zh>所有任务 <strong>p &lt; 0.001</strong> 显著优于所有 baselines。SSIM 提升 <strong>4.5%/33.8%/10.7%</strong>，LPIPS 降低 <strong>20.1%/7.0%/20.0%</strong>。AF2HE: PCC <strong>0.935</strong> (次优 Pix2Pix 仅 0.565)。HE2PAS: MAE <strong>2.93</strong> (次优 RegGAN 7.03)。</p>
      <p lang-en>All tasks <strong>p &lt; 0.001</strong> significantly better than all baselines. SSIM improvements: <strong>4.5%/33.8%/10.7%</strong>. LPIPS reductions: <strong>20.1%/7.0%/20.0%</strong>. AF2HE: PCC <strong>0.935</strong> (runner-up Pix2Pix only 0.565). HE2PAS: MAE <strong>2.93</strong> (runner-up RegGAN 7.03).</p>

      <div class="box box-insight">
        <span lang-zh><strong>Insight &mdash; 修复与染色的协同效应</strong>：LPFM 在虚拟染色上的巨大优势（HE2PAS SSIM 提升 33.8%）可能源于 Stage 1 中修复与染色的<strong>联合预训练</strong>——对比学习使 encoder 学会了染色不变的组织特征表示，修复任务中学到的"退化&rarr;高质量"映射知识可迁移到"一种染色&rarr;另一种染色"的映射中。</span>
        <span lang-en><strong>Insight &mdash; Restoration-staining synergy</strong>: LPFM's large advantage in virtual staining (HE2PAS SSIM +33.8%) likely stems from <strong>joint pre-training</strong> of restoration and staining in Stage 1—contrastive learning teaches the encoder stain-invariant tissue representations, and knowledge from "degraded&rarr;high-quality" mapping transfers to "one stain&rarr;another stain" mapping.</span>
      </div>

{img_ph("ph-fig5", "fig5_virtual_staining.png",
        "Figure 5: Virtual Staining Results",
        "虚拟染色实验结果",
        "Virtual staining results",
        ICO_PALETTE)}
    </div>

    <div class="subsection">
      <h3 lang-zh>4.6 退化图像的虚拟染色 (3 tasks)</h3>
      <h3 lang-en>4.6 Virtual Staining on Degraded Images (3 tasks)</h3>

      <p lang-zh><strong>动机</strong>：临床中需要虚拟染色的图像<strong>往往本身就存在退化</strong>（染色不均、切片伪影等），现有方法通常假设输入是高质量的——这是它们的核心痛点。</p>
      <p lang-en><strong>Motivation</strong>: Clinical images requiring virtual staining <strong>often already contain degradations</strong> (staining inhomogeneity, sectioning artifacts, etc.). Existing methods typically assume high-quality inputs—this is their core vulnerability.</p>

      <div class="box box-key">
        <span lang-zh><strong>核心优势</strong>：退化输入下其他方法性能严重下降（CycleGAN: 19.41&rarr;7.87 PSNR），而 LPFM 保持鲁棒：HE2PAS 23.03&rarr;19.93，HEMIT 26.43&rarr;25.53——性能下降幅度远小于竞争方法。</span>
        <span lang-en><strong>Core Advantage</strong>: Other methods severely degrade under degraded inputs (CycleGAN: 19.41&rarr;7.87 PSNR), while LPFM remains robust: HE2PAS 23.03&rarr;19.93, HEMIT 26.43&rarr;25.53—much smaller performance drop than competitors.</span>
      </div>

{img_ph("ph-fig7", "fig7_degraded_staining.png",
        "Figure 7: Virtual Staining on Degraded Images",
        "退化图像虚拟染色结果——LPFM 在退化输入下仍维持较高的染色质量",
        "Virtual staining on degraded images—LPFM maintains high staining quality under degraded inputs",
        ICO_PALETTE)}
    </div>

    <div class="subsection">
      <h3 lang-zh>4.7 跨实验总结</h3>
      <h3 lang-en>4.7 Cross-Experiment Summary</h3>

      <div class="box box-key">
        <span lang-zh><strong>超越 "效果好" 的关键结论</strong>：<br>
        1. <strong>统一不等于妥协</strong>：一个模型处理 6 类任务，在 56/66 个任务上 p&lt;0.01 显著优于 SOTA——统一框架<strong>没有牺牲</strong>单任务性能。<br>
        2. <strong>退化越强，优势越大</strong>：8&times; SR、15px 模糊、复合退化等极端场景下差距扩大，说明对比预训练提供的<strong>组织先验</strong>在信息严重缺失时尤为关键。<br>
        3. <strong>外部验证一致性强</strong>：在完全独立的 OCELOT/MIDOG/TIGER 上保持优势，排除了过拟合内部数据集的可能。<br>
        4. <strong>SSIM &gt; PSNR 的临床价值</strong>：去噪实验揭示了 PSNR 最优可能来自过平滑，在病理场景中三指标平衡比单指标更重要。<br>
        5. <strong>修复&harr;染色协同增益</strong>：联合预训练使两类任务相互促进——修复学到的退化不变性 helps 染色任务，染色学到的跨域映射 helps 修复任务。</span>
        <span lang-en><strong>Key Conclusions Beyond "Good Results"</strong>:<br>
        1. <strong>Unified &ne; Compromise</strong>: One model for 6 task categories, p&lt;0.01 significantly better than SOTA on 56/66 tasks—the unified framework <strong>does not sacrifice</strong> per-task performance.<br>
        2. <strong>Stronger degradation, larger advantage</strong>: The gap widens under extreme scenarios (8&times; SR, 15px blur, compound degradation), indicating contrastive pre-training provides <strong>tissue priors</strong> critical when information is severely lost.<br>
        3. <strong>Consistent external validation</strong>: Maintains advantage on fully independent OCELOT/MIDOG/TIGER, ruling out overfitting to internal datasets.<br>
        4. <strong>SSIM &gt; PSNR clinical value</strong>: Denoising experiments reveal that best PSNR may come from over-smoothing; in pathology, metric balance matters more than single-metric optimality.<br>
        5. <strong>Restoration&harr;Staining synergy</strong>: Joint pre-training enables mutual benefit—degradation invariance from restoration helps staining, cross-domain mapping from staining helps restoration.</span>
      </div>
    </div>
  </section>
''')

    # ============================================================
    # SECTION 5: ABLATION
    # ============================================================
    cl_chart = bar_chart(
        "AF2HE PSNR 对比", "AF2HE PSNR Comparison",
        [
            ("w/ CL", 20.92, " dB", "linear-gradient(90deg,#0d9488,#14b8a6)"),
            ("w/o CL", 11.59, " dB", "linear-gradient(90deg,#ef4444,#f87171)"),
        ],
        25,
        source_zh="数据来源：原文 Figure 12 (消融实验)",
        source_en="Source: Paper Figure 12 (Ablation Study)"
    )

    rf_chart = bar_chart(
        "低分辨率修复 PSNR", "Low-Res Restoration PSNR",
        [
            ("w/ RF", 24.58, " dB", "linear-gradient(90deg,#0d9488,#14b8a6)"),
            ("w/o RF", 22.32, " dB", "linear-gradient(90deg,#d97706,#fbbf24)"),
        ],
        28,
        source_zh="数据来源：原文 Figure 13 (消融实验)",
        source_en="Source: Paper Figure 13 (Ablation Study)"
    )

    html_parts.append(f'''  <!-- ======================== 5. ABLATION ======================== -->
  <section id="ablation" class="fade-in">
    <div class="section-header">
      <span class="section-num">5</span>
      <h2 lang-zh>消融实验</h2>
      <h2 lang-en>Ablation Studies</h2>
    </div>

    <div class="subsection">
      <h3 lang-zh>5.1 对比预训练的有效性</h3>
      <h3 lang-en>5.1 Effectiveness of Contrastive Pre-training</h3>

{cl_chart}

      <p lang-zh>无对比学习版本在 AF2HE 上 PSNR 仅 <strong>11.59 dB</strong>（有 CL 为 <strong>20.92 dB</strong>），差距巨大。对比学习使 encoder 学会将退化/染色变化视为"同一组织的不同视角"。</p>
      <p lang-en>Without contrastive learning, AF2HE PSNR is only <strong>11.59 dB</strong> (with CL: <strong>20.92 dB</strong>), a huge gap. CL teaches the encoder to view degradation/staining changes as "different views of the same tissue."</p>

{img_ph("ph-fig12", "fig12_ablation_cl.png",
        "Figure 12: Ablation - Contrastive Learning",
        "有/无对比学习的消融实验对比",
        "Ablation study comparing with/without contrastive learning",
        ICO_FLASK)}
    </div>

    <div class="subsection">
      <h3 lang-zh>5.2 扩散精炼的有效性</h3>
      <h3 lang-en>5.2 Effectiveness of Diffusion Refinement</h3>

{rf_chart}

      <p lang-zh>精炼模块在所有任务上一致提升三个指标。噪声修复: 26.03&rarr;28.82 dB。AF2HE: 21.57&rarr;26.09 dB。主要贡献：恢复高频细节（核膜、染色质纹理）。</p>
      <p lang-en>Refinement module consistently improves all three metrics across all tasks. Noise restoration: 26.03&rarr;28.82 dB. AF2HE: 21.57&rarr;26.09 dB. Main contribution: recovering high-frequency details (nuclear membrane, chromatin texture).</p>

{img_ph("ph-fig13", "fig13_ablation_rf.png",
        "Figure 13: Ablation - Diffusion Refinement",
        "有/无扩散精炼的消融实验对比",
        "Ablation study comparing with/without diffusion refinement",
        ICO_FLASK)}
    </div>
  </section>
''')

    # ============================================================
    # SECTION 6: DISCUSSION
    # ============================================================
    html_parts.append('''  <!-- ======================== 6. DISCUSSION ======================== -->
  <section id="discussion" class="fade-in">
    <div class="section-header">
      <span class="section-num">6</span>
      <h2 lang-zh>讨论与思考</h2>
      <h2 lang-en>Discussion &amp; Thoughts</h2>
    </div>

    <div class="subsection">
      <h3 lang-zh>值得肯定的设计</h3>
      <h3 lang-en>Commendable Design Choices</h3>

      <div class="compare-grid">
        <div class="compare-card" style="border-left: 4px solid var(--emerald);">
          <h5 lang-zh>统一框架的范式价值</h5>
          <h5 lang-en>Paradigm Value of Unified Framework</h5>
          <p lang-zh>一个模型解决 6 类任务，不仅是工程简化，更说明 low-level pathology tasks 之间共享 underlying structure。</p>
          <p lang-en>One model for 6 task categories—not just engineering simplification, but evidence of shared underlying structure across low-level pathology tasks.</p>
        </div>
        <div class="compare-card" style="border-left: 4px solid var(--emerald);">
          <h5 lang-zh>对比预训练的 Insight</h5>
          <h5 lang-en>Contrastive Pre-training Insight</h5>
          <p lang-zh>将退化/染色变化建模为同一组织的"不同视角"，优雅且有效。</p>
          <p lang-en>Modeling degradation/staining changes as "different views" of the same tissue—elegant and effective.</p>
        </div>
        <div class="compare-card" style="border-left: 4px solid var(--emerald);">
          <h5 lang-zh>两阶段渐进精炼</h5>
          <h5 lang-en>Two-Stage Progressive Refinement</h5>
          <p lang-zh>粗糙修复&rarr;扩散精炼利用了 AE 的全局结构 vs Diffusion 的高频细节互补优势。</p>
          <p lang-en>Coarse restoration &rarr; diffusion refinement leverages complementary strengths of AE (global structure) vs Diffusion (high-frequency details).</p>
        </div>
        <div class="compare-card" style="border-left: 4px solid var(--emerald);">
          <h5 lang-zh>实验设计严谨</h5>
          <h5 lang-en>Rigorous Experimental Design</h5>
          <p lang-zh>66 个任务 + 内/外部双重验证 + 统计检验 + PCC 分析。</p>
          <p lang-en>66 tasks + internal/external validation + statistical tests + PCC analysis.</p>
        </div>
      </div>
    </div>

    <div class="subsection">
      <h3 lang-zh>可深入讨论的问题</h3>
      <h3 lang-en>Discussion Points</h3>

      <details class="discussion-card" open>
        <summary><span lang-zh>1. PSNR 非最优的辩护是否充分？</span><span lang-en>1. Is the PSNR Non-Optimality Defense Sufficient?</span></summary>
        <div class="detail-body">
          <p lang-zh>过平滑是否一定导致更高 PSNR？MSE 最小化和平滑并不等价。更根本的问题：<strong>在病理场景中，什么是"好"的去噪？</strong></p>
          <p lang-en>Does over-smoothing necessarily lead to higher PSNR? MSE minimization and smoothing are not equivalent. A more fundamental question: <strong>what defines "good" denoising in pathology?</strong></p>
        </div>
      </details>

      <details class="discussion-card" open>
        <summary><span lang-zh>2. 合成退化 vs 真实退化的 Domain Gap</span><span lang-en>2. Synthetic vs Real Degradation Domain Gap</span></summary>
        <div class="detail-body">
          <p lang-zh>所有修复任务基于合成退化。真实临床退化可能更复杂：非均匀模糊、spatially-varying noise、染色伪影与结构退化耦合。</p>
          <p lang-en>All restoration tasks use synthetic degradation. Real clinical degradation may be more complex: non-uniform blur, spatially-varying noise, staining artifacts coupled with structural degradation.</p>
        </div>
      </details>

      <details class="discussion-card" open>
        <summary><span lang-zh>3. 计算开销与临床可部署性</span><span lang-en>3. Computational Cost &amp; Clinical Deployability</span></summary>
        <div class="detail-body">
          <p lang-zh>两阶段训练 + 扩散推理 (50-100 步)。一张 100K &times; 100K WSI 包含约 150K patches。<strong>论文未报告推理时间和 GPU 需求。</strong></p>
          <p lang-en>Two-stage training + diffusion inference (50-100 steps). A 100K &times; 100K WSI has ~150K patches. <strong>Paper does not report inference time or GPU requirements.</strong></p>
        </div>
      </details>

      <details class="discussion-card" open>
        <summary><span lang-zh>4. Prompt 的实际灵活性</span><span lang-en>4. Actual Prompt Flexibility</span></summary>
        <div class="detail-body">
          <p lang-zh>当前 prompt 高度模板化。是否真需要 CLIP 级别的文本理解，还是简单的 task embedding 就够了？</p>
          <p lang-en>Current prompts are highly templated. Is CLIP-level text understanding truly necessary, or would simple task embeddings suffice?</p>
        </div>
      </details>

      <details class="discussion-card" open>
        <summary><span lang-zh>5. 与 High-level FM 的集成</span><span lang-en>5. Integration with High-level FMs</span></summary>
        <div class="detail-body">
          <p lang-zh>缺乏 LPFM + high-level FM (UNI, CONCH) 的端到端验证。核心问题：<strong>增强后的图像是否显著提升下游诊断性能？</strong></p>
          <p lang-en>Lacks LPFM + high-level FM (UNI, CONCH) end-to-end validation. Core question: <strong>Do enhanced images significantly improve downstream diagnostic performance?</strong></p>
        </div>
      </details>

      <details class="discussion-card" open>
        <summary><span lang-zh>6. Hallucination 风险</span><span lang-en>6. Hallucination Risk</span></summary>
        <div class="detail-body">
          <p lang-zh>生成模型在严重退化输入下可能 hallucinate 不存在的结构。论文承认但未提供定量评估。是否需要 uncertainty estimation 或 confidence map？</p>
          <p lang-en>Generative models may hallucinate nonexistent structures under severe degradation. Acknowledged but no quantitative assessment. Need for uncertainty estimation or confidence maps?</p>
        </div>
      </details>
    </div>
  </section>
''')

    # ============================================================
    # SECTION 7: QUICK REFERENCE
    # ============================================================
    html_parts.append('''  <!-- ======================== 7. QUICK REFERENCE ======================== -->
  <section id="quickref" class="fade-in">
    <div class="section-header">
      <span class="section-num">7</span>
      <h2 lang-zh>技术细节速查</h2>
      <h2 lang-en>Technical Quick Reference</h2>
    </div>

    <div class="table-wrap">
      <table class="ref-table">
        <tbody>
          <tr>
            <td lang-zh>输入 Patch 大小</td><td lang-en>Input Patch Size</td>
            <td>256&times;256, 32 pixel overlap</td>
          </tr>
          <tr>
            <td>Stage 1</td><td>Stage 1</td>
            <td>KL-Autoencoder (LDM) + CLIP text encoder</td>
          </tr>
          <tr>
            <td>Stage 2</td><td>Stage 2</td>
            <td>U-Net diffusion + trainable ControlNet-style module</td>
          </tr>
          <tr>
            <td lang-zh>条件注入</td><td lang-en>Conditioning</td>
            <td>Cross-attention (Stage 1), Zero conv (Stage 2)</td>
          </tr>
          <tr>
            <td lang-zh>推理</td><td lang-en>Inference</td>
            <td>DDIM scheduler, 50-100 steps</td>
          </tr>
          <tr>
            <td lang-zh>评估指标</td><td lang-en>Metrics</td>
            <td>PSNR &uarr;, SSIM &uarr;, LPIPS &darr;, MAE &darr;, PCC</td>
          </tr>
          <tr>
            <td lang-zh>预训练数据</td><td lang-en>Pre-training Data</td>
            <td>190M patches, 37 sources (87,810 WSIs)</td>
          </tr>
          <tr>
            <td lang-zh>内部测试集</td><td lang-en>Internal Test</td>
            <td>CAMELYON16, PANDA, PAIP2020 (7:1:2)</td>
          </tr>
          <tr>
            <td lang-zh>外部验证集</td><td lang-en>External Val</td>
            <td>OCELOT, MIDOG2022, TIGER2021</td>
          </tr>
          <tr>
            <td lang-zh>虚拟染色数据</td><td lang-en>Staining Data</td>
            <td>AF2HE, HE2PAS, HEMIT</td>
          </tr>
          <tr>
            <td>Code</td><td>Code</td>
            <td><a href="https://github.com/ziniBRC/LPFM" target="_blank" style="color:var(--accent);">github.com/ziniBRC/LPFM</a></td>
          </tr>
          <tr>
            <td>Ethics</td><td>Ethics</td>
            <td>HKUST HAREC, HREP-2024-0429</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 lang-zh>对比方法总结</h3>
      <h3 lang-en>Compared Methods Summary</h3>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th lang-zh>方法</th><th lang-en>Method</th>
              <th lang-zh>架构</th><th lang-en>Architecture</th>
              <th lang-zh>核心特点</th><th lang-en>Key Feature</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>CycleGAN</td><td>GAN</td><td lang-zh>循环一致性，无配对数据</td><td lang-en>Cycle consistency, unpaired</td></tr>
            <tr><td>Pix2Pix</td><td>Conditional GAN</td><td>U-Net + PatchGAN</td></tr>
            <tr><td>BSRGAN</td><td lang-zh>盲超分</td><td lang-en>Blind SR</td><td lang-zh>综合退化模型</td><td lang-en>Comprehensive degradation model</td></tr>
            <tr><td>SwinIR</td><td>Transformer</td><td lang-zh>倾向过平滑</td><td lang-en>Tends to over-smooth</td></tr>
            <tr><td>HistoDiff</td><td lang-zh>扩散模型</td><td lang-en>Diffusion</td><td lang-zh>形态感知注意力</td><td lang-en>Morphology-aware attention</td></tr>
            <tr><td>LDM</td><td lang-zh>潜在扩散</td><td lang-en>Latent Diffusion</td><td lang-zh>压缩感知空间</td><td lang-en>Compressed latent space</td></tr>
            <tr><td>RegGAN</td><td>GAN + Reg</td><td lang-zh>可微 STN 空间对齐</td><td lang-en>Differentiable STN alignment</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
''')

    # ── FOOTER ──
    html_parts.append('''  <!-- Footer -->
  <footer style="text-align:center;padding:40px 0 20px;color:var(--text-secondary);font-size:13px;border-top:1px solid var(--border);margin-top:40px;">
    <span lang-zh>LPFM 论文学习笔记 &middot; 组会展示用</span>
    <span lang-en>LPFM Paper Study Notes &middot; Group Meeting Presentation</span>
  </footer>

</div><!-- end .main-content -->
''')

    # ── JAVASCRIPT ──
    html_parts.append('''<script>
// ===== Theme Toggle =====
function toggleTheme() {
  const isDark = document.body.classList.toggle('dark');
  localStorage.setItem('lpfm-theme', isDark ? 'dark' : 'light');
}
// Restore theme preference
const savedTheme = localStorage.getItem('lpfm-theme');
if (savedTheme === 'dark') document.body.classList.add('dark');

// ===== Language Toggle =====
function setLang(lang) {
  document.body.classList.toggle('en', lang === 'en');
  document.getElementById('btn-zh').classList.toggle('active', lang === 'zh');
  document.getElementById('btn-en').classList.toggle('active', lang === 'en');
  localStorage.setItem('lpfm-lang', lang);
}
// Restore language preference
const savedLang = localStorage.getItem('lpfm-lang');
if (savedLang === 'en') setLang('en');

// ===== TOC Toggle (Mobile) =====
function toggleTOC() {
  document.getElementById('toc').classList.toggle('open');
}
// Close TOC when clicking a link (mobile)
document.querySelectorAll('.toc-sidebar a').forEach(a => {
  a.addEventListener('click', () => {
    document.getElementById('toc').classList.remove('open');
  });
});

// ===== Active TOC Highlight =====
const sections = document.querySelectorAll('section[id], .subsection[id]');
const tocLinks = document.querySelectorAll('.toc-sidebar a');
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      tocLinks.forEach(link => {
        link.classList.toggle('active', link.getAttribute('href') === '#' + entry.target.id);
      });
    }
  });
}, { rootMargin: '-20% 0px -70% 0px' });
sections.forEach(s => observer.observe(s));

// ===== Fade-in on Scroll =====
const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.fade-in').forEach(el => fadeObserver.observe(el));

// ===== Image Placeholder -> Real Image Replacement =====
// When you add images to the same directory, update this mapping:
const imageMap = {
  'ph-fig1b': 'figures/fig1b_architecture.png',
  'ph-fig1c': 'figures/fig1c_dataset_distribution.png',
  'ph-fig8':  'figures/fig8_training_pipeline.png',
  'ph-fig9':  'figures/fig9_inference_pipeline.png',
  'ph-fig10': 'figures/fig10_prompt_restoration.png',
  'ph-fig11': 'figures/fig11_prompt_staining.png',
  'ph-fig2':  'figures/fig2_super_resolution.png',
  'ph-fig3':  'figures/fig3_deblurring.png',
  'ph-fig4':  'figures/fig4_denoising.png',
  'ph-fig5':  'figures/fig5_virtual_staining.png',
  'ph-fig6':  'figures/fig6_compound_degradation.png',
  'ph-fig7':  'figures/fig7_degraded_staining.png',
  'ph-fig12': 'figures/fig12_ablation_cl.png',
  'ph-fig13': 'figures/fig13_ablation_rf.png',
};

// Auto-replace placeholders with images (preserving bilingual captions)
Object.entries(imageMap).forEach(([id, src]) => {
  const el = document.getElementById(id);
  if (el) {
    const img = new Image();
    img.onload = () => {
      const label = el.querySelector('.ph-label');
      const labelText = label ? label.textContent : '';
      const captionZh = el.querySelector('.ph-caption[lang-zh]');
      const captionEn = el.querySelector('.ph-caption[lang-en]');
      const zhText = captionZh ? captionZh.textContent : '';
      const enText = captionEn ? captionEn.textContent : '';
      el.outerHTML = `<figure style="margin:0;">
        <img class="fig-img" src="${src}" alt="${labelText}" loading="lazy"
             style="width:100%;border-radius:var(--radius);border:1px solid var(--border);">
        <figcaption style="font-size:12.5px;color:var(--text-secondary);margin-top:8px;line-height:1.5;">
          <strong>${labelText}</strong><br>
          <span lang-zh>${zhText}</span>
          <span lang-en>${enText}</span>
        </figcaption>
      </figure>`;
    };
    img.src = src;
  }
});
</script>

</body>
</html>
''')

    return "".join(html_parts)


def main() -> None:
    """Generate the LPFM presentation HTML."""
    html = build_html()
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated: {OUTPUT}")
    print(f"Size: {len(html):,} characters, {html.count(chr(10)):,} lines")


if __name__ == "__main__":
    main()
