#!/usr/bin/env python3
"""
app.py - DLsite 收藏浏览器 (标签分组 / 收藏 / 占位图 / 密度切换 / 社团筛选)
依赖: pip install flask
用法: python app.py  → 打开 http://localhost:5000
"""

import sqlite3
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_from_directory

_HERE   = Path(__file__).parent
DB_PATH = _HERE / "dlsite.db"

app = Flask(__name__)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_favorites(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            rj_id TEXT PRIMARY KEY,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dlsite-同人音声</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500&display=swap" rel="stylesheet">
<style>

:root {
  --bg:        #0c0c11;
  --surface:   #13131a;
  --card:      #18181f;
  --card-h:    #1f1f2a;
  --border:    #252530;
  --border-h:  #3a3a50;
  --accent:    #a78bfa;
  --accent-d:  #7c3aed;
  --accent-g:  linear-gradient(135deg, #a78bfa, #818cf8);
  --text:      #ede9f8;
  --sub:       #9490a8;
  --muted:     #52505e;
  --r18:       #e0191c;
  --r15:       #fb923c;
  --all:       #34d399;
  --gold:      #fbbf24;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-h); border-radius: 2px; }

body {
  background:
    radial-gradient(ellipse 1200px 600px at 15% -10%, rgba(167,139,250,.07), transparent 60%),
    radial-gradient(ellipse 900px 500px at 100% 10%, rgba(124,58,237,.05), transparent 55%),
    var(--bg);
  color: var(--text);
  font-family: 'Space Grotesk', 'Noto Sans JP', sans-serif;
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ─── Sidebar ─────────────────────────────────────── */
#sidebar {
  width: 230px;
  min-width: 230px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

#sidebar-header {
  padding: 20px 16px 14px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 12px;
}
.logo-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--accent-g);
  box-shadow: 0 0 8px rgba(167,139,250,.6);
  animation: pulse-dot 2.4s ease-in-out infinite;
  flex-shrink: 0;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: .5; transform: scale(.8); }
}
.logo-mark {
  font-size: 18px;
  font-weight: 700;
  background: var(--accent-g);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}
.logo-sub {
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.search-wrap { position: relative; }
.search-wrap svg {
  position: absolute;
  left: 10px; top: 50%;
  transform: translateY(-50%);
  color: var(--muted);
  pointer-events: none;
}
#search {
  width: 100%;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px 8px 32px;
  color: var(--text);
  font-size: 12px;
  font-family: inherit;
  outline: none;
  transition: border-color .15s;
}
#search:focus { border-color: var(--accent-d); }
#search::placeholder { color: var(--muted); }

#sidebar-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-section { border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 4px; }
.filter-section:last-child { border-bottom: none; }

.filter-heading {
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}
.filter-heading .chev { transition: transform .15s; font-size: 9px; }
.filter-heading.collapsed .chev { transform: rotate(-90deg); }

.filter-pills { display: flex; flex-wrap: wrap; gap: 4px; overflow: hidden; max-height: 600px; transition: max-height .2s ease; }
.filter-pills.collapsed { max-height: 0; }

.pill {
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 3px 9px;
  font-size: 11px;
  color: var(--sub);
  cursor: pointer;
  background: transparent;
  font-family: inherit;
  transition: all .15s;
  white-space: nowrap;
}
.pill:hover { border-color: var(--border-h); color: var(--text); }
.pill.on { background: var(--accent-d); border-color: var(--accent-d); color: #fff; }

.age-pill-全年齢.on { background: #065f46; border-color: var(--all); color: var(--all); }
.age-pill-R-15.on   { background: #7c2d12; border-color: var(--r15); color: var(--r15); }
.age-pill-R18.on   { background: #7f1d1d; border-color: var(--r18); color: var(--r18); }

/* ─── Main ───────────────────────────────────────── */
#main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

#topbar {
  padding: 14px 24px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(167,139,250,.03), transparent);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 10px;
  flex-wrap: wrap;
}

#stats { font-size: 11px; color: var(--muted); letter-spacing: 0.03em; white-space: nowrap; }
#stats b { color: var(--accent); font-weight: 500; }

.topbar-group { display: flex; align-items: center; gap: 8px; }

#fav-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 5px 12px;
  font-size: 11px;
  color: var(--sub);
  cursor: pointer;
  font-family: inherit;
  transition: all .2s;
}
#fav-toggle.on { border-color: var(--gold); color: var(--gold); background: rgba(251,191,36,.08); }

#density-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 5px 10px;
  font-size: 11px;
  color: var(--sub);
  cursor: pointer;
  font-family: inherit;
  transition: all .2s;
}
#density-toggle:hover { color: var(--text); border-color: var(--border-h); }

#blur-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 5px 12px;
  font-size: 11px;
  color: var(--sub);
  cursor: pointer;
  font-family: inherit;
  transition: all .2s;
}
#blur-toggle.on { border-color: var(--r18); color: var(--r18); background: rgba(248,113,113,.08); }
.blur-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--muted); transition: background .2s; }
#blur-toggle.on .blur-dot { background: var(--r18); }

#sort-btns { display: flex; gap: 4px; }
.sort-btn {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 4px 11px;
  font-size: 11px;
  color: var(--muted);
  cursor: pointer;
  font-family: inherit;
  transition: all .15s;
}
.sort-btn:hover { color: var(--text); border-color: var(--border-h); }
.sort-btn.on { border-color: var(--accent-d); color: var(--accent); background: rgba(124,58,237,.1); }

#grid-wrap { flex: 1; overflow-y: auto; padding: 20px 24px 24px; }

#grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(172px, 1fr));
  gap: 14px;
}
#grid.dense {
  grid-template-columns: repeat(auto-fill, minmax(118px, 1fr));
  gap: 10px;
}

