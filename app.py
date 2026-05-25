import streamlit as st
import json, math, os, tempfile, zipfile
from io import BytesIO

st.set_page_config(page_title="حاسبة شبكات السيول", page_icon="🌊",
                   layout="wide", initial_sidebar_state="expanded",
                   menu_items={
                       'Get Help': None,
                       'Report a bug': None,
                       'About': None
                   })

# ══════════════════════════════
# نظام تسجيل الدخول
# ══════════════════════════════
def check_credentials(username: str, password: str) -> bool:
    """التحقق من بيانات المستخدم من st.secrets"""
    try:
        users = st.secrets["users"]
        stored = users.get(username)
        return stored is not None and stored == password
    except Exception:
        return False

HIDE_TOOLBAR_CSS = """
<style>
/* ════════════════════════════════════════════════════════
   إخفاء شامل وقاطع لكل عناصر Streamlit العلوية والسفلية
   يسري على صفحة الدخول وبعد الدخول في كل مكان
   ════════════════════════════════════════════════════════ */

/* الشريط العلوي وكل أزراره */
header[data-testid="stHeader"],
header,
[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
[data-testid="baseButton-header"],
[data-testid="stDecoration"],
.stToolbar, #stToolbar,
div[class*="Toolbar"],
div[class*="toolbar"],
div[class*="StatusWidget"],
[data-testid="stStatusWidget"],
.viewerBadge_container__1QSob,
.viewerBadge_link__1S137,
#MainMenu,
[data-testid="collapsedControl"],
button[title="View app fullscreen"],
a[href*="streamlit.io"],
a[href*="github.com"],
svg[class*="octocat"],
/* نقاط القائمة الثلاث */
button[kind="header"],
[data-testid="baseButton-headerNoPadding"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
}

/* الفوتر */
footer,
footer * {
    display: none !important;
    visibility: hidden !important;
}

/* إزالة المسافة الفارغة التي يتركها الهيدر */
.stApp > header { display: none !important; }
.block-container { padding-top: 1rem !important; }
</style>
"""

HIDE_TOOLBAR_JS = """
<script>
(function() {
    const SELECTORS = [
        'header[data-testid="stHeader"]',
        '[data-testid="stToolbar"]',
        '[data-testid="stToolbarActions"]',
        '[data-testid="baseButton-header"]',
        '[data-testid="stDecoration"]',
        '[data-testid="stStatusWidget"]',
        '#MainMenu',
        'footer',
        'a[href*="github.com"]',
        'a[href*="streamlit.io"]',
    ];
    function hideAll(doc) {
        if (!doc) return;
        try {
            SELECTORS.forEach(sel => {
                doc.querySelectorAll(sel).forEach(el => {
                    el.style.cssText += 'display:none!important;visibility:hidden!important;opacity:0!important;height:0!important;overflow:hidden!important;pointer-events:none!important;';
                    if (el.parentElement) {
                        const tag = el.parentElement.tagName;
                        if (tag === 'HEADER' || el.parentElement.getAttribute('data-testid') === 'stHeader') {
                            el.parentElement.style.cssText += 'display:none!important;height:0!important;';
                        }
                    }
                });
            });
            // إخفاء أي زر يحتوي على نص Fork أو GitHub
            doc.querySelectorAll('button, a, span').forEach(el => {
                const t = (el.innerText || el.textContent || '').trim();
                if (['Fork','fork','GitHub','github','Share','Hosted with'].some(w => t.includes(w))) {
                    el.style.cssText += 'display:none!important;';
                    if (el.parentElement) el.parentElement.style.cssText += 'display:none!important;';
                }
            });
        } catch(e){}
    }
    function run() {
        hideAll(document);
        try { hideAll(window.parent.document); } catch(e){}
    }
    run();
    const iv = setInterval(run, 200);
    setTimeout(() => clearInterval(iv), 15000);
    try {
        new MutationObserver(run).observe(document.documentElement, {childList:true, subtree:true});
        new MutationObserver(run).observe(window.parent.document.documentElement, {childList:true, subtree:true});
    } catch(e) {}
})();
</script>
"""

def inject_security():
    """حقن CSS+JS لإخفاء الشريط — يُستدعى في كل صفحة"""
    import streamlit.components.v1 as components
    st.markdown(HIDE_TOOLBAR_CSS, unsafe_allow_html=True)
    components.html(HIDE_TOOLBAR_JS, height=0)

def login_page():
    """صفحة تسجيل الدخول — تصميم احترافي"""
    inject_security()
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=Tajawal:wght@300;400;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Cairo', sans-serif !important;
    direction: rtl;
}

/* خلفية الصفحة — تدرج عميق مع نقوش هندسية */
.stApp {
    background:
        radial-gradient(ellipse at 20% 50%, rgba(26,95,168,0.18) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(10,42,94,0.25) 0%, transparent 55%),
        radial-gradient(ellipse at 60% 80%, rgba(26,95,168,0.12) 0%, transparent 50%),
        linear-gradient(135deg, #050e1f 0%, #091830 40%, #0d2447 100%) !important;
    min-height: 100vh;
}

/* إزالة padding الافتراضي */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
.element-container, .stVerticalBlock { gap: 0 !important; }

/* ── بطاقة الدخول ── */
.login-wrap {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}
.login-card {
    width: 100%;
    max-width: 440px;
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 24px;
    padding: 48px 44px 40px;
    box-shadow:
        0 32px 80px rgba(0,0,0,0.5),
        0 0 0 1px rgba(26,95,168,0.15) inset,
        0 1px 0 rgba(255,255,255,0.08) inset;
    position: relative;
    overflow: hidden;
}
.login-card::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(26,95,168,0.35) 0%, transparent 70%);
    pointer-events: none;
}
.login-card::after {
    content: '';
    position: absolute;
    bottom: -40px; left: -40px;
    width: 160px; height: 160px;
    background: radial-gradient(circle, rgba(10,42,94,0.4) 0%, transparent 70%);
    pointer-events: none;
}

