"""
جامعہ ملیہ اسلامیہ فیصل آباد
Smart ERP System - Streamlit Cloud Ready
"""

import streamlit as st

# ══════════════════════════════════════════
# PAGE CONFIG - MUST BE FIRST
# ══════════════════════════════════════════
st.set_page_config(
    page_title="جامعہ ملیہ | ERP",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import hashlib
import os
import io
import zipfile

# ══════════════════════════════════════════
# DATABASE - PERSISTENT PATH
# ══════════════════════════════════════════
DB_PATH = "jamia_data.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn

def run(sql, params=()):
    """Execute write query, return lastrowid"""
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid

def fetch(sql, params=(), one=False):
    """Fetch rows as list of dicts"""
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        result = [dict(r) for r in rows]
        return result[0] if one and result else (None if one else result)

def scalar(sql, params=()):
    """Fetch single value"""
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        r = cur.fetchone()
        return r[0] if r else 0

def col_exists(table, col):
    rows = fetch(f"PRAGMA table_info({table})")
    return any(r['name'] == col for r in rows)

def add_col_safe(table, col, typ):
    if not col_exists(table, col):
        try:
            run(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
        except:
            pass

# ══════════════════════════════════════════
# DATABASE SETUP - hash_pw DEFINED FIRST
# ══════════════════════════════════════════
def hash_pw(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def init_db():
    run("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'teacher',
        dept TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        address TEXT DEFAULT '',
        id_card TEXT DEFAULT '',
        joining_date TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")

    run("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        father_name TEXT NOT NULL,
        mother_name TEXT DEFAULT '',
        roll_no TEXT DEFAULT '',
        dob TEXT DEFAULT '',
        admission_date TEXT DEFAULT '',
        exit_date TEXT DEFAULT '',
        exit_reason TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        address TEXT DEFAULT '',
        teacher TEXT DEFAULT '',
        dept TEXT DEFAULT '',
        class_name TEXT DEFAULT '',
        section TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")

    run("""CREATE TABLE IF NOT EXISTS hifz_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rec_date TEXT NOT NULL,
        student_id INTEGER NOT NULL,
        teacher TEXT NOT NULL,
        attendance TEXT NOT NULL DEFAULT 'حاضر',
        sabaq TEXT DEFAULT '',
        sabaq_lines INTEGER DEFAULT 0,
        sabaq_nagha INTEGER DEFAULT 0,
        sq_text TEXT DEFAULT '',
        sq_nagha INTEGER DEFAULT 0,
        sq_atkan INTEGER DEFAULT 0,
        sq_mistakes INTEGER DEFAULT 0,
        manzil_text TEXT DEFAULT '',
        manzil_nagha INTEGER DEFAULT 0,
        manzil_atkan INTEGER DEFAULT 0,
        manzil_mistakes INTEGER DEFAULT 0,
        cleanliness TEXT DEFAULT '',
        grade TEXT DEFAULT '',
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    run("""CREATE TABLE IF NOT EXISTS qaida_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rec_date TEXT NOT NULL,
        student_id INTEGER NOT NULL,
        teacher TEXT NOT NULL,
        attendance TEXT NOT NULL DEFAULT 'حاضر',
        lesson_no TEXT DEFAULT '',
        total_lines INTEGER DEFAULT 0,
        details TEXT DEFAULT '',
        cleanliness TEXT DEFAULT '',
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    run("""CREATE TABLE IF NOT EXISTS general_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rec_date TEXT NOT NULL,
        student_id INTEGER NOT NULL,
        teacher TEXT NOT NULL,
        dept TEXT DEFAULT '',
        attendance TEXT NOT NULL DEFAULT 'حاضر',
        subject TEXT DEFAULT '',
        lesson TEXT DEFAULT '',
        homework TEXT DEFAULT '',
        performance TEXT DEFAULT '',
        cleanliness TEXT DEFAULT '',
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    run("""CREATE TABLE IF NOT EXISTS teacher_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        att_date TEXT NOT NULL,
        arrival TEXT DEFAULT '',
        departure TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime')),
        UNIQUE(username, att_date)
    )""")

    run("""CREATE TABLE IF NOT EXISTS leave_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        leave_type TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        days INTEGER DEFAULT 1,
        reason TEXT DEFAULT '',
        status TEXT DEFAULT 'پینڈنگ',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")

    run("""CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        teacher TEXT DEFAULT '',
        dept TEXT DEFAULT '',
        exam_type TEXT DEFAULT '',
        from_para INTEGER DEFAULT 0,
        to_para INTEGER DEFAULT 0,
        book_name TEXT DEFAULT '',
        amount_read TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        total_days INTEGER DEFAULT 0,
        q1 INTEGER DEFAULT 0,
        q2 INTEGER DEFAULT 0,
        q3 INTEGER DEFAULT 0,
        q4 INTEGER DEFAULT 0,
        q5 INTEGER DEFAULT 0,
        total INTEGER DEFAULT 0,
        grade TEXT DEFAULT '',
        status TEXT DEFAULT 'پینڈنگ',
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    run("""CREATE TABLE IF NOT EXISTS passed_paras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        para_no INTEGER DEFAULT 0,
        book_name TEXT DEFAULT '',
        passed_date TEXT DEFAULT '',
        exam_type TEXT DEFAULT '',
        grade TEXT DEFAULT '',
        marks INTEGER DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    run("""CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher TEXT NOT NULL,
        day_name TEXT DEFAULT '',
        period TEXT DEFAULT '',
        subject TEXT DEFAULT '',
        room TEXT DEFAULT ''
    )""")

    run("""CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT DEFAULT '',
        target TEXT DEFAULT 'تمام',
        created_by TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")

    run("""CREATE TABLE IF NOT EXISTS staff_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff TEXT NOT NULL,
        note_date TEXT DEFAULT '',
        note_type TEXT DEFAULT '',
        description TEXT DEFAULT '',
        action_taken TEXT DEFAULT '',
        status TEXT DEFAULT 'زیر التواء',
        created_by TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")

    run("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT DEFAULT '',
        action TEXT DEFAULT '',
        details TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # Default admin account
    existing = fetch("SELECT id FROM users WHERE username='admin'", one=True)
    if not existing:
        run("INSERT INTO users (username,password,role,dept) VALUES (?,?,?,?)",
            ("admin", hash_pw("jamia123"), "admin", "انتظامیہ"))

init_db()

# ══════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════
def check_pw(plain, stored):
    """Support multiple hash formats for backward compat"""
    if not plain or not stored:
        return False
    if hash_pw(plain) == stored:
        return True
    if hashlib.sha256(plain.encode()).hexdigest() == stored:
        return True
    if plain == stored:
        return True
    return False

def audit(user, action, details=""):
    try:
        run("INSERT INTO audit_log (username,action,details) VALUES (?,?,?)",
            (user, action, str(details)[:500]))
    except:
        pass

def calc_grade_hifz(att, s_nagha, sq_nagha, m_nagha, sq_mis, m_mis):
    if att == "غیر حاضر": return "غیر حاضر"
    if att == "رخصت": return "رخصت"
    nagha = int(s_nagha) + int(sq_nagha) + int(m_nagha)
    if nagha == 1: return "ناقص"
    if nagha == 2: return "کمزور"
    if nagha >= 3: return "ناکام"
    total_mis = int(sq_mis) + int(m_mis)
    if total_mis <= 2: return "ممتاز"
    if total_mis <= 5: return "جید جداً"
    if total_mis <= 8: return "جید"
    if total_mis <= 12: return "مقبول"
    return "ناکام"

def exam_grade(total):
    if total >= 90: return "ممتاز"
    if total >= 80: return "جید جداً"
    if total >= 70: return "جید"
    if total >= 60: return "مقبول"
    return "ناکام"

def to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

def html_report(df, title, sub=""):
    tbl = df.to_html(index=False, border=0, classes="rtbl", escape=False)
    return f"""<!DOCTYPE html><html dir="rtl" lang="ur">
<head><meta charset="UTF-8"><title>{title}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap');
*{{font-family:'Noto Nastaliq Urdu',serif;}}
body{{background:#f5f9f7;margin:0;padding:20px;direction:rtl;}}
.wrap{{background:#fff;border-radius:12px;padding:24px;max-width:960px;margin:auto;
       box-shadow:0 4px 20px rgba(0,77,50,.1);}}
.hdr{{text-align:center;border-bottom:3px solid #0a6640;padding-bottom:16px;margin-bottom:20px;}}
.hdr h2{{color:#0a6640;margin:0 0 4px;}}
.hdr p{{color:#555;margin:0;font-size:.9rem;}}
table.rtbl{{width:100%;border-collapse:collapse;margin-top:16px;}}
table.rtbl th{{background:#0a6640;color:#fff;padding:8px 12px;font-weight:600;text-align:center;}}
table.rtbl td{{padding:7px 12px;border-bottom:1px solid #e8f0ec;text-align:center;}}
table.rtbl tr:nth-child(even) td{{background:#f0f8f4;}}
.sig{{display:flex;justify-content:space-between;margin-top:48px;padding-top:16px;border-top:1px solid #ddd;}}
.print-btn{{text-align:center;margin-top:24px;}}
.print-btn button{{padding:10px 32px;background:#0a6640;color:#fff;border:none;border-radius:8px;
                   cursor:pointer;font-size:1rem;font-family:inherit;}}
@media print{{.print-btn{{display:none;}}}}
</style></head>
<body><div class="wrap">
<div class="hdr">
  <h2>🕌 جامعہ ملیہ اسلامیہ فیصل آباد</h2>
  <p>{title}</p>
  {f'<p style="color:#0a6640;font-weight:600">{sub}</p>' if sub else ''}
</div>
{tbl}
<div class="sig">
  <span>دستخط استاذ: ___________________</span>
  <span>دستخط مہتمم: ___________________</span>
</div>
</div>
<div class="print-btn"><button onclick="window.print()">🖨️ پرنٹ کریں</button></div>
</body></html>"""

# ══════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════
SURAHS = [
    "الفاتحة","البقرة","آل عمران","النساء","المائدة","الأنعام","الأعراف",
    "الأنفال","التوبة","يونس","هود","يوسف","الرعد","إبراهيم","الحجر",
    "النحل","الإسراء","الكهف","مريم","طه","الأنبياء","الحج","المؤمنون",
    "النور","الفرقان","الشعراء","النمل","القصص","العنكبوت","الروم","لقمان",
    "السجدة","الأحزاب","سبأ","فاطر","يس","الصافات","ص","الزمر","غافر",
    "فصلت","الشورى","الزخرف","الدخان","الجاثية","الأحقاف","محمد","الفتح",
    "الحجرات","ق","الذاريات","الطور","النجم","القمر","الرحمن","الواقعة",
    "الحديد","المجادلة","الحشر","الممتحنة","الصف","الجمعة","المنافقون",
    "التغابن","الطلاق","التحریم","الملک","القلم","الحاقة","المعارج","نوح",
    "الجن","المزمل","المدثر","القیامة","الإنسان","المرسلات","النبأ","النازعات",
    "عبس","التکویر","الإنفطار","المطففین","الإنشقاق","البروج","الطارق",
    "الأعلى","الغاشیة","الفجر","البلد","الشمس","اللیل","الضحى","الشرح",
    "التین","العلق","القدر","البینة","الزلزلة","العادیات","القارعة","التکاثر",
    "العصر","الهمزة","الفیل","قریش","الماعون","الکوثر","الکافرون","النصر",
    "المسد","الإخلاص","الفلق","الناس"
]
PARAS = [f"پارہ {i}" for i in range(1, 31)]
DAYS_UR = ["پیر","منگل","بدھ","جمعرات","جمعہ","ہفتہ","اتوار"]
CLEANLINESS = ["بہترین", "بہتر", "ناقص"]
DEPTS = ["حفظ", "قاعدہ", "درسِ نظامی", "عصری تعلیم"]
MIQDAR = ["مکمل", "آدھا", "پون", "پاؤ"]
ATT_OPTS = ["حاضر", "غیر حاضر", "رخصت"]

# ══════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "page" not in st.session_state:
    st.session_state.page = "home"

# ══════════════════════════════════════════
# MASTER CSS - PakID Inspired
# ══════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;500;600;700&display=swap');

/* ── Variables ── */
:root {
  --g1: #0a5c3c;
  --g2: #0d7a52;
  --g3: #10966a;
  --g4: #e8f6f0;
  --g5: #c8eadb;
  --gold: #c9982a;
  --gold2: #f5c842;
  --white: #ffffff;
  --off: #f4f9f6;
  --dark: #0d1f18;
  --txt: #1a2e25;
  --gray: #6b7c73;
  --lgray: #e8f0ec;
  --danger: #c0392b;
  --warn: #d68910;
  --info: #1a6b9a;
  --rad: 12px;
  --rad-sm: 8px;
  --shad: 0 2px 16px rgba(10,92,60,.10);
  --shad2: 0 6px 32px rgba(10,92,60,.16);
}

/* ── Base ── */
* { font-family: 'Noto Nastaliq Urdu', Georgia, serif !important;
    direction: rtl; box-sizing: border-box; }
html, body, [class*="css"] { direction: rtl; text-align: right; }
.stApp { background: var(--off); }
#MainMenu, footer, header { visibility: hidden !important; }
.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}
section[data-testid="stSidebar"] { display: none !important; }

/* ── TOP HEADER BAR ── */
.top-header {
  background: linear-gradient(135deg, var(--g1) 0%, var(--g2) 100%);
  padding: 0;
  position: sticky; top: 0; z-index: 100;
  box-shadow: 0 2px 12px rgba(0,0,0,.20);
}
.top-header-inner {
  display: flex; align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  max-width: 1200px; margin: 0 auto;
}
.brand { display: flex; align-items: center; gap: 10px; }
.brand-icon { font-size: 2rem; }
.brand-name { color: #fff; font-size: 1.1rem; font-weight: 700; line-height: 1.2; }
.brand-sub { color: var(--gold2); font-size: .75rem; }
.user-chip {
  background: rgba(255,255,255,.15);
  border: 1px solid rgba(255,255,255,.25);
  border-radius: 30px;
  padding: 5px 14px;
  color: #fff;
  font-size: .82rem;
  display: flex; align-items: center; gap: 6px;
}

/* ── MAIN WRAP ── */
.main-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px 16px 40px;
}

/* ── SECTION HEADER ── */
.sec-hdr {
  display: flex; align-items: center;
  gap: 10px; margin: 20px 0 12px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--lgray);
}
.sec-hdr-icon {
  width: 38px; height: 38px;
  background: linear-gradient(135deg, var(--g1), var(--g3));
  border-radius: var(--rad-sm);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; color: #fff;
}
.sec-hdr-title { color: var(--g1); font-size: 1.15rem; font-weight: 700; }

/* ── NAV TABS (PakID style) ── */
.nav-bar {
  background: var(--white);
  border-bottom: 1px solid var(--lgray);
  padding: 0 16px;
  position: sticky; top: 64px; z-index: 90;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.nav-inner {
  max-width: 1100px; margin: 0 auto;
  display: flex; gap: 4px;
  overflow-x: auto; padding: 6px 0;
  scrollbar-width: none;
}
.nav-inner::-webkit-scrollbar { display: none; }

/* ── PAGE CARD ── */
.page-card {
  background: var(--white);
  border-radius: var(--rad);
  padding: 20px;
  box-shadow: var(--shad);
  margin-bottom: 14px;
  border: 1px solid rgba(10,92,60,.06);
  animation: fadeUp .3s ease;
}
@keyframes fadeUp {
  from { opacity:0; transform:translateY(12px); }
  to   { opacity:1; transform:translateY(0); }
}

/* ── METRIC CARDS ── */
.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 16px;
}
@media(max-width:700px){ .metrics{grid-template-columns:repeat(2,1fr);} }
.met-card {
  background: var(--white);
  border-radius: var(--rad);
  padding: 16px 12px;
  text-align: center;
  box-shadow: var(--shad);
  border: 1px solid rgba(10,92,60,.07);
  position: relative; overflow: hidden;
  transition: transform .2s, box-shadow .2s;
}
.met-card:hover { transform: translateY(-3px); box-shadow: var(--shad2); }
.met-card::after {
  content:''; position:absolute;
  bottom:0;left:0;right:0;height:3px;
  background: linear-gradient(90deg,var(--g1),var(--gold));
}
.met-ico { font-size: 1.7rem; display:block; margin-bottom:4px; }
.met-val { font-size: 2rem; font-weight:800; color:var(--g1); line-height:1; }
.met-lbl { font-size:.78rem; color:var(--gray); margin-top:3px; }

/* ── ICON GRID (PakID app grid) ── */
.icon-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 8px;
}
@media(max-width:600px){ .icon-grid{grid-template-columns:repeat(3,1fr);} }
@media(max-width:400px){ .icon-grid{grid-template-columns:repeat(2,1fr);} }

/* ── STUDENT ROW CARD ── */
.stu-card {
  background: var(--white);
  border: 1px solid var(--lgray);
  border-radius: var(--rad);
  padding: 14px 16px;
  margin-bottom: 10px;
  border-right: 4px solid var(--g2);
  box-shadow: var(--shad);
  transition: box-shadow .2s;
}
.stu-card:hover { box-shadow: var(--shad2); }
.stu-name { color:var(--g1); font-size:.95rem; font-weight:700; margin-bottom:6px; }

/* ── GRADE CHIPS ── */
.chip {
  display:inline-block; padding:2px 10px;
  border-radius:20px; font-size:.78rem; font-weight:700;
}
.chip-green  { background:#d1fae5; color:#065f46; }
.chip-blue   { background:#dbeafe; color:#1e40af; }
.chip-purple { background:#ede9fe; color:#4c1d95; }
.chip-yellow { background:#fef3c7; color:#92400e; }
.chip-red    { background:#fee2e2; color:#991b1b; }
.chip-gray   { background:#f3f4f6; color:#374151; }

/* ── STATUS CHIPS ── */
.st-pending { background:#fef3c7; color:#92400e; border-radius:20px;
              padding:2px 10px; font-size:.78rem; font-weight:700; }
.st-ok      { background:#d1fae5; color:#065f46; border-radius:20px;
              padding:2px 10px; font-size:.78rem; font-weight:700; }
.st-reject  { background:#fee2e2; color:#991b1b; border-radius:20px;
              padding:2px 10px; font-size:.78rem; font-weight:700; }

/* ── BUTTONS ── */
.stButton>button {
  background: linear-gradient(135deg, var(--g1), var(--g2)) !important;
  color: #fff !important; border: none !important;
  border-radius: var(--rad-sm) !important;
  padding: 8px 18px !important;
  font-weight: 600 !important;
  transition: all .2s !important;
  box-shadow: 0 2px 10px rgba(10,92,60,.22) !important;
  font-size: .88rem !important;
}
.stButton>button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 5px 18px rgba(10,92,60,.32) !important;
  background: linear-gradient(135deg, var(--dark), var(--g1)) !important;
}

/* ── FORM ELEMENTS ── */
.stTextInput>div>div>input,
.stTextArea textarea,
.stNumberInput input,
.stDateInput input,
.stTimeInput input,
.stSelectbox>div>div {
  border-radius: var(--rad-sm) !important;
  border: 1.5px solid #cdddd6 !important;
  direction: rtl !important;
  font-size: .88rem !important;
}
.stTextInput>div>div>input:focus,
.stTextArea textarea:focus {
  border-color: var(--g2) !important;
  box-shadow: 0 0 0 3px rgba(13,122,82,.12) !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--g4) !important;
  border-radius: var(--rad) !important;
  padding: 4px !important; gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: var(--rad-sm) !important;
  border: none !important;
  color: var(--gray) !important;
  font-weight: 600 !important;
  font-size: .85rem !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--g1), var(--g2)) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(10,92,60,.25) !important;
}

/* ── ALERTS ── */
.stSuccess>div { background:#f0fdf4!important; border-color:#86efac!important;
                 border-radius:var(--rad-sm)!important; color:#14532d!important; }
.stError>div   { background:#fff1f2!important; border-color:#fca5a5!important;
                 border-radius:var(--rad-sm)!important; }
.stWarning>div { background:#fffbeb!important; border-color:#fcd34d!important;
                 border-radius:var(--rad-sm)!important; }
.stInfo>div    { background:#f0f9ff!important; border-color:#93c5fd!important;
                 border-radius:var(--rad-sm)!important; }

/* ── DATAFRAME ── */
.stDataFrame { border-radius:var(--rad-sm)!important;
               overflow:hidden!important; box-shadow:var(--shad)!important; }
[data-testid="stDataFrameResizable"] th {
  background:var(--g1)!important; color:#fff!important; }

/* ── EXPANDER ── */
.streamlit-expanderHeader {
  background: linear-gradient(135deg,#f0f8f4,#e4f2eb) !important;
  border-radius: var(--rad-sm) !important;
  border: 1px solid rgba(10,92,60,.12) !important;
}

/* ── PROGRESS ── */
.prog-wrap { background:#e5e7eb; border-radius:10px; overflow:hidden; height:16px; }
.prog-bar  { height:100%;
             background:linear-gradient(90deg,var(--g1),var(--gold));
             border-radius:10px;
             display:flex; align-items:center; justify-content:center; }
.prog-txt  { color:#fff; font-size:.7rem; font-weight:700; }

/* ── NOTIF CARD ── */
.notif-item {
  background: linear-gradient(135deg,#f0f9ff,#e0f2fe);
  border-right: 4px solid var(--info);
  border-radius: var(--rad-sm);
  padding: 10px 14px; margin-bottom: 8px;
}
.notif-item h5 { color:var(--info)!important; margin:0 0 4px!important; font-size:.9rem!important; }
.notif-item p  { color:var(--txt); margin:0; font-size:.82rem; }
.notif-item small { color:var(--gray); font-size:.72rem; }

/* ── LEAVE CARD ── */
.leave-item {
  background: var(--white);
  border-right: 4px solid var(--warn);
  border-radius: var(--rad);
  padding: 12px 16px; margin-bottom: 8px;
  box-shadow: var(--shad);
}

/* ── TROPHY ── */
.trophy-card {
  background: linear-gradient(145deg,#fffdf0,#fdf3d0);
  border: 2px solid rgba(201,152,42,.22);
  border-radius: 18px; padding: 20px 14px;
  text-align: center; position: relative;
  overflow: hidden;
  box-shadow: 0 6px 28px rgba(201,152,42,.12);
  transition: transform .25s, box-shadow .25s;
}
.trophy-card::before {
  content:''; position:absolute; top:0;left:0;right:0; height:4px;
  background:linear-gradient(90deg,var(--gold),var(--gold2),var(--gold));
}
.trophy-card:hover { transform:translateY(-5px);
                     box-shadow:0 14px 40px rgba(201,152,42,.22); }
.trophy-medal { font-size:2.6rem; display:block; margin-bottom:6px; }
.trophy-name  { font-size:1rem; font-weight:700; color:var(--dark); margin:4px 0 2px; }
.trophy-sub   { font-size:.78rem; color:var(--gray); margin:2px 0; }
.trophy-score {
  display:inline-block;
  background:linear-gradient(135deg,var(--g1),var(--g2));
  color:#fff; border-radius:20px;
  padding:3px 14px; font-size:.82rem; font-weight:700;
  margin-top:8px;
  box-shadow:0 2px 8px rgba(10,92,60,.25);
}

/* ── LOGIN PAGE ── */
.login-bg {
  background: linear-gradient(145deg, var(--g1) 0%, var(--g2) 60%, var(--g3) 100%);
  min-height: 100vh; display:flex;
  align-items:center; justify-content:center;
  padding: 20px;
}
.login-card {
  background: #fff; border-radius: 20px;
  padding: 32px 28px; width:100%; max-width:400px;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
}
.login-logo { text-align:center; margin-bottom:20px; }
.login-logo .mosque { font-size:3.5rem; display:block; }
.login-logo h3 { color:var(--g1)!important; margin:6px 0 2px!important;
                 font-size:1.2rem!important; }
.login-logo p { color:var(--gold); font-size:.82rem; margin:0; }
.login-divider { border:none; border-top:1px solid var(--lgray); margin:16px 0; }

/* ── ICON BTN CARD (PakID grid item) ── */
.icon-btn-card {
  background: var(--white);
  border: 1.5px solid var(--lgray);
  border-radius: var(--rad);
  padding: 16px 10px;
  text-align: center; cursor: pointer;
  transition: all .2s cubic-bezier(.34,1.56,.64,1);
  box-shadow: var(--shad);
}
.icon-btn-card:hover {
  border-color: var(--g2);
  transform: translateY(-3px);
  box-shadow: var(--shad2);
}
.icon-btn-card.active {
  background: linear-gradient(135deg,var(--g1),var(--g2));
  border-color: var(--g1);
  transform: translateY(-2px);
}
.icon-btn-card .btn-ico { font-size:1.5rem; display:block; margin-bottom:5px; }
.icon-btn-card .btn-lbl {
  font-size:.75rem; color:var(--txt); font-weight:600; line-height:1.25;
}
.icon-btn-card.active .btn-lbl { color:#fff; }

/* ── BOTTOM NAV (mobile-like) ── */
.bottom-nav {
  position:fixed; bottom:0; left:0; right:0;
  background:var(--g1); z-index:200;
  display:flex; justify-content:space-around;
  padding:8px 0; box-shadow:0 -2px 12px rgba(0,0,0,.2);
}
.bnav-item { text-align:center; color:rgba(255,255,255,.7); cursor:pointer;
             font-size:.65rem; padding:2px 10px; }
.bnav-item .bnav-ico { font-size:1.1rem; display:block; }
.bnav-item.active { color:#fff; }

/* ── EXTRA PADDING FOR BOTTOM NAV ── */
.bottom-pad { height: 70px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
# PAGE SWITCH HELPER
# ══════════════════════════════════════════
def go(page):
    st.session_state.page = page
    st.rerun()

# ══════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("---")
        st.markdown("""
        <div style="text-align:center;padding:10px 0 4px">
          <span style="font-size:3.5rem">🕌</span>
          <h2 style="color:#0a5c3c;margin:6px 0 2px;font-size:1.3rem">جامعہ ملیہ اسلامیہ</h2>
          <p style="color:#c9982a;margin:0;font-size:.88rem">فیصل آباد — اسمارٹ تعلیمی پورٹل</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("lf", clear_on_submit=False):
            uname = st.text_input("👤 صارف نام", placeholder="username درج کریں")
            passw = st.text_input("🔑 پاسورڈ", type="password", placeholder="password")
            sub = st.form_submit_button("▶  لاگ ان کریں", use_container_width=True)

        if sub:
            if uname.strip() and passw:
                u = fetch("SELECT * FROM users WHERE username=? AND is_active=1",
                          (uname.strip(),), one=True)
                if u and check_pw(passw, u['password']):
                    st.session_state.logged_in = True
                    st.session_state.username = uname.strip()
                    st.session_state.role = u['role']
                    st.session_state.page = "home"
                    audit(uname.strip(), "Login")
                    st.rerun()
                else:
                    st.error("❌ غلط نام یا پاسورڈ")
            else:
                st.warning("براہ کرم نام اور پاسورڈ درج کریں")

        st.markdown("""
        <p style="text-align:center;color:#9ca3af;font-size:.72rem;margin-top:8px">
          🔒 ڈیفالٹ: <b>admin</b> / <b>jamia123</b>
        </p>
        """, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════
# LOGGED IN - TOP HEADER
# ══════════════════════════════════════════
IS_ADMIN = st.session_state.role == "admin"
pg = st.session_state.page

st.markdown(f"""
<div class="top-header">
  <div class="top-header-inner">
    <div class="brand">
      <span class="brand-icon">🕌</span>
      <div>
        <div class="brand-name">جامعہ ملیہ اسلامیہ</div>
        <div class="brand-sub">فیصل آباد</div>
      </div>
    </div>
    <div class="user-chip">
      {'🛡️' if IS_ADMIN else '👩‍🏫'} {st.session_state.username}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# NAVIGATION - PakID Style Icon Grid
# ══════════════════════════════════════════
st.markdown("<div class='main-wrap'>", unsafe_allow_html=True)

if IS_ADMIN:
    NAV = [
        ("home",        "📊", "ڈیش بورڈ"),
        ("daily",       "📋", "یومیہ رپورٹ"),
        ("exams",       "🎓", "امتحانات"),
        ("result",      "📜", "رزلٹ کارڈ"),
        ("para",        "📖", "پارہ رپورٹ"),
        ("t_att_admin", "🕒", "حاضری"),
        ("leaves",      "🏛️", "رخصت"),
        ("users",       "👥", "یوزرز"),
        ("timetable",   "📚", "ٹائم ٹیبل"),
        ("monitor",     "📋", "نگرانی"),
        ("notifs",      "📢", "اعلانات"),
        ("analytics",   "📈", "تجزیہ"),
        ("best",        "🏆", "بہترین"),
        ("password",    "🔑", "پاسورڈ"),
        ("backup",      "⚙️", "بیک اپ"),
    ]
else:
    NAV = [
        ("home",      "🏠", "مرکزی صفحہ"),
        ("entry",     "📝", "سبق اندراج"),
        ("t_exam",    "🎓", "امتحان"),
        ("t_leave",   "📩", "رخصت"),
        ("t_att",     "🕒", "حاضری"),
        ("t_tt",      "📚", "ٹائم ٹیبل"),
        ("notifs",    "📢", "اعلانات"),
        ("password",  "🔑", "پاسورڈ"),
    ]

cols_per_row = 5 if IS_ADMIN else 4
nav_rows = [NAV[i:i+cols_per_row] for i in range(0, len(NAV), cols_per_row)]

for row in nav_rows:
    cols = st.columns(len(row))
    for col, (pid, ico, lbl) in zip(cols, row):
        with col:
            if st.button(f"{ico}\n{lbl}", key=f"nav_{pid}", use_container_width=True):
                go(pid)

logout_c = st.columns([6, 1])[1]
with logout_c:
    if st.button("🚪 آؤٹ", use_container_width=True):
        audit(st.session_state.username, "Logout")
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.page = "home"
        st.rerun()

st.markdown("---")

# ══════════════════════════════════════════
# HELPER: Section Header
# ══════════════════════════════════════════
def sec(icon, title, sub=""):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0a5c3c,#0d7a52);
         border-radius:12px;padding:14px 18px;margin-bottom:16px;
         display:flex;align-items:center;gap:12px">
      <span style="font-size:1.6rem">{icon}</span>
      <div>
        <div style="color:#fff;font-size:1.05rem;font-weight:700">{title}</div>
        {f'<div style="color:rgba(255,255,255,.75);font-size:.78rem">{sub}</div>' if sub else ''}
      </div>
    </div>""", unsafe_allow_html=True)

def card(content=""):
    st.markdown(f"<div class='page-card'>{content}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════
# ████  ADMIN HOME / DASHBOARD  ████
# ══════════════════════════════════════════
if pg == "home" and IS_ADMIN:
    sec("📊", "ایڈمن ڈیش بورڈ", "جامعہ ملیہ کا مکمل جائزہ")

    ts  = scalar("SELECT COUNT(*) FROM students WHERE is_active=1")
    tt  = scalar("SELECT COUNT(*) FROM users WHERE role='teacher' AND is_active=1")
    ta  = scalar("SELECT COUNT(*) FROM teacher_attendance WHERE att_date=?", (str(date.today()),))
    pe  = scalar("SELECT COUNT(*) FROM exams WHERE status='پینڈنگ'")
    pl  = scalar("SELECT COUNT(*) FROM leave_requests WHERE status='پینڈنگ'")
    tr  = scalar("SELECT COUNT(*) FROM hifz_records") + scalar("SELECT COUNT(*) FROM qaida_records")

    st.markdown(f"""
    <div class="metrics">
      <div class="met-card"><span class="met-ico">👨‍🎓</span>
        <div class="met-val">{ts}</div><div class="met-lbl">کل طلباء</div></div>
      <div class="met-card"><span class="met-ico">👩‍🏫</span>
        <div class="met-val">{tt}</div><div class="met-lbl">کل اساتذہ</div></div>
      <div class="met-card"><span class="met-ico">✅</span>
        <div class="met-val">{ta}</div><div class="met-lbl">آج کی حاضری</div></div>
      <div class="met-card"><span class="met-ico">📋</span>
        <div class="met-val">{tr}</div><div class="met-lbl">کل ریکارڈز</div></div>
    </div>
    """, unsafe_allow_html=True)

    if pl > 0:
        st.warning(f"⏳ {pl} رخصت درخواستیں منتظر منظوری ہیں")
    if pe > 0:
        st.info(f"🎓 {pe} امتحان پینڈنگ ہیں")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='page-card'>", unsafe_allow_html=True)
        st.markdown("**📅 آج کی اساتذہ حاضری**")
        rows = fetch("SELECT username as استاد, arrival as آمد, departure as رخصت FROM teacher_attendance WHERE att_date=?", (str(date.today()),))
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("ابھی کوئی حاضری نہیں")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='page-card'>", unsafe_allow_html=True)
        st.markdown("**📊 شعبہ وار طلباء**")
        dept_d = fetch("SELECT dept, COUNT(*) as cnt FROM students WHERE is_active=1 GROUP BY dept")
        if dept_d:
            for d in dept_d:
                pct = int((d['cnt'] / (ts or 1)) * 100)
                st.markdown(f"""
                <div style="margin-bottom:8px">
                  <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:.82rem;font-weight:600">{d['dept']}</span>
                    <span style="font-size:.82rem;color:#0a5c3c">{d['cnt']}</span>
                  </div>
                  <div class="prog-wrap"><div class="prog-bar" style="width:{pct}%">
                    <span class="prog-txt">{pct}%</span></div></div>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════
# ████  DAILY REPORT  ████
# ══════════════════════════════════════════
elif pg == "daily" and IS_ADMIN:
    sec("📋", "یومیہ تعلیمی رپورٹ", "تمام شعبوں کا روزانہ ریکارڈ")

    c1, c2, c3, c4 = st.columns(4)
    d1 = c1.date_input("از", date.today().replace(day=1), key="d1")
    d2 = c2.date_input("تا", date.today(), key="d2")
    dept_s = c3.selectbox("شعبہ", ["تمام"] + DEPTS, key="dept_daily")
    t_list = ["تمام"] + [r['username'] for r in fetch("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
    t_s = c4.selectbox("استاد", t_list, key="t_daily")

    combined = []
    t_f = "" if t_s == "تمام" else f" AND h.teacher='{t_s}'"

    if dept_s in ["تمام", "حفظ"]:
        rows = fetch(f"""SELECT h.rec_date as تاریخ, s.name as نام, s.father_name as والد,
                        s.roll_no as رول, h.teacher as استاد, 'حفظ' as شعبہ,
                        h.sabaq as سبق, h.sabaq_lines as ستر,
                        h.sq_text as سبقی, h.sq_mistakes as 'سبقی غلطی',
                        h.manzil_text as منزل, h.manzil_mistakes as 'منزل غلطی',
                        h.attendance as حاضری, h.cleanliness as صفائی, h.grade as درجہ
                        FROM hifz_records h JOIN students s ON h.student_id=s.id
                        WHERE h.rec_date BETWEEN ? AND ?{t_f}
                        ORDER BY h.rec_date DESC""", (str(d1), str(d2)))
        combined.extend(rows)

    if dept_s in ["تمام", "قاعدہ"]:
        t_f2 = "" if t_s == "تمام" else f" AND q.teacher='{t_s}'"
        rows = fetch(f"""SELECT q.rec_date as تاریخ, s.name as نام, s.father_name as والد,
                        s.roll_no as رول, q.teacher as استاد, 'قاعدہ' as شعبہ,
                        q.lesson_no as سبق, q.total_lines as لائنیں,
                        '' as سبقی, 0 as 'سبقی غلطی', '' as منزل, 0 as 'منزل غلطی',
                        q.attendance as حاضری, q.cleanliness as صفائی, '' as درجہ
                        FROM qaida_records q JOIN students s ON q.student_id=s.id
                        WHERE q.rec_date BETWEEN ? AND ?{t_f2}
                        ORDER BY q.rec_date DESC""", (str(d1), str(d2)))
        combined.extend(rows)

    if dept_s in ["تمام", "درسِ نظامی", "عصری تعلیم"]:
        d_f = "" if dept_s == "تمام" else f" AND g.dept='{dept_s}'"
        t_f3 = "" if t_s == "تمام" else f" AND g.teacher='{t_s}'"
        rows = fetch(f"""SELECT g.rec_date as تاریخ, s.name as نام, s.father_name as والد,
                        s.roll_no as رول, g.teacher as استاد, g.dept as شعبہ,
                        g.subject as سبق, 0 as ستر,
                        '' as سبقی, 0 as 'سبقی غلطی', '' as منزل, 0 as 'منزل غلطی',
                        g.attendance as حاضری, g.cleanliness as صفائی, g.performance as درجہ
                        FROM general_records g JOIN students s ON g.student_id=s.id
                        WHERE g.rec_date BETWEEN ? AND ?{d_f}{t_f3}
                        ORDER BY g.rec_date DESC""", (str(d1), str(d2)))
        combined.extend(rows)

    if combined:
        df = pd.DataFrame(combined)
        st.success(f"✅ کل **{len(df)}** ریکارڈ ملے")
        st.dataframe(df, use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        c1.download_button("📥 CSV", to_csv(df), "daily.csv", "text/csv")
        c2.download_button("📥 HTML رپورٹ", html_report(df, "یومیہ تعلیمی رپورٹ", f"{d1} تا {d2}"),
                           "daily.html", "text/html")
    else:
        st.info("اس مدت میں کوئی ریکارڈ نہیں")

# ══════════════════════════════════════════
# ████  EXAMS  ████
# ══════════════════════════════════════════
elif pg == "exams" and IS_ADMIN:
    sec("🎓", "امتحانی نظام", "امتحانات کا انتظام اور نتائج")
    tab1, tab2 = st.tabs(["⏳ پینڈنگ امتحانات", "✅ مکمل شدہ"])

    with tab1:
        pend = fetch("""SELECT e.*, s.name, s.father_name, s.roll_no
                       FROM exams e JOIN students s ON e.student_id=s.id
                       WHERE e.status='پینڈنگ' ORDER BY e.created_at DESC""")
        if not pend:
            st.success("✅ کوئی پینڈنگ امتحان نہیں")
        for ex in pend:
            with st.expander(f"👤 {ex['name']} | {ex['dept']} | {ex['exam_type']}"):
                c1, c2, c3 = st.columns(3)
                c1.info(f"📅 شروع: {ex['start_date']}")
                c2.info(f"📅 ختم: {ex.get('end_date','—')}")
                c3.info(f"🗓️ دن: {ex.get('total_days','—')}")
                if ex.get('from_para'):
                    st.info(f"📖 پارہ {ex['from_para']} تا {ex['to_para']}")
                if ex.get('book_name'):
                    st.info(f"📚 {ex['book_name']} | {ex.get('amount_read','')}")

                qcols = st.columns(5)
                qs = []
                for i in range(5):
                    v = qcols[i].number_input(f"س{i+1}", 0, 20, 0, key=f"q{i}_{ex['id']}")
                    qs.append(v)
                total = sum(qs)
                g = exam_grade(total)
                gcls = {"ممتاز":"chip-green","جید جداً":"chip-purple",
                        "جید":"chip-blue","مقبول":"chip-yellow","ناکام":"chip-red"}.get(g,"chip-gray")
                st.markdown(f"**کل:** {total}/100 &nbsp; <span class='chip {gcls}'>{g}</span>",
                            unsafe_allow_html=True)
                if st.button("✅ نتیجہ محفوظ کریں", key=f"save_ex_{ex['id']}"):
                    run("""UPDATE exams SET q1=?,q2=?,q3=?,q4=?,q5=?,total=?,grade=?,
                           status='مکمل',end_date=? WHERE id=?""",
                        (*qs, total, g, str(date.today()), ex['id']))
                    if g != "ناکام":
                        sid = ex['student_id']
                        if ex.get('from_para') and ex['from_para'] > 0:
                            for p in range(int(ex['from_para']), int(ex['to_para']) + 1):
                                if not fetch("SELECT id FROM passed_paras WHERE student_id=? AND para_no=?",
                                             (sid, p), one=True):
                                    run("""INSERT INTO passed_paras
                                          (student_id,para_no,passed_date,exam_type,grade,marks)
                                          VALUES (?,?,?,?,?,?)""",
                                        (sid, p, str(date.today()), ex['exam_type'], g, total))
                        if ex.get('book_name'):
                            if not fetch("SELECT id FROM passed_paras WHERE student_id=? AND book_name=?",
                                         (sid, ex['book_name']), one=True):
                                run("""INSERT INTO passed_paras
                                      (student_id,book_name,passed_date,exam_type,grade,marks)
                                      VALUES (?,?,?,?,?,?)""",
                                    (sid, ex['book_name'], str(date.today()), ex['exam_type'], g, total))
                    audit(st.session_state.username, "Exam Cleared", f"id={ex['id']},g={g}")
                    st.success("✅ محفوظ!")
                    st.rerun()

    with tab2:
        done = fetch("""SELECT s.name as نام, s.father_name as والد, s.roll_no as رول,
                       e.dept as شعبہ, e.exam_type as امتحان,
                       e.total as نمبر, e.grade as گریڈ, e.end_date as تاریخ
                       FROM exams e JOIN students s ON e.student_id=s.id
                       WHERE e.status='مکمل' ORDER BY e.end_date DESC""")
        if done:
            df = pd.DataFrame(done)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("📥 CSV", to_csv(df), "exams_done.csv")
        else:
            st.info("کوئی مکمل امتحان نہیں")

# ══════════════════════════════════════════
# ████  RESULT CARD  ████
# ══════════════════════════════════════════
elif pg == "result" and IS_ADMIN:
    sec("📜", "ماہانہ رزلٹ کارڈ", "طالب علم کی کارکردگی")
    studs = fetch("SELECT id,name,father_name,roll_no,dept FROM students WHERE is_active=1 ORDER BY name")
    if not studs:
        st.warning("کوئی طالب علم نہیں")
    else:
        names = [f"{s['name']} ولد {s['father_name']} ({s['dept']})" for s in studs]
        c1, c2, c3 = st.columns([3, 1, 1])
        idx = c1.selectbox("طالب علم", range(len(names)), format_func=lambda i: names[i])
        s = studs[idx]
        d1 = c2.date_input("از", date.today().replace(day=1))
        d2 = c3.date_input("تا", date.today())

        rows = []
        if s['dept'] == "حفظ":
            rows = fetch("""SELECT rec_date as تاریخ, attendance as حاضری, sabaq as سبق,
                           sabaq_lines as ستر, sq_text as سبقی, sq_mistakes as 'سبقی غلطی',
                           manzil_text as منزل, manzil_mistakes as 'منزل غلطی',
                           cleanliness as صفائی, grade as درجہ
                           FROM hifz_records WHERE student_id=? AND rec_date BETWEEN ? AND ?
                           ORDER BY rec_date""", (s['id'], str(d1), str(d2)))
        elif s['dept'] == "قاعدہ":
            rows = fetch("""SELECT rec_date as تاریخ, attendance as حاضری, lesson_no as سبق,
                           total_lines as لائنیں, cleanliness as صفائی, note as نوٹ
                           FROM qaida_records WHERE student_id=? AND rec_date BETWEEN ? AND ?
                           ORDER BY rec_date""", (s['id'], str(d1), str(d2)))
        else:
            rows = fetch("""SELECT rec_date as تاریخ, attendance as حاضری, subject as مضمون,
                           lesson as سبق, performance as کارکردگی, cleanliness as صفائی
                           FROM general_records WHERE student_id=? AND dept=?
                           AND rec_date BETWEEN ? AND ? ORDER BY rec_date""",
                         (s['id'], s['dept'], str(d1), str(d2)))

        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            sub_txt = f"{s['name']} ولد {s['father_name']} | {d1} تا {d2}"
            c1, c2 = st.columns(2)
            c1.download_button("📥 HTML", html_report(df, "ماہانہ رزلٹ کارڈ", sub_txt),
                               f"result_{s['name']}.html", "text/html")
            c2.download_button("📥 CSV", to_csv(df), f"result_{s['name']}.csv")
        else:
            st.info("اس مدت میں کوئی ریکارڈ نہیں")

# ══════════════════════════════════════════
# ████  PARA REPORT  ████
# ══════════════════════════════════════════
elif pg == "para" and IS_ADMIN:
    sec("📖", "پارہ تعلیمی رپورٹ", "حفظ کی پیشرفت")
    studs = fetch("SELECT id,name,father_name FROM students WHERE dept='حفظ' AND is_active=1 ORDER BY name")
    if not studs:
        st.warning("کوئی حفظ کا طالب علم نہیں")
    else:
        names = [f"{s['name']} ولد {s['father_name']}" for s in studs]
        idx = st.selectbox("طالب علم", range(len(names)), format_func=lambda i: names[i])
        s = studs[idx]
        passed = fetch("""SELECT para_no as 'پارہ نمبر', passed_date as 'تاریخ پاس',
                         exam_type as امتحان, grade as گریڈ, marks as نمبر
                         FROM passed_paras WHERE student_id=? AND para_no > 0
                         ORDER BY para_no""", (s['id'],))
        cnt = len(passed)
        pct = int((cnt / 30) * 100)
        st.markdown(f"""
        <div class="page-card">
          <div style="font-size:.9rem;font-weight:700;color:#0a5c3c;margin-bottom:6px">
            قرآن مجید کی پیشرفت: {cnt}/30 پارے
          </div>
          <div class="prog-wrap">
            <div class="prog-bar" style="width:{pct}%">
              <span class="prog-txt">{pct}%</span>
            </div>
          </div>
          <div style="font-size:.75rem;color:#6b7c73;margin-top:4px">{30-cnt} پارے باقی</div>
        </div>""", unsafe_allow_html=True)
        if passed:
            df = pd.DataFrame(passed)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("📥 رپورٹ", html_report(df, "پارہ تعلیمی رپورٹ",
                               f"{s['name']} ولد {s['father_name']}"),
                               f"para_{s['name']}.html", "text/html")
        else:
            st.info("کوئی پاس شدہ پارہ نہیں")

# ══════════════════════════════════════════
# ████  TEACHER ATTENDANCE - ADMIN  ████
# ══════════════════════════════════════════
elif pg == "t_att_admin" and IS_ADMIN:
    sec("🕒", "اساتذہ حاضری", "مکمل ریکارڈ اور ترمیم")
    tab1, tab2 = st.tabs(["📋 ریکارڈ دیکھیں", "✏️ درج/ترمیم کریں"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        fd1 = c1.date_input("از", date.today().replace(day=1))
        fd2 = c2.date_input("تا", date.today())
        tlist = ["تمام"] + [r['username'] for r in fetch("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
        ft = c3.selectbox("استاد", tlist)
        tf = "" if ft == "تمام" else f" AND username='{ft}'"
        rows = fetch(f"""SELECT username as استاد, att_date as تاریخ,
                        arrival as آمد, departure as رخصت
                        FROM teacher_attendance
                        WHERE att_date BETWEEN ? AND ?{tf}
                        ORDER BY att_date DESC""", (str(fd1), str(fd2)))
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("📥 CSV", to_csv(df), "att.csv")
        else:
            st.info("کوئی ریکارڈ نہیں")

    with tab2:
        with st.form("admin_att"):
            c1, c2, c3, c4 = st.columns(4)
            tl2 = [r['username'] for r in fetch("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
            at = c1.selectbox("استاد", tl2)
            ad = c2.date_input("تاریخ", date.today())
            arr = c3.text_input("آمد", placeholder="09:00 AM")
            dep = c4.text_input("رخصت", placeholder="03:00 PM")
            if st.form_submit_button("💾 محفوظ کریں"):
                existing = fetch("SELECT id FROM teacher_attendance WHERE username=? AND att_date=?",
                                 (at, str(ad)), one=True)
                if existing:
                    run("UPDATE teacher_attendance SET arrival=?,departure=? WHERE username=? AND att_date=?",
                        (arr, dep, at, str(ad)))
                else:
                    run("INSERT INTO teacher_attendance (username,att_date,arrival,departure) VALUES (?,?,?,?)",
                        (at, str(ad), arr, dep))
                st.success("✅ محفوظ!")
                st.rerun()

# ══════════════════════════════════════════
# ████  LEAVES - ADMIN  ████
# ══════════════════════════════════════════
elif pg == "leaves" and IS_ADMIN:
    sec("🏛️", "رخصت کی منظوری", "درخواستوں کا انتظام")
    tab1, tab2 = st.tabs(["⏳ پینڈنگ", "📜 تمام"])

    with tab1:
        pend = fetch("SELECT * FROM leave_requests WHERE status='پینڈنگ' ORDER BY created_at DESC")
        if not pend:
            st.success("✅ کوئی پینڈنگ درخواست نہیں")
        for lv in pend:
            st.markdown(f"""
            <div class="leave-item">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span><strong>👤 {lv['username']}</strong> &nbsp;
                  <span class="st-pending">{lv['leave_type']}</span></span>
                <span style="font-size:.8rem;color:#6b7c73">
                  📅 {lv['start_date']} | {lv['days']} دن</span>
              </div>
              <p style="color:#4b5563;font-size:.82rem;margin:5px 0 0">
                وجہ: {lv['reason'][:100]}</p>
            </div>""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("✅ منظور", key=f"apr_{lv['id']}", use_container_width=True):
                run("UPDATE leave_requests SET status='منظور' WHERE id=?", (lv['id'],))
                audit(st.session_state.username, "Leave Approved", lv['id'])
                st.rerun()
            if c2.button("❌ مسترد", key=f"rej_{lv['id']}", use_container_width=True):
                run("UPDATE leave_requests SET status='مسترد' WHERE id=?", (lv['id'],))
                st.rerun()

    with tab2:
        all_lv = fetch("""SELECT username as استاد, leave_type as نوعیت, start_date as تاریخ,
                         days as دن, status as حالت FROM leave_requests ORDER BY created_at DESC""")
        if all_lv:
            df = pd.DataFrame(all_lv)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("📥 CSV", to_csv(df), "leaves.csv")

# ══════════════════════════════════════════
# ████  USER MANAGEMENT  ████
# ══════════════════════════════════════════
elif pg == "users" and IS_ADMIN:
    sec("👥", "یوزر مینجمنٹ", "اساتذہ اور طلباء کا انتظام")
    tab1, tab2 = st.tabs(["👩‍🏫 اساتذہ", "👨‍🎓 طلبہ"])

    with tab1:
        rows = fetch("""SELECT id, username as نام, dept as شعبہ, phone as فون,
                       id_card as 'شناختی کارڈ', joining_date as 'تاریخ شمولیت',
                       is_active as فعال
                       FROM users WHERE role='teacher' ORDER BY username""")
        if rows:
            df = pd.DataFrame(rows)
            edited = st.data_editor(df, use_container_width=True, num_rows="dynamic",
                                    key="t_edit", hide_index=True)
            if st.button("💾 اساتذہ محفوظ کریں"):
                for _, row in edited.iterrows():
                    if pd.notna(row.get('id')):
                        run("""UPDATE users SET dept=?,phone=?,id_card=?,
                               joining_date=?,is_active=? WHERE id=?""",
                            (str(row.get('شعبہ','')), str(row.get('فون','')),
                             str(row.get('شناختی کارڈ','')),
                             str(row.get('تاریخ شمولیت','')),
                             int(row.get('فعال', 1)), int(row['id'])))
                st.success("✅ محفوظ!")
                st.rerun()

        st.markdown("---")
        st.markdown("**➕ نیا استاد**")
        with st.form("add_t"):
            c1, c2 = st.columns(2)
            tn = c1.text_input("نام*")
            tp = c2.text_input("پاسورڈ*", type="password")
            td = c1.selectbox("شعبہ", DEPTS)
            tph = c2.text_input("فون")
            tic = c1.text_input("شناختی کارڈ")
            tjd = c2.date_input("شمولیت", date.today())
            if st.form_submit_button("✅ رجسٹر کریں"):
                if tn.strip() and tp:
                    try:
                        run("""INSERT INTO users (username,password,role,dept,phone,id_card,joining_date)
                               VALUES (?,?,?,?,?,?,?)""",
                            (tn.strip(), hash_pw(tp), 'teacher', td, tph, tic, str(tjd)))
                        audit(st.session_state.username, "Teacher Added", tn)
                        st.success(f"✅ {tn} رجسٹر!")
                        st.rerun()
                    except:
                        st.error("یہ نام پہلے سے موجود ہے")
                else:
                    st.error("نام اور پاسورڈ ضروری ہیں")

    with tab2:
        rows = fetch("""SELECT id, name as نام, father_name as والد, roll_no as رول,
                       dept as شعبہ, teacher as استاد, phone as فون, is_active as فعال
                       FROM students ORDER BY name""")
        if rows:
            df = pd.DataFrame(rows)
            edited = st.data_editor(df, use_container_width=True, num_rows="dynamic",
                                    key="s_edit", hide_index=True)
            if st.button("💾 طلبہ محفوظ کریں"):
                for _, row in edited.iterrows():
                    if pd.notna(row.get('id')):
                        run("""UPDATE students SET name=?,father_name=?,roll_no=?,
                               dept=?,teacher=?,phone=?,is_active=? WHERE id=?""",
                            (str(row.get('نام','')), str(row.get('والد','')),
                             str(row.get('رول','')), str(row.get('شعبہ','')),
                             str(row.get('استاد','')), str(row.get('فون','')),
                             int(row.get('فعال', 1)), int(row['id'])))
                st.success("✅ محفوظ!")
                st.rerun()

        st.markdown("---")
        st.markdown("**➕ نیا طالب علم**")
        with st.form("add_s"):
            c1, c2 = st.columns(2)
            sn = c1.text_input("نام*")
            sf = c2.text_input("والد کا نام*")
            sm = c1.text_input("والدہ کا نام")
            sr = c2.text_input("رول نمبر")
            sd = c1.date_input("تاریخ پیدائش", date.today() - timedelta(days=3650))
            sa = c2.date_input("تاریخ داخلہ", date.today())
            sdept = c1.selectbox("شعبہ*", DEPTS)
            tl = [r['username'] for r in fetch("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
            st_ = c2.selectbox("استاد*", tl) if tl else c2.text_input("استاد*")
            scl = c1.text_input("کلاس")
            ssec = c2.text_input("سیکشن")
            sph = c1.text_input("فون")
            sadr = st.text_area("پتہ")
            if st.form_submit_button("✅ داخلہ کریں"):
                if sn.strip() and sf.strip():
                    run("""INSERT INTO students
                          (name,father_name,mother_name,roll_no,dob,admission_date,
                           phone,address,teacher,dept,class_name,section)
                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (sn.strip(), sf.strip(), sm, sr, str(sd), str(sa),
                         sph, sadr, st_, sdept, scl, ssec))
                    audit(st.session_state.username, "Student Added", sn)
                    st.success(f"✅ {sn} داخل!")
                    st.rerun()
                else:
                    st.error("نام اور والد کا نام ضروری")

# ══════════════════════════════════════════
# ████  TIMETABLE  ████
# ══════════════════════════════════════════
elif pg == "timetable" and IS_ADMIN:
    sec("📚", "ٹائم ٹیبل", "اساتذہ کا ٹائم ٹیبل")
    tl = [r['username'] for r in fetch("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
    if not tl:
        st.warning("پہلے اساتذہ رجسٹر کریں")
    else:
        st_ = st.selectbox("استاد", tl)
        tt = fetch("""SELECT id, day_name as دن, period as وقت,
                     subject as مضمون, room as کمرہ
                     FROM timetable WHERE teacher=? ORDER BY day_name, period""", (st_,))
        if tt:
            df = pd.DataFrame(tt)
            edited = st.data_editor(df, use_container_width=True, num_rows="dynamic",
                                    key="tt_e", hide_index=True)
            c1, c2 = st.columns(2)
            if c1.button("💾 ٹائم ٹیبل محفوظ کریں"):
                for _, row in edited.iterrows():
                    if pd.notna(row.get('id')):
                        run("UPDATE timetable SET day_name=?,period=?,subject=?,room=? WHERE id=?",
                            (str(row.get('دن','')), str(row.get('وقت','')),
                             str(row.get('مضمون','')), str(row.get('کمرہ','')), int(row['id'])))
                    else:
                        run("INSERT INTO timetable (teacher,day_name,period,subject,room) VALUES (?,?,?,?,?)",
                            (st_, str(row.get('دن','')), str(row.get('وقت','')),
                             str(row.get('مضمون','')), str(row.get('کمرہ',''))))
                st.success("✅ محفوظ!")
                st.rerun()
            if c2.button("🗑️ مکمل حذف کریں"):
                run("DELETE FROM timetable WHERE teacher=?", (st_,))
                st.success("حذف!")
                st.rerun()

        with st.expander("➕ نیا پیریڈ"):
            with st.form("add_per"):
                c1, c2, c3, c4 = st.columns(4)
                dn = c1.selectbox("دن", DAYS_UR)
                per = c2.text_input("وقت", placeholder="08:00-09:00")
                sub = c3.text_input("مضمون")
                rm = c4.text_input("کمرہ")
                if st.form_submit_button("➕ شامل"):
                    run("INSERT INTO timetable (teacher,day_name,period,subject,room) VALUES (?,?,?,?,?)",
                        (st_, dn, per, sub, rm))
                    st.success("✅ شامل!")
                    st.rerun()

# ══════════════════════════════════════════
# ████  STAFF MONITORING  ████
# ══════════════════════════════════════════
elif pg == "monitor" and IS_ADMIN:
    sec("📋", "عملہ نگرانی", "کارکردگی اور شکایات")
    tab1, tab2 = st.tabs(["➕ نیا اندراج", "📜 ریکارڈ"])

    with tab1:
        tl = [r['username'] for r in fetch("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
        with st.form("mon_f"):
            c1, c2 = st.columns(2)
            stf = c1.selectbox("عملہ", tl) if tl else c1.text_input("عملہ")
            nd = c2.date_input("تاریخ", date.today())
            nt = c1.selectbox("نوعیت", ["یادداشت","شکایت","تنبیہ","تعریف","جائزہ"])
            ns = c2.selectbox("حالت", ["زیر التواء","حل شدہ","زیر غور"])
            desc = st.text_area("تفصیل*", max_chars=1000)
            act = st.text_area("کارروائی", max_chars=500)
            if st.form_submit_button("✅ محفوظ"):
                if desc.strip():
                    run("""INSERT INTO staff_notes
                          (staff,note_date,note_type,description,action_taken,status,created_by)
                          VALUES (?,?,?,?,?,?,?)""",
                        (stf, str(nd), nt, desc, act, ns, st.session_state.username))
                    audit(st.session_state.username, "Staff Note", f"{stf}-{nt}")
                    st.success("✅ محفوظ!")
                    st.rerun()
                else:
                    st.error("تفصیل ضروری")

    with tab2:
        notes = fetch("""SELECT id, staff as عملہ, note_date as تاریخ,
                        note_type as نوعیت, description as تفصیل,
                        action_taken as کارروائی, status as حالت
                        FROM staff_notes ORDER BY note_date DESC""")
        if notes:
            df = pd.DataFrame(notes)
            edited = st.data_editor(df, use_container_width=True, num_rows="dynamic",
                                    key="notes_e", hide_index=True)
            c1, c2 = st.columns(2)
            if c1.button("💾 تبدیلیاں محفوظ"):
                for _, row in edited.iterrows():
                    if pd.notna(row.get('id')):
                        run("UPDATE staff_notes SET status=?,action_taken=? WHERE id=?",
                            (str(row.get('حالت','')), str(row.get('کارروائی','')), int(row['id'])))
                st.success("✅ محفوظ!")
                st.rerun()
            c2.download_button("📥 CSV", to_csv(df), "notes.csv")
        else:
            st.info("کوئی ریکارڈ نہیں")

# ══════════════════════════════════════════
# ████  NOTIFICATIONS  ████
# ══════════════════════════════════════════
elif pg == "notifs":
    sec("📢", "اعلانات", "نوٹیفیکیشن سینٹر")
    if IS_ADMIN:
        with st.expander("➕ نیا اعلان"):
            with st.form("notif_f"):
                t_ = st.text_input("عنوان*")
                m_ = st.text_area("پیغام*")
                tg = st.selectbox("وصول کنندہ", ["تمام","اساتذہ","طلبہ"])
                if st.form_submit_button("📤 بھیجیں"):
                    if t_.strip() and m_.strip():
                        run("INSERT INTO notifications (title,message,target,created_by) VALUES (?,?,?,?)",
                            (t_, m_, tg, st.session_state.username))
                        st.success("✅ بھیج دیا!")
                        st.rerun()
                    else:
                        st.error("عنوان اور پیغام ضروری")

    notifs = fetch("""SELECT title, message, target, created_by, created_at
                     FROM notifications ORDER BY created_at DESC LIMIT 30""")
    if notifs:
        for n in notifs:
            st.markdown(f"""
            <div class="notif-item">
              <h5>🔔 {n['title']}
                <small style="font-weight:400;color:#6b7c73"> ({n['target']})</small>
              </h5>
              <p>{n['message']}</p>
              <small>از: {n['created_by']} | {n['created_at'][:16]}</small>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("کوئی اعلان نہیں")

# ══════════════════════════════════════════
# ████  ANALYTICS  ████
# ══════════════════════════════════════════
elif pg == "analytics" and IS_ADMIN:
    try:
        import plotly.express as px
        sec("📈", "تجزیہ و رپورٹس", "اعداد و شمار")

        c1, c2 = st.columns(2)
        with c1:
            dd = fetch("SELECT dept, COUNT(*) as cnt FROM students WHERE is_active=1 GROUP BY dept")
            if dd:
                fig = px.pie(pd.DataFrame(dd), values='cnt', names='dept',
                             title='شعبہ وار طلباء',
                             color_discrete_sequence=['#0a5c3c','#0d7a52','#c9982a','#f5c842'])
                fig.update_layout(font_family="serif", title_x=0.5)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            ed = fetch("""SELECT grade, COUNT(*) as cnt FROM exams
                         WHERE status='مکمل' AND grade!='' GROUP BY grade""")
            if ed:
                fig2 = px.bar(pd.DataFrame(ed), x='grade', y='cnt',
                              title='امتحانی نتائج',
                              color='cnt', color_continuous_scale=['#e8f6f0','#0a5c3c'])
                fig2.update_layout(font_family="serif", title_x=0.5)
                st.plotly_chart(fig2, use_container_width=True)

        att_d = fetch("""SELECT att_date, COUNT(*) as cnt FROM teacher_attendance
                        WHERE att_date >= ? GROUP BY att_date ORDER BY att_date""",
                      (str(date.today() - timedelta(days=30)),))
        if att_d:
            fig3 = px.line(pd.DataFrame(att_d), x='att_date', y='cnt',
                           title='ماہانہ حاضری (30 دن)',
                           color_discrete_sequence=['#0a5c3c'], markers=True)
            fig3.update_layout(font_family="serif", title_x=0.5)
            st.plotly_chart(fig3, use_container_width=True)
    except ImportError:
        st.warning("plotly انسٹال نہیں ہے۔ requirements.txt میں plotly شامل کریں۔")

# ══════════════════════════════════════════
# ████  BEST STUDENTS  ████
# ══════════════════════════════════════════
elif pg == "best" and IS_ADMIN:
    sec("🏆", "ماہانہ بہترین طلباء", "تعلیمی اور صفائی کی بنیاد پر")
    c1, c2 = st.columns(2)
    mnth = c1.date_input("مہینہ", date.today().replace(day=1))
    df_ = c2.selectbox("شعبہ", ["تمام"] + DEPTS)
    d1 = mnth.replace(day=1)
    if mnth.month == 12:
        d2 = mnth.replace(year=mnth.year+1, month=1, day=1) - timedelta(days=1)
    else:
        d2 = mnth.replace(month=mnth.month+1, day=1) - timedelta(days=1)

    dw = "" if df_ == "تمام" else f" AND dept='{df_}'"
    studs = fetch(f"SELECT id,name,father_name,roll_no,dept FROM students WHERE is_active=1{dw}")

    scores = []
    for s in studs:
        gs, cs = [], []
        if s['dept'] == "حفظ":
            recs = fetch("""SELECT attendance, sabaq_nagha, sq_nagha, manzil_nagha,
                           sq_mistakes, manzil_mistakes, cleanliness
                           FROM hifz_records WHERE student_id=? AND rec_date BETWEEN ? AND ?""",
                         (s['id'], str(d1), str(d2)))
            for r in recs:
                gr = calc_grade_hifz(r['attendance'], r['sabaq_nagha'], r['sq_nagha'],
                                     r['manzil_nagha'], r['sq_mistakes'], r['manzil_mistakes'])
                gm = {"ممتاز":100,"جید جداً":85,"جید":75,"مقبول":60,"ناقص":40,
                      "کمزور":25,"ناکام":10,"غیر حاضر":0,"رخصت":50}
                gs.append(gm.get(gr, 0))
                if r.get('cleanliness'):
                    cs.append({"بہترین":3,"بہتر":2,"ناقص":1}.get(r['cleanliness'], 0))
        else:
            recs = fetch("""SELECT attendance, performance, cleanliness
                           FROM general_records WHERE student_id=? AND rec_date BETWEEN ? AND ?""",
                         (s['id'], str(d1), str(d2)))
            for r in recs:
                pm = {"بہت بہتر":90,"بہتر":80,"مناسب":65,"کمزور":45}
                if r['attendance'] == "حاضر":
                    gs.append(pm.get(r.get('performance',''), 70))
                elif r['attendance'] == "رخصت":
                    gs.append(50)
                else:
                    gs.append(0)
                if r.get('cleanliness'):
                    cs.append({"بہترین":3,"بہتر":2,"ناقص":1}.get(r['cleanliness'], 0))

        if gs:
            scores.append({
                "name": s['name'], "father": s['father_name'],
                "roll": s['roll_no'] or "—", "dept": s['dept'],
                "ga": round(sum(gs)/len(gs), 1),
                "ca": round(sum(cs)/len(cs), 2) if cs else 0,
                "days": len(gs)
            })

    if not scores:
        st.warning("اس مدت میں کوئی ریکارڈ نہیں")
    else:
        bg = sorted(scores, key=lambda x: x['ga'], reverse=True)
        bc = sorted(scores, key=lambda x: x['ca'], reverse=True)
        medals = [("🥇","#c9982a"), ("🥈","#9ca3af"), ("🥉","#cd7f32")]

        st.subheader("📚 تعلیمی کارکردگی")
        c1, c2, c3 = st.columns(3)
        for col, (st_, (m, _)) in zip([c1,c2,c3], zip(bg[:3], medals)):
            with col:
                st.markdown(f"""
                <div class="trophy-card">
                  <span class="trophy-medal">{m}</span>
                  <div class="trophy-name">{st_['name']}</div>
                  <div class="trophy-sub">والد: {st_['father']}</div>
                  <div class="trophy-sub">🏫 {st_['dept']} | {st_['days']} دن</div>
                  <div class="trophy-score">{st_['ga']}%</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🧹 صفائی")
        c1, c2, c3 = st.columns(3)
        for col, (st_, (m, _)) in zip([c1,c2,c3], zip(bc[:3], medals)):
            with col:
                cp = round((st_['ca']/3)*100, 1)
                st.markdown(f"""
                <div class="trophy-card">
                  <span class="trophy-medal">{m}</span>
                  <div class="trophy-name">{st_['name']}</div>
                  <div class="trophy-sub">والد: {st_['father']}</div>
                  <div class="trophy-sub">🏫 {st_['dept']}</div>
                  <div class="trophy-score">🧹 {cp}%</div>
                </div>""", unsafe_allow_html=True)

        with st.expander("📊 تمام طلباء"):
            df_a = pd.DataFrame(scores)
            df_a.columns = ["نام","والد","رول","شعبہ","تعلیمی %","صفائی","دن"]
            st.dataframe(df_a.sort_values("تعلیمی %", ascending=False),
                         use_container_width=True, hide_index=True)
            st.download_button("📥 CSV", to_csv(df_a), "best.csv")

# ══════════════════════════════════════════
# ████  PASSWORD  ████
# ══════════════════════════════════════════
elif pg == "password":
    sec("🔑", "پاسورڈ تبدیل کریں")
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if IS_ADMIN:
            st.markdown("**استاد کا پاسورڈ ری سیٹ کریں**")
            tl = [r['username'] for r in fetch("SELECT username FROM users WHERE role='teacher'")]
            with st.form("adm_pw"):
                sel_t = st.selectbox("استاد", tl) if tl else st.text_input("استاد")
                np1 = st.text_input("نیا پاسورڈ*", type="password")
                np2 = st.text_input("تصدیق*", type="password")
                if st.form_submit_button("✅ ری سیٹ کریں"):
                    if np1 and np1 == np2 and len(np1) >= 6:
                        run("UPDATE users SET password=? WHERE username=?",
                            (hash_pw(np1), sel_t))
                        audit(st.session_state.username, "PW Reset", sel_t)
                        st.success(f"✅ {sel_t} کا پاسورڈ تبدیل!")
                    elif len(np1) < 6:
                        st.error("کم از کم 6 حروف")
                    else:
                        st.error("پاسورڈ میل نہیں")
            st.markdown("---")

        st.markdown("**اپنا پاسورڈ تبدیل کریں**")
        with st.form("my_pw"):
            op = st.text_input("پرانا پاسورڈ*", type="password")
            np1 = st.text_input("نیا پاسورڈ*", type="password")
            np2 = st.text_input("تصدیق*", type="password")
            if st.form_submit_button("✅ تبدیل کریں"):
                u = fetch("SELECT password FROM users WHERE username=?",
                          (st.session_state.username,), one=True)
                if u and check_pw(op, u['password']):
                    if np1 == np2 and len(np1) >= 6:
                        run("UPDATE users SET password=? WHERE username=?",
                            (hash_pw(np1), st.session_state.username))
                        audit(st.session_state.username, "PW Changed")
                        st.success("✅ تبدیل! دوبارہ لاگ ان کریں")
                        st.session_state.logged_in = False
                        st.rerun()
                    elif len(np1) < 6:
                        st.error("کم از کم 6 حروف")
                    else:
                        st.error("پاسورڈ میل نہیں")
                else:
                    st.error("❌ پرانا پاسورڈ غلط")

# ══════════════════════════════════════════
# ████  BACKUP  ████
# ══════════════════════════════════════════
elif pg == "backup" and IS_ADMIN:
    sec("⚙️", "بیک اپ & سیٹنگز")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<div class='page-card'>", unsafe_allow_html=True)
        st.markdown("**📥 بیک اپ ڈاؤن لوڈ**")
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "rb") as f:
                st.download_button("💾 مکمل ڈیٹا بیس (.db)",
                                   f, f"jamia_bkp_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
                                   "application/x-sqlite3", use_container_width=True)
        if st.button("📦 تمام CSV زپ", use_container_width=True):
            tables = ["users","students","hifz_records","qaida_records","general_records",
                      "teacher_attendance","leave_requests","exams","passed_paras",
                      "timetable","notifications","staff_notes","audit_log"]
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as zf:
                for t in tables:
                    try:
                        rows = fetch(f"SELECT * FROM {t}")
                        if rows:
                            zf.writestr(f"{t}.csv",
                                        pd.DataFrame(rows).to_csv(index=False).encode('utf-8-sig'))
                    except:
                        pass
            buf.seek(0)
            st.download_button("📥 CSV زپ ڈاؤن لوڈ", buf,
                               f"csv_{datetime.now().strftime('%Y%m%d')}.zip",
                               "application/zip", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='page-card'>", unsafe_allow_html=True)
        st.markdown("**🔄 ری سٹور**")
        st.warning("⚠️ موجودہ ڈیٹا بدل جائے گا!")
        upf = st.file_uploader(".db فائل", type=["db"])
        if upf:
            if st.checkbox("میں سمجھتا/سمجھتی ہوں") and st.button("🔄 ری سٹور"):
                import shutil
                if os.path.exists(DB_PATH):
                    shutil.copy(DB_PATH, DB_PATH + ".bak")
                with open(DB_PATH, "wb") as f:
                    f.write(upf.getbuffer())
                st.success("✅ ری سٹور مکمل")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='page-card'>", unsafe_allow_html=True)
    st.markdown("**📋 آڈٹ لاگ (آخری 50)**")
    logs = fetch("""SELECT username as صارف, action as عمل, details as تفصیل,
                   created_at as وقت FROM audit_log ORDER BY created_at DESC LIMIT 50""")
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════
# ████  TEACHER HOME  ████
# ══════════════════════════════════════════
elif pg == "home" and not IS_ADMIN:
    sec("🏠", f"خوش آمدید، {st.session_state.username}!", "استاد پورٹل")
    my_s = scalar("SELECT COUNT(*) FROM students WHERE teacher=? AND is_active=1",
                  (st.session_state.username,))
    my_recs = scalar("SELECT COUNT(*) FROM hifz_records WHERE teacher=?",
                     (st.session_state.username,))
    my_lv = scalar("SELECT COUNT(*) FROM leave_requests WHERE username=? AND status='پینڈنگ'",
                   (st.session_state.username,))
    today_done = scalar("""SELECT COUNT(*) FROM hifz_records
                          WHERE teacher=? AND rec_date=?""",
                        (st.session_state.username, str(date.today())))

    st.markdown(f"""
    <div class="metrics">
      <div class="met-card"><span class="met-ico">👨‍🎓</span>
        <div class="met-val">{my_s}</div><div class="met-lbl">میرے طلباء</div></div>
      <div class="met-card"><span class="met-ico">📋</span>
        <div class="met-val">{my_recs}</div><div class="met-lbl">کل ریکارڈز</div></div>
      <div class="met-card"><span class="met-ico">✅</span>
        <div class="met-val">{today_done}</div><div class="met-lbl">آج کے اندراج</div></div>
      <div class="met-card"><span class="met-ico">📩</span>
        <div class="met-val">{my_lv}</div><div class="met-lbl">پینڈنگ رخصت</div></div>
    </div>""", unsafe_allow_html=True)

    notifs = fetch("""SELECT title, message FROM notifications
                     WHERE target IN ('تمام','اساتذہ') ORDER BY created_at DESC LIMIT 5""")
    if notifs:
        st.markdown("**🔔 تازہ اعلانات**")
        for n in notifs:
            st.markdown(f"""
            <div class="notif-item">
              <h5>{n['title']}</h5>
              <p>{n['message'][:100]}</p>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# ████  TEACHER DAILY ENTRY  ████
# ══════════════════════════════════════════
elif pg == "entry" and not IS_ADMIN:
    sec("📝", "روزانہ سبق اندراج", "آج کا ریکارڈ درج کریں")
    c1, c2 = st.columns(2)
    entry_date = c1.date_input("تاریخ", date.today())
    dept = c2.selectbox("شعبہ", DEPTS)

    my_studs = fetch("SELECT id,name,father_name FROM students WHERE teacher=? AND dept=? AND is_active=1",
                     (st.session_state.username, dept))

    if not my_studs:
        st.info(f"آپ کی {dept} کلاس میں کوئی طالب علم نہیں")
        st.stop()

    st.caption(f"**{len(my_studs)} طلباء | {dept} | {entry_date}**")

    # ── HIFZ ──
    if dept == "حفظ":
        for s in my_studs:
            existing = fetch("SELECT id FROM hifz_records WHERE student_id=? AND rec_date=?",
                             (s['id'], str(entry_date)), one=True)
            st.markdown(f"""
            <div class="stu-card">
              <div class="stu-name">{'✅' if existing else '📝'} {s['name']} ولد {s['father_name']}</div>
            """, unsafe_allow_html=True)

            if existing:
                st.caption("آج کا ریکارڈ موجود ہے")
                st.markdown("</div>", unsafe_allow_html=True)
                continue

            k = str(s['id'])
            att = st.radio("حاضری", ATT_OPTS, key=f"att_{k}", horizontal=True)
            cln = st.selectbox("صفائی", CLEANLINESS, key=f"cln_{k}")

            s_nagha = sq_nagha = m_nagha = 0
            sabaq_txt = sq_txt = m_txt = ""
            s_lines = sq_atk = sq_mis = m_atk = m_mis = 0

            if att == "حاضر":
                st.markdown("**📖 سبق**")
                sc1, sc2 = st.columns(2)
                sn = sc1.checkbox("ناغہ", key=f"sn_{k}")
                sy = sc2.checkbox("یاد نہیں", key=f"sy_{k}")
                if sn or sy:
                    s_nagha = 1
                    sabaq_txt = "ناغہ" if sn else "یاد نہیں"
                else:
                    rc1, rc2, rc3 = st.columns(3)
                    sur = rc1.selectbox("سورت", SURAHS, key=f"sr_{k}")
                    af = rc2.text_input("سے", key=f"af_{k}")
                    at = rc3.text_input("تک", key=f"at_{k}")
                    s_lines = st.number_input("ستر (لائنیں)", 0, 50, 0, key=f"sl_{k}")
                    sabaq_txt = f"{sur}:{af}-{at}" if af or at else sur

                st.markdown("**📚 سبقی**")
                sc1, sc2 = st.columns(2)
                sqn_ = sc1.checkbox("ناغہ", key=f"sqn_{k}")
                sqy = sc2.checkbox("یاد نہیں", key=f"sqy_{k}")
                if sqn_ or sqy:
                    sq_nagha = 1
                    sq_txt = "ناغہ" if sqn_ else "یاد نہیں"
                else:
                    rc1, rc2, rc3, rc4 = st.columns(4)
                    sqp = rc1.selectbox("پارہ", PARAS, key=f"sqp_{k}")
                    sqm = rc2.selectbox("مقدار", MIQDAR, key=f"sqm_{k}")
                    sq_atk = rc3.number_input("اٹکن", 0, key=f"sqat_{k}")
                    sq_mis = rc4.number_input("غلطی", 0, key=f"sqms_{k}")
                    sq_txt = f"{sqp}:{sqm}"

                st.markdown("**🌙 منزل**")
                sc1, sc2 = st.columns(2)
                mn_ = sc1.checkbox("ناغہ", key=f"mn_{k}")
                my_ = sc2.checkbox("یاد نہیں", key=f"my_{k}")
                if mn_ or my_:
                    m_nagha = 1
                    m_txt = "ناغہ" if mn_ else "یاد نہیں"
                else:
                    rc1, rc2, rc3, rc4 = st.columns(4)
                    mp = rc1.selectbox("پارہ", PARAS, key=f"mp_{k}")
                    mm = rc2.selectbox("مقدار", MIQDAR, key=f"mm_{k}")
                    m_atk = rc3.number_input("اٹکن", 0, key=f"mat_{k}")
                    m_mis = rc4.number_input("غلطی", 0, key=f"mms_{k}")
                    m_txt = f"{mp}:{mm}"

                grade = calc_grade_hifz(att, s_nagha, sq_nagha, m_nagha, sq_mis, m_mis)
                gcls = {"ممتاز":"chip-green","جید جداً":"chip-purple","جید":"chip-blue",
                        "مقبول":"chip-yellow"}.get(grade,"chip-red")
                st.markdown(f"**درجہ:** <span class='chip {gcls}'>{grade}</span>",
                            unsafe_allow_html=True)
            else:
                grade = "غیر حاضر" if att == "غیر حاضر" else "رخصت"

            note = st.text_input("نوٹ", key=f"nt_{k}", placeholder="اختیاری")

            if st.button(f"💾 {s['name']} محفوظ کریں", key=f"sv_{k}"):
                run("""INSERT INTO hifz_records
                      (rec_date,student_id,teacher,attendance,sabaq,sabaq_lines,sabaq_nagha,
                       sq_text,sq_nagha,sq_atkan,sq_mistakes,
                       manzil_text,manzil_nagha,manzil_atkan,manzil_mistakes,
                       cleanliness,grade,note)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (str(entry_date), s['id'], st.session_state.username, att,
                     sabaq_txt, s_lines, s_nagha,
                     sq_txt, sq_nagha, sq_atk, sq_mis,
                     m_txt, m_nagha, m_atk, m_mis,
                     cln, grade, note))
                audit(st.session_state.username, "Hifz Entry", f"{s['name']} {entry_date}")
                st.success(f"✅ {s['name']} محفوظ!")
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ── QAIDA ──
    elif dept == "قاعدہ":
        for s in my_studs:
            existing = fetch("SELECT id FROM qaida_records WHERE student_id=? AND rec_date=?",
                             (s['id'], str(entry_date)), one=True)
            st.markdown(f"""<div class="stu-card">
            <div class="stu-name">{'✅' if existing else '📝'} {s['name']} ولد {s['father_name']}</div>
            """, unsafe_allow_html=True)
            if existing:
                st.caption("ریکارڈ موجود")
                st.markdown("</div>", unsafe_allow_html=True)
                continue
            k = str(s['id'])
            att = st.radio("حاضری", ATT_OPTS, key=f"att_{k}", horizontal=True)
            cln = st.selectbox("صفائی", CLEANLINESS, key=f"cln_{k}")
            ln = lines = 0
            det = ""
            if att == "حاضر":
                ln = st.text_input("تختی/سبق نمبر", key=f"ln_{k}")
                lines = st.number_input("لائنیں", 0, key=f"lns_{k}")
                det = st.text_area("تفصیل", key=f"det_{k}")
            if st.button(f"💾 {s['name']} محفوظ", key=f"sv_{k}"):
                run("""INSERT INTO qaida_records
                      (rec_date,student_id,teacher,attendance,lesson_no,total_lines,details,cleanliness)
                      VALUES (?,?,?,?,?,?,?,?)""",
                    (str(entry_date), s['id'], st.session_state.username, att, ln, lines, det, cln))
                audit(st.session_state.username, "Qaida Entry", f"{s['name']} {entry_date}")
                st.success(f"✅ {s['name']} محفوظ!")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ── GENERAL ──
    else:
        with st.form(f"gen_{dept}"):
            recs = []
            for s in my_studs:
                st.markdown(f"**👤 {s['name']} ولد {s['father_name']}**")
                k = str(s['id'])
                att = st.radio("حاضری", ATT_OPTS, key=f"att_{k}", horizontal=True)
                cln = st.selectbox("صفائی", CLEANLINESS, key=f"cln_{k}")
                sub_ = les_ = hw_ = prf_ = ""
                if att == "حاضر":
                    sub_ = st.text_input("مضمون/کتاب", key=f"sub_{k}")
                    les_ = st.text_area("سبق", key=f"les_{k}")
                    hw_  = st.text_input("ہوم ورک", key=f"hw_{k}")
                    prf_ = st.select_slider("کارکردگی", ["بہت بہتر","بہتر","مناسب","کمزور"], key=f"prf_{k}")
                recs.append((str(entry_date), s['id'], st.session_state.username, dept,
                             att, sub_, les_, hw_, prf_, cln))
                st.markdown("---")
            if st.form_submit_button("✅ تمام محفوظ کریں"):
                for r in recs:
                    run("""INSERT INTO general_records
                          (rec_date,student_id,teacher,dept,attendance,subject,lesson,homework,performance,cleanliness)
                          VALUES (?,?,?,?,?,?,?,?,?,?)""", r)
                audit(st.session_state.username, f"{dept} Entry", str(entry_date))
                st.success("✅ تمام محفوظ!")
                st.rerun()

# ══════════════════════════════════════════
# ████  TEACHER EXAM REQUEST  ████
# ══════════════════════════════════════════
elif pg == "t_exam" and not IS_ADMIN:
    sec("🎓", "امتحانی درخواست", "طالب علم کو نامزد کریں")
    my_s = fetch("SELECT id,name,father_name,dept FROM students WHERE teacher=? AND is_active=1",
                 (st.session_state.username,))
    if not my_s:
        st.warning("آپ کی کلاس میں کوئی طالب علم نہیں")
    else:
        with st.form("ex_req"):
            names = [f"{s['name']} ولد {s['father_name']} ({s['dept']})" for s in my_s]
            idx = st.selectbox("طالب علم", range(len(names)), format_func=lambda i: names[i])
            s = my_s[idx]
            et = st.selectbox("امتحان", ["پارہ ٹیسٹ","ماہانہ","سہ ماہی","سالانہ"])
            c1, c2 = st.columns(2)
            sd = c1.date_input("شروع", date.today())
            ed = c2.date_input("ختم", date.today() + timedelta(days=7))
            td = (ed - sd).days + 1
            st.caption(f"کل دن: {td}")
            fp = tp = 0
            bk = amt = ""
            if et == "پارہ ٹیسٹ" or s['dept'] == "حفظ":
                c1, c2 = st.columns(2)
                fp = c1.number_input("پارہ (شروع)", 1, 30, 1)
                tp = c2.number_input("پارہ (ختم)", int(fp), 30, int(fp))
            if s['dept'] != "حفظ":
                bk = st.text_input("کتاب")
            amt = st.text_input("مقدار خواندگی")
            if st.form_submit_button("📤 درخواست بھیجیں"):
                run("""INSERT INTO exams
                      (student_id,teacher,dept,exam_type,from_para,to_para,
                       book_name,amount_read,start_date,end_date,total_days)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (s['id'], st.session_state.username, s['dept'],
                     et, fp, tp, bk, amt, str(sd), str(ed), td))
                audit(st.session_state.username, "Exam Request", f"{s['name']}-{et}")
                st.success("✅ درخواست بھیج دی گئی")

# ══════════════════════════════════════════
# ████  TEACHER LEAVE  ████
# ══════════════════════════════════════════
elif pg == "t_leave" and not IS_ADMIN:
    sec("📩", "رخصت کی درخواست")
    my_leaves = fetch("""SELECT leave_type as نوعیت, start_date as تاریخ,
                        days as دن, status as حالت
                        FROM leave_requests WHERE username=? ORDER BY created_at DESC LIMIT 10""",
                      (st.session_state.username,))
    if my_leaves:
        st.markdown("**حالیہ درخواستیں**")
        for lv in my_leaves:
            sc = "st-ok" if lv['حالت'] == "منظور" else ("st-reject" if lv['حالت'] == "مسترد" else "st-pending")
            st.markdown(f"""
            <div class="leave-item">
              <span class="{sc}">{lv['حالت']}</span> &nbsp;
              <strong>{lv['نوعیت']}</strong> | {lv['تاریخ']} | {lv['دن']} دن
            </div>""", unsafe_allow_html=True)
        st.markdown("---")

    with st.form("lv_f"):
        c1, c2 = st.columns(2)
        lt = c1.selectbox("نوعیت", ["بیماری","ضروری کام","ہنگامی","دیگر"])
        sd = c2.date_input("تاریخ شروع", date.today())
        days = c1.number_input("دن", 1, 30, 1)
        back = sd + timedelta(days=int(days)-1)
        c2.caption(f"واپسی: {back}")
        rsn = st.text_area("وجہ*", max_chars=500)
        if st.form_submit_button("📤 بھیجیں"):
            if rsn.strip():
                run("""INSERT INTO leave_requests (username,leave_type,start_date,days,reason)
                      VALUES (?,?,?,?,?)""",
                    (st.session_state.username, lt, str(sd), days, rsn))
                audit(st.session_state.username, "Leave Request", f"{lt},{days}d")
                st.success("✅ درخواست بھیج دی گئی")
                st.rerun()
            else:
                st.error("وجہ ضروری ہے")

# ══════════════════════════════════════════
# ████  TEACHER ATTENDANCE  ████
# ══════════════════════════════════════════
elif pg == "t_att" and not IS_ADMIN:
    sec("🕒", "میری حاضری")
    today = date.today()
    rec = fetch("SELECT * FROM teacher_attendance WHERE username=? AND att_date=?",
                (st.session_state.username, str(today)), one=True)

    st.markdown(f"""
    <div class="page-card" style="text-align:center">
      <div style="font-size:1.1rem;font-weight:700;color:#0a5c3c">
        📅 {today.strftime('%A, %d %B %Y')}
      </div>
    </div>""", unsafe_allow_html=True)

    if not rec:
        arr = st.time_input("آمد کا وقت", datetime.now().time())
        if st.button("✅ آمد درج کریں", use_container_width=True):
            try:
                run("""INSERT INTO teacher_attendance (username,att_date,arrival) VALUES (?,?,?)""",
                    (st.session_state.username, str(today), arr.strftime("%I:%M %p")))
                st.success("✅ آمد درج!")
                st.rerun()
            except:
                st.warning("آمد پہلے سے درج ہے")
    elif not rec.get('departure'):
        st.success(f"✅ آمد: {rec['arrival']}")
        dep = st.time_input("رخصت کا وقت", datetime.now().time())
        if st.button("✅ رخصت درج کریں", use_container_width=True):
            run("""UPDATE teacher_attendance SET departure=? WHERE username=? AND att_date=?""",
                (dep.strftime("%I:%M %p"), st.session_state.username, str(today)))
            st.success("✅ رخصت درج!")
            st.rerun()
    else:
        c1, c2 = st.columns(2)
        c1.metric("🟢 آمد", rec['arrival'])
        c2.metric("🔴 رخصت", rec['departure'])

    st.markdown("---")
    st.markdown("**ماہانہ ریکارڈ**")
    monthly = fetch("""SELECT att_date as تاریخ, arrival as آمد, departure as رخصت
                      FROM teacher_attendance WHERE username=? AND att_date >= ?
                      ORDER BY att_date DESC""",
                    (st.session_state.username, str(date.today().replace(day=1))))
    if monthly:
        st.dataframe(pd.DataFrame(monthly), use_container_width=True, hide_index=True)
    else:
        st.caption("اس ماہ کوئی ریکارڈ نہیں")

# ══════════════════════════════════════════
# ████  TEACHER TIMETABLE  ████
# ══════════════════════════════════════════
elif pg == "t_tt" and not IS_ADMIN:
    sec("📚", "میرا ٹائم ٹیبل")
    tt = fetch("""SELECT day_name as دن, period as وقت, subject as مضمون, room as کمرہ
                 FROM timetable WHERE teacher=? ORDER BY day_name, period""",
               (st.session_state.username,))
    if tt:
        df = pd.DataFrame(tt)
        try:
            pivot = df.pivot(index='وقت', columns='دن', values='مضمون').fillna("—")
            st.dataframe(pivot, use_container_width=True)
        except:
            st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("📥 ٹائم ٹیبل ڈاؤن لوڈ",
                           html_report(df, "ٹائم ٹیبل", st.session_state.username),
                           "timetable.html", "text/html")
    else:
        st.info("آپ کا ٹائم ٹیبل ابھی ترتیب نہیں دیا گیا")

# ══════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════
st.markdown("""
<div class="bottom-pad"></div>
<div style="text-align:center;padding:16px 0 8px;color:#9ca3af;font-size:.72rem;
     border-top:1px solid #e8f0ec;margin-top:24px">
  🕌 جامعہ ملیہ اسلامیہ فیصل آباد — Smart ERP | تمام حقوق محفوظ
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