/* ─── Card ───────────────────────────────────────── */
@keyframes card-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: transform .18s ease, border-color .18s, box-shadow .18s;
  position: relative;
  animation: card-in .35s ease backwards;
}
.card:hover {
  transform: translateY(-4px) scale(1.012);
  border-color: var(--accent-d);
  box-shadow: 0 12px 28px rgba(0,0,0,.5), 0 0 0 1px rgba(167,139,250,.15);
}

.card-img-wrap { position: relative; overflow: hidden; background: var(--card-h); }
.card-img-wrap img {
  width: 100%;
  aspect-ratio: 4/3;
  object-fit: cover;
  display: block;
  transition: filter .3s, transform .3s, opacity .4s;
  opacity: 0;
  animation: img-fade .4s ease forwards;
}
@keyframes img-fade { to { opacity: 1; } }
.card-img-wrap.no-cover {
  aspect-ratio: 4/3;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1c1c2a, #14141c);
}
.card-img-wrap.no-cover svg { color: var(--muted); width: 32px; height: 32px; }
.dense .card-img-wrap.no-cover svg { width: 22px; height: 22px; }

.card-img-wrap img.blurred { filter: blur(16px); transform: scale(1.08); }
.card-img-wrap img.blurred:hover { filter: blur(0); transform: scale(1); }

.card-age {
  position: absolute;
  top: 7px; right: 7px;
  font-size: 9px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.05em;
  backdrop-filter: blur(6px);
  z-index: 2;
}
.age-R18  { background: rgba(248,113,113,.28); color: var(--r18); border: 1px solid rgba(248,113,113,.35); box-shadow: 0 2px 8px rgba(224,25,28,.25); }
.age-R-15  { background: rgba(251,146,60,.28);  color: var(--r15); border: 1px solid rgba(251,146,60,.35); box-shadow: 0 2px 8px rgba(251,146,60,.2); }
.age-全年齢 { background: rgba(52,211,153,.22);   color: var(--all); border: 1px solid rgba(52,211,153,.3); box-shadow: 0 2px 8px rgba(52,211,153,.15); }

.fav-btn {
  position: absolute;
  top: 7px; left: 7px;
  z-index: 3;
  width: 22px; height: 22px;
  border-radius: 50%;
  background: rgba(0,0,0,.45);
  backdrop-filter: blur(4px);
  border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  color: rgba(255,255,255,.6);
  transition: all .15s;
}
.fav-btn:hover { background: rgba(0,0,0,.7); color: #fff; }
.fav-btn.on { color: var(--gold); animation: fav-pop .3s ease; }
@keyframes fav-pop {
  0% { transform: scale(1); }
  40% { transform: scale(1.35); }
  100% { transform: scale(1); }
}
.fav-btn svg { width: 13px; height: 13px; }

.card-body { padding: 10px 11px 11px; }
.dense .card-body { padding: 7px 8px 8px; }

.card-rj {
  font-size: 9px;
  font-weight: 500;
  color: var(--accent);
  letter-spacing: 0.06em;
  margin-bottom: 4px;
  font-family: 'Space Grotesk', monospace;
}
.dense .card-rj { font-size: 8px; margin-bottom: 2px; }

.card-title {
  font-size: 11px;
  line-height: 1.45;
  color: var(--text);
  font-weight: 400;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 5px;
}
.dense .card-title { font-size: 10px; margin-bottom: 3px; -webkit-line-clamp: 2; }

.card-cv {
  font-size: 10px;
  color: var(--sub);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dense .card-cv { font-size: 9px; }

.card-date { font-size: 9px; color: var(--muted); margin-top: 3px; font-variant-numeric: tabular-nums; }
.dense .card-date { display: none; }

#empty {
  color: var(--muted);
  font-size: 13px;
  text-align: center;
  padding-top: 80px;
  opacity: 0;
  animation: fade-in .4s ease forwards;
}
@keyframes fade-in { to { opacity: 1; } }

/* ─── Modal ─────────────────── */
#modal-bg {
  display: none;
  position: fixed; inset: 0;
  background: rgba(0,0,0,.75);
  backdrop-filter: blur(5px);
  z-index: 200;
  align-items: center;
  justify-content: center;
}
#modal-bg.open { display: flex; }

#modal {
  background: var(--surface);
  border: 1px solid var(--border-h);
  border-radius: 14px;
  width: min(720px, 94vw);
  max-height: 88vh;
  overflow-y: auto;
  position: relative;
  animation: modal-in .22s cubic-bezier(.16,1,.3,1);
  box-shadow: 0 24px 64px rgba(0,0,0,.6), 0 0 0 1px rgba(167,139,250,.08);
}
@keyframes modal-in {
  from { opacity: 0; transform: scale(.96) translateY(8px); }
  to   { opacity: 1; transform: scale(1)   translateY(0); }
}

#modal-close {
  position: absolute; top: 14px; right: 14px; z-index: 10;
  width: 28px; height: 28px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 50%;
  color: var(--sub);
  font-size: 13px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
#modal-close:hover { border-color: var(--border-h); color: var(--text); }