/* الشعار والعنوان */
.login-logo {
    text-align: center;
    margin-bottom: 8px;
}
.login-logo .wave-icon {
    font-size: 3.2rem;
    display: block;
    filter: drop-shadow(0 0 20px rgba(26,95,168,0.8));
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%,100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}
.login-title {
    text-align: center;
    color: #fff;
    font-size: 1.5rem;
    font-weight: 900;
    letter-spacing: -0.3px;
    margin: 10px 0 4px;
    text-shadow: 0 2px 20px rgba(26,95,168,0.6);
}
.login-sub {
    text-align: center;
    color: rgba(180,210,255,0.7);
    font-size: .82rem;
    font-weight: 400;
    margin-bottom: 32px;
    letter-spacing: 0.2px;
}
.login-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(26,95,168,0.5), rgba(100,160,255,0.3), transparent);
    margin-bottom: 28px;
}

/* حقول الإدخال */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1.5px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: .93rem !important;
    padding: 12px 16px !important;
    direction: rtl !important;
    transition: all 0.25s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(26,95,168,0.8) !important;
    background: rgba(26,95,168,0.12) !important;
    box-shadow: 0 0 0 3px rgba(26,95,168,0.18) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder {
    color: rgba(180,210,255,0.4) !important;
}
.stTextInput label {
    color: rgba(180,210,255,0.85) !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: .85rem !important;
    font-weight: 600 !important;
    margin-bottom: 6px !important;
}

