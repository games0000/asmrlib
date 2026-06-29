#!/usr/bin/env python3
"""
add.py - DLsite 作品入库脚本（含贩售日）
依赖: pip install requests beautifulsoup4
"""
import json
import re
import sqlite3
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# ═══════════════════════════════════════════════════════
#  配置区
# ═══════════════════════════════════════════════════════

RJ_ID = "RJ01546420"

_HERE     = Path(__file__).parent
DB_PATH   = _HERE / "dlsite.db"
COVER_DIR = _HERE / "covers"

# ═══════════════════════════════════════════════════════

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
    "Referer": "https://www.dlsite.com/",
}
COOKIES = {"locale": "ja-jp", "adultchecked": "1"}

AGE_MAP = {1: "全年齢", 2: "R-15", 3: "R18"}
SITES   = ("maniax", "home", "girls", "bl", "soft", "indie")

# ── 数据库初始化 ──────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS works (
            rj_id        TEXT PRIMARY KEY,
            title        TEXT,
            circle       TEXT,
            description  TEXT,
            cover_path   TEXT,
            age_rating   TEXT,
            release_date TEXT,
            added_at     DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS cvs (
            cv_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name_jp TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS work_cvs (
            rj_id TEXT,
            cv_id INTEGER,
            PRIMARY KEY (rj_id, cv_id)
        );
        CREATE TABLE IF NOT EXISTS tag_categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS tags (
            tag_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name_jp     TEXT,
            UNIQUE(category_id, name_jp)
        );
        CREATE TABLE IF NOT EXISTS work_tags (
            rj_id  TEXT,
            tag_id INTEGER,
            PRIMARY KEY (rj_id, tag_id)
        );
    """)
    # 对旧数据库兼容：如果 release_date 列不存在则补上
    try:
        conn.execute("ALTER TABLE works ADD COLUMN release_date TEXT")
        conn.commit()
    except Exception:
        pass

# ── 日期格式统一 ──────────────────────────────────────────────────────────────
def clean_date(raw):
    """把各种格式统一成 YYYY-MM-DD，解析失败返回空字符串"""
    if not raw:
        return ""
    s = str(raw).strip()
    # 2022年03月15日 → 2022-03-15
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", s)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    # 2024-03-15T00:00:00 → 2024-03-15
    s = re.sub(r"T.*", "", s)
    # 2024/03/15 → 2024-03-15
    s = s.replace("/", "-")
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    return m.group(1) if m else ""

# ── 抓取核心逻辑 ──────────────────────────────────────────────────────────────
def fetch_work(rj_id):
    for site in SITES:
        url = f"https://www.dlsite.com/{site}/product/info/ajax?product_id={rj_id}&cdn_cache_min=1"
        try:
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
            if r.status_code != 200:
                continue
            data = r.json()
            if isinstance(data, dict):
                rj_stripped = "RJ" + str(int(rj_id[2:]))
                for key in (rj_id, rj_stripped):
                    if key in data:
                        return ("api", data[key], site)
                for k, v in data.items():
                    if k.upper().startswith("RJ") and isinstance(v, dict):
                        return ("api", v, site)
            elif isinstance(data, list) and data:
                return ("api", data[0], site)
        except Exception:
            continue

    for site in SITES:
        url = f"https://www.dlsite.com/{site}/work/=/product_id/{rj_id}.html"
        try:
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15, allow_redirects=True)
            if r.status_code == 200 and rj_id.lower() in r.url.lower():
                if "この地域" not in r.text and "ご利用いただけません" not in r.text:
                    return ("html", r.text, site)
        except Exception:
            continue

    raise RuntimeError(f"无法获取 {rj_id}，所有方法均失败")

# ── 解析 API 响应 ─────────────────────────────────────────────────────────────
def parse_api(raw, rj_id, site):
    title  = raw.get("work_name", "")
    circle = raw.get("maker_name", "")

    age_code   = raw.get("age_category", 0)
    age_rating = AGE_MAP.get(age_code, "")
    if not age_rating:
        age_rating = "18禁" if site in ("maniax", "girls", "bl") else "全年齢"

    # 贩售日（穷举所有已知字段名）
    release_date = clean_date(
        raw.get("regist_date") or raw.get("work_regist_date") or
        raw.get("sales_date")  or raw.get("release_date")     or
        raw.get("dl_date")     or ""
    )

    genres_data = raw.get("genres", [])
    va_data     = raw.get("voice_actor", [])

    translation_info = raw.get("translation_info", {})
    if (not genres_data) and translation_info and translation_info.get("is_child"):
        parent_rj = translation_info.get("original_workno") or translation_info.get("parent_workno")
        if parent_rj and parent_rj != rj_id:
            print(f"  [提示] 翻译版，追溯原版 ({parent_rj}) 标签和 CV...")
            try:
                p_url = f"https://www.dlsite.com/{site}/work/=/product_id/{parent_rj}.html"
                r = requests.get(p_url, headers=HEADERS, cookies=COOKIES, timeout=15, allow_redirects=True)
                if r.status_code == 200 and "この地域" not in r.text:
                    parent_data = parse_html(r.text, parent_rj, site)
                    genres_data = [{"category": cat, "name": n}
                                   for cat, names in parent_data["tags"].items() for n in names]
                    va_data = parent_data["cvs"]
                    # 原版贩售日也一并带回（翻译版通常没有独立日期）
                    if not release_date and parent_data.get("release_date"):
                        release_date = parent_data["release_date"]
                    print(f"  [成功] 获取到 {len(va_data)} CV / {len(genres_data)} 标签")
                else:
                    _, p_payload, _ = fetch_work(parent_rj)
                    va_data     = p_payload.get("voice_actor", [])
                    genres_data = p_payload.get("genres", [])
            except Exception as e:
                print(f"  [警告] 追溯失败: {e}")

    cvs = []
    if isinstance(va_data, list):
        for item in va_data:
            if isinstance(item, str):   cvs.append(item)
            elif isinstance(item, dict):cvs.append(item.get("name", ""))
    elif isinstance(va_data, str) and va_data:
        cvs = [v.strip() for v in re.split(r"[,、/・]", va_data) if v.strip()]

    tags = {}
    for g in genres_data:
        if isinstance(g, dict):
            cat  = g.get("category", "ジャンル") or "ジャンル"
            name = g.get("name", "")
            if name:
                tags.setdefault(cat, []).append(name)

    cover_url = ""
    img = raw.get("work_image", "") or raw.get("image_main", {})
    if isinstance(img, str) and img:
        cover_url = ("https:" + img) if img.startswith("//") else img
    elif isinstance(img, dict):
        src = img.get("url", "") or img.get("src", "")
        cover_url = ("https:" + src) if src.startswith("//") else src

    description = raw.get("work_intro", "") or raw.get("intro_s", "") or ""

    return {
        "rj_id": rj_id, "title": title, "circle": circle,
        "description": description, "cover_url": cover_url,
        "cvs": [c for c in cvs if c], "tags": tags,
        "age_rating": age_rating, "release_date": release_date,
    }

# ── 解析 HTML 响应 ────────────────────────────────────────────────────────────
def parse_html(html, rj_id, site):
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    el = soup.select_one("#work_name")
    if el:
        for s in el.select("span"):
            s.decompose()
        title = el.get_text(strip=True)

    cover_url = ""
    for sel in (".product-slider-data [data-src]", "#work_left_inner [data-src]",
                "#work_left_inner img", ".work_img_main img", "meta[property='og:image']"):
        el = soup.select_one(sel)
        if not el:
            continue
        src = el.get("data-src") or el.get("src") or el.get("content", "")
        if src and ("dlsite" in src or src.startswith("//")):
            cover_url = ("https:" + src) if src.startswith("//") else src
            break

    circle = ""
    cvs    = []
    tags   = {}
    age_rating   = ""
    release_date = ""

    table = soup.select_one("table#work_outline") or soup.select_one("#work_right_inner table")
    if table:
        for row in table.select("tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if not th or not td:
                continue
            key = th.get_text(strip=True)
            val = td.get_text(strip=True)

            if any(k in key for k in ("サークル", "ブランド", "メーカー")):
                a = td.select_one("a")
                circle = a.get_text(strip=True) if a else val
            elif any(k in key for k in ("声優", "CV", "キャスト")):
                names = [a.get_text(strip=True) for a in td.select("a")]
                if not names and val:
                    names = [n.strip() for n in re.split(r"[,、/・\s ]+", val) if n.strip()]
                cvs = names
            elif any(k in key for k in ("ジャンル", "タグ")):
                tag_list = [a.get_text(strip=True) for a in td.select("a")]
                if not tag_list:
                    tag_list = [s.get_text(strip=True) for s in td.select("span") if s.get_text(strip=True)]
                if tag_list:
                    tags["ジャンル"] = tag_list
            elif any(k in key for k in ("年齢", "レーティング")):
                age_rating = val
            elif any(k in key for k in ("販売日", "発売日", "登録日", "更新日", "配信開始日")):
                release_date = clean_date(val)

    if not circle:
        for sel in (".maker_name a", "#work_maker_name a"):
            el = soup.select_one(sel)
            if el:
                circle = el.get_text(strip=True)
                break

    if not age_rating:
        age_rating = "18禁" if site in ("maniax", "girls", "bl") else "全年齢"

    description = ""
    for sel in ("#work_parts", ".work_parts_container", "#work_intro"):
        el = soup.select_one(sel)
        if el:
            description = el.get_text(separator="\n", strip=True)[:1000]
            break

    return {
        "rj_id": rj_id, "title": title, "circle": circle,
        "description": description, "cover_url": cover_url,
        "cvs": cvs, "tags": tags,
        "age_rating": age_rating, "release_date": release_date,
    }

# ── 封面下载 ──────────────────────────────────────────────────────────────────
def download_cover(rj_id, url):
    if not url:
        return ""
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    ext = re.sub(r"\?.*", "", url.split(".")[-1]).lower() or "jpg"
    if len(ext) > 4 or "/" in ext:
        ext = "webp" if "webp" in url else "jpg"
    dest = COVER_DIR / f"{rj_id}.{ext}"
    if dest.exists():
        return str(dest)
    try:
        r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=30)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return str(dest)
    except Exception as e:
        print(f"  [警告] 封面下载失败: {e}")
        return ""

# ── 写入数据库 ────────────────────────────────────────────────────────────────
def upsert_work(conn, data, cover_path):
    rj_id = data["rj_id"]
    conn.execute("""
        INSERT INTO works (rj_id, title, circle, description, cover_path, age_rating, release_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(rj_id) DO UPDATE SET
            title=excluded.title, circle=excluded.circle,
            description=excluded.description, cover_path=excluded.cover_path,
            age_rating=excluded.age_rating, release_date=excluded.release_date
    """, (rj_id, data["title"], data["circle"], data["description"],
          cover_path, data["age_rating"], data.get("release_date", "")))

    conn.execute("DELETE FROM work_cvs  WHERE rj_id = ?", (rj_id,))
    conn.execute("DELETE FROM work_tags WHERE rj_id = ?", (rj_id,))

    for name in data["cvs"]:
        conn.execute("INSERT OR IGNORE INTO cvs (name_jp) VALUES (?)", (name,))
        cv_id = conn.execute("SELECT cv_id FROM cvs WHERE name_jp=?", (name,)).fetchone()["cv_id"]
        conn.execute("INSERT OR IGNORE INTO work_cvs (rj_id, cv_id) VALUES (?,?)", (rj_id, cv_id))

    for category, tag_list in data["tags"].items():
        conn.execute("INSERT OR IGNORE INTO tag_categories (name) VALUES (?)", (category,))
        cat_id = conn.execute(
            "SELECT category_id FROM tag_categories WHERE name=?", (category,)
        ).fetchone()["category_id"]
        for tag_name in tag_list:
            conn.execute("INSERT OR IGNORE INTO tags (category_id, name_jp) VALUES (?,?)", (cat_id, tag_name))
            tag_id = conn.execute(
                "SELECT tag_id FROM tags WHERE category_id=? AND name_jp=?", (cat_id, tag_name)
            ).fetchone()["tag_id"]
            conn.execute("INSERT OR IGNORE INTO work_tags (rj_id, tag_id) VALUES (?,?)", (rj_id, tag_id))

    conn.commit()


# ── 单作处理 ──────────────────────────────────────────────────────────────────
def process_single_rj(conn, rj_id):
    rj_id = rj_id.strip().upper()
    if not rj_id.startswith("RJ"):
        rj_id = "RJ" + rj_id

    print(f"\n[{rj_id}] 正在获取数据...")
    try:
        method, payload, site = fetch_work(rj_id)
    except Exception as e:
        print(f"  [错误] {e}")
        return False

    data = parse_api(payload, rj_id, site) if method == "api" else parse_html(payload, rj_id, site)

    total_tags = sum(len(v) for v in data["tags"].values())
    if method == "api" and (not data["circle"] or total_tags == 0):
        print(f"  [注意] API 数据不完整，切换网页端...")
        try:
            url = f"https://www.dlsite.com/{site}/work/=/product_id/{rj_id}.html"
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15, allow_redirects=True)
            if r.status_code == 200 and "この地域" not in r.text:
                html_data = parse_html(r.text, rj_id, site)
                # 智能合并：以网页端为主，API 端已有的字段作为兜底
                merged = html_data.copy()
                for field in ("title", "circle", "cvs", "tags", "release_date"):
                    api_val = data.get(field)
                    html_val = html_data.get(field)
                    # 网页端有值用网页端，否则保留 API 端
                    empty = lambda v: not v or v == [] or v == {}
                    if empty(html_val) and not empty(api_val):
                        merged[field] = api_val
                data = merged
                total_tags = sum(len(v) for v in data["tags"].values())
                print(f"  [成功] 网页端补全完成")
        except Exception as e:
            print(f"  [警告] 切换网页端失败: {e}")

    print(f"  来源:    {method.upper()} / {site}")
    print(f"  标题:    {data['title']}")
    print(f"  社团:    {data['circle'] or '(未找到)'}")
    print(f"  CV:      {', '.join(data['cvs']) or '(未找到)'}")
    print(f"  分级:    {data['age_rating']}")
    print(f"  贩售日:  {data.get('release_date') or '(未找到)'}")
    print(f"  标签:    {total_tags} 个")

    cover_path = download_cover(rj_id, data["cover_url"])
    print(f"  封面:    {cover_path or '(无)'}")

    upsert_work(conn, data, cover_path)
    print(f"[{rj_id}] 完成 ✓")
    return True

# ── 执行 ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    conn = get_conn()
    init_db(conn)

    BATCH_MODE = "list"
    rj_queue   = []

    if BATCH_MODE == "list":
        target_list =[ "RJ01512640"]
 # ← 单个时只改顶部 RJ_ID；批量时在这里填列表
        for item in target_list:
            cleaned = item.strip().upper()
            if cleaned and not cleaned.startswith("RJ"):
                cleaned = "RJ" + cleaned
            if cleaned:
                rj_queue.append(cleaned)

    elif BATCH_MODE == "file":
        txt_path = _HERE / "rj_list.txt"
        if not txt_path.exists():
            txt_path.write_text("", encoding="utf-8")
            print(f"已创建 rj_list.txt，请填入 RJ 号后重新运行")
            conn.close(); exit(0)
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                cleaned = line.strip().upper()
                if cleaned:
                    if not cleaned.startswith("RJ"):
                        cleaned = "RJ" + cleaned
                    rj_queue.append(cleaned)

    rj_queue = list(dict.fromkeys(rj_queue))
    total    = len(rj_queue)
    print(f"\n====== 批量抓取开始，共 {total} 个 ======")

    ok = fail = 0
    for i, rj in enumerate(rj_queue, 1):
        print(f"\n[{i}/{total}] ──────────────────────")
        if process_single_rj(conn, rj): ok += 1
        else: fail += 1

    conn.close()
    print(f"\n====== 结束：成功 {ok} / 失败 {fail} / 共 {total} ======\n")