.modal-fav-btn {
  position: absolute; top: 14px; right: 52px; z-index: 10;
  width: 28px; height: 28px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 50%;
  color: var(--sub);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.modal-fav-btn.on { color: var(--gold); border-color: var(--gold); }
.modal-fav-btn svg { width: 14px; height: 14px; }

.modal-grid-layout { display: flex; gap: 20px; margin-bottom: 16px; }
@media (max-width: 576px) { .modal-grid-layout { flex-direction: column; align-items: center; } }

.modal-cover-side { width: 220px; min-width: 220px; display: flex; align-items: flex-start; justify-content: center; }
.modal-cover-side img {
  width: 100%; height: auto; max-height: 380px;
  object-fit: contain;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card);
}
.modal-cover-side.no-cover {
  height: 220px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: linear-gradient(135deg, #1c1c2a, #14141c);
}
.modal-cover-side.no-cover svg { width: 40px; height: 40px; color: var(--muted); }

.modal-info-side { flex: 1; display: flex; flex-direction: column; justify-content: flex-start; }
.modal-body { padding: 24px 24px 24px; }

.modal-rj {
  font-size: 11px; font-weight: 600; color: var(--accent);
  letter-spacing: 0.1em; margin-bottom: 6px;
  font-family: 'Space Grotesk', monospace;
}
.modal-title { font-size: 15px; font-weight: 500; line-height: 1.5; margin-bottom: 14px; color: var(--text); }

.modal-info { display: grid; grid-template-columns: auto 1fr; gap: 8px 12px; font-size: 12px; align-items: baseline; }
.modal-info-label { color: var(--muted); white-space: nowrap; }
.modal-info-val { color: var(--text); }

.link-click { color: var(--accent); cursor: pointer; text-decoration: underline; text-underline-offset: 3px; transition: color 0.12s; }
.link-click:hover { color: #c084fc; }

.modal-age-badge { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 5px; letter-spacing: 0.05em; }

.modal-tag-group { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border); }
.modal-tag-group:first-of-type { border-top: none; margin-top: 0; padding-top: 0; }
.modal-tag-group-label { font-size: 9px; color: var(--muted); letter-spacing: .1em; text-transform: uppercase; margin-bottom: 6px; }
.modal-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.modal-tag {
  background: var(--card); border: 1px solid var(--border); border-radius: 5px;
  font-size: 11px; padding: 3px 9px; color: var(--sub);
  cursor: pointer; transition: all .12s;
}
.modal-tag:hover { border-color: var(--accent); color: var(--accent); }

.modal-desc {
  font-size: 12px; line-height: 1.8; color: var(--sub);
  margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border);
  white-space: pre-wrap; max-height: 280px; overflow-y: auto;
}
</style>
</head>
<body>

<aside id="sidebar">
  <div id="sidebar-header">
    <div class="logo">
      <span class="logo-dot"></span>
      <span class="logo-mark">Dlsite-ASMR</span>
      <span class="logo-sub">Collection</span>
    </div>
    <div class="search-wrap">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <input id="search" placeholder="タイトル · CV · RJ番号 · 社团" oninput="filter()">
    </div>
  </div>

  <div id="sidebar-body">
    <div class="filter-section">
      <div class="filter-heading" onclick="toggleSection(this)">分级 <span class="chev">▾</span></div>
      <div class="filter-pills" id="age-filters"></div>
    </div>
    <div class="filter-section">
      <div class="filter-heading" onclick="toggleSection(this)">社团 <span class="chev">▾</span></div>
      <div class="filter-pills" id="circle-filters"></div>
    </div>
    <div class="filter-section">
      <div class="filter-heading" onclick="toggleSection(this)">声优 <span class="chev">▾</span></div>
      <div class="filter-pills" id="cv-filters"></div>
    </div>
    <div id="tag-group-container"></div>
  </div>
</aside>

<div id="main">
  <div id="topbar">
    <div id="stats"></div>
    <div class="topbar-group">
      <div id="sort-btns">
        <button class="sort-btn on" onclick="setSort('release_date',this)">发售日</button>
        <button class="sort-btn" onclick="setSort('added_at',this)">入库日</button>
        <button class="sort-btn" onclick="setSort('title',this)">标题</button>
      </div>
      <button id="fav-toggle" onclick="toggleFavOnly()">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
        收藏
      </button>
      <button id="density-toggle" onclick="toggleDensity()">
        <svg id="density-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
        <span id="density-label">小图</span>
      </button>
      <button id="blur-toggle" class="on" onclick="toggleBlur()">
        <span class="blur-dot"></span>
        R18 遮蔽
      </button>
    </div>
  </div>
  <div id="grid-wrap">
    <div id="grid"></div>
    <div id="empty" style="display:none">没有找到符合条件的作品</div>
  </div>
</div>

<div id="modal-bg" onclick="closeModal(event)">
  <div id="modal">
    <button id="modal-close" onclick="closeModal()">✕</button>
    <div id="modal-content"></div>
  </div>
</div>

<script>
let ALL = [];
let activeCVs  = new Set();
let activeTags = new Set();
let activeAges = new Set();
let activeCircles = new Set();
let favorites = new Set();
let blurOn   = true;
let sortKey  = 'release_date';
let favOnly  = false;
let dense    = false;