/* زر الدخول */
.stButton > button {
    background: linear-gradient(135deg, #1a5fa8 0%, #0a2a5e 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 13px !important;
    width: 100% !important;
    margin-top: 8px !important;
    box-shadow: 0 6px 24px rgba(10,42,94,0.5) !important;
    transition: all 0.25s ease !important;
    letter-spacing: 0.5px !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 32px rgba(26,95,168,0.55) !important;
    background: linear-gradient(135deg, #2070c8 0%, #0d3570 100%) !important;
}

/* رسائل الخطأ */
.stAlert {
    border-radius: 10px !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: .85rem !important;
    margin-top: 10px !important;
}

/* الفوتر داخل البطاقة */
.login-footer {
    text-align: center;
    color: rgba(180,210,255,0.35);
    font-size: .72rem;
    margin-top: 24px;
    letter-spacing: 0.3px;
}

/* نقاط الزخرفة */
.dots-bg {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}
.dot {
    position: absolute;
    width: 2px; height: 2px;
    background: rgba(100,160,255,0.4);
    border-radius: 50%;
    animation: twinkle 4s ease-in-out infinite;
}
@keyframes twinkle {
    0%,100%{opacity:.2;transform:scale(1)}
    50%{opacity:1;transform:scale(1.8)}
}
</style>
""", unsafe_allow_html=True)

    # خلفية نقاط ديكورية
    st.markdown("""
<div class="dots-bg">
  <div class="dot" style="top:12%;left:15%;animation-delay:0s"></div>
  <div class="dot" style="top:25%;left:72%;animation-delay:.8s"></div>
  <div class="dot" style="top:60%;left:8%;animation-delay:1.5s"></div>
  <div class="dot" style="top:75%;left:88%;animation-delay:.3s"></div>
  <div class="dot" style="top:40%;left:50%;animation-delay:2.1s"></div>
  <div class="dot" style="top:85%;left:35%;animation-delay:1.1s"></div>
  <div class="dot" style="top:5%;left:90%;animation-delay:2.7s"></div>
  <div class="dot" style="top:50%;left:25%;animation-delay:.6s"></div>
</div>
""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        st.markdown("""
<div class="login-logo">
  <span class="wave-icon">🌊</span>
</div>
<div class="login-title">حاسبة شبكات تصريف السيول</div>
<div class="login-sub">Flood Drainage Network Calculator &nbsp;·&nbsp; Eng. Ahmed Adam</div>
<div class="login-divider"></div>
""", unsafe_allow_html=True)

        username = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم", key="login_user", label_visibility="visible")
        password = st.text_input("كلمة المرور", type="password", placeholder="• • • • • • • •", key="login_pass", label_visibility="visible")

        if st.button("🔑  تسجيل الدخول", use_container_width=True):
            if check_credentials(username.strip(), password):
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username.strip()
                st.rerun()
            else:
                st.error("❌  اسم المستخدم أو كلمة المرور غير صحيحة")

        st.markdown('<div class="login-footer">© 2025 Flood Drainage Networks — جميع الحقوق محفوظة</div>', unsafe_allow_html=True)

# التحقق من حالة تسجيل الدخول
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_page()
    st.stop()

# حقن الأمان في الصفحة الرئيسية أيضاً
inject_security()

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
html,body,[class*="css"],.stApp{font-family:'Cairo',sans-serif!important;direction:rtl}
[data-testid="stSidebar"]{min-width:320px!important;max-width:360px!important;background:#f7f9fc!important}
.hdr{background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff;padding:14px 20px;border-radius:10px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between}
.hdr h1{margin:0;font-size:1.25rem;font-weight:900}.hdr p{margin:2px 0 0;font-size:.8rem;color:#b8d9f8}
.hdr .bdg{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);padding:4px 12px;border-radius:14px;font-size:.75rem;font-weight:700;white-space:nowrap}
.mc{background:#fff;border-radius:8px;padding:10px 14px;box-shadow:0 2px 6px rgba(0,0,0,.07);border-top:3px solid #1a5fa8;text-align:center}
.mc .v{font-size:1.35rem;font-weight:900;color:#0a2a5e}.mc .l{font-size:.75rem;color:#6b7a99;margin-top:2px}
.res{background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff!important;padding:16px 20px;border-radius:10px;font-size:1rem;font-weight:700;text-align:center;box-shadow:0 4px 14px rgba(26,95,168,.3);margin-top:8px;line-height:2}
.ib{background:#eaf4ff;border-right:4px solid #1a5fa8;border-radius:6px;padding:9px 13px;font-size:.83rem;color:#0a2a5e;margin-bottom:8px;direction:rtl;line-height:1.8}
.pc{background:#fff;border:1.5px solid #d0e4f7;border-right:5px solid #1a5fa8;border-radius:6px;padding:8px 12px;margin-bottom:6px;font-size:.82rem;color:#1a2a3a}
.pc b{color:#0a2a5e}.pc span{color:#c0392b;font-weight:900;font-size:.88rem}
.sig{background:#0a2a5e;color:#a8d0f0!important;text-align:center;padding:9px;border-radius:7px;margin-top:10px;font-size:.78rem}
.sig b{color:#fff!important}
.stButton>button{background:linear-gradient(135deg,#1a5fa8,#0a2a5e)!important;color:#fff!important;border:none!important;border-radius:8px!important;font-family:'Cairo',sans-serif!important;font-weight:700!important;font-size:.93rem!important;width:100%!important;padding:8px!important}
</style>""", unsafe_allow_html=True)

RLAT, RLON = 24.7136, 46.6753

# ══════════════════════════════
# دوال الحساب
# ══════════════════════════════
def hav(lon1, lat1, lon2, lat2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2
    return 2*R*math.asin(math.sqrt(a))

def length_m_wgs(coords):
    t = 0.0
    for i in range(len(coords)-1):
        try: t += hav(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
        except: pass
    return t

def length_m_proj(coords):
    t = 0.0
    for i in range(len(coords)-1):
        dx = coords[i+1][0]-coords[i][0]; dy = coords[i+1][1]-coords[i][1]
        t += math.sqrt(dx*dx+dy*dy)
    return t

def is_projected(coords):
    if not coords: return False
    return abs(coords[0][0]) > 180 or abs(coords[0][1]) > 90

def map_center(coords):
    if not coords: return RLAT, RLON
    return sum(c[1] for c in coords)/len(coords), sum(c[0] for c in coords)/len(coords)

def sanitize_props(props):
    """تحويل كل قيم الخصائص إلى أنواع قابلة للـ JSON"""
    import datetime
    clean = {}
    for k, v in props.items():
        if v is None:
            clean[str(k)] = None
        elif isinstance(v, (int, float, bool)):
            clean[str(k)] = v
        elif isinstance(v, str):
            clean[str(k)] = v
        elif isinstance(v, bytes):
            try: clean[str(k)] = v.decode("utf-8","ignore")
            except: clean[str(k)] = ""
        elif isinstance(v, (datetime.date, datetime.datetime)):
            clean[str(k)] = str(v)
        else:
            try: clean[str(k)] = float(v)
            except:
                try: clean[str(k)] = str(v)
                except: clean[str(k)] = ""
    return clean

def parse_geom(geom):
    if not geom: return []
    t = geom.get("type",""); raw = geom.get("coordinates",[])
    pts = raw if t=="LineString" else [p for part in raw for p in part] if t=="MultiLineString" else []
    return [[float(c[0]),float(c[1])] for c in pts if isinstance(c,(list,tuple)) and len(c)>=2]

@st.cache_data(show_spinner=False)
def convert_wgs84(coords_tuple, epsg):
    from pyproj import Transformer
    try:
        tr = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
        result = []
        for x, y in coords_tuple:
            lon, lat = tr.transform(x, y)
            result.append([lon, lat])
        return result
    except:
        return [list(c) for c in coords_tuple]

@st.cache_data(show_spinner=False)
def load_geojson_cached(file_hash, text):
    try: gj = json.loads(text)
    except: return [], []
    crs_info = gj.get("crs",{}); epsg_file = None
    if crs_info:
        name = crs_info.get("properties",{}).get("name","")
        if "EPSG:" in name.upper():
            try: epsg_file = int(name.upper().split("EPSG:")[-1].strip().split()[0])
            except: pass
    feats, all_c = [], []
    for i, f in enumerate(gj.get("features",[])):
        if not isinstance(f, dict): continue
        coords = parse_geom(f.get("geometry") or {})
        if len(coords) < 2: continue
        props = sanitize_props(f.get("properties") or {})
        if is_projected(coords):
            length = round(length_m_proj(coords), 2)
            coords = convert_wgs84(tuple(map(tuple, coords)), epsg_file or 32637)
        else:
            length = round(length_m_wgs(coords), 2)
        feats.append({"i":i,"len":length,"coords":coords,"props":props})
        all_c.extend(coords)
    return feats, all_c

@st.cache_data(show_spinner=False)
def load_shp_cached(file_hash, zb):
    try: import shapefile
    except: return [], []
    try:
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(BytesIO(zb)) as z: z.extractall(td)
            shp = next((os.path.join(r,f) for r,_,fs in os.walk(td) for f in fs if f.lower().endswith(".shp")),None)
            if not shp: return [], []
            epsg = None
            prj = shp.replace(".shp",".prj")
            if os.path.exists(prj):
                try:
                    from pyproj import CRS
                    with open(prj,"r",errors="ignore") as pf: wkt = pf.read()
                    ep = CRS.from_wkt(wkt).to_epsg()
                    if ep: epsg = ep
                except: pass
            sf = shapefile.Reader(shp)
            fnames = [f[0] for f in sf.fields[1:]]
            feats, all_c = [], []
            for i, sr in enumerate(sf.shapeRecords()):
                coords = [[float(p[0]),float(p[1])] for p in sr.shape.points if len(p)>=2]
                if len(coords) < 2: continue
                props = sanitize_props(dict(zip(fnames, sr.record)))
                if is_projected(coords):
                    length = round(length_m_proj(coords), 2)
                    coords = convert_wgs84(tuple(map(tuple,coords)), epsg or 32637)
                else:
                    length = round(length_m_wgs(coords), 2)
                feats.append({"i":i,"len":length,"coords":coords,"props":props})
                all_c.extend(coords)
            return feats, all_c
    except: return [], []

@st.cache_data(show_spinner=False)
def make_df_cached(feats_json):
    import pandas as pd
    feats = json.loads(feats_json)
    rows = []
    for f in feats:
        r = {"رقم الخط":f["i"],"الطول (م)":f["len"],"الطول (كم)":round(f["len"]/1000,4)}
        r.update({str(k):v for k,v in f["props"].items()})
        rows.append(r)
    return pd.DataFrame(rows)

def gen_pdf(sfeats, drawn_len, drawn_segments, stot, cost, pr1):
    """PDF مع خريطة staticmap — الخطوط المختارة + المرسوم"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rlc
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    C = rlc.HexColor

    def S(nm, **kw): return ParagraphStyle(nm, parent=styles["Normal"], **kw)

    story = [
        Paragraph("Flood Network Cost Report", S("t",fontSize=16,textColor=C("#0a2a5e"),alignment=TA_CENTER,spaceAfter=4)),
        Paragraph("Eng. Ahmed Adam | Flood Drainage Networks 2025", S("s",fontSize=9,textColor=C("#1a5fa8"),alignment=TA_CENTER,spaceAfter=12)),
        HRFlowable(width="100%",thickness=2,color=C("#1a5fa8"),spaceAfter=10),
    ]

    # ملخص
    rows_sum = [["Parameter","Value"],
        ["Lines Selected", str(len(sfeats))],
        ["Lines Length", "%.2f m  /  %.3f km" % (sum(f["len"] for f in sfeats), sum(f["len"] for f in sfeats)/1000)],
    ]
    if drawn_len > 0:
        rows_sum.append(["Drawn Line", "%.2f m  /  %.3f km" % (drawn_len, drawn_len/1000)])
    rows_sum += [
        ["Total Length","%.2f m  /  %.3f km" % (stot, stot/1000)],
        ["Price / Meter","%.2f SAR" % pr1],
        ["TOTAL COST","%.2f SAR" % cost],
        ["Millions","%.4f M SAR" % (cost/1e6)],
    ]
    t1 = Table(rows_sum, colWidths=[7*cm,10*cm])
    t1.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),C("#0a2a5e")),("TEXTCOLOR",(0,0),(-1,0),rlc.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,1),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),10),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("BACKGROUND",(0,-2),(-1,-1),C("#eaf4ff")),
        ("BACKGROUND",(0,-1),(-1,-1),C("#1a5fa8")),("TEXTCOLOR",(0,-1),(-1,-1),rlc.white),
        ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,-1),(-1,-1),12),
        ("ROWBACKGROUNDS",(0,1),(-1,-3),[rlc.white,C("#f0f7ff")]),
        ("GRID",(0,0),(-1,-1),.5,C("#d0e4f7")),("ROWHEIGHT",(0,0),(-1,-1),22),
    ]))
    story += [t1, Spacer(1,12)]

    # تفاصيل الخطوط
    if sfeats:
        story.append(Paragraph("Selected Lines", S("h",fontSize=11,textColor=C("#0a2a5e"),spaceAfter=5)))
        ld = [["Index","Length (m)","Length (km)","Cost (SAR)"]]
        for f in sfeats:
            ld.append([str(f["i"]),"%.2f"%f["len"],"%.4f"%(f["len"]/1000),"%.2f"%(f["len"]*pr1)])
        if drawn_len > 0:
            ld.append(["✏️ Drawn","%.2f"%drawn_len,"%.4f"%(drawn_len/1000),"%.2f"%(drawn_len*pr1)])
        lt = Table(ld, colWidths=[3*cm,4.5*cm,4.5*cm,7*cm])
        lt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),C("#1a5fa8")),("TEXTCOLOR",(0,0),(-1,0),rlc.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,1),(-1,-1),"Helvetica"),
            ("FONTSIZE",(0,0),(-1,-1),9),("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[rlc.white,C("#f0f7ff")]),
            ("GRID",(0,0),(-1,-1),.4,C("#d0e4f7")),("ROWHEIGHT",(0,0),(-1,-1),18),
        ]))
        story += [lt, Spacer(1,12)]

    # خريطة staticmap — zoom تلقائي مركّز على الخطوط
    try:
        from staticmap import StaticMap, Line, CircleMarker
        from reportlab.platypus import Image as RLImg

        # جمع كل الإحداثيات لحساب الـ bounding box
        all_pts = []
        for f in sfeats:
            all_pts.extend(f["coords"])
        for seg in drawn_segments:
            all_pts.extend(seg)

        if all_pts:
            lons = [p[0] for p in all_pts]
            lats = [p[1] for p in all_pts]
            min_lon, max_lon = min(lons), max(lons)
            min_lat, max_lat = min(lats), max(lats)

            span_lon = max_lon - min_lon
            span_lat = max_lat - min_lat
            max_span = max(span_lon, span_lat * 1.5)

            if max_span == 0:
                auto_zoom = 17
            else:
                raw = math.log2(360.0 / max_span) + math.log2(800 / 256) - 0.5
                auto_zoom = max(10, min(18, int(raw)))

            sm = StaticMap(800, 450,
                           url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                           padding_x=50, padding_y=40)

            COLS = ["#e74c3c", "#2980b9", "#2ecc71", "#9b59b6",
                    "#1abc9c", "#f39c12", "#16a085", "#8e44ad"]

            for idx, f in enumerate(sfeats):
                if not f["coords"]: continue
                col = COLS[idx % len(COLS)]
                pts = [(c[0], c[1]) for c in f["coords"]]
                sm.add_line(Line(pts, col, 5))
                sm.add_marker(CircleMarker(pts[0],  "#27ae60", 10))
                sm.add_marker(CircleMarker(pts[-1], "#c0392b", 10))

            # كل خط مرسوم كـ segment منفصل — هذا يمنع خطوط الوتر
            for seg in drawn_segments:
                if len(seg) < 2: continue
                pts_d = [(c[0], c[1]) for c in seg]
                sm.add_line(Line(pts_d, "#e67e22", 6))
                sm.add_marker(CircleMarker(pts_d[0],  "#27ae60", 10))
                sm.add_marker(CircleMarker(pts_d[-1], "#c0392b", 10))

            img = sm.render(zoom=auto_zoom)
            ib = BytesIO(); img.save(ib, "PNG"); ib.seek(0)

            story.append(Paragraph(
                "Location Map (OpenStreetMap) — Zoom %d" % auto_zoom,
                S("mh", fontSize=11, textColor=C("#0a2a5e"), spaceAfter=5)))
            story.append(RLImg(ib, width=17*cm, height=9.5*cm))

            # مفتاح الألوان
            legend_parts = []
            for idx, f in enumerate(sfeats):
                col = COLS[idx % len(COLS)]
                legend_parts.append(
                    f'<font color="{col}">■</font> خط #{f["i"]}')
            if drawn_segments:
                legend_parts.append('<font color="#e67e22">■</font> ✏️ Drawn')
            legend_parts += ['<font color="#27ae60">●</font> Start',
                             '<font color="#c0392b">●</font> End']
            story.append(Paragraph(
                "  |  ".join(legend_parts),
                S("leg", fontSize=8, textColor=rlc.HexColor("#555"), spaceAfter=3)))
            story.append(Paragraph(
                "© OpenStreetMap contributors",
                S("cap", fontSize=7, textColor=rlc.grey, alignment=TA_CENTER)))

    except Exception as e:
        story.append(Paragraph(
            f"Map not available: {e}",
            S("e", fontSize=8, textColor=rlc.orange, alignment=TA_CENTER)))

    story += [
        Spacer(1,10),
        HRFlowable(width="100%",thickness=1,color=C("#1a5fa8"),spaceAfter=5),
        Paragraph("Eng. Ahmed Adam | Flood Drainage Networks © 2025", S("ft",fontSize=8,textColor=C("#888"),alignment=TA_CENTER))
    ]
    doc.build(story)
    return buf.getvalue()

