"""
جامعہ ملیہ اسلامیہ فیصل آباد
Smart ERP v4.0 - Mobile First, Square Icons
"""
import streamlit as st
st.set_page_config(
    page_title="جامعہ ملیہ ERP",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3, hashlib, os, io, zipfile, shutil

# ════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════
DB = "jamia_data.db"

def con():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c

def wr(sql, p=()):
    with con() as c:
        cur = c.execute(sql, p)
        c.commit()
        return cur.lastrowid

def rd(sql, p=(), one=False):
    with con() as c:
        rows = [dict(r) for r in c.execute(sql, p).fetchall()]
        return rows[0] if one and rows else (None if one else rows)

def sc(sql, p=()):
    with con() as c:
        r = c.execute(sql, p).fetchone()
        return r[0] if r else 0

def col_ok(t, c):
    return any(r['name'] == c for r in rd(f"PRAGMA table_info({t})"))

def add_col(t, c, typ):
    if not col_ok(t, c):
        try: wr(f"ALTER TABLE {t} ADD COLUMN {c} {typ}")
        except: pass

def ensure_columns():
    """تمام ٹیبلز میں ضروری کالمز کی موجودگی یقینی بنائیں"""
    # users
    for col, typ in [('dept','TEXT'),('phone','TEXT'),('address','TEXT'),
                     ('id_card','TEXT'),('joining_date','TEXT'),('is_active','INTEGER DEFAULT 1')]:
        add_col('users', col, typ)
    # students
    for col, typ in [('mother_name','TEXT'),('exit_date','TEXT'),('exit_reason','TEXT'),
                     ('class_name','TEXT'),('section','TEXT'),('is_active','INTEGER DEFAULT 1')]:
        add_col('students', col, typ)
    # hifz_records
    for col, typ in [('sabaq_lines','INTEGER DEFAULT 0'),('sq_atkan','INTEGER DEFAULT 0'),
                     ('manzil_atkan','INTEGER DEFAULT 0'),('cleanliness','TEXT'),
                     ('grade','TEXT'),('note','TEXT')]:
        add_col('hifz_records', col, typ)
    # qaida_records
    for col, typ in [('cleanliness','TEXT'),('note','TEXT')]:
        add_col('qaida_records', col, typ)
    # general_records
    for col, typ in [('cleanliness','TEXT'),('note','TEXT')]:
        add_col('general_records', col, typ)
    # exams
    for col, typ in [('from_para','INTEGER'),('to_para','INTEGER'),('book_name','TEXT'),
                     ('amount_read','TEXT'),('end_date','TEXT'),('total_days','INTEGER'),
                     ('q1','INTEGER'),('q2','INTEGER'),('q3','INTEGER'),('q4','INTEGER'),('q5','INTEGER'),
                     ('total','INTEGER'),('grade','TEXT'),('status','TEXT')]:
        add_col('exams', col, typ)
    # passed_paras
    for col, typ in [('book_name','TEXT'),('grade','TEXT'),('marks','INTEGER')]:
        add_col('passed_paras', col, typ)

def setup():
    wr("""CREATE TABLE IF NOT EXISTS users(
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
        created_at TEXT DEFAULT(datetime('now','localtime')))""")

    wr("""CREATE TABLE IF NOT EXISTS students(
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
        created_at TEXT DEFAULT(datetime('now','localtime')))""")

    wr("""CREATE TABLE IF NOT EXISTS hifz_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rec_date TEXT NOT NULL,
        student_id INTEGER NOT NULL,
        teacher TEXT NOT NULL,
        attendance TEXT DEFAULT 'حاضر',
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
        created_at TEXT DEFAULT(datetime('now','localtime')),
        FOREIGN KEY(student_id) REFERENCES students(id))""")

    wr("""CREATE TABLE IF NOT EXISTS qaida_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rec_date TEXT NOT NULL,
        student_id INTEGER NOT NULL,
        teacher TEXT NOT NULL,
        attendance TEXT DEFAULT 'حاضر',
        lesson_no TEXT DEFAULT '',
        total_lines INTEGER DEFAULT 0,
        details TEXT DEFAULT '',
        cleanliness TEXT DEFAULT '',
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT(datetime('now','localtime')),
        FOREIGN KEY(student_id) REFERENCES students(id))""")

    wr("""CREATE TABLE IF NOT EXISTS general_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rec_date TEXT NOT NULL,
        student_id INTEGER NOT NULL,
        teacher TEXT NOT NULL,
        dept TEXT DEFAULT '',
        attendance TEXT DEFAULT 'حاضر',
        subject TEXT DEFAULT '',
        lesson TEXT DEFAULT '',
        homework TEXT DEFAULT '',
        performance TEXT DEFAULT '',
        cleanliness TEXT DEFAULT '',
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT(datetime('now','localtime')),
        FOREIGN KEY(student_id) REFERENCES students(id))""")

    wr("""CREATE TABLE IF NOT EXISTS teacher_attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        att_date TEXT NOT NULL,
        arrival TEXT DEFAULT '',
        departure TEXT DEFAULT '',
        created_at TEXT DEFAULT(datetime('now','localtime')),
        UNIQUE(username,att_date))""")

    wr("""CREATE TABLE IF NOT EXISTS leave_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        leave_type TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        days INTEGER DEFAULT 1,
        reason TEXT DEFAULT '',
        status TEXT DEFAULT 'پینڈنگ',
        created_at TEXT DEFAULT(datetime('now','localtime')))""")

    wr("""CREATE TABLE IF NOT EXISTS exams(
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
        q1 INTEGER DEFAULT 0,q2 INTEGER DEFAULT 0,
        q3 INTEGER DEFAULT 0,q4 INTEGER DEFAULT 0,q5 INTEGER DEFAULT 0,
        total INTEGER DEFAULT 0,
        grade TEXT DEFAULT '',
        status TEXT DEFAULT 'پینڈنگ',
        created_at TEXT DEFAULT(datetime('now','localtime')),
        FOREIGN KEY(student_id) REFERENCES students(id))""")

    wr("""CREATE TABLE IF NOT EXISTS passed_paras(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        para_no INTEGER DEFAULT 0,
        book_name TEXT DEFAULT '',
        passed_date TEXT DEFAULT '',
        exam_type TEXT DEFAULT '',
        grade TEXT DEFAULT '',
        marks INTEGER DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(id))""")

    wr("""CREATE TABLE IF NOT EXISTS timetable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher TEXT NOT NULL,
        day_name TEXT DEFAULT '',
        period TEXT DEFAULT '',
        subject TEXT DEFAULT '',
        room TEXT DEFAULT '')""")

    wr("""CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT DEFAULT '',
        target TEXT DEFAULT 'تمام',
        created_by TEXT DEFAULT '',
        created_at TEXT DEFAULT(datetime('now','localtime')))""")

    wr("""CREATE TABLE IF NOT EXISTS staff_notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff TEXT NOT NULL,
        note_date TEXT DEFAULT '',
        note_type TEXT DEFAULT '',
        description TEXT DEFAULT '',
        action_taken TEXT DEFAULT '',
        status TEXT DEFAULT 'زیر التواء',
        created_by TEXT DEFAULT '',
        created_at TEXT DEFAULT(datetime('now','localtime')))""")

    wr("""CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT DEFAULT '',
        action TEXT DEFAULT '',
        details TEXT DEFAULT '',
        created_at TEXT DEFAULT(datetime('now','localtime')))""")

    # Default admin
    if not rd("SELECT id FROM users WHERE username='admin'", one=True):
        wr("INSERT INTO users(username,password,role,dept)VALUES(?,?,?,?)",
           ("admin", ("jamia123"), "admin", "انتظامیہ"))

    ensure_columns()  # <-- کالم چیک

setup()

# ════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════
def hp(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def chk(plain, stored):
    if not plain or not stored: return False
    if hp(plain) == stored: return True
    if hashlib.sha256(plain.encode()).hexdigest() == stored: return True
    if plain == stored: return True
    return False

def audit(u, a, d=""):
    try: wr("INSERT INTO audit_log(username,action,details)VALUES(?,?,?)",(u,a,str(d)[:300]))
    except: pass

def grade_hifz(att, sn, sqn, mn, sqm, mm):
    if att=="غیر حاضر": return "غیر حاضر"
    if att=="رخصت": return "رخصت"
    ng = int(sn)+int(sqn)+int(mn)
    if ng==1: return "ناقص"
    if ng==2: return "کمزور"
    if ng>=3: return "ناکام"
    t = int(sqm)+int(mm)
    if t<=2: return "ممتاز"
    if t<=5: return "جید جداً"
    if t<=8: return "جید"
    if t<=12: return "مقبول"
    return "ناکام"

def exam_gr(tot):
    if tot>=90: return "ممتاز"
    if tot>=80: return "جید جداً"
    if tot>=70: return "جید"
    if tot>=60: return "مقبول"
    return "ناکام"

def to_csv(df): return df.to_csv(index=False).encode('utf-8-sig')

def html_rep(df, title, sub=""):
    tbl = df.to_html(index=False, border=0, classes="t", escape=False)
    return f"""<!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');
*{{font-family:'Noto Nastaliq Urdu',serif;direction:rtl;}}
body{{background:#f5f9f7;margin:0;padding:20px;}}
.w{{background:#fff;border-radius:12px;padding:24px;max-width:960px;margin:auto;
    box-shadow:0 4px 20px rgba(0,77,50,.1);}}
h2{{text-align:center;color:#0a6640;border-bottom:3px solid #c9982a;padding-bottom:12px;}}
p{{text-align:center;color:#555;}}
table.t{{width:100%;border-collapse:collapse;margin-top:16px;}}
table.t th{{background:#0a6640;color:#fff;padding:9px 12px;text-align:center;font-size:14px;}}
table.t td{{padding:7px 12px;border-bottom:1px solid #e8f0ec;text-align:center;font-size:13px;}}
table.t tr:nth-child(even) td{{background:#f0f8f4;}}
.sig{{display:flex;justify-content:space-between;margin-top:48px;padding-top:16px;border-top:1px solid #ddd;}}
.pb{{text-align:center;margin-top:24px;}}
.pb button{{padding:10px 32px;background:#0a6640;color:#fff;border:none;border-radius:8px;
            cursor:pointer;font-size:15px;font-family:inherit;}}
@media print{{.pb{{display:none;}}}}
</style></head><body><div class="w">
<h2>🕌 جامعہ ملیہ اسلامیہ فیصل آباد</h2>
<p><b>{title}</b>{f' | {sub}' if sub else ''}</p>
{tbl}
<div class="sig">
<span>دستخط استاذ: ___________________</span>
<span>دستخط مہتمم: ___________________</span>
</div></div>
<div class="pb"><button onclick="window.print()">🖨️ پرنٹ کریں</button></div>
</body></html>"""

# ════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════
SURAHS = ["الفاتحة","البقرة","آل عمران","النساء","المائدة","الأنعام","الأعراف",
"الأنفال","التوبة","يونس","هود","يوسف","الرعد","إبراهيم","الحجر","النحل",
"الإسراء","الكهف","مريم","طه","الأنبياء","الحج","المؤمنون","النور","الفرقان",
"الشعراء","النمل","القصص","العنكبوت","الروم","لقمان","السجدة","الأحزاب","سبأ",
"فاطر","يس","الصافات","ص","الزمر","غافر","فصلت","الشورى","الزخرف","الدخان",
"الجاثية","الأحقاف","محمد","الفتح","الحجرات","ق","الذاريات","الطور","النجم",
"القمر","الرحمن","الواقعة","الحديد","المجادلة","الحشر","الممتحنة","الصف",
"الجمعة","المنافقون","التغابن","الطلاق","التحریم","الملک","القلم","الحاقة",
"المعارج","نوح","الجن","المزمل","المدثر","القیامة","الإنسان","المرسلات","النبأ",
"النازعات","عبس","التکویر","الإنفطار","المطففین","الإنشقاق","البروج","الطارق",
"الأعلى","الغاشیة","الفجر","البلد","الشمس","اللیل","الضحى","الشرح","التین",
"العلق","القدر","البینة","الزلزلة","العادیات","القارعة","التکاثر","العصر",
"الهمزة","الفیل","قریش","الماعون","الکوثر","الکافرون","النصر","المسد",
"الإخلاص","الفلق","الناس"]
PARAS   = [f"پارہ {i}" for i in range(1,31)]
DAYS_UR = ["پیر","منگل","بدھ","جمعرات","جمعہ","ہفتہ","اتوار"]
CLEAN   = ["بہترین","بہتر","ناقص"]
DEPTS   = ["حفظ","قاعدہ","درسِ نظامی","عصری تعلیم"]
MIQDAR  = ["مکمل","آدھا","پون","پاؤ"]
ATT     = ["حاضر","غیر حاضر","رخصت"]
GCLS    = {"ممتاز":"gn","جید جداً":"gp","جید":"gb","مقبول":"gy",
           "ناقص":"go","کمزور":"go","ناکام":"gr","غیر حاضر":"gg","رخصت":"gg"}

# ════════════════════════════════════════════
# SESSION
# ════════════════════════════════════════════
for k,v in [("logged_in",False),("username",""),("role",""),
            ("page","home"),("sel_student",None),("entry_dept","حفظ")]:
    if k not in st.session_state: st.session_state[k]=v

def go(p): st.session_state.page=p; st.rerun()

# ════════════════════════════════════════════
# MASTER CSS — Square Icons, Urdu Font Large
# ════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;500;600;700&display=swap');

:root{
  --g1:#0a5c3c; --g2:#0d7a52; --g3:#10966a;
  --g4:#e6f4ee; --g5:#c5e8d8;
  --gold:#c9982a; --gold2:#f5c842;
  --white:#fff; --off:#f2f7f4;
  --dark:#0d1f18; --txt:#1a2e25; --gray:#5a6e64;
  --lgray:#ddeae3; --rad:14px; --rads:10px;
  --sh:0 2px 14px rgba(10,92,60,.10);
  --sh2:0 6px 28px rgba(10,92,60,.18);
}
*{font-family:'Noto Nastaliq Urdu',Georgia,serif!important;
  direction:rtl; box-sizing:border-box;}
html,body,[class*="css"]{direction:rtl;text-align:right;}
.stApp{background:var(--off);}
#MainMenu,footer,header{visibility:hidden!important;}
.block-container{padding:0!important;max-width:100%!important;}
section[data-testid="stSidebar"]{display:none!important;}

/* ── TOP BAR ── */
.topbar{
  background:linear-gradient(135deg,var(--g1) 0%,var(--g2) 100%);
  padding:10px 18px;
  display:flex;align-items:center;justify-content:space-between;
  box-shadow:0 2px 12px rgba(0,0,0,.22);
  position:sticky;top:0;z-index:100;
}
.tb-brand{display:flex;align-items:center;gap:10px;}
.tb-icon{font-size:2rem;}
.tb-name{color:#fff;font-size:1.05rem;font-weight:700;line-height:1.2;}
.tb-sub{color:var(--gold2);font-size:.72rem;}
.tb-user{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.28);
  border-radius:24px;padding:5px 14px;color:#fff;font-size:.82rem;}

/* ── MAIN WRAP ── */
.mw{max-width:1080px;margin:0 auto;padding:14px 14px 90px;}

/* ═══ SQUARE NAV ICONS (Like mobile apps) ═══ */
.sq-grid{
  display:grid;
  grid-template-columns:repeat(5,1fr);
  gap:10px;margin-bottom:4px;
}
@media(max-width:680px){.sq-grid{grid-template-columns:repeat(4,1fr);}}
@media(max-width:480px){.sq-grid{grid-template-columns:repeat(3,1fr);}}

.sq-btn{
  background:var(--white);
  border:2px solid var(--lgray);
  border-radius:16px;          /* ← چورس بٹن */
  padding:14px 6px 10px;
  text-align:center;
  cursor:pointer;
  transition:all .18s cubic-bezier(.34,1.56,.64,1);
  box-shadow:var(--sh);
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  gap:5px; min-height:80px;
}
.sq-btn:hover{
  border-color:var(--g2);
  transform:translateY(-3px) scale(1.03);
  box-shadow:var(--sh2);
}
.sq-btn.active{
  background:linear-gradient(145deg,var(--g1),var(--g2));
  border-color:var(--g1);
  transform:translateY(-2px);
  box-shadow:var(--sh2);
}
.sq-ico{font-size:1.5rem;display:block;line-height:1;}
.sq-lbl{font-size:.73rem;color:var(--txt);font-weight:700;line-height:1.25;display:block;}
.sq-btn.active .sq-lbl{color:#fff;}

/* ═══ STUDENT ICON CARDS (for entry page) ═══ */
.stu-grid{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:10px; margin-bottom:14px;
}
@media(max-width:600px){.stu-grid{grid-template-columns:repeat(3,1fr);}}
@media(max-width:400px){.stu-grid{grid-template-columns:repeat(2,1fr);}}

.stu-icon-btn{
  background:var(--white);
  border:2.5px solid var(--lgray);
  border-radius:16px;
  padding:14px 8px 10px;
  text-align:center;cursor:pointer;
  transition:all .2s ease;
  box-shadow:var(--sh);
  position:relative;
}
.stu-icon-btn:hover{border-color:var(--g2);box-shadow:var(--sh2);transform:translateY(-2px);}
.stu-icon-btn.done{background:linear-gradient(145deg,#e6f4ee,#c5e8d8);border-color:var(--g2);}
.stu-icon-btn.selected{background:linear-gradient(145deg,var(--g1),var(--g2));border-color:var(--g1);}
.stu-avatar{
  width:52px;height:52px;border-radius:12px;
  background:linear-gradient(145deg,var(--g1),var(--g3));
  display:flex;align-items:center;justify-content:center;
  margin:0 auto 7px;font-size:1.5rem;color:#fff;
  box-shadow:0 3px 10px rgba(10,92,60,.25);
}
.stu-icon-btn.done .stu-avatar{background:linear-gradient(145deg,#16a34a,#15803d);}
.stu-icon-btn.selected .stu-avatar{background:rgba(255,255,255,.25);}
.stu-nm{font-size:.8rem;font-weight:700;color:var(--txt);line-height:1.3;margin-bottom:2px;}
.stu-fn{font-size:.68rem;color:var(--gray);line-height:1.2;}
.stu-icon-btn.selected .stu-nm,
.stu-icon-btn.selected .stu-fn{color:#fff;}
.done-badge{
  position:absolute;top:5px;left:5px;
  background:#16a34a;color:#fff;border-radius:8px;
  font-size:.6rem;padding:1px 6px;font-weight:700;
}

/* ── PAGE CARD ── */
.pc{background:var(--white);border-radius:var(--rad);
    padding:18px;box-shadow:var(--sh);margin-bottom:12px;
    border:1px solid rgba(10,92,60,.06);animation:fu .3s ease;}
@keyframes fu{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

/* ── SECTION HEADER ── */
.sh2{background:linear-gradient(135deg,var(--g1),var(--g2));
  border-radius:var(--rad);padding:13px 18px;margin-bottom:14px;
  display:flex;align-items:center;gap:10px;}
.sh2 .si{font-size:1.5rem;}
.sh2 .st{color:#fff;font-size:1rem;font-weight:700;}
.sh2 .ss{color:rgba(255,255,255,.78);font-size:.75rem;}

/* ── METRICS ── */
.mets{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;}
@media(max-width:600px){.mets{grid-template-columns:repeat(2,1fr);}}
.mc{background:var(--white);border-radius:var(--rad);padding:14px 10px;
    text-align:center;box-shadow:var(--sh);border:1px solid rgba(10,92,60,.07);
    position:relative;overflow:hidden;transition:transform .2s;}
.mc:hover{transform:translateY(-3px);box-shadow:var(--sh2);}
.mc::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,var(--g1),var(--gold));}
.mi{font-size:1.6rem;display:block;margin-bottom:3px;}
.mv{font-size:1.9rem;font-weight:800;color:var(--g1);line-height:1;}
.ml{font-size:.75rem;color:var(--gray);margin-top:2px;}

/* ── GRADE CHIPS ── */
.ch{display:inline-block;padding:2px 10px;border-radius:20px;
    font-size:.78rem;font-weight:700;}
.gn{background:#d1fae5;color:#065f46;}
.gp{background:#ede9fe;color:#4c1d95;}
.gb{background:#dbeafe;color:#1e40af;}
.gy{background:#fef3c7;color:#92400e;}
.go{background:#ffedd5;color:#9a3412;}
.gr{background:#fee2e2;color:#991b1b;}
.gg{background:#f3f4f6;color:#374151;}

/* ── STATUS ── */
.sp{background:#fef3c7;color:#92400e;border-radius:20px;padding:2px 10px;
    font-size:.75rem;font-weight:700;}
.so{background:#d1fae5;color:#065f46;border-radius:20px;padding:2px 10px;
    font-size:.75rem;font-weight:700;}
.sr{background:#fee2e2;color:#991b1b;border-radius:20px;padding:2px 10px;
    font-size:.75rem;font-weight:700;}

/* ── LEAVE CARD ── */
.lc{background:var(--white);border-right:4px solid var(--gold);
    border-radius:var(--rad);padding:12px 16px;margin-bottom:8px;box-shadow:var(--sh);}

/* ── NOTIF ── */
.ni{background:linear-gradient(135deg,#f0f9ff,#e0f2fe);
    border-right:4px solid #0369a1;border-radius:var(--rads);
    padding:10px 14px;margin-bottom:8px;}
.ni h5{color:#0369a1!important;margin:0 0 3px!important;font-size:.88rem!important;}
.ni p{color:var(--txt);margin:0;font-size:.80rem;}
.ni small{color:var(--gray);font-size:.70rem;}

/* ── PROGRESS ── */
.pw{background:#e5e7eb;border-radius:10px;overflow:hidden;height:16px;}
.pb2{height:100%;background:linear-gradient(90deg,var(--g1),var(--gold));
    border-radius:10px;display:flex;align-items:center;justify-content:center;}
.pt{color:#fff;font-size:.68rem;font-weight:700;}

/* ── TROPHY ── */
.tc{background:linear-gradient(145deg,#fffdf0,#fdf3d0);
    border:2px solid rgba(201,152,42,.22);border-radius:18px;
    padding:18px 12px;text-align:center;position:relative;overflow:hidden;
    box-shadow:0 5px 24px rgba(201,152,42,.12);transition:transform .25s,box-shadow .25s;}
.tc::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;
  background:linear-gradient(90deg,var(--gold),var(--gold2),var(--gold));}
.tc:hover{transform:translateY(-5px);box-shadow:0 14px 40px rgba(201,152,42,.22);}
.tm{font-size:2.4rem;display:block;margin-bottom:5px;}
.tn{font-size:.95rem;font-weight:700;color:var(--dark);margin:4px 0 2px;}
.tsb{font-size:.74rem;color:var(--gray);margin:2px 0;}
.ts{display:inline-block;background:linear-gradient(135deg,var(--g1),var(--g2));
    color:#fff;border-radius:20px;padding:3px 14px;font-size:.78rem;
    font-weight:700;margin-top:7px;box-shadow:0 2px 8px rgba(10,92,60,.25);}

/* ── ADMIN ACTION ROW ── */
.arow{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;}
.abtn{padding:4px 12px;border-radius:8px;font-size:.72rem;
      font-weight:700;cursor:pointer;border:none;}
.abtn-edit{background:#dbeafe;color:#1e40af;}
.abtn-del{background:#fee2e2;color:#991b1b;}

/* ── BUTTONS ── */
.stButton>button{
  background:linear-gradient(135deg,var(--g1),var(--g2))!important;
  color:#fff!important;border:none!important;
  border-radius:var(--rads)!important;
  padding:8px 18px!important;font-weight:700!important;
  font-size:.85rem!important;
  box-shadow:0 2px 10px rgba(10,92,60,.22)!important;
  transition:all .2s!important;
}
.stButton>button:hover{
  transform:translateY(-1px)!important;
  box-shadow:0 5px 18px rgba(10,92,60,.32)!important;
  background:linear-gradient(135deg,var(--dark),var(--g1))!important;
}

/* ── INPUTS ── */
.stTextInput>div>div>input,
.stTextArea textarea,
.stNumberInput input,
.stDateInput input,
.stTimeInput input{
  border-radius:var(--rads)!important;
  border:1.5px solid #cdddd6!important;
  direction:rtl!important;
  font-size:.88rem!important;
}
.stTextInput>div>div>input:focus,.stTextArea textarea:focus{
  border-color:var(--g2)!important;
  box-shadow:0 0 0 3px rgba(13,122,82,.12)!important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{
  background:var(--g4)!important;border-radius:var(--rad)!important;
  padding:4px!important;gap:4px!important;}
.stTabs [data-baseweb="tab"]{border-radius:var(--rads)!important;border:none!important;
  color:var(--gray)!important;font-weight:700!important;font-size:.82rem!important;}
.stTabs [aria-selected="true"]{
  background:linear-gradient(135deg,var(--g1),var(--g2))!important;
  color:#fff!important;box-shadow:0 2px 8px rgba(10,92,60,.25)!important;}

/* ── ALERTS ── */
.stSuccess>div{background:#f0fdf4!important;border-color:#86efac!important;
  border-radius:var(--rads)!important;color:#14532d!important;}
.stError>div{background:#fff1f2!important;border-color:#fca5a5!important;
  border-radius:var(--rads)!important;}
.stWarning>div{background:#fffbeb!important;border-color:#fcd34d!important;
  border-radius:var(--rads)!important;}
.stInfo>div{background:#f0f9ff!important;border-color:#93c5fd!important;
  border-radius:var(--rads)!important;}

/* ── DATAFRAME ── */
.stDataFrame{border-radius:var(--rads)!important;overflow:hidden!important;
  box-shadow:var(--sh)!important;}
[data-testid="stDataFrameResizable"] th{background:var(--g1)!important;color:#fff!important;}

/* ── EXPANDER ── */
.streamlit-expanderHeader{background:linear-gradient(135deg,#f0f8f4,#e4f2eb)!important;
  border-radius:var(--rads)!important;border:1px solid rgba(10,92,60,.12)!important;}

/* ── BOTTOM PAD ── */
.bpad{height:80px;}

/* ── LOGIN ── */
.lbox{background:#fff;border-radius:20px;padding:30px 24px;
  box-shadow:0 20px 60px rgba(0,0,0,.22);max-width:400px;margin:0 auto;}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════
# LOGIN
# ════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1.3,1])
    with col:
        st.markdown("""
        <div class="lbox">
          <div style="text-align:center;margin-bottom:18px">
            <span style="font-size:3.5rem">🕌</span>
            <h2 style="color:#0a5c3c;margin:6px 0 2px;font-size:1.25rem">
              جامعہ ملیہ اسلامیہ</h2>
            <p style="color:#c9982a;margin:0;font-size:.82rem">
              فیصل آباد — اسمارٹ تعلیمی پورٹل</p>
          </div>
        </div>""", unsafe_allow_html=True)
        with st.form("lf"):
            un = st.text_input("👤 صارف نام")
            pw = st.text_input("🔑 پاسورڈ", type="password")
            sub = st.form_submit_button("▶ لاگ ان کریں", use_container_width=True)
        if sub:
            if un.strip() and pw:
                u = rd("SELECT * FROM users WHERE username=? AND is_active=1",
                       (un.strip(),), one=True)
                if u and chk(pw, u['password']):
                    st.session_state.logged_in = True
                    st.session_state.username  = un.strip()
                    st.session_state.role      = u['role']
                    st.session_state.page      = "home"
                    audit(un.strip(), "Login")
                    st.rerun()
                else:
                    st.error("❌ غلط نام یا پاسورڈ")
            else:
                st.warning("نام اور پاسورڈ ضروری ہیں")
        st.markdown("<p style='text-align:center;color:#9ca3af;font-size:.72rem'>"
                    "🔒 ڈیفالٹ: admin / jamia123</p>", unsafe_allow_html=True)
    st.stop()

# ════════════════════════════════════════════
# TOP BAR
# ════════════════════════════════════════════
IS_ADMIN = st.session_state.role == "admin"
pg = st.session_state.page

st.markdown(f"""
<div class="topbar">
  <div class="tb-brand">
    <span class="tb-icon">🕌</span>
    <div>
      <div class="tb-name">جامعہ ملیہ اسلامیہ فیصل آباد</div>
      <div class="tb-sub">Smart ERP v4.0</div>
    </div>
  </div>
  <div class="tb-user">
    {'🛡️ ایڈمن' if IS_ADMIN else '👩‍🏫 استاد'} — {st.session_state.username}
  </div>
</div>""", unsafe_allow_html=True)

st.markdown("<div class='mw'>", unsafe_allow_html=True)

# ════════════════════════════════════════════
# NAVIGATION — Square Icon Buttons
# ════════════════════════════════════════════
if IS_ADMIN:
    NAV = [
        ("home","📊","ڈیش بورڈ"),("daily","📋","یومیہ رپورٹ"),
        ("exams","🎓","امتحانات"),("result","📜","رزلٹ"),
        ("para","📖","پارہ"),("t_att_a","🕒","حاضری"),
        ("leaves","🏛️","رخصت"),("users","👥","یوزرز"),
        ("timetable","📚","ٹائم ٹیبل"),("monitor","📋","نگرانی"),
        ("notifs","📢","اعلانات"),("analytics","📈","تجزیہ"),
        ("best","🏆","بہترین"),("password","🔑","پاسورڈ"),
        ("backup","⚙️","بیک اپ"),
    ]
else:
    NAV = [
        ("home","🏠","مرکزی"),("entry","📝","سبق"),
        ("t_exam","🎓","امتحان"),("t_leave","📩","رخصت"),
        ("t_att","🕒","حاضری"),("t_tt","📚","ٹائم ٹیبل"),
        ("notifs","📢","اعلانات"),("password","🔑","پاسورڈ"),
    ]

CPR = 5 if IS_ADMIN else 4
rows = [NAV[i:i+CPR] for i in range(0,len(NAV),CPR)]
for row in rows:
    cols = st.columns(len(row))
    for col,(pid,ico,lbl) in zip(cols,row):
        with col:
            if st.button(f"{ico}\n{lbl}", key=f"n_{pid}", use_container_width=True):
                st.session_state.page = pid
                st.session_state.sel_student = None
                st.rerun()

# Logout
lc = st.columns([5,1])[1]
with lc:
    if st.button("🚪 آؤٹ", use_container_width=True):
        audit(st.session_state.username,"Logout")
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

st.markdown("---")
pg = st.session_state.page

# ════════════════════════════════════════════
# HELPERS UI
# ════════════════════════════════════════════
def sh(icon, title, sub=""):
    st.markdown(f"""
    <div class="sh2">
      <span class="si">{icon}</span>
      <div><div class="st">{title}</div>
      {f'<div class="ss">{sub}</div>' if sub else ''}</div>
    </div>""", unsafe_allow_html=True)

def chip(g):
    c = GCLS.get(g,"gg")
    return f"<span class='ch {c}'>{g}</span>"

# ════════════════════════════════════════════
# ████  ADMIN DASHBOARD  ████
# ════════════════════════════════════════════
if pg=="home" and IS_ADMIN:
    sh("📊","ایڈمن ڈیش بورڈ","جامعہ ملیہ کا مکمل جائزہ")
    ts=sc("SELECT COUNT(*) FROM students WHERE is_active=1")
    tt=sc("SELECT COUNT(*) FROM users WHERE role='teacher' AND is_active=1")
    ta=sc("SELECT COUNT(*) FROM teacher_attendance WHERE att_date=?",(str(date.today()),))
    pe=sc("SELECT COUNT(*) FROM exams WHERE status='پینڈنگ'")
    pl=sc("SELECT COUNT(*) FROM leave_requests WHERE status='پینڈنگ'")
    hr=sc("SELECT COUNT(*) FROM hifz_records")+sc("SELECT COUNT(*) FROM qaida_records")
    st.markdown(f"""
    <div class="mets">
      <div class="mc"><span class="mi">👨‍🎓</span><div class="mv">{ts}</div><div class="ml">کل طلباء</div></div>
      <div class="mc"><span class="mi">👩‍🏫</span><div class="mv">{tt}</div><div class="ml">اساتذہ</div></div>
      <div class="mc"><span class="mi">✅</span><div class="mv">{ta}</div><div class="ml">آج حاضر</div></div>
      <div class="mc"><span class="mi">📋</span><div class="mv">{hr}</div><div class="ml">کل ریکارڈز</div></div>
    </div>""",unsafe_allow_html=True)
    if pl>0: st.warning(f"⏳ {pl} رخصت درخواستیں پینڈنگ")
    if pe>0: st.info(f"🎓 {pe} امتحان پینڈنگ")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("<div class='pc'>",unsafe_allow_html=True)
        st.markdown("**📅 آج کی اساتذہ حاضری**")
        rows=rd("SELECT username as استاد,arrival as آمد,departure as رخصت FROM teacher_attendance WHERE att_date=?",(str(date.today()),))
        if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        else: st.caption("ابھی کوئی حاضری نہیں")
        st.markdown("</div>",unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='pc'>",unsafe_allow_html=True)
        st.markdown("**📊 شعبہ وار طلباء**")
        dd=rd("SELECT dept,COUNT(*) as cnt FROM students WHERE is_active=1 GROUP BY dept")
        for d in dd:
            p=int((d['cnt']/(ts or 1))*100)
            st.markdown(f"""<div style="margin-bottom:7px">
              <div style="display:flex;justify-content:space-between;font-size:.82rem">
                <b>{d['dept']}</b><span style="color:var(--g1)">{d['cnt']}</span></div>
              <div class="pw"><div class="pb2" style="width:{p}%">
                <span class="pt">{p}%</span></div></div></div>""",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# ════════════════════════════════════════════
# ████  DAILY REPORT  ████
# ════════════════════════════════════════════
elif pg=="daily" and IS_ADMIN:
    sh("📋","یومیہ تعلیمی رپورٹ","تمام شعبوں کا روزانہ ریکارڈ")
    c1,c2,c3,c4=st.columns(4)
    d1=c1.date_input("از",date.today().replace(day=1))
    d2=c2.date_input("تا",date.today())
    ds=c3.selectbox("شعبہ",["تمام"]+DEPTS)
    tl=["تمام"]+[r['username'] for r in rd("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
    ts2=c4.selectbox("استاد",tl)
    tf="" if ts2=="تمام" else f" AND h.teacher='{ts2}'"
    combined=[]
    if ds in["تمام","حفظ"]:
        rows=rd(f"""SELECT h.id,h.rec_date as تاریخ,s.name as نام,s.father_name as والد,
            s.roll_no as رول,h.teacher as استاد,'حفظ' as شعبہ,h.sabaq as سبق,
            h.sabaq_lines as ستر,h.sq_text as سبقی,h.sq_mistakes as 'سبقی غلطی',
            h.manzil_text as منزل,h.manzil_mistakes as 'منزل غلطی',
            h.attendance as حاضری,h.cleanliness as صفائی,h.grade as درجہ
            FROM hifz_records h JOIN students s ON h.student_id=s.id
            WHERE h.rec_date BETWEEN ? AND ?{tf} ORDER BY h.rec_date DESC""",(str(d1),str(d2)))
        combined.extend(rows)
    if ds in["تمام","قاعدہ"]:
        tf2="" if ts2=="تمام" else f" AND q.teacher='{ts2}'"
        rows=rd(f"""SELECT q.id,q.rec_date as تاریخ,s.name as نام,s.father_name as والد,
            s.roll_no as رول,q.teacher as استاد,'قاعدہ' as شعبہ,
            q.lesson_no as سبق,q.total_lines as لائنیں,
            '' as سبقی,0 as 'سبقی غلطی','' as منزل,0 as 'منزل غلطی',
            q.attendance as حاضری,q.cleanliness as صفائی,'' as درجہ
            FROM qaida_records q JOIN students s ON q.student_id=s.id
            WHERE q.rec_date BETWEEN ? AND ?{tf2} ORDER BY q.rec_date DESC""",(str(d1),str(d2)))
        combined.extend(rows)
    if ds in["تمام","درسِ نظامی","عصری تعلیم"]:
        df2="" if ds=="تمام" else f" AND g.dept='{ds}'"
        tf3="" if ts2=="تمام" else f" AND g.teacher='{ts2}'"
        rows=rd(f"""SELECT g.id,g.rec_date as تاریخ,s.name as نام,s.father_name as والد,
            s.roll_no as رول,g.teacher as استاد,g.dept as شعبہ,
            g.subject as سبق,0 as ستر,'' as سبقی,0 as 'سبقی غلطی',
            '' as منزل,0 as 'منزل غلطی',
            g.attendance as حاضری,g.cleanliness as صفائی,g.performance as درجہ
            FROM general_records g JOIN students s ON g.student_id=s.id
            WHERE g.rec_date BETWEEN ? AND ?{df2}{tf3} ORDER BY g.rec_date DESC""",(str(d1),str(d2)))
        combined.extend(rows)
    if combined:
        df=pd.DataFrame(combined)
        st.success(f"✅ کل {len(df)} ریکارڈ")
        if IS_ADMIN:
            st.info("کسی ریکارڈ کو حذف کرنے کے لیے ID لکھیں:")
            with st.form("del_rec"):
                rc1,rc2,rc3=st.columns(3)
                del_tbl=rc1.selectbox("ٹیبل",["hifz_records","qaida_records","general_records"])
                del_id=rc2.number_input("ریکارڈ ID",1,step=1)
                if rc3.form_submit_button("🗑️ حذف"):
                    wr(f"DELETE FROM {del_tbl} WHERE id=?",(int(del_id),))
                    st.success("✅ حذف!"); st.rerun()
        st.dataframe(df,use_container_width=True,hide_index=True)
        c1,c2=st.columns(2)
        c1.download_button("📥 CSV",to_csv(df),"daily.csv","text/csv")
        c2.download_button("📥 HTML",html_rep(df,"یومیہ تعلیمی رپورٹ",f"{d1} تا {d2}"),
                           "daily.html","text/html")
    else: st.info("کوئی ریکارڈ نہیں")

# ════════════════════════════════════════════
# ████  EXAMS  ████
# ════════════════════════════════════════════
elif pg=="exams" and IS_ADMIN:
    sh("🎓","امتحانی نظام")
    tab1,tab2=st.tabs(["⏳ پینڈنگ","✅ مکمل"])
    with tab1:
        pend=rd("""SELECT e.*,s.name,s.father_name,s.roll_no
                   FROM exams e JOIN students s ON e.student_id=s.id
                   WHERE e.status='پینڈنگ' ORDER BY e.created_at DESC""")
        if not pend: st.success("✅ کوئی پینڈنگ نہیں")
        for ex in pend:
            with st.expander(f"👤 {ex['name']} | {ex['dept']} | {ex['exam_type']}"):
                c1,c2,c3=st.columns(3)
                c1.info(f"📅 شروع: {ex['start_date']}")
                c2.info(f"📅 ختم: {ex.get('end_date','—')}")
                c3.info(f"🗓️ دن: {ex.get('total_days','—')}")
                if ex.get('from_para'): st.info(f"📖 پارہ {ex['from_para']} تا {ex['to_para']}")
                if ex.get('book_name'): st.info(f"📚 {ex['book_name']} | {ex.get('amount_read','')}")
                qc=st.columns(5)
                qs=[qc[i].number_input(f"س{i+1}",0,20,0,key=f"q{i}_{ex['id']}") for i in range(5)]
                tot=sum(qs); g=exam_gr(tot)
                st.markdown(f"**کل:** {tot}/100 &nbsp; {chip(g)}",unsafe_allow_html=True)
                rc1,rc2=st.columns(2)
                if rc1.button("✅ نتیجہ محفوظ",key=f"ex_{ex['id']}"):
                    wr("""UPDATE exams SET q1=?,q2=?,q3=?,q4=?,q5=?,total=?,grade=?,
                           status='مکمل',end_date=? WHERE id=?""",
                       (*qs,tot,g,str(date.today()),ex['id']))
                    if g!="ناکام":
                        sid=ex['student_id']
                        if ex.get('from_para') and int(ex['from_para'])>0:
                            for p in range(int(ex['from_para']),int(ex['to_para'])+1):
                                if not rd("SELECT id FROM passed_paras WHERE student_id=? AND para_no=?",(sid,p),one=True):
                                    wr("INSERT INTO passed_paras(student_id,para_no,passed_date,exam_type,grade,marks)VALUES(?,?,?,?,?,?)",
                                       (sid,p,str(date.today()),ex['exam_type'],g,tot))
                        if ex.get('book_name'):
                            if not rd("SELECT id FROM passed_paras WHERE student_id=? AND book_name=?",(sid,ex['book_name']),one=True):
                                wr("INSERT INTO passed_paras(student_id,book_name,passed_date,exam_type,grade,marks)VALUES(?,?,?,?,?,?)",
                                   (sid,ex['book_name'],str(date.today()),ex['exam_type'],g,tot))
                    audit(st.session_state.username,"Exam Cleared",ex['id'])
                    st.success("✅ محفوظ!"); st.rerun()
                if rc2.button("🗑️ حذف",key=f"exd_{ex['id']}"):
                    wr("DELETE FROM exams WHERE id=?",(ex['id'],)); st.rerun()
    with tab2:
        done=rd("""SELECT e.id,s.name as نام,s.father_name as والد,e.dept as شعبہ,
                   e.exam_type as امتحان,e.total as نمبر,e.grade as گریڈ,e.end_date as تاریخ
                   FROM exams e JOIN students s ON e.student_id=s.id
                   WHERE e.status='مکمل' ORDER BY e.end_date DESC""")
        if done:
            df=pd.DataFrame(done)
            st.dataframe(df,use_container_width=True,hide_index=True)
            if IS_ADMIN:
                with st.form("del_exam"):
                    di=st.number_input("حذف کریں ID",1,step=1)
                    if st.form_submit_button("🗑️ حذف"):
                        wr("DELETE FROM exams WHERE id=?",(int(di),)); st.success("✅"); st.rerun()
            st.download_button("📥 CSV",to_csv(df),"exams.csv")

# ════════════════════════════════════════════
# ████  RESULT CARD  ████
# ════════════════════════════════════════════
elif pg=="result" and IS_ADMIN:
    sh("📜","ماہانہ رزلٹ کارڈ")
    studs=rd("SELECT id,name,father_name,roll_no,dept FROM students WHERE is_active=1 ORDER BY name")
    if not studs: st.warning("کوئی طالب علم نہیں")
    else:
        names=[f"{s['name']} ولد {s['father_name']} ({s['dept']})" for s in studs]
        c1,c2,c3=st.columns([3,1,1])
        idx=c1.selectbox("طالب علم",range(len(names)),format_func=lambda i:names[i])
        s=studs[idx]
        d1=c2.date_input("از",date.today().replace(day=1))
        d2=c3.date_input("تا",date.today())
        rows=[]
        if s['dept']=="حفظ":
            rows=rd("""SELECT rec_date as تاریخ,attendance as حاضری,sabaq as سبق,
                      sabaq_lines as ستر,sq_text as سبقی,sq_mistakes as 'سبقی غلطی',
                      manzil_text as منزل,manzil_mistakes as 'منزل غلطی',
                      cleanliness as صفائی,grade as درجہ
                      FROM hifz_records WHERE student_id=? AND rec_date BETWEEN ? AND ?
                      ORDER BY rec_date""",(s['id'],str(d1),str(d2)))
        elif s['dept']=="قاعدہ":
            rows=rd("""SELECT rec_date as تاریخ,attendance as حاضری,lesson_no as سبق,
                      total_lines as لائنیں,cleanliness as صفائی,note as نوٹ
                      FROM qaida_records WHERE student_id=? AND rec_date BETWEEN ? AND ?
                      ORDER BY rec_date""",(s['id'],str(d1),str(d2)))
        else:
            rows=rd("""SELECT rec_date as تاریخ,attendance as حاضری,subject as مضمون,
                      lesson as سبق,performance as کارکردگی,cleanliness as صفائی
                      FROM general_records WHERE student_id=? AND dept=?
                      AND rec_date BETWEEN ? AND ? ORDER BY rec_date""",
                    (s['id'],s['dept'],str(d1),str(d2)))
        if rows:
            df=pd.DataFrame(rows)
            st.dataframe(df,use_container_width=True,hide_index=True)
            sub=f"{s['name']} ولد {s['father_name']} | {d1} تا {d2}"
            c1,c2=st.columns(2)
            c1.download_button("📥 HTML",html_rep(df,"ماہانہ رزلٹ کارڈ",sub),
                               f"result_{s['name']}.html","text/html")
            c2.download_button("📥 CSV",to_csv(df),f"result_{s['name']}.csv")
        else: st.info("کوئی ریکارڈ نہیں")

# ════════════════════════════════════════════
# ████  PARA REPORT  ████
# ════════════════════════════════════════════
elif pg=="para" and IS_ADMIN:
    sh("📖","پارہ تعلیمی رپورٹ","حفظ کی پیشرفت")
    studs=rd("SELECT id,name,father_name FROM students WHERE dept='حفظ' AND is_active=1 ORDER BY name")
    if not studs: st.warning("کوئی حفظ کا طالب علم نہیں")
    else:
        names=[f"{s['name']} ولد {s['father_name']}" for s in studs]
        idx=st.selectbox("طالب علم",range(len(names)),format_func=lambda i:names[i])
        s=studs[idx]
        passed=rd("""SELECT id,para_no as 'پارہ نمبر',passed_date as 'تاریخ پاس',
                    exam_type as امتحان,grade as گریڈ,marks as نمبر
                    FROM passed_paras WHERE student_id=? AND para_no>0
                    ORDER BY para_no""",(s['id'],))
        cnt=len(passed); pct=int((cnt/30)*100)
        st.markdown(f"""<div class="pc">
          <div style="font-size:.88rem;font-weight:700;color:var(--g1);margin-bottom:6px">
            قرآن مجید: {cnt}/30 پارے</div>
          <div class="pw"><div class="pb2" style="width:{pct}%">
            <span class="pt">{pct}%</span></div></div>
          <div style="font-size:.72rem;color:var(--gray);margin-top:3px">{30-cnt} پارے باقی</div>
        </div>""",unsafe_allow_html=True)
        if passed:
            df=pd.DataFrame(passed)
            st.dataframe(df,use_container_width=True,hide_index=True)
            if IS_ADMIN:
                with st.form("del_para"):
                    di=st.number_input("حذف ID",1,step=1)
                    if st.form_submit_button("🗑️ حذف"):
                        wr("DELETE FROM passed_paras WHERE id=?",(int(di),)); st.success("✅"); st.rerun()
            st.download_button("📥 رپورٹ",html_rep(df,"پارہ تعلیمی رپورٹ",
                               f"{s['name']} ولد {s['father_name']}"),
                               f"para_{s['name']}.html","text/html")
        else: st.info("کوئی پاس شدہ پارہ نہیں")

# ════════════════════════════════════════════
# ████  TEACHER ATTENDANCE ADMIN  ████
# ════════════════════════════════════════════
elif pg=="t_att_a" and IS_ADMIN:
    sh("🕒","اساتذہ حاضری")
    tab1,tab2=st.tabs(["📋 ریکارڈ","✏️ درج/ترمیم"])
    with tab1:
        c1,c2,c3=st.columns(3)
        fd1=c1.date_input("از",date.today().replace(day=1))
        fd2=c2.date_input("تا",date.today())
        tl=["تمام"]+[r['username'] for r in rd("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
        ft=c3.selectbox("استاد",tl)
        tf="" if ft=="تمام" else f" AND username='{ft}'"
        rows=rd(f"""SELECT id,username as استاد,att_date as تاریخ,
                   arrival as آمد,departure as رخصت
                   FROM teacher_attendance WHERE att_date BETWEEN ? AND ?{tf}
                   ORDER BY att_date DESC""",(str(fd1),str(fd2)))
        if rows:
            df=pd.DataFrame(rows)
            st.dataframe(df,use_container_width=True,hide_index=True)
            with st.form("del_att"):
                di=st.number_input("حذف ID",1,step=1)
                if st.form_submit_button("🗑️ حذف"):
                    wr("DELETE FROM teacher_attendance WHERE id=?",(int(di),)); st.success("✅"); st.rerun()
            st.download_button("📥 CSV",to_csv(df),"att.csv")
        else: st.info("کوئی ریکارڈ نہیں")
    with tab2:
        with st.form("adm_att"):
            c1,c2,c3,c4=st.columns(4)
            tl2=[r['username'] for r in rd("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
            at=c1.selectbox("استاد",tl2)
            ad=c2.date_input("تاریخ",date.today())
            arr=c3.text_input("آمد","09:00 AM")
            dep=c4.text_input("رخصت","03:00 PM")
            if st.form_submit_button("💾 محفوظ"):
                ex=rd("SELECT id FROM teacher_attendance WHERE username=? AND att_date=?",(at,str(ad)),one=True)
                if ex: wr("UPDATE teacher_attendance SET arrival=?,departure=? WHERE username=? AND att_date=?",(arr,dep,at,str(ad)))
                else: wr("INSERT INTO teacher_attendance(username,att_date,arrival,departure)VALUES(?,?,?,?)",(at,str(ad),arr,dep))
                st.success("✅ محفوظ!"); st.rerun()

# ════════════════════════════════════════════
# ████  LEAVES ADMIN  ████
# ════════════════════════════════════════════
elif pg=="leaves" and IS_ADMIN:
    sh("🏛️","رخصت کی منظوری")
    tab1,tab2=st.tabs(["⏳ پینڈنگ","📜 تمام"])
    with tab1:
        pend=rd("SELECT * FROM leave_requests WHERE status='پینڈنگ' ORDER BY created_at DESC")
        if not pend: st.success("✅ کوئی پینڈنگ نہیں")
        for lv in pend:
            st.markdown(f"""<div class="lc">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span><b>👤 {lv['username']}</b> &nbsp; <span class="sp">{lv['leave_type']}</span></span>
                <span style="font-size:.78rem;color:var(--gray)">📅{lv['start_date']}|{lv['days']}دن</span>
              </div>
              <p style="font-size:.80rem;color:#4b5563;margin:5px 0 0">وجہ: {lv['reason'][:120]}</p>
            </div>""",unsafe_allow_html=True)
            c1,c2,c3=st.columns(3)
            if c1.button("✅ منظور",key=f"ap_{lv['id']}",use_container_width=True):
                wr("UPDATE leave_requests SET status='منظور' WHERE id=?",(lv['id'],)); st.rerun()
            if c2.button("❌ مسترد",key=f"rj_{lv['id']}",use_container_width=True):
                wr("UPDATE leave_requests SET status='مسترد' WHERE id=?",(lv['id'],)); st.rerun()
            if c3.button("🗑️ حذف",key=f"dl_{lv['id']}",use_container_width=True):
                wr("DELETE FROM leave_requests WHERE id=?",(lv['id'],)); st.rerun()
    with tab2:
        all_lv=rd("""SELECT id,username as استاد,leave_type as نوعیت,
                    start_date as تاریخ,days as دن,status as حالت
                    FROM leave_requests ORDER BY created_at DESC""")
        if all_lv:
            df=pd.DataFrame(all_lv)
            st.dataframe(df,use_container_width=True,hide_index=True)
            with st.form("del_lv"):
                di=st.number_input("حذف ID",1,step=1)
                if st.form_submit_button("🗑️ حذف"):
                    wr("DELETE FROM leave_requests WHERE id=?",(int(di),)); st.success("✅"); st.rerun()
            st.download_button("📥 CSV",to_csv(df),"leaves.csv")

# ════════════════════════════════════════════
# ████  USER MANAGEMENT  ████
# ════════════════════════════════════════════
elif pg=="users" and IS_ADMIN:
    sh("👥","یوزر مینجمنٹ","اساتذہ اور طلباء")
    tab1,tab2=st.tabs(["👩‍🏫 اساتذہ","👨‍🎓 طلبہ"])

    with tab1:
        rows=rd("""SELECT id,username as نام,dept as شعبہ,phone as فون,
                  id_card as شناختی,joining_date as شمولیت,is_active as فعال
                  FROM users WHERE role='teacher' ORDER BY username""")
        if rows:
            df=pd.DataFrame(rows)
            edited=st.data_editor(df,use_container_width=True,num_rows="dynamic",
                                  key="te",hide_index=True)
            c1,c2=st.columns(2)
            if c1.button("💾 اساتذہ محفوظ کریں"):
                for _,row in edited.iterrows():
                    if pd.notna(row.get('id')):
                        wr("UPDATE users SET dept=?,phone=?,id_card=?,joining_date=?,is_active=? WHERE id=?",
                           (str(row.get('شعبہ','')),str(row.get('فون','')),
                            str(row.get('شناختی','')),str(row.get('شمولیت','')),
                            int(row.get('فعال',1)),int(row['id'])))
                st.success("✅ محفوظ!"); st.rerun()
            if c2.button("🗑️ استاد حذف (ID سے)"):
                st.session_state['del_t']=True
        if st.session_state.get('del_t'):
            with st.form("del_t_f"):
                di=st.number_input("استاد ID",1,step=1)
                if st.form_submit_button("🗑️ حذف کریں"):
                    wr("DELETE FROM users WHERE id=? AND role='teacher'",(int(di),))
                    st.success("✅ حذف!"); st.session_state['del_t']=False; st.rerun()

        with st.expander("➕ نیا استاد"):
            with st.form("add_t"):
                c1,c2=st.columns(2)
                tn=c1.text_input("نام*"); tp=c2.text_input("پاسورڈ*",type="password")
                td=c1.selectbox("شعبہ",DEPTS); tph=c2.text_input("فون")
                tic=c1.text_input("شناختی کارڈ"); tjd=c2.date_input("شمولیت",date.today())
                if st.form_submit_button("✅ رجسٹر"):
                    if tn.strip() and tp:
                        try:
                            wr("INSERT INTO users(username,password,role,dept,phone,id_card,joining_date)VALUES(?,?,?,?,?,?,?)",
                               (tn.strip(),hp(tp),'teacher',td,tph,tic,str(tjd)))
                            audit(st.session_state.username,"Teacher Added",tn)
                            st.success(f"✅ {tn} رجسٹر!"); st.rerun()
                        except: st.error("یہ نام پہلے سے موجود ہے")
                    else: st.error("نام اور پاسورڈ ضروری")

    with tab2:
        rows=rd("""SELECT id,name as نام,father_name as والد,roll_no as رول,
                  dept as شعبہ,teacher as استاد,phone as فون,is_active as فعال
                  FROM students ORDER BY name""")
        if rows:
            df=pd.DataFrame(rows)
            edited=st.data_editor(df,use_container_width=True,num_rows="dynamic",
                                  key="se",hide_index=True)
            c1,c2=st.columns(2)
            if c1.button("💾 طلبہ محفوظ کریں"):
                for _,row in edited.iterrows():
                    if pd.notna(row.get('id')):
                        wr("UPDATE students SET name=?,father_name=?,roll_no=?,dept=?,teacher=?,phone=?,is_active=? WHERE id=?",
                           (str(row.get('نام','')),str(row.get('والد','')),
                            str(row.get('رول','')),str(row.get('شعبہ','')),
                            str(row.get('استاد','')),str(row.get('فون','')),
                            int(row.get('فعال',1)),int(row['id'])))
                st.success("✅ محفوظ!"); st.rerun()
            if c2.button("🗑️ طالب علم حذف (ID سے)"):
                st.session_state['del_s']=True
        if st.session_state.get('del_s'):
            with st.form("del_s_f"):
                di=st.number_input("طالب علم ID",1,step=1)
                if st.form_submit_button("🗑️ حذف کریں"):
                    wr("DELETE FROM students WHERE id=?",(int(di),))
                    st.success("✅ حذف!"); st.session_state['del_s']=False; st.rerun()

        with st.expander("➕ نیا طالب علم"):
            with st.form("add_s"):
                c1,c2=st.columns(2)
                sn=c1.text_input("نام*"); sf=c2.text_input("والد کا نام*")
                sm=c1.text_input("والدہ"); sr=c2.text_input("رول نمبر")
                sd=c1.date_input("پیدائش",date.today()-timedelta(days=3650))
                sa=c2.date_input("داخلہ",date.today())
                sdept=c1.selectbox("شعبہ*",DEPTS)
                tl=[r['username'] for r in rd("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
                st_=c2.selectbox("استاد*",tl) if tl else c2.text_input("استاد*")
                scl=c1.text_input("کلاس"); ssec=c2.text_input("سیکشن")
                sph=c1.text_input("فون"); sadr=st.text_area("پتہ")
                if st.form_submit_button("✅ داخلہ کریں"):
                    if sn.strip() and sf.strip():
                        wr("""INSERT INTO students(name,father_name,mother_name,roll_no,
                              dob,admission_date,phone,address,teacher,dept,class_name,section)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (sn.strip(),sf.strip(),sm,sr,str(sd),str(sa),sph,sadr,st_,sdept,scl,ssec))
                        audit(st.session_state.username,"Student Added",sn)
                        st.success(f"✅ {sn} داخل!"); st.rerun()
                    else: st.error("نام اور والد ضروری")

# ════════════════════════════════════════════
# ████  TIMETABLE  ████
# ════════════════════════════════════════════
elif pg=="timetable" and IS_ADMIN:
    sh("📚","ٹائم ٹیبل")
    tl=[r['username'] for r in rd("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
    if not tl: st.warning("پہلے اساتذہ رجسٹر کریں")
    else:
        st_=st.selectbox("استاد",tl)
        tt=rd("SELECT id,day_name as دن,period as وقت,subject as مضمون,room as کمرہ FROM timetable WHERE teacher=? ORDER BY day_name,period",(st_,))
        if tt:
            df=pd.DataFrame(tt)
            edited=st.data_editor(df,use_container_width=True,num_rows="dynamic",key="tte",hide_index=True)
            c1,c2,c3=st.columns(3)
            if c1.button("💾 محفوظ"):
                for _,row in edited.iterrows():
                    if pd.notna(row.get('id')):
                        wr("UPDATE timetable SET day_name=?,period=?,subject=?,room=? WHERE id=?",
                           (str(row.get('دن','')),str(row.get('وقت','')),
                            str(row.get('مضمون','')),str(row.get('کمرہ','')),int(row['id'])))
                    elif pd.isna(row.get('id')):
                        wr("INSERT INTO timetable(teacher,day_name,period,subject,room)VALUES(?,?,?,?,?)",
                           (st_,str(row.get('دن','')),str(row.get('وقت','')),
                            str(row.get('مضمون','')),str(row.get('کمرہ',''))))
                st.success("✅!"); st.rerun()
            if c2.button("🗑️ مکمل حذف"):
                wr("DELETE FROM timetable WHERE teacher=?",(st_,)); st.rerun()
        with st.expander("➕ نیا پیریڈ"):
            with st.form("add_per"):
                c1,c2,c3,c4=st.columns(4)
                dn=c1.selectbox("دن",DAYS_UR); per=c2.text_input("وقت","08:00-09:00")
                sub=c3.text_input("مضمون"); rm=c4.text_input("کمرہ")
                if st.form_submit_button("➕"):
                    wr("INSERT INTO timetable(teacher,day_name,period,subject,room)VALUES(?,?,?,?,?)",
                       (st_,dn,per,sub,rm)); st.success("✅!"); st.rerun()

# ════════════════════════════════════════════
# ████  STAFF MONITORING  ████
# ════════════════════════════════════════════
elif pg=="monitor" and IS_ADMIN:
    sh("📋","عملہ نگرانی")
    tab1,tab2=st.tabs(["➕ نیا اندراج","📜 ریکارڈ"])
    with tab1:
        tl=[r['username'] for r in rd("SELECT username FROM users WHERE role='teacher' AND is_active=1")]
        with st.form("mon"):
            c1,c2=st.columns(2)
            stf=c1.selectbox("عملہ",tl) if tl else c1.text_input("عملہ")
            nd=c2.date_input("تاریخ",date.today())
            nt=c1.selectbox("نوعیت",["یادداشت","شکایت","تنبیہ","تعریف","جائزہ"])
            ns=c2.selectbox("حالت",["زیر التواء","حل شدہ","زیر غور"])
            desc=st.text_area("تفصیل*",max_chars=1000)
            act=st.text_area("کارروائی",max_chars=500)
            if st.form_submit_button("✅ محفوظ"):
                if desc.strip():
                    wr("INSERT INTO staff_notes(staff,note_date,note_type,description,action_taken,status,created_by)VALUES(?,?,?,?,?,?,?)",
                       (stf,str(nd),nt,desc,act,ns,st.session_state.username))
                    st.success("✅!"); st.rerun()
                else: st.error("تفصیل ضروری")
    with tab2:
        notes=rd("""SELECT id,staff as عملہ,note_date as تاریخ,note_type as نوعیت,
                   description as تفصیل,status as حالت FROM staff_notes ORDER BY note_date DESC""")
        if notes:
            df=pd.DataFrame(notes)
            edited=st.data_editor(df,use_container_width=True,num_rows="dynamic",key="ne",hide_index=True)
            c1,c2=st.columns(2)
            if c1.button("💾 محفوظ"):
                for _,row in edited.iterrows():
                    if pd.notna(row.get('id')):
                        wr("UPDATE staff_notes SET status=? WHERE id=?",(str(row.get('حالت','')),int(row['id'])))
                st.success("✅"); st.rerun()
            with st.form("del_note"):
                di=st.number_input("حذف ID",1,step=1)
                if st.form_submit_button("🗑️ حذف"):
                    wr("DELETE FROM staff_notes WHERE id=?",(int(di),)); st.success("✅"); st.rerun()
            c2.download_button("📥 CSV",to_csv(df),"notes.csv")

# ════════════════════════════════════════════
# ████  NOTIFICATIONS  ████
# ════════════════════════════════════════════
elif pg=="notifs":
    sh("📢","اعلانات")
    if IS_ADMIN:
        with st.expander("➕ نیا اعلان"):
            with st.form("nf"):
                t_=st.text_input("عنوان*"); m_=st.text_area("پیغام*")
                tg=st.selectbox("وصول کنندہ",["تمام","اساتذہ","طلبہ"])
                if st.form_submit_button("📤 بھیجیں"):
                    if t_.strip() and m_.strip():
                        wr("INSERT INTO notifications(title,message,target,created_by)VALUES(?,?,?,?)",
                           (t_,m_,tg,st.session_state.username))
                        st.success("✅!"); st.rerun()
                    else: st.error("ضروری فیلڈز")
        with st.expander("🗑️ اعلان حذف کریں"):
            with st.form("del_notif"):
                di=st.number_input("ID",1,step=1)
                if st.form_submit_button("🗑️ حذف"):
                    wr("DELETE FROM notifications WHERE id=?",(int(di),)); st.success("✅"); st.rerun()

    notifs=rd("""SELECT id,title,message,target,created_by,created_at
                FROM notifications ORDER BY created_at DESC LIMIT 30""")
    if notifs:
        for n in notifs:
            st.markdown(f"""<div class="ni">
              <h5>🔔 {n['title']} <small style="font-weight:400">({n['target']})</small></h5>
              <p>{n['message']}</p>
              <small>از:{n['created_by']}|{n['created_at'][:16]}|ID:{n['id']}</small>
            </div>""",unsafe_allow_html=True)
    else: st.info("کوئی اعلان نہیں")

# ════════════════════════════════════════════
# ████  ANALYTICS  ████
# ════════════════════════════════════════════
elif pg=="analytics" and IS_ADMIN:
    try:
        import plotly.express as px
        sh("📈","تجزیہ و رپورٹس")
        c1,c2=st.columns(2)
        with c1:
            dd=rd("SELECT dept,COUNT(*) as cnt FROM students WHERE is_active=1 GROUP BY dept")
            if dd:
                fig=px.pie(pd.DataFrame(dd),values='cnt',names='dept',title='شعبہ وار طلباء',
                           color_discrete_sequence=['#0a5c3c','#0d7a52','#c9982a','#f5c842'])
                fig.update_layout(font_family="serif",title_x=0.5)
                st.plotly_chart(fig,use_container_width=True)
        with c2:
            ed=rd("SELECT grade,COUNT(*) as cnt FROM exams WHERE status='مکمل' AND grade!='' GROUP BY grade")
            if ed:
                fig2=px.bar(pd.DataFrame(ed),x='grade',y='cnt',title='امتحانی نتائج',
                            color='cnt',color_continuous_scale=['#e8f6f0','#0a5c3c'])
                fig2.update_layout(font_family="serif",title_x=0.5)
                st.plotly_chart(fig2,use_container_width=True)
        att_d=rd("""SELECT att_date,COUNT(*) as cnt FROM teacher_attendance
                   WHERE att_date>=? GROUP BY att_date ORDER BY att_date""",
                 (str(date.today()-timedelta(days=30)),))
        if att_d:
            fig3=px.line(pd.DataFrame(att_d),x='att_date',y='cnt',
                         title='ماہانہ حاضری (30 دن)',
                         color_discrete_sequence=['#0a5c3c'],markers=True)
            fig3.update_layout(font_family="serif",title_x=0.5)
            st.plotly_chart(fig3,use_container_width=True)
    except ImportError:
        st.warning("plotly install کریں: requirements.txt میں plotly شامل ہے")

# ════════════════════════════════════════════
# ████  BEST STUDENTS  ████
# ════════════════════════════════════════════
elif pg=="best" and IS_ADMIN:
    sh("🏆","ماہانہ بہترین طلباء")
    c1,c2=st.columns(2)
    mnth=c1.date_input("مہینہ",date.today().replace(day=1))
    df_=c2.selectbox("شعبہ",["تمام"]+DEPTS)
    d1=mnth.replace(day=1)
    d2=mnth.replace(month=mnth.month%12+1,day=1)-timedelta(days=1) if mnth.month<12 else mnth.replace(year=mnth.year+1,month=1,day=1)-timedelta(days=1)
    dw="" if df_=="تمام" else f" AND dept='{df_}'"
    studs=rd(f"SELECT id,name,father_name,roll_no,dept FROM students WHERE is_active=1{dw}")
    scores=[]
    for s in studs:
        gs,cs=[],[]
        if s['dept']=="حفظ":
            recs=rd("""SELECT attendance,sabaq_nagha,sq_nagha,manzil_nagha,
                      sq_mistakes,manzil_mistakes,cleanliness
                      FROM hifz_records WHERE student_id=? AND rec_date BETWEEN ? AND ?""",
                    (s['id'],str(d1),str(d2)))
            for r in recs:
                g=grade_hifz(r['attendance'],r['sabaq_nagha'],r['sq_nagha'],
                             r['manzil_nagha'],r['sq_mistakes'],r['manzil_mistakes'])
                gm={"ممتاز":100,"جید جداً":85,"جید":75,"مقبول":60,
                    "ناقص":40,"کمزور":25,"ناکام":10,"غیر حاضر":0,"رخصت":50}
                gs.append(gm.get(g,0))
                if r.get('cleanliness'):
                    cs.append({"بہترین":3,"بہتر":2,"ناقص":1}.get(r['cleanliness'],0))
        else:
            recs=rd("""SELECT attendance,performance,cleanliness
                      FROM general_records WHERE student_id=? AND rec_date BETWEEN ? AND ?""",
                    (s['id'],str(d1),str(d2)))
            for r in recs:
                pm={"بہت بہتر":90,"بہتر":80,"مناسب":65,"کمزور":45}
                gs.append(pm.get(r.get('performance',''),70) if r['attendance']=="حاضر"
                          else (50 if r['attendance']=="رخصت" else 0))
                if r.get('cleanliness'):
                    cs.append({"بہترین":3,"بہتر":2,"ناقص":1}.get(r['cleanliness'],0))
        if gs:
            scores.append({"name":s['name'],"father":s['father_name'],
                           "dept":s['dept'],"ga":round(sum(gs)/len(gs),1),
                           "ca":round(sum(cs)/len(cs),2) if cs else 0,"days":len(gs)})
    if not scores: st.warning("کوئی ریکارڈ نہیں")
    else:
        bg=sorted(scores,key=lambda x:x['ga'],reverse=True)
        bc=sorted(scores,key=lambda x:x['ca'],reverse=True)
        medals=[("🥇",),(("🥈",)),(("🥉",))]
        st.subheader("📚 تعلیمی کارکردگی")
        c1,c2,c3=st.columns(3)
        for col,st_,m in zip([c1,c2,c3],bg[:3],["🥇","🥈","🥉"]):
            with col:
                st.markdown(f"""<div class="tc">
                  <span class="tm">{m}</span>
                  <div class="tn">{st_['name']}</div>
                  <div class="tsb">والد: {st_['father']}</div>
                  <div class="tsb">🏫{st_['dept']}|{st_['days']}دن</div>
                  <div class="ts">{st_['ga']}%</div>
                </div>""",unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("🧹 صفائی")
        c1,c2,c3=st.columns(3)
        for col,st_,m in zip([c1,c2,c3],bc[:3],["🥇","🥈","🥉"]):
            with col:
                cp=round((st_['ca']/3)*100,1)
                st.markdown(f"""<div class="tc">
                  <span class="tm">{m}</span>
                  <div class="tn">{st_['name']}</div>
                  <div class="tsb">والد: {st_['father']}</div>
                  <div class="tsb">🏫{st_['dept']}</div>
                  <div class="ts">🧹{cp}%</div>
                </div>""",unsafe_allow_html=True)
        with st.expander("📊 تمام"):
            df_a=pd.DataFrame(scores)
            df_a.columns=["نام","والد","شعبہ","تعلیمی %","صفائی","دن"]
            st.dataframe(df_a.sort_values("تعلیمی %",ascending=False),
                         use_container_width=True,hide_index=True)
            st.download_button("📥 CSV",to_csv(df_a),"best.csv")

# ════════════════════════════════════════════
# ████  PASSWORD  ████
# ════════════════════════════════════════════
elif pg=="password":
    sh("🔑","پاسورڈ تبدیل کریں")
    _,col,_=st.columns([1,2,1])
    with col:
        if IS_ADMIN:
            st.markdown("**استاد کا پاسورڈ ری سیٹ**")
            tl=[r['username'] for r in rd("SELECT username FROM users WHERE role='teacher'")]
            with st.form("adm_pw"):
                sel=st.selectbox("استاد",tl)
                np1=st.text_input("نیا پاسورڈ*",type="password")
                np2=st.text_input("تصدیق*",type="password")
                if st.form_submit_button("✅ ری سیٹ"):
                    if np1==np2 and len(np1)>=6:
                        wr("UPDATE users SET password=? WHERE username=?",(hp(np1),sel))
                        st.success(f"✅ {sel} کا پاسورڈ تبدیل!")
                    else: st.error("پاسورڈ میل نہیں یا 6 حرف سے کم")
            st.markdown("---")
        st.markdown("**اپنا پاسورڈ**")
        with st.form("my_pw"):
            op=st.text_input("پرانا*",type="password")
            np1=st.text_input("نیا*",type="password")
            np2=st.text_input("تصدیق*",type="password")
            if st.form_submit_button("✅ تبدیل کریں"):
                u=rd("SELECT password FROM users WHERE username=?",(st.session_state.username,),one=True)
                if u and chk(op,u['password']):
                    if np1==np2 and len(np1)>=6:
                        wr("UPDATE users SET password=? WHERE username=?",(hp(np1),st.session_state.username))
                        st.success("✅ تبدیل! دوبارہ لاگ ان کریں")
                        for k in list(st.session_state.keys()): del st.session_state[k]
                        st.rerun()
                    else: st.error("پاسورڈ میل نہیں یا 6 حرف سے کم")
                else: st.error("❌ پرانا پاسورڈ غلط")

# ════════════════════════════════════════════
# ████  BACKUP  ████
# ════════════════════════════════════════════
elif pg=="backup" and IS_ADMIN:
    sh("⚙️","بیک اپ & سیٹنگز")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("<div class='pc'>",unsafe_allow_html=True)
        st.markdown("**📥 بیک اپ ڈاؤن لوڈ**")
        if os.path.exists(DB):
            with open(DB,"rb") as f:
                st.download_button("💾 مکمل ڈیٹا بیس (.db)",f,
                                   f"jamia_bkp_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
                                   "application/x-sqlite3",use_container_width=True)
        if st.button("📦 CSV زپ بنائیں",use_container_width=True):
            tables=["users","students","hifz_records","qaida_records","general_records",
                    "teacher_attendance","leave_requests","exams","passed_paras",
                    "timetable","notifications","staff_notes","audit_log"]
            buf=io.BytesIO()
            with zipfile.ZipFile(buf,'w') as zf:
                for t in tables:
                    try:
                        rows=rd(f"SELECT * FROM {t}")
                        if rows: zf.writestr(f"{t}.csv",pd.DataFrame(rows).to_csv(index=False).encode('utf-8-sig'))
                    except: pass
            buf.seek(0)
            st.download_button("📥 CSV زپ",buf,f"csv_{datetime.now().strftime('%Y%m%d')}.zip",
                               "application/zip",use_container_width=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='pc'>",unsafe_allow_html=True)
        st.markdown("**🔄 ری سٹور**")
        st.warning("⚠️ پہلے بیک اپ لیں!")
        upf=st.file_uploader(".db فائل",type=["db"])
        if upf:
            if st.checkbox("میں سمجھتا/سمجھتی ہوں") and st.button("🔄 ری سٹور"):
                if os.path.exists(DB): shutil.copy(DB,DB+".bak")
                with open(DB,"wb") as f: f.write(upf.getbuffer())
                st.success("✅ ری سٹور مکمل!"); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)
    st.markdown("<div class='pc'>",unsafe_allow_html=True)
    st.markdown("**📋 آڈٹ لاگ**")
    logs=rd("SELECT username as صارف,action as عمل,details as تفصیل,created_at as وقت FROM audit_log ORDER BY created_at DESC LIMIT 50")
    if logs: st.dataframe(pd.DataFrame(logs),use_container_width=True,hide_index=True)
    st.markdown("</div>",unsafe_allow_html=True)

# ════════════════════════════════════════════
# ████  TEACHER HOME  ████
# ════════════════════════════════════════════
elif pg=="home" and not IS_ADMIN:
    sh("🏠",f"خوش آمدید، {st.session_state.username}!","استاد پورٹل")
    ms=sc("SELECT COUNT(*) FROM students WHERE teacher=? AND is_active=1",(st.session_state.username,))
    mr=sc("SELECT COUNT(*) FROM hifz_records WHERE teacher=?",(st.session_state.username,))
    td=sc("SELECT COUNT(*) FROM hifz_records WHERE teacher=? AND rec_date=?",(st.session_state.username,str(date.today())))
    ml=sc("SELECT COUNT(*) FROM leave_requests WHERE username=? AND status='پینڈنگ'",(st.session_state.username,))
    st.markdown(f"""<div class="mets">
      <div class="mc"><span class="mi">👨‍🎓</span><div class="mv">{ms}</div><div class="ml">میرے طلباء</div></div>
      <div class="mc"><span class="mi">📋</span><div class="mv">{mr}</div><div class="ml">کل ریکارڈ</div></div>
      <div class="mc"><span class="mi">✅</span><div class="mv">{td}</div><div class="ml">آج اندراج</div></div>
      <div class="mc"><span class="mi">📩</span><div class="mv">{ml}</div><div class="ml">رخصت پینڈنگ</div></div>
    </div>""",unsafe_allow_html=True)
    notifs=rd("SELECT title,message FROM notifications WHERE target IN ('تمام','اساتذہ') ORDER BY created_at DESC LIMIT 5")
    if notifs:
        st.markdown("**🔔 تازہ اعلانات**")
        for n in notifs:
            st.markdown(f"""<div class="ni"><h5>{n['title']}</h5><p>{n['message'][:100]}</p></div>""",unsafe_allow_html=True)

# ════════════════════════════════════════════
# ████  TEACHER ENTRY — IMPROVED  ████
# ════════════════════════════════════════════
elif pg=="entry" and not IS_ADMIN:
    sh("📝","روزانہ سبق اندراج","طالب علم کا آئیکن دبائیں")
    c1,c2=st.columns(2)
    entry_date=c1.date_input("تاریخ",date.today())
    dept=c2.selectbox("شعبہ",DEPTS,
                      index=DEPTS.index(st.session_state.entry_dept)
                      if st.session_state.entry_dept in DEPTS else 0)
    st.session_state.entry_dept=dept

    my_studs=rd("SELECT id,name,father_name FROM students WHERE teacher=? AND dept=? AND is_active=1",
               (st.session_state.username,dept))
    if not my_studs:
        st.info(f"آپ کی {dept} کلاس میں کوئی طالب علم نہیں"); st.stop()

    # ── Student Icon Grid ──
    st.markdown(f"**{len(my_studs)} طلباء — کسی کا بٹن دبائیں:**")
    done_ids=set()
    if dept=="حفظ":
        for s in my_studs:
            if rd("SELECT id FROM hifz_records WHERE student_id=? AND rec_date=?",(s['id'],str(entry_date)),one=True):
                done_ids.add(s['id'])
    elif dept=="قاعدہ":
        for s in my_studs:
            if rd("SELECT id FROM qaida_records WHERE student_id=? AND rec_date=?",(s['id'],str(entry_date)),one=True):
                done_ids.add(s['id'])

    COLS=4
    chunks=[my_studs[i:i+COLS] for i in range(0,len(my_studs),COLS)]
    sel=st.session_state.sel_student

    for chunk in chunks:
        cols=st.columns(COLS)
        for col,s in zip(cols,chunk):
            is_done=s['id'] in done_ids
            is_sel=sel==s['id']
            done_txt="✅" if is_done else "📝"
            with col:
                if st.button(f"{done_txt}\n{s['name'][:8]}\n{s['father_name'][:6]}",
                             key=f"stu_{s['id']}",use_container_width=True):
                    if not is_done:
                        st.session_state.sel_student=s['id']
                        st.rerun()

    st.markdown("---")

    # ── Entry Form for Selected Student ──
    if sel and sel not in done_ids:
        s_data=next((s for s in my_studs if s['id']==sel),None)
        if s_data:
            k=str(s_data['id'])
            st.markdown(f"""<div class="sh2" style="padding:10px 16px">
              <span class="si">📝</span>
              <div><div class="st">{s_data['name']} ولد {s_data['father_name']}</div>
              <div class="ss">{dept} | {entry_date}</div></div>
            </div>""",unsafe_allow_html=True)

            att=st.radio("حاضری",ATT,key=f"att_{k}",horizontal=True)
            cln=st.selectbox("صفائی",CLEAN,key=f"cln_{k}")

            # Initialize all variables to avoid UnboundLocalError
            s_nagha=sq_nagha=m_nagha=0
            sabaq_txt=sq_txt=m_txt=""
            s_lines=sq_atk=sq_mis=m_atk=m_mis=0
            ln=lines=det=""
            sub_=les_=hw_=prf_=""
            gr=""

            # حاضری کی بنیاد پر فارم دکھائیں
            if att == "حاضر":
                if dept == "حفظ":
                    st.markdown("**📖 سبق**")
                    sc1, sc2 = st.columns(2)
                    sn = sc1.checkbox("ناغہ", key=f"sn_{k}")
                    sy = sc2.checkbox("یاد نہیں", key=f"sy_{k}")
                    if sn or sy:
                        s_nagha = 1
                        sabaq_txt = "ناغہ" if sn else "یاد نہیں"
                        s_lines = 0
                    else:
                        rc1, rc2, rc3 = st.columns(3)
                        sur = rc1.selectbox("سورت", SURAHS, key=f"sr_{k}")
                        af = rc2.text_input("آیت سے", key=f"af_{k}")
                        at_ = rc3.text_input("آیت تک", key=f"at_{k}")
                        s_lines = st.number_input("ستر", 0, 50, 0, key=f"sl_{k}")
                        sabaq_txt = f"{sur}:{af}-{at_}"

                    st.markdown("**📚 سبقی**")
                    sc1, sc2 = st.columns(2)
                    sqn_ = sc1.checkbox("ناغہ", key=f"sqn_{k}")
                    sqy = sc2.checkbox("یاد نہیں", key=f"sqy_{k}")
                    if sqn_ or sqy:
                        sq_nagha = 1
                        sq_txt = "ناغہ" if sqn_ else "یاد نہیں"
                        sq_atk = sq_mis = 0
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
                        m_atk = m_mis = 0
                    else:
                        rc1, rc2, rc3, rc4 = st.columns(4)
                        mp = rc1.selectbox("پارہ", PARAS, key=f"mp_{k}")
                        mm_ = rc2.selectbox("مقدار", MIQDAR, key=f"mm_{k}")
                        m_atk = rc3.number_input("اٹکن", 0, key=f"mat_{k}")
                        m_mis = rc4.number_input("غلطی", 0, key=f"mms_{k}")
                        m_txt = f"{mp}:{mm_}"

                    gr = grade_hifz(att, s_nagha, sq_nagha, m_nagha, sq_mis, m_mis)
                    st.markdown(f"**درجہ:** {chip(gr)}", unsafe_allow_html=True)

                elif dept == "قاعدہ":
                    ln = st.text_input("تختی/سبق نمبر", key=f"ln_{k}")
                    lines = st.number_input("لائنیں", 0, key=f"lns_{k}")
                    det = st.text_area("تفصیل", key=f"det_{k}")

                elif dept in ["درسِ نظامی", "عصری تعلیم"]:
                    sub_ = st.text_input("مضمون/کتاب", key=f"sub_{k}")
                    les_ = st.text_area("سبق", key=f"les_{k}")
                    hw_ = st.text_input("ہوم ورک", key=f"hw_{k}")
                    prf_ = st.select_slider("کارکردگی",
                                            ["بہت بہتر", "بہتر", "مناسب", "کمزور"],
                                            key=f"prf_{k}")

            else:
                # جب حاضری "حاضر" نہ ہو
                if dept == "حفظ":
                    gr = "غیر حاضر" if att == "غیر حاضر" else "رخصت"
                # دیگر شعبوں کے لیے کوئی اضافی فیلڈ نہیں

            note=st.text_input("نوٹ (اختیاری)",key=f"nt_{k}")

            c1,c2=st.columns(2)
            if c1.button(f"💾 {s_data['name']} محفوظ کریں",use_container_width=True):
                if dept=="حفظ":
                    # Ensure grade is calculated if not already
                    if att == "حاضر" and not gr:
                        gr = grade_hifz(att, s_nagha, sq_nagha, m_nagha, sq_mis, m_mis)
                    elif att != "حاضر":
                        gr = "غیر حاضر" if att == "غیر حاضر" else "رخصت"
                    wr("""INSERT INTO hifz_records
                          (rec_date,student_id,teacher,attendance,sabaq,sabaq_lines,sabaq_nagha,
                           sq_text,sq_nagha,sq_atkan,sq_mistakes,
                           manzil_text,manzil_nagha,manzil_atkan,manzil_mistakes,
                           cleanliness,grade,note)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (str(entry_date),s_data['id'],st.session_state.username,att,
                        sabaq_txt,s_lines,s_nagha,
                        sq_txt,sq_nagha,sq_atk,sq_mis,
                        m_txt,m_nagha,m_atk,m_mis,cln,gr,note))
                elif dept=="قاعدہ":
                    wr("""INSERT INTO qaida_records
                          (rec_date,student_id,teacher,attendance,lesson_no,total_lines,details,cleanliness,note)
                          VALUES(?,?,?,?,?,?,?,?,?)""",
                       (str(entry_date),s_data['id'],st.session_state.username,
                        att,ln,lines,det,cln,note))
                else:
                    wr("""INSERT INTO general_records
                          (rec_date,student_id,teacher,dept,attendance,subject,lesson,homework,performance,cleanliness,note)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                       (str(entry_date),s_data['id'],st.session_state.username,dept,
                        att,sub_,les_,hw_,prf_,cln,note))
                audit(st.session_state.username,"Entry",f"{s_data['name']}{entry_date}")
                st.success(f"✅ {s_data['name']} محفوظ!")
                st.session_state.sel_student=None
                st.rerun()
            if c2.button("← واپس",use_container_width=True):
                st.session_state.sel_student=None; st.rerun()
    elif sel in done_ids:
        st.success("✅ اس طالب علم کا آج کا ریکارڈ پہلے سے موجود ہے")
        if st.button("← واپس"): st.session_state.sel_student=None; st.rerun()

# ════════════════════════════════════════════
# ████  TEACHER EXAM  ████
# ════════════════════════════════════════════
elif pg=="t_exam" and not IS_ADMIN:
    sh("🎓","امتحانی درخواست")
    ms=rd("SELECT id,name,father_name,dept FROM students WHERE teacher=? AND is_active=1",(st.session_state.username,))
    if not ms: st.warning("کوئی طالب علم نہیں"); st.stop()
    with st.form("ex"):
        names=[f"{s['name']} ولد {s['father_name']} ({s['dept']})" for s in ms]
        idx=st.selectbox("طالب علم",range(len(names)),format_func=lambda i:names[i])
        s=ms[idx]; et=st.selectbox("امتحان",["پارہ ٹیسٹ","ماہانہ","سہ ماہی","سالانہ"])
        c1,c2=st.columns(2)
        sd=c1.date_input("شروع",date.today()); ed=c2.date_input("ختم",date.today()+timedelta(days=7))
        td=(ed-sd).days+1; st.caption(f"کل دن: {td}")
        fp=tp=0; bk=amt=""
        if et=="پارہ ٹیسٹ" or s['dept']=="حفظ":
            c1,c2=st.columns(2)
            fp=c1.number_input("پارہ (شروع)",1,30,1); tp=c2.number_input("پارہ (ختم)",int(fp),30,int(fp))
        if s['dept']!="حفظ": bk=st.text_input("کتاب")
        amt=st.text_input("مقدار خواندگی")
        if st.form_submit_button("📤 درخواست بھیجیں"):
            wr("""INSERT INTO exams(student_id,teacher,dept,exam_type,from_para,to_para,
                  book_name,amount_read,start_date,end_date,total_days)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
               (s['id'],st.session_state.username,s['dept'],et,fp,tp,bk,amt,str(sd),str(ed),td))
            st.success("✅ درخواست بھیج دی گئی")

# ════════════════════════════════════════════
# ████  TEACHER LEAVE  ████
# ════════════════════════════════════════════
elif pg=="t_leave" and not IS_ADMIN:
    sh("📩","رخصت کی درخواست")
    ml=rd("""SELECT leave_type as نوعیت,start_date as تاریخ,days as دن,status as حالت
             FROM leave_requests WHERE username=? ORDER BY created_at DESC LIMIT 10""",(st.session_state.username,))
    if ml:
        st.markdown("**حالیہ درخواستیں**")
        for lv in ml:
            sc_="so" if lv['حالت']=="منظور" else("sr" if lv['حالت']=="مسترد" else "sp")
            st.markdown(f"""<div class="lc">
              <span class="{sc_}">{lv['حالت']}</span> &nbsp;
              <b>{lv['نوعیت']}</b>|{lv['تاریخ']}|{lv['دن']}دن</div>""",unsafe_allow_html=True)
        st.markdown("---")
    with st.form("lv"):
        c1,c2=st.columns(2)
        lt=c1.selectbox("نوعیت",["بیماری","ضروری کام","ہنگامی","دیگر"])
        sd=c2.date_input("شروع",date.today())
        days=c1.number_input("دن",1,30,1)
        c2.caption(f"واپسی: {sd+timedelta(days=int(days)-1)}")
        rsn=st.text_area("وجہ*",max_chars=500)
        if st.form_submit_button("📤 بھیجیں"):
            if rsn.strip():
                wr("INSERT INTO leave_requests(username,leave_type,start_date,days,reason)VALUES(?,?,?,?,?)",
                   (st.session_state.username,lt,str(sd),days,rsn))
                st.success("✅ بھیج دی گئی!"); st.rerun()
            else: st.error("وجہ ضروری")

# ════════════════════════════════════════════
# ████  TEACHER ATTENDANCE  ████
# ════════════════════════════════════════════
elif pg=="t_att" and not IS_ADMIN:
    sh("🕒","میری حاضری")
    today=date.today()
    rec=rd("SELECT * FROM teacher_attendance WHERE username=? AND att_date=?",(st.session_state.username,str(today)),one=True)
    st.markdown(f"""<div class="pc" style="text-align:center">
      <div style="font-size:1rem;font-weight:700;color:var(--g1)">📅 {today}</div>
    </div>""",unsafe_allow_html=True)
    if not rec:
        arr=st.time_input("آمد",datetime.now().time())
        if st.button("✅ آمد درج کریں",use_container_width=True):
            try:
                wr("INSERT INTO teacher_attendance(username,att_date,arrival)VALUES(?,?,?)",
                   (st.session_state.username,str(today),arr.strftime("%I:%M %p")))
                st.success("✅ آمد!"); st.rerun()
            except: st.warning("پہلے سے درج ہے")
    elif not rec.get('departure'):
        st.success(f"✅ آمد: {rec['arrival']}")
        dep=st.time_input("رخصت",datetime.now().time())
        if st.button("✅ رخصت درج کریں",use_container_width=True):
            wr("UPDATE teacher_attendance SET departure=? WHERE username=? AND att_date=?",
               (dep.strftime("%I:%M %p"),st.session_state.username,str(today)))
            st.success("✅ رخصت!"); st.rerun()
    else:
        c1,c2=st.columns(2)
        c1.metric("🟢 آمد",rec['arrival']); c2.metric("🔴 رخصت",rec['departure'])
    st.markdown("---")
    monthly=rd("""SELECT att_date as تاریخ,arrival as آمد,departure as رخصت
                 FROM teacher_attendance WHERE username=? AND att_date>=?
                 ORDER BY att_date DESC""",(st.session_state.username,str(date.today().replace(day=1))))
    if monthly: st.dataframe(pd.DataFrame(monthly),use_container_width=True,hide_index=True)

# ════════════════════════════════════════════
# ████  TEACHER TIMETABLE  ████
# ════════════════════════════════════════════
elif pg=="t_tt" and not IS_ADMIN:
    sh("📚","میرا ٹائم ٹیبل")
    tt=rd("SELECT day_name as دن,period as وقت,subject as مضمون,room as کمرہ FROM timetable WHERE teacher=? ORDER BY day_name,period",(st.session_state.username,))
    if tt:
        df=pd.DataFrame(tt)
        try:
            pivot=df.pivot(index='وقت',columns='دن',values='مضمون').fillna("—")
            st.dataframe(pivot,use_container_width=True)
        except: st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("📥 ڈاؤن لوڈ",html_rep(df,"ٹائم ٹیبل",st.session_state.username),"tt.html","text/html")
    else: st.info("ٹائم ٹیبل ترتیب نہیں دیا گیا")

# ════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════
st.markdown("""
<div class="bpad"></div>
<div style="text-align:center;padding:14px 0 6px;color:#9ca3af;font-size:.7rem;
     border-top:1px solid #ddeae3;margin-top:20px">
  🕌 جامعہ ملیہ اسلامیہ فیصل آباد — Smart ERP v4.0 | تمام حقوق محفوظ
</div>""",unsafe_allow_html=True)
st.markdown("</div>",unsafe_allow_html=True)