const NO_COVER_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>`;

const TAG_GROUPS = {
  "纯爱/日常": [
    "オールハッピー",
    "純愛",
    "ラブラブ/あまあま",
    "甘々",
    "溺愛",
    "感動",
    "日常/生活",
    "ほのぼの",
    "健全",
    "癒し",
    "睡眠",
    "睡眠導入",
    "添い寝",
    "同床",
    "おやすみ",
    "起こし",
    "朝起こし"
  ],

  "非全年龄剧情/倾向": [
    "NTR",
    "寝取り",
    "寝取られ",
    "ハーレム",
    "逆ハーレム",
    "退廃/背徳/インモラル",
    "鬱",
    "シリアス",
    "萌え"
  ],

  "背景/世界观/机制": [
    "ミステリー",
    "SF",
    "現代",
    "異世界",
    "異世界転生",
    "ファンタジー",
    "和風",
    "着物/和服",
    "学校/学園",
    "学園もの",
    "オフィス",
    "オフィス/職場",
    "電車",
    "風俗/ソープ",
    "シリーズもの",
    "同居",
    "同棲"
  ],

  "角色身份/人设": [
    "芸能人",
    "アイドル",
    "モデル",
    "Vtuber",
    "VTuber",
    "本人出演作品",
    "男主人公",
    "女教師",
    "保健医",
    "先生",
    "生徒",
    "学生",
    "同級生/同僚",
    "先輩",
    "後輩",
    "先輩/後輩",
    "上司",
    "部下",
    "人妻",
    "嫁",
    "旦那",
    "彼女",
    "彼氏",
    "恋人同士",
    "妹",
    "義妹",
    "義姉",
    "実姉",
    "双子姉妹",
    "幼馴染",
    "幼なじみ",
    "お姉さん",
    "シスター",
    "ナース",
    "メイド",
    "OL",
    "巫女",
    "悪役令嬢",
    "魔法使い/魔女",
    "エルフ",
    "エルフ/妖精",
    "サキュバス",
    "サキュバス/淫魔",
    "幽霊",
    "吸血鬼",
    "人外",
    "人外娘/モンスター娘",
    "獣人",
    "外国人",
    "ギャル",
    "少女",
    "ボクっ娘",
    "百合",
    "主従"
  ],

  "性格/属性/声线": [
    "ツンデレ",
    "ヤンデレ",
    "クール",
    "天然",
    "強気",
    "強気攻",
    "無表情",
    "ダウナー",
    "ぷに",
    "ロングヘア",
    "黒髪",
    "金髪",
    "ショートカット",
    "ツインテール",
    "ネコミミ",
    "獣耳",
    "メガネ",
    "女性視点",
    "男性受け",
    "総受",
    "低音ボイス",
    "高音ボイス",
    "ロリ系ボイス",
    "ボイス",
    "方言"
  ],

  "外貌/体型": [
    "巨乳",
    "爆乳",
    "巨乳/爆乳",
    "貧乳",
    "つるぺた",
    "ロリ",
    "ショタ",
    "おっぱい",
    "胸部",
    "おしり",
    "ふともも",
    "処女"
  ],

  "前戏/互动/边缘行为": [
    "マッサージ",
    "耳舐め",
    "耳かき",
    "囁き",
    "ささやき",
    "吐息",
    "耳ふー",
    "キス",
    "色仕掛け",
    "焦らし",
    "コスプレ",
    "制服",
    "セーラー服",
    "水着",
    "脱衣",
    "パンツ",
    "動物/ペット",
    "工作サポ",
    "オナサポ",
    "自慰辅助"
  ],

  "正戏/体位/绝顶表现": [
    "えっち",
    "イチャイチャ",
    "連続絶頂",
    "オホ声",
    "本番なし",
    "潮吹き",
    "中出し",
    "内射",
    "顔射",
    "大量射精",
    "口内射精",
    "フェラチオ",
    "クンニ",
    "手コキ",
    "パイズリ",
    "イマラチオ",
    "イラマチオ",
    "アナル",
    "オナニー",
    "乳首責め",
    "ぶっかけ",
    "ごっくん/食ザー",
    "妊娠/孕ませ",
    "アニメ汁/液大量",
    "淫語",
    "淡白/あっさり"
  ],

  "控场/攻受/特殊性癖": [
    "女性優位",
    "逆転無し",
    "逆レ",
    "逆レイプ",
    "レイプ",
    "痴女",
    "sissy",
    "フェチ",
    "複数プレイ/乱交",
    "SM",
    "拘束",
    "緊縛",
    "首輪/鎖/拘束具",
    "命令/無理矢理",
    "しつけ",
    "調教",
    "快楽堕ち",
    "メス堕ち",
    "おねショタ",
    "赤ちゃんプレイ",
    "電車"
  ],

  "精神控制/互动机制/音频系统": [
    "催眠",
    "洗脳",
    "精神支配",
    "支配",
    "トランス/暗示",
    "トランス/暗示ボイス",
    "オナニー指示",
    "言語責め",
    "言葉責め",
    "言語侵犯",
    "罵倒",
    "羞恥/恥辱",
    "ざぁ～こ♡",
    "マニアック/変態",
    "ASMR",
    "バイノーラル/ダミヘ",
    "ダミーヘッド",
    "立体音響",
    "環境音",
    "BGMなし",
    "高音質",
    "テキスト付き",
    "日本語",
    "中国語"
  ]
};

function toggleSection(headEl) {
  headEl.classList.toggle('collapsed');
  const pillsEl = headEl.nextElementSibling;
  pillsEl.classList.toggle('collapsed');
}

function setSort(key, btn) {
  sortKey = key;
  document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  filter();
}

function sortWorks(works) {
  return [...works].sort((a, b) => {
    if (sortKey === 'title') return (a.title||'').localeCompare(b.title||'', 'ja');
    const va = a[sortKey] || '';
    const vb = b[sortKey] || '';
    if (!va && !vb) return 0;
    if (!va) return 1;
    if (!vb) return -1;
    return vb.localeCompare(va);
  });
}

async function init() {
  const [works, cvs, tags, circles, favs] = await Promise.all([
    fetch('/api/works').then(r => r.json()),
    fetch('/api/cvs').then(r => r.json()),
    fetch('/api/tags').then(r => r.json()),
    fetch('/api/circles').then(r => r.json()),
    fetch('/api/favorites').then(r => r.json()),
  ]);
  ALL = works;
  favorites = new Set(favs);
  buildAgeFilters();
  buildCircleFilters(circles);
  buildCVFilters(cvs);
  buildTagGroups(tags);
  render(ALL);
}

function buildAgeFilters() {
  const ages = [...new Set(ALL.map(w => w.age_rating).filter(Boolean))];
  document.getElementById('age-filters').innerHTML = ages.map(a =>
    `<button class="pill age-pill-${a}" data-value="${a}" onclick="toggleAge('${a}',this)">${a}</button>`
  ).join('');
}
function buildCircleFilters(circles) {
  document.getElementById('circle-filters').innerHTML = circles.map(c =>
    `<button class="pill" data-value="${esc(c.circle)}" onclick="toggleCircle('${esc(c.circle)}',this)">${esc(c.circle)}<span style="color:var(--muted);font-size:9px;margin-left:3px">${c.cnt}</span></button>`
  ).join('');
}
function buildCVFilters(cvs) {
  document.getElementById('cv-filters').innerHTML = cvs.map(c =>
    `<button class="pill" data-value="${esc(c.name_jp)}" onclick="toggleCV('${esc(c.name_jp)}',this)">${esc(c.name_jp)}</button>`
  ).join('');
}
function buildTagGroups(tags) {
  const tagSet = new Set(tags.map(t => t.name_jp));
  const grouped = new Set();
  const container = document.getElementById('tag-group-container');
  let html = '';

  for (const [groupName, tagList] of Object.entries(TAG_GROUPS)) {
    const present = tagList.filter(t => tagSet.has(t));
    if (!present.length) continue;
    present.forEach(t => grouped.add(t));
    html += `<div class="filter-section">
      <div class="filter-heading" onclick="toggleSection(this)">${groupName} <span class="chev">▾</span></div>
      <div class="filter-pills">
        ${present.map(t => `<button class="pill" data-value="${esc(t)}" onclick="toggleTag('${esc(t)}',this)">${esc(TAG_JP2CN[t]||t)}</button>`).join('')}
      </div>
    </div>`;
  }

  const others = tags.map(t => t.name_jp).filter(t => !grouped.has(t));
  if (others.length) {
    html += `<div class="filter-section">
      <div class="filter-heading" onclick="toggleSection(this)">其他 <span class="chev">▾</span></div>
      <div class="filter-pills">
        ${others.map(t => `<button class="pill" data-value="${esc(t)}" onclick="toggleTag('${esc(t)}',this)">${esc(TAG_JP2CN[t]||t)}</button>`).join('')}
      </div>
    </div>`;
  }

  container.innerHTML = html;
}

function toggleAge(v, b) { toggle(activeAges, v, b); filter(); }
function toggleCV(v, b)  { toggle(activeCVs,  v, b); filter(); }
function toggleTag(v, b) { toggle(activeTags, v, b); filter(); }
function toggleCircle(v, b) { toggle(activeCircles, v, b); filter(); }
function toggle(set, v, btn) {
  set.has(v) ? set.delete(v) : set.add(v);
  if(btn) btn.classList.toggle('on', set.has(v));
}

function toggleFavOnly() {
  favOnly = !favOnly;
  document.getElementById('fav-toggle').classList.toggle('on', favOnly);
  filter();
}

function toggleDensity() {
  dense = !dense;
  document.getElementById('grid').classList.toggle('dense', dense);
  document.getElementById('density-label').textContent = dense ? '大图' : '小图';
}

async function toggleFavorite(rj_id, btnEl) {
  const isFav = favorites.has(rj_id);
  const method = isFav ? 'DELETE' : 'POST';
  await fetch('/api/favorites/' + rj_id, { method });
  if (isFav) favorites.delete(rj_id); else favorites.add(rj_id);
  if (btnEl) btnEl.classList.toggle('on', !isFav);
  if (favOnly) filter();
}

function linkSearchCircle(circleName) {
  closeModal();
  const btn = document.querySelector(`#circle-filters .pill[data-value="${CSS.escape(circleName)}"]`);
  if (btn) { if (!activeCircles.has(circleName)) toggleCircle(circleName, btn); }
  else { document.getElementById('search').value = circleName; filter(); }
}
function linkToggleCV(cvName) {
  closeModal();
  document.getElementById('search').value = "";
  const btn = document.querySelector(`#cv-filters .pill[data-value="${CSS.escape(cvName)}"]`);
  if (btn) { if (!activeCVs.has(cvName)) toggleCV(cvName, btn); }
  else { document.getElementById('search').value = cvName; filter(); }
}
function linkToggleTag(tagName) {
  closeModal();
  const btn = document.querySelector(`.filter-pills .pill[data-value="${CSS.escape(tagName)}"]`);
  if (btn) { if (!activeTags.has(tagName)) toggleTag(tagName, btn); }
}