# ══ Session State ══
for k,v in [("feats",[]),("ac",[]),("feats_json","[]"),("sel_set","[]"),
            ("cost_result",None),("pdf_bytes",None),("_fhash",None)]:
    if k not in st.session_state: st.session_state[k]=v

# ══ Sidebar ══
with st.sidebar:
    st.markdown('<div style="background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff;padding:12px 16px;text-align:center;margin:-1px -1px 12px"><b style="font-size:.97rem">🌊 حاسبة شبكات السيول</b><br><small style="color:#b8d9f8">Eng. Ahmed Adam</small></div>', unsafe_allow_html=True)
    # مستخدم حالي + تسجيل خروج
    user_col1, user_col2 = st.columns([2,1])
    with user_col1:
        st.markdown(f'<div style="font-size:.82rem;color:#0a2a5e;padding:4px 0">👤 <b>{st.session_state.get("current_user","")}</b></div>', unsafe_allow_html=True)
    with user_col2:
        if st.button("خروج 🚪", key="logout_btn"):
            st.session_state["authenticated"] = False
            st.session_state["current_user"] = ""
            st.rerun()
    st.markdown("---")
    st.markdown("**📂 رفع بيانات الشبكة**")
    up = st.file_uploader("GeoJSON أو Shapefile (zip)", type=["geojson","json","zip"], label_visibility="collapsed")
    if up:
        raw = up.read(); ext = up.name.lower().rsplit(".",1)[-1]
        fhash = hash(raw)
        if fhash != st.session_state._fhash:
            with st.spinner("جاري التحميل..."):
                if ext in ("geojson","json"):
                    f,c = load_geojson_cached(fhash, raw.decode("utf-8","ignore"))
                else:
                    f,c = load_shp_cached(fhash, raw)
            if f:
                st.session_state.feats=f; st.session_state.ac=c
                st.session_state.feats_json=json.dumps(f,ensure_ascii=False)
                st.session_state.sel_set="[]"; st.session_state.cost_result=None
                st.session_state.pdf_bytes=None; st.session_state._fhash=fhash
                st.success(f"✅ {len(f)} خط")
            else: st.warning("لم تُوجد خطوط صالحة")

    if st.session_state.feats:
        tl = sum(x["len"] for x in st.session_state.feats)
        st.caption(f"📊 {len(st.session_state.feats)} خط — {tl/1000:.2f} كم")

    st.markdown("---")
    st.markdown("**💲 أسعار إرشادية**")
    st.markdown("""
<div class="pc"><b>🔵 أنابيب 1400 ملم</b><br><span>4,004 ريال / متر</span></div>
<div class="pc"><b>🟠 قناة صندوقية 1.8×1.4م</b><br><span>9,336 ريال / متر</span></div>
<div class="pc"><b>🟢 قناة مفتوحة 12م×1.5م</b><br><span>13,052 ريال / متر</span></div>
<div class="sig"><b>Eng: Ahmed Adam</b><br>شبكات تصريف السيول © 2025</div>""", unsafe_allow_html=True)