function filter() {
  const q = document.getElementById('search').value.toLowerCase();
  const res = ALL.filter(w => {
    if (q && !w.title?.toLowerCase().includes(q)
          && !w.rj_id?.toLowerCase().includes(q)
          && !w.circle?.toLowerCase().includes(q)
          && !(w.cvs||[]).some(c => c.toLowerCase().includes(q))) return false;
    if (activeCVs.size && !(w.cvs||[]).some(c => activeCVs.has(c))) return false;
    if (activeCircles.size && !activeCircles.has(w.circle)) return false;
    if (activeTags.size && ![...activeTags].every(t => (w.tags||[]).includes(t))) return false;
    if (activeAges.size && !activeAges.has(w.age_rating)) return false;
    if (favOnly && !favorites.has(w.rj_id)) return false;
    return true;
  });
  render(res);
}

function ageClass(r) {
  if (r === 'R18') return 'age-R18';
  if (r === 'R-15') return 'age-R-15';
  return 'age-全年齢';
}

function render(works) {
  const grid  = document.getElementById('grid');
  const empty = document.getElementById('empty');
  const stats = document.getElementById('stats');
  stats.innerHTML = `<b>${works.length}</b> / ${ALL.length} 作品`;
  works = sortWorks(works);
  if (!works.length) { grid.innerHTML = ''; empty.style.display = 'block'; return; }
  empty.style.display = 'none';
  grid.innerHTML = works.map((w, i) => {
    const isFav = favorites.has(w.rj_id);
    const delay = Math.min(i * 0.02, 0.3);
    return `
    <div class="card" style="animation-delay:${delay}s" onclick="showDetail('${w.rj_id}')">
      <div class="card-img-wrap">
        <button class="fav-btn ${isFav?'on':''}" onclick="event.stopPropagation();toggleFavorite('${w.rj_id}',this)">
          <svg viewBox="0 0 24 24" fill="${isFav?'currentColor':'none'}" stroke="currentColor" stroke-width="2"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
        </button>
        ${w.cover_path ? `
        <img src="/cover/${encodeURIComponent(w.rj_id)}"
             data-age="${w.age_rating||''}"
             onerror="this.style.display='none';this.parentElement.classList.add('no-cover');this.parentElement.insertAdjacentHTML('beforeend', NO_COVER_SVG)"
             loading="lazy">
        ` : `<div class="card-img-wrap no-cover">${NO_COVER_SVG}</div>`}
        ${w.age_rating ? `<span class="card-age ${ageClass(w.age_rating)}">${w.age_rating}</span>` : ''}
      </div>
      <div class="card-body">
        <div class="card-rj">${w.rj_id}</div>
        <div class="card-title">${esc(w.title)}</div>
        <div class="card-cv">${(w.cvs||[]).map(esc).join(' · ') || '—'}</div>
        ${w.release_date ? `<div class="card-date">${w.release_date}</div>` : ''}
      </div>
    </div>`;
  }).join('');
  setTimeout(() => document.querySelectorAll('img[data-age]').forEach(applyBlur), 0);
}

function toggleBlur() {
  blurOn = !blurOn;
  const btn = document.getElementById('blur-toggle');
  btn.classList.toggle('on', blurOn);
  btn.lastChild.textContent = blurOn ? ' R18 遮蔽' : ' R18 显示';
  document.querySelectorAll('img[data-age]').forEach(applyBlur);
}
function applyBlur(img) {
  img.classList.toggle('blurred', blurOn && img.dataset.age === 'R18');
}

async function showDetail(rj_id) {
  const w = await fetch('/api/work/' + rj_id).then(r => r.json());
  const ageCls = ageClass(w.age_rating);
  const isFav = favorites.has(rj_id);

  const cvsHtml = (w.cvs || []).map(cv =>
    `<span class="link-click" onclick="linkToggleCV('${esc(cv)}')">${esc(cv)}</span>`
  ).join(' ') || '—';

  const tagsByGroup = {};
  const ungrouped = [];
  for (const tag of (w.tags || [])) {
    let found = false;
    for (const [groupName, tagList] of Object.entries(TAG_GROUPS)) {
      if (tagList.includes(tag)) {
        (tagsByGroup[groupName] = tagsByGroup[groupName] || []).push(tag);
        found = true; break;
      }
    }
    if (!found) ungrouped.push(tag);
  }
  let tagsHtml = '';
  for (const [groupName, tagList] of Object.entries(tagsByGroup)) {
    tagsHtml += `<div class="modal-tag-group">
      <div class="modal-tag-group-label">${groupName}</div>
      <div class="modal-tags">${tagList.map(tag => `<span class="modal-tag" onclick="linkToggleTag('${esc(tag)}')">${esc(TAG_JP2CN[tag]||tag)}</span>`).join('')}</div>
    </div>`;
  }
  if (ungrouped.length) {
    tagsHtml += `<div class="modal-tag-group">
      <div class="modal-tag-group-label">其他</div>
      <div class="modal-tags">${ungrouped.map(tag => `<span class="modal-tag" onclick="linkToggleTag('${esc(tag)}')">${esc(TAG_JP2CN[tag]||tag)}</span>`).join('')}</div>
    </div>`;
  }

  document.getElementById('modal-content').innerHTML = `
    <button class="modal-fav-btn ${isFav?'on':''}" onclick="toggleModalFav('${rj_id}', this)">
      <svg viewBox="0 0 24 24" fill="${isFav?'currentColor':'none'}" stroke="currentColor" stroke-width="2"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
    </button>
    <div class="modal-body">
      <div class="modal-grid-layout">
        <div class="modal-cover-side ${w.cover_path?'':'no-cover'}">
          ${w.cover_path
            ? `<img src="/cover/${encodeURIComponent(rj_id)}" onerror="this.parentElement.classList.add('no-cover');this.outerHTML=NO_COVER_SVG">`
            : NO_COVER_SVG}
        </div>
        <div class="modal-info-side">
          <div class="modal-rj">${w.rj_id}</div>
          <div class="modal-title">${esc(w.title)}</div>
          <div class="modal-info">
            <span class="modal-info-label">社团</span>
            <span class="modal-info-val link-click" onclick="linkSearchCircle('${esc(w.circle||'')}')">${esc(w.circle||'—')}</span>
            <span class="modal-info-label">声优</span>
            <span class="modal-info-val">${cvsHtml}</span>
            ${w.release_date ? `<span class="modal-info-label">发售日</span><span class="modal-info-val">${esc(w.release_date)}</span>` : ''}
            <span class="modal-info-label">分级</span>
            <span class="modal-info-val"><span class="modal-age-badge ${ageCls}">${w.age_rating||'—'}</span></span>
          </div>
        </div>
      </div>
      ${tagsHtml}
      ${w.description ? `<div class="modal-desc">${esc(w.description)}</div>` : ''}
    </div>
  `;
  document.getElementById('modal-bg').classList.add('open');
}

async function toggleModalFav(rj_id, btnEl) {
  await toggleFavorite(rj_id, null);
  btnEl.classList.toggle('on');
  const svg = btnEl.querySelector('svg');
  svg.setAttribute('fill', btnEl.classList.contains('on') ? 'currentColor' : 'none');
}

function closeModal(e) {
  if (!e || e.target === document.getElementById('modal-bg') || e.currentTarget.id === 'modal-close')
    document.getElementById('modal-bg').classList.remove('open');
}

function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