# ══ Header ══
st.markdown("""<div class="hdr">
  <div><h1>🌊 حاسبة تكلفة شبكات تصريف السيول</h1>
  <p>تحليل الشبكات · حساب الأطوال · تقدير التكاليف</p></div>
  <div class="bdg">Eng: Ahmed Adam</div>
</div>""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🗺️ الشبكة والحساب","📊 جدول البيانات"])

# ══════════════════════════════════════════
# TAB 1 — الشبكة والحساب (دمج التبويبين)
# ══════════════════════════════════════════
with tab1:
    import folium
    from folium.plugins import Draw, Fullscreen
    from streamlit_folium import st_folium

    feats = st.session_state.feats

    # إحصائيات سريعة
    if feats:
        tl = sum(x["len"] for x in feats)
        c1,c2,c3 = st.columns(3)
        c1.markdown(f'<div class="mc"><div class="v">{len(feats):,}</div><div class="l">عدد الخطوط</div></div>',unsafe_allow_html=True)
        c2.markdown(f'<div class="mc"><div class="v">{tl/1000:,.2f}</div><div class="l">إجمالي الطول (كم)</div></div>',unsafe_allow_html=True)
        c3.markdown(f'<div class="mc"><div class="v">{tl:,.0f}</div><div class="l">إجمالي الطول (م)</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)

    # ── الخريطة الموحدة ──
    mc = list(map_center(st.session_state.ac)) if st.session_state.ac else [RLAT, RLON]
    mz = 13 if st.session_state.ac else 10

    m = folium.Map(location=mc, zoom_start=mz, tiles="OpenStreetMap", prefer_canvas=True)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صورة فضائية").add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)

    # ── زر تكبير الخريطة (Fullscreen) ──
    Fullscreen(
        position="topleft",
        title="تكبير الخريطة",
        title_cancel="تصغير الخريطة",
        force_separate_button=True
    ).add_to(m)

    # ── رسم خطوط الملف المرفوع مع اتجاه البداية والنهاية ──
    sel_set = set(json.loads(st.session_state.sel_set))

    def arrow_icon(bearing_deg, color):
        """سهم SVG يشير باتجاه الخط"""
        return folium.DivIcon(
            html=(
                f'<div style="transform:rotate({bearing_deg}deg);'
                f'width:0;height:0;'
                f'border-left:6px solid transparent;'
                f'border-right:6px solid transparent;'
                f'border-bottom:14px solid {color};'
                f'filter:drop-shadow(0 1px 2px rgba(0,0,0,.4));"></div>'
            ),
            icon_size=(12, 14),
            icon_anchor=(6, 7)
        )

    def bearing(p1, p2):
        """زاوية الاتجاه بين نقطتين [lon,lat]"""
        lat1, lat2 = math.radians(p1[1]), math.radians(p2[1])
        dlon = math.radians(p2[0] - p1[0])
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
        return (math.degrees(math.atan2(x, y)) + 360) % 360

    for f in feats:
        is_sel = f["i"] in sel_set
        line_color  = "#e74c3c" if is_sel else "#1a5fa8"
        start_color = "#27ae60"   # أخضر — البداية دائماً
        end_color   = "#c0392b"   # أحمر — النهاية دائماً
        latlngs = [(c[1], c[0]) for c in f["coords"]]

        popup_html = (
            f"<div dir='rtl' style='font-family:Cairo,sans-serif;font-size:13px;min-width:170px'>"
            f"<b style='color:#1a5fa8;font-size:14px'>خط #{f['i']}</b><br>"
            f"الطول: <b>{f['len']:,.1f} م</b> ({f['len']/1000:.3f} كم)<br>"
            f"<span style='color:#27ae60'>● بداية</span> &nbsp; "
            f"<span style='color:#c0392b'>● نهاية</span></div>"
        )

        # الخط نفسه
        folium.PolyLine(
            latlngs,
            color=line_color, weight=5 if is_sel else 3, opacity=0.92,
            tooltip=f"خط #{f['i']} | {f['len']:,.0f} م",
            popup=folium.Popup(popup_html, max_width=220)
        ).add_to(m)

        if len(f["coords"]) >= 2:
            c_start = f["coords"][0]
            c_end   = f["coords"][-1]

            # نقطة البداية — دائرة خضراء
            folium.CircleMarker(
                location=(c_start[1], c_start[0]),
                radius=5, color="#fff", weight=2,
                fill=True, fill_color=start_color, fill_opacity=1.0,
                tooltip="بداية الخط"
            ).add_to(m)

            # نقطة النهاية — دائرة حمراء
            folium.CircleMarker(
                location=(c_end[1], c_end[0]),
                radius=5, color="#fff", weight=2,
                fill=True, fill_color=end_color, fill_opacity=1.0,
                tooltip="نهاية الخط"
            ).add_to(m)

            # سهم الاتجاه في منتصف الخط — بلون الخط نفسه
            n = len(f["coords"])
            if n >= 3:
                mid_idx = n // 2
                p1 = f["coords"][mid_idx - 1]
                p2 = f["coords"][min(mid_idx + 1, n - 1)]
                mid_coord = f["coords"][mid_idx]
                if p1 != p2:
                    b = bearing(p1, p2)
                    folium.Marker(
                        location=(mid_coord[1], mid_coord[0]),
                        icon=arrow_icon(b, line_color),
                        tooltip=f"اتجاه خط #{f['i']}"
                    ).add_to(m)
            elif n == 2:
                # خط من نقطتين فقط — السهم في المنتصف الجغرافي
                p1, p2 = f["coords"][0], f["coords"][1]
                mid_coord = [(p1[0]+p2[0])/2, (p1[1]+p2[1])/2]
                b = bearing(p1, p2)
                folium.Marker(
                    location=(mid_coord[1], mid_coord[0]),
                    icon=arrow_icon(b, line_color),
                    tooltip=f"اتجاه خط #{f['i']}"
                ).add_to(m)

    # أداة الرسم
    Draw(draw_options={
        "polyline":{"shapeOptions":{"color":"#e67e22","weight":4,"opacity":.9}},
        "polygon":False,"circle":False,"rectangle":False,
        "circlemarker":False,"marker":False},
        edit_options={"edit":True,"remove":True}).add_to(m)

    map_data = st_folium(m, width="100%", height=430,
                          returned_objects=["all_drawings"], key="main_map")

    # حساب طول الخط المرسوم + حفظ كل segment منفصلاً
    drawn_len = 0.0
    drawn_segments = []   # [ [[lon,lat],...], [[lon,lat],...] ] — كل خط مرسوم منفصل
    if map_data and map_data.get("all_drawings"):
        for drw in map_data["all_drawings"]:
            g = drw.get("geometry") or {}
            if g.get("type") == "LineString":
                c = g.get("coordinates", [])
                if len(c) >= 2:
                    seg = [[float(p[0]), float(p[1])] for p in c]
                    drawn_len += length_m_wgs(seg)
                    drawn_segments.append(seg)
    # للتوافق مع الكود القديم: drawn_coords = أول segment (أو فارغ)
    drawn_coords = drawn_segments[0] if drawn_segments else []

    # ── معلومات الخط المرسوم ──
    if drawn_len > 0:
        st.markdown('<div class="ib">✏️ <b>خط مرسوم:</b> ' + f'{drawn_len:,.2f} م ({drawn_len/1000:.3f} كم)</div>', unsafe_allow_html=True)

    # ── اختيار الخطوط (multiselect فقط) ──
    if feats:
        st.markdown("### 📌 اختيار الخطوط من الملف")
        ca1,ca2,_ = st.columns([2,2,4])
        with ca1:
            if st.button("✅ تحديد الكل",key="sel_all"):
                st.session_state.sel_set=json.dumps([f["i"] for f in feats])
                st.rerun()
        with ca2:
            if st.button("❌ إلغاء الكل",key="desel_all"):
                st.session_state.sel_set="[]"
                st.rerun()

        cur_sel = set(json.loads(st.session_state.sel_set))
        opts = [f"خط #{f['i']}  ——  {f['len']:,.1f} م" for f in feats]
        cur_opts = [opts[i] for i,f in enumerate(feats) if f["i"] in cur_sel]
        sel = st.multiselect("ابحث واختر الخطوط:", opts, default=cur_opts,
                              placeholder="اكتب رقم الخط أو اختر...", key="sel_multi")
        new_sel = set(feats[opts.index(s)]["i"] for s in sel)
        if new_sel != cur_sel:
            st.session_state.sel_set=json.dumps(list(new_sel))
            st.rerun()

    # الخطوط المختارة
    sfeats = [f for f in feats if f["i"] in set(json.loads(st.session_state.sel_set))]
    sel_len = sum(x["len"] for x in sfeats)
    stot = sel_len + drawn_len

    # إحصائيات الاختيار
    if sfeats or drawn_len > 0:
        cols_st = st.columns(4 if (sfeats and drawn_len>0) else 2)
        idx = 0
        if sfeats:
            cols_st[idx].markdown(f'<div class="mc"><div class="v">{len(sfeats)}</div><div class="l">خطوط مختارة</div></div>',unsafe_allow_html=True); idx+=1
            cols_st[idx].markdown(f'<div class="mc"><div class="v">{sel_len:,.1f} م</div><div class="l">طول الخطوط</div></div>',unsafe_allow_html=True); idx+=1
        if drawn_len > 0:
            cols_st[idx].markdown(f'<div class="mc"><div class="v">{drawn_len:,.1f} م</div><div class="l">طول المرسوم</div></div>',unsafe_allow_html=True); idx+=1
        if sfeats and drawn_len > 0:
            cols_st[idx].markdown(f'<div class="mc"><div class="v" style="color:#c0392b">{stot:,.1f} م</div><div class="l">المجموع الكلي</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)

    # ── حساب التكلفة ──
    st.markdown("### 💰 حساب التكلفة")

    PRICES = {
        "أنابيب 1400 ملم — 4,004 ر": 4004.0,
        "قناة صندوقية 1.8×1.4 — 9,336 ر": 9336.0,
        "قناة مفتوحة 12×1.5 — 13,052 ر": 13052.0,
        "سعر مخصص": None
    }
    pc1,pc2 = st.columns([3,2])
    with pc1:
        choice = st.selectbox("نوع الشبكة:", list(PRICES.keys()), key="price_choice")
    with pc2:
        if PRICES[choice] is None:
            pr1 = st.number_input("سعر المتر:", min_value=0.0, value=4004.0, step=100.0, format="%.0f", key="pr_custom")
        else:
            pr1 = PRICES[choice]
            st.markdown(f'<div class="mc" style="margin-top:8px"><div class="v" style="font-size:1.1rem">{pr1:,.0f}</div><div class="l">ريال / متر</div></div>',unsafe_allow_html=True)

    if st.button("⚡ احسب التكلفة الآن", key="b_calc"):
        if not sfeats and drawn_len == 0:
            st.warning("اختر خطاً من الملف أو ارسم خطاً على الخريطة")
        else:
            cost = stot * pr1
            st.session_state.cost_result = {
                "sfeats": sfeats,
                "drawn_len": drawn_len,
                "drawn_segments": drawn_segments,   # كل خط مرسوم كـ segment منفصل
                "drawn_coords": drawn_coords,
                "stot": stot, "cost": cost, "pr1": pr1
            }
            st.session_state.pdf_bytes = None

    if st.session_state.cost_result:
        cr = st.session_state.cost_result
        parts = []
        if cr["sfeats"]:
            parts += [f"خط #{f['i']} ({f['len']:,.0f}م)" for f in cr["sfeats"]]
        if cr["drawn_len"] > 0:
            parts.append(f"✏️ مرسوم ({cr['drawn_len']:,.0f}م)")
        info = " | ".join(parts)
        st.markdown(f"""<div class="res">
{info}<br>📏 مجموع الأطوال: <b>{cr['stot']:,.2f} م</b> ({cr['stot']/1000:.3f} كم)<br>
💲 سعر المتر: <b>{cr['pr1']:,.0f} ريال</b><br>━━━━━━━━━━━━━━━━━<br>
💰 التكلفة الإجمالية: <b style="font-size:1.3rem">{cr['cost']:,.2f} ريال</b><br>
≈ <b>{cr['cost']/1e6:.3f} مليون ريال</b></div>""",unsafe_allow_html=True)

        st.markdown("<br>",unsafe_allow_html=True)
        bp1,bp2 = st.columns(2)
        with bp1:
            if st.button("📄 إصدار تقرير PDF",key="gen_pdf"):
                with st.spinner("جاري الإنشاء..."):
                    try:
                        st.session_state.pdf_bytes = gen_pdf(
                            cr["sfeats"], cr["drawn_len"],
                            cr.get("drawn_segments", []),
                            cr["stot"], cr["cost"], cr["pr1"]
                        )
                        st.success("✅ جاهز!")
                    except Exception as e:
                        st.error(f"خطأ: {e}")
        with bp2:
            if st.session_state.pdf_bytes:
                st.download_button("⬇️ تحميل PDF",
                    data=st.session_state.pdf_bytes,
                    file_name="flood_cost_report.pdf",
                    mime="application/pdf", key="dl_pdf")

    if not feats and drawn_len == 0:
        st.markdown('<div class="ib">⬅️ ارفع ملف من القائمة الجانبية، أو ارسم خطاً مباشرة على الخريطة لحساب التكلفة.</div>',unsafe_allow_html=True)

# ══ TAB 2 — جدول البيانات ══
with tab2:
    if not st.session_state.feats:
        st.markdown('<div class="ib">⬅️ ارفع ملف من القائمة الجانبية لعرض الجدول.</div>',unsafe_allow_html=True)
    else:
        st.markdown(f"### 📋 بيانات الشبكة — {len(st.session_state.feats)} خط")
        search_idx = st.text_input("🔍 بحث برقم الخط:", placeholder="مثال: 0 أو 5", key="search_idx")
        df = make_df_cached(st.session_state.feats_json)
        if search_idx.strip():
            try:
                idx_val = int(search_idx.strip())
                df_f = df[df["رقم الخط"] == idx_val]
                if df_f.empty: st.warning(f"لا يوجد خط #{idx_val}")
                else: st.dataframe(df_f, use_container_width=True, height=200)
            except: st.warning("أدخل رقماً صحيحاً")
        else:
            st.dataframe(df, use_container_width=True, height=500)
        st.download_button("⬇️ تحميل CSV",
            df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
            "flood_network.csv","text/csv")