const TAG_JP2CN = {
  // === 核心声效与技术 ===
  "ASMR": "ASMR",
  "バイノーラル/ダミヘ": "双耳录音/Dummy Head",
  "ダミーヘッド": "Dummy Head麦克风",
  "立体音響": "3D立体音效",
  "高音質": "高音质",
  "BGMなし": "无背景音乐",
  "テキスト付き": "附文本",
  "ボイス": "语音作品",

  // === 互动与耳边轻语 ===
  "ささやき": "耳语",
  "囁き": "耳语",
  "吐息": "吐息",
  "耳かき": "掏耳",
  "耳舐め": "舔耳",
  "耳ふー": "吹耳",
  "睡眠": "睡眠",
  "睡眠導入": "助眠",
  "添い寝": "陪睡",
  "同床": "同床",
  "おやすみ": "晚安",
  "起こし": "叫醒",
  "朝起こし": "晨间叫醒",
  "癒し": "治愈",
  "マッサージ": "按摩", // 已补回

  // === 身体部位与服装 ===
  "おっぱい": "胸部",
  "胸部": "胸部",
  "巨乳": "巨乳",
  "爆乳": "爆乳",
  "巨乳/爆乳": "巨乳/爆乳",
  "貧乳": "贫乳",
  "つるぺた": "平胸",
  "おしり": "臀部",
  "ふともも": "大腿",
  "ぷに": "肉感",
  "ロングヘア": "长发",
  "黒髪": "黑发",
  "ショートカット": "短发",
  "金髪": "金发",
  "メガネ": "眼镜",
  "制服": "制服",
  "セーラー服": "水手服",
  "水着": "泳装",
  "脱衣": "脱衣",
  "パンツ": "内裤",

  // === 角色身份与属性 ===
  "お姉さん": "大姐姐",
  "妹": "妹妹",
  "義妹": "义妹",
  "義姐": "义姐",
  "実姉": "亲姐姐",
  "人妻": "人妻",
  "嫁": "妻子",
  "旦那": "丈夫",
  "恋人同士": "情侣",
  "彼女": "女友",
  "彼氏": "男友",
  "幼馴染": "青梅竹马",
  "幼なじみ": "青梅竹马",
  "同級生/同僚": "同学/同事",
  "先輩": "前辈",
  "後輩": "后辈",
  "先輩/後輩": "前后辈",
  "上司": "上司",
  "部下": "下属",
  "先生": "老师",
  "生徒": "学生",
  "学生": "学生",
  "女教師": "女教师",
  "保健医": "校医",
  "ナース": "护士",
  "シスター": "修女",
  "メイド": "女仆",
  "お嬢様": "大小姐",
  "悪役令嬢": "恶役大小姐",
  "ギャル": "辣妹",
  "少女": "少女",
  "ロリ": "萝莉",
  "ショタ": "正太",
  "おねショタ": "姐姐×正太",
  "男主人公": "男主角",
  "ボクっ娘": "仆娘",
  "ヤリチン/プレイボーイ": "花花公子",
  "外国人": "外国人",
  "芸能人": "艺人",
  "アイドル": "偶像",
  "モデル": "模特",
  "芸能人/アイドル/モデル": "艺人/偶像/模特",
  "Vtuber": "VTuber",
  "VTuber": "VTuber",
  "本人出演作品": "本人出演作品",

  // === 幻想与非人生物 ===
  "異世界": "异世界",
  "異世界転生": "异世界转生",
  "ファンタジー": "奇幻",
  "エルフ": "精灵",
  "エルフ/妖精": "精灵/妖精",
  "サキュバス": "魅魔",
  "サキュバス/淫魔": "魅魔",
  "巫女": "巫女",
  "人外": "非人",
  "人外娘/モンスター娘": "魔物娘",
  "獣人": "兽人",
  "獣耳": "兽耳",
  "ネコミミ": "猫耳",
  "幽霊": "幽灵",
  "吸血鬼": "吸血鬼",
  "魔法使い/魔女": "魔法师/魔女",
  "動物/ペット": "动物/宠物", // 已补回

  // === 角色性格与声音特质 ===
  "ツンデレ": "傲娇",
  "ヤンデレ": "病娇",
  "クール": "高冷",
  "天然": "天然呆",
  "強気": "强势",
  "強気攻": "强势攻",
  "クール攻め": "高冷攻",
  "ダウナー": "低气压系",
  "無表情": "无表情",
  "ツインテール": "双马尾", // 已补回
  "低音ボイス": "低音嗓音",
  "高音ボイス": "高音嗓音",
  "ロリ系ボイス": "萝莉音",
  "方言": "方言",

  // === 剧情发展与世界观 ===
  "現代": "现代",
  "和風": "和风",
  "着物/和服": "和服",
  "日常/生活": "日常生活",
  "ほのぼの": "温馨日常",
  "学園もの": "校园题材",
  "学校/学園": "学校/校园",
  "オフィス": "办公室",
  "オフィス/職場": "办公室/职场",
  "同居": "同居",
  "同棲": "同居生活",
  "シリーズもの": "系列作品",
  "健全": "全年龄",
  "シリアス": "严肃剧情",
  "SF": "科幻",
  "ミステリー": "悬疑",
  "感动": "感动系",
  "感動": "感动系",
  "溺愛": "溺爱",
  "純愛": "纯爱",
  "百合": "百合",
  "オールハッピー": "全员HE",
  "退廃/背徳/インモラル": "颓废/背德/不伦",
  "鬱": "致郁",
  "アニメ": "动画",
  "ラブコメ": "恋爱喜剧", // 已补回

  // === 玩法、调教与控制 (含特殊/重口分类) ===
  "しつけ": "调教",
  "調教": "调教",
  "命令/無理矢理": "命令/强迫",
  "精神支配": "精神支配",
  "催眠": "催眠",
  "洗脳": "洗脑",
  "トランス/暗示": "出神/暗示",
  "トランス/暗示ボイス": "暗示催眠语音",
  "支配": "支配",
  "拘束": "拘束",
  "首輪/鎖/拘束具": "项圈/锁链/拘束具",
  "緊縛": "绳缚",
  "SM": "SM",
  "羞恥/恥辱": "羞耻/耻辱",
  "言葉責め": "言语凌辱",
  "罵倒": "辱骂",
  "ざぁ～こ♡": "杂鱼♡",
  "痴女": "痴女",
  "色仕掛け": "色诱",
  "マニアック/変態": "重口/变态",
  "风俗/ソープ": "风俗店/泡泡浴", // 已补回
  "風俗/ソープ": "风俗店/泡泡浴", // 补全繁简日体混写格式
  "電車": "电车",
  "キャットファイト": "女子格斗",
  "双子姉妹": "双胞胎姐妹",

  // === 性爱场景与体液 (含敏感分类) ===
  "えっち": "H",
  "イチャイチャ": "卿卿我我",
  "ラブラブ/あまあま": "甜蜜恩爱",
  "甘々": "甜甜蜜蜜",
  "淡白/あっさり": "清淡系",
  "本番なし": "无插入",
  "逆転無し": "无逆转",
  "男性受け": "男性受向",
  "女性優位": "女性主导",
  "女性視点": "女性视角",
  "NTR": "NTR",
  "寝取り": "寝取",
  "寝取られ": "被寝取",
  "ハーレム": "后宫",
  "逆ハーレム": "逆后宫",
  "複数プレイ/乱交": "多人玩法/乱交",
  "总受": "总受",
  "総受": "总受",
  "年上": "年长",
  "年下": "年幼",
  "年下攻め": "年下攻",
  "工作サポ": "自慰辅助",
  "自慰辅助": "自慰辅助",
  "オナサポ": "自慰辅助",
  "オナニー": "自慰",
  "オナニー指示": "自慰指示",
  "焦らし": "寸止/挑逗",
  "おもちゃ": "情趣玩具",
  "ローション": "润滑液",
  "連続絶頂": "连续高潮",
  "快楽堕ち": "快感堕落",
  "メス堕ち": "雌堕",
  "逆レ": "逆推",
  "逆レイプ": "逆强奸",
  "レイプ": "强奸",
  "媚薬": "媚药",
  "処女": "处女",
  "淫語": "淫语",
  "淫乱": "淫乱",
  "乳首責め": "乳头刺激",
  "キス": "接吻",
  "手コキ": "手交",
  "パイズリ": "乳交",
  "フェラチオ": "口交",
  "クンニ": "舔阴",
  "口内射精": "口内射精",
  "イマラチオ": "强制口交",
  "イラマチオ": "强制口交",
  "アナル": "肛交",
  "中出し": "内射",
  "内射": "内射",
  "顔射": "颜射",
  "大量射精": "大量射精",
  "ぶっかけ": "大量射液",
  "アニメ汁/液大量": "大量体液",
  "潮吹き": "潮吹",
  "ごっくん/食ザー": "吞精",
  "妊娠/孕ませ": "受孕",
  "赤ちゃんプレイ": "婴儿扮演",
  "コスプレ": "角色扮演",
  "フェチ": "癖好",
  "オホ声": "娇喘（オホ声）", // 已补回

  // === 语言 ===
  "日本語": "日语",
  "中国語": "中文"
};

init();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/works")
def api_works():
    conn = get_conn()
    init_favorites(conn)
    rows = conn.execute("SELECT rj_id, title, circle, cover_path, age_rating, release_date FROM works ORDER BY added_at DESC").fetchall()
    result = []
    for w in rows:
        cvs = [r["name_jp"] for r in conn.execute(
            "SELECT c.name_jp FROM cvs c JOIN work_cvs wc ON c.cv_id=wc.cv_id WHERE wc.rj_id=?",
            (w["rj_id"],)
        ).fetchall()]
        tags = [r["name_jp"] for r in conn.execute(
            "SELECT t.name_jp FROM tags t JOIN work_tags wt ON t.tag_id=wt.tag_id WHERE wt.rj_id=?",
            (w["rj_id"],)
        ).fetchall()]
        result.append(dict(w) | {"cvs": cvs, "tags": tags})
    conn.close()
    return jsonify(result)

@app.route("/api/work/<rj_id>")
def api_work(rj_id):
    conn = get_conn()
    w = conn.execute("SELECT * FROM works WHERE rj_id=?", (rj_id,)).fetchone()
    if not w:
        return jsonify({"error": "not found"}), 404
    cvs = [r["name_jp"] for r in conn.execute(
        "SELECT c.name_jp FROM cvs c JOIN work_cvs wc ON c.cv_id=wc.cv_id WHERE wc.rj_id=?",
        (rj_id,)
    ).fetchall()]
    tags = [r["name_jp"] for r in conn.execute(
        "SELECT t.name_jp FROM tags t JOIN work_tags wt ON t.tag_id=wt.tag_id WHERE wt.rj_id=?",
        (rj_id,)
    ).fetchall()]
    conn.close()
    return jsonify(dict(w) | {"cvs": cvs, "tags": tags})

@app.route("/api/cvs")
def api_cvs():
    conn = get_conn()
    rows = conn.execute(
        "SELECT c.cv_id, c.name_jp, COUNT(wc.rj_id) as cnt "
        "FROM cvs c JOIN work_cvs wc ON c.cv_id=wc.cv_id "
        "GROUP BY c.cv_id ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/circles")
def api_circles():
    conn = get_conn()
    rows = conn.execute(
        "SELECT circle, COUNT(*) as cnt FROM works "
        "WHERE circle IS NOT NULL AND circle != '' "
        "GROUP BY circle ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/tags")
def api_tags():
    conn = get_conn()
    rows = conn.execute(
        "SELECT t.tag_id, t.name_jp, COUNT(wt.rj_id) as cnt "
        "FROM tags t JOIN work_tags wt ON t.tag_id=wt.tag_id "
        "GROUP BY t.tag_id ORDER BY cnt DESC LIMIT 200"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/favorites")
def api_favorites():
    conn = get_conn()
    init_favorites(conn)
    rows = conn.execute("SELECT rj_id FROM favorites").fetchall()
    conn.close()
    return jsonify([r["rj_id"] for r in rows])

@app.route("/api/favorites/<rj_id>", methods=["POST"])
def add_favorite(rj_id):
    conn = get_conn()
    init_favorites(conn)
    conn.execute("INSERT OR IGNORE INTO favorites (rj_id) VALUES (?)", (rj_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/favorites/<rj_id>", methods=["DELETE"])
def remove_favorite(rj_id):
    conn = get_conn()
    init_favorites(conn)
    conn.execute("DELETE FROM favorites WHERE rj_id=?", (rj_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/cover/<rj_id>")
def serve_cover(rj_id):
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = _HERE / "covers" / f"{rj_id}.{ext}"
        if p.exists():
            return send_from_directory(p.parent, p.name)
    return "", 404

if __name__ == "__main__":
    import os
    conn = get_conn()
    init_favorites(conn)
    conn.close()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)