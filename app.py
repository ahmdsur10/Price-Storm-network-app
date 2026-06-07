
import streamlit as st
import json, math, os, tempfile, zipfile
from io import BytesIO

st.set_page_config(page_title="حاسبة شبكات السيول", page_icon="🌊",
                   layout="wide", initial_sidebar_state="expanded",
                   menu_items={'Get Help': None, 'Report a bug': None, 'About': None})

# ══════════════════════════════
# أسعار الأنابيب حسب القطر (ملم)
# ══════════════════════════════
PIPE_PRICES = {
    400:  2713,
    500:  2935,
    600:  3145,
    700:  3431,
    800:  4009,
    900:  4299,
    1000: 4625,
    1100: 5010,
    1200: 5335,
    1300: 5725,
    1400: 6055,
}
BOX_CHANNEL_PRICE  = 9336.0
OPEN_CHANNEL_PRICE = 13052.0

LINE_TYPES = {
    "pipe":         "أنبوب",
    "box_channel":  "قناة صندوقية",
    "open_channel": "قناة مفتوحة",
}

# ══════════════════════════════
# نظام تسجيل الدخول
# ══════════════════════════════
def check_credentials(username, password):
    try:
        users = st.secrets["users"]
        stored = users.get(username)
        return stored is not None and stored == password
    except Exception:
        return False

HIDE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
html,body,[class*="css"],.stApp{font-family:'Cairo',sans-serif!important;direction:rtl}
header[data-testid="stHeader"],header,[data-testid="stToolbar"],[data-testid="stToolbarActions"],
[data-testid="baseButton-header"],[data-testid="stDecoration"],.stToolbar,#stToolbar,
div[class*="Toolbar"],div[class*="StatusWidget"],[data-testid="stStatusWidget"],
#MainMenu,[data-testid="collapsedControl"],button[title="View app fullscreen"],
a[href*="streamlit.io"],a[href*="github.com"],button[kind="header"],
[data-testid="baseButton-headerNoPadding"]{
    display:none!important;visibility:hidden!important;opacity:0!important;
    height:0!important;max-height:0!important;overflow:hidden!important;pointer-events:none!important}
footer,footer *{display:none!important;visibility:hidden!important}
.stApp>header{display:none!important}
.block-container{padding-top:1rem!important}
</style>
"""

HIDE_JS = """<script>
(function(){
  const S=['header[data-testid="stHeader"]','[data-testid="stToolbar"]',
    '#MainMenu','footer','a[href*="github.com"]','a[href*="streamlit.io"]'];
  function h(d){if(!d)return;try{S.forEach(s=>d.querySelectorAll(s)
    .forEach(el=>el.style.cssText+='display:none!important;'));
    d.querySelectorAll('button,a,span').forEach(el=>{const t=(el.innerText||'').trim();
    if(['Fork','GitHub','Share'].some(w=>t.includes(w))){
      el.style.cssText+='display:none!important;';}});}catch(e){}}
  function r(){h(document);try{h(window.parent.document);}catch(e){}}
  r();setInterval(r,300);
  try{new MutationObserver(r).observe(document.documentElement,{childList:true,subtree:true});}catch(e){}
})();
</script>"""

def inject_security():
    import streamlit.components.v1 as components
    st.markdown(HIDE_CSS, unsafe_allow_html=True)
    components.html(HIDE_JS, height=0)

def login_page():
    inject_security()
    st.markdown("""<style>
.stApp{background:linear-gradient(135deg,#050e1f 0%,#091830 40%,#0d2447 100%)!important;min-height:100vh}
.block-container{padding:0!important;max-width:100%!important}
.login-title{text-align:center;color:#fff;font-size:1.5rem;font-weight:900;margin:10px 0 4px}
.login-sub{text-align:center;color:rgba(180,210,255,.7);font-size:.82rem;margin-bottom:28px}
.login-div{height:1px;background:linear-gradient(90deg,transparent,rgba(26,95,168,.5),transparent);margin-bottom:24px}
.login-foot{text-align:center;color:rgba(180,210,255,.35);font-size:.72rem;margin-top:20px}
.stTextInput>div>div>input{background:rgba(255,255,255,.06)!important;border:1.5px solid rgba(255,255,255,.12)!important;
  border-radius:12px!important;color:#fff!important;font-family:'Cairo',sans-serif!important;padding:12px 16px!important;direction:rtl!important}
.stTextInput label{color:rgba(180,210,255,.85)!important;font-family:'Cairo',sans-serif!important;font-size:.85rem!important;font-weight:600!important}
.stButton>button{background:linear-gradient(135deg,#1a5fa8,#0a2a5e)!important;border:none!important;
  border-radius:12px!important;color:#fff!important;font-family:'Cairo',sans-serif!important;font-weight:700!important;padding:13px!important;width:100%!important}
</style>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        st.markdown('<div style="text-align:center;font-size:3rem;margin:20px 0 8px">🌊</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-title">حاسبة شبكات تصريف السيول</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Flood Drainage Network Calculator · Eng. Ahmed Adam</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-div"></div>', unsafe_allow_html=True)
        username = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم", key="login_user")
        password = st.text_input("كلمة المرور", type="password", placeholder="• • • • • • • •", key="login_pass")
        if st.button("🔑  تسجيل الدخول", use_container_width=True):
            if check_credentials(username.strip(), password):
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username.strip()
                st.rerun()
            else:
                st.error("❌  اسم المستخدم أو كلمة المرور غير صحيحة")
        st.markdown('<div class="login-foot">© 2025 Flood Drainage Networks — جميع الحقوق محفوظة</div>', unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    login_page()
    st.stop()

inject_security()

# ══ CSS رئيسي ══
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
html,body,[class*="css"],.stApp{font-family:'Cairo',sans-serif!important;direction:rtl}
[data-testid="stSidebar"]{min-width:330px!important;max-width:380px!important;background:#f7f9fc!important}
.hdr{background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff;padding:14px 20px;border-radius:10px;
  margin-bottom:12px;display:flex;align-items:center;justify-content:space-between}
.hdr h1{margin:0;font-size:1.25rem;font-weight:900}
.hdr p{margin:2px 0 0;font-size:.8rem;color:#b8d9f8}
.hdr .bdg{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);
  padding:4px 12px;border-radius:14px;font-size:.75rem;font-weight:700}
.mc{background:#fff;border-radius:8px;padding:10px 14px;box-shadow:0 2px 6px rgba(0,0,0,.07);
  border-top:3px solid #1a5fa8;text-align:center}
.mc .v{font-size:1.35rem;font-weight:900;color:#0a2a5e}
.mc .l{font-size:.75rem;color:#6b7a99;margin-top:2px}
.res{background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff!important;padding:16px 20px;
  border-radius:10px;font-size:1rem;font-weight:700;text-align:center;
  box-shadow:0 4px 14px rgba(26,95,168,.3);margin-top:8px;line-height:2}
.ib{background:#eaf4ff;border-right:4px solid #1a5fa8;border-radius:6px;
  padding:9px 13px;font-size:.83rem;color:#0a2a5e;margin-bottom:8px;direction:rtl;line-height:1.8}
.pc{background:#fff;border:1.5px solid #d0e4f7;border-right:5px solid #1a5fa8;
  border-radius:6px;padding:7px 11px;margin-bottom:5px;font-size:.8rem;color:#1a2a3a}
.pc b{color:#0a2a5e}
.sig{background:#0a2a5e;color:#a8d0f0!important;text-align:center;
  padding:9px;border-radius:7px;margin-top:10px;font-size:.78rem}
.sig b{color:#fff!important}
.stButton>button{background:linear-gradient(135deg,#1a5fa8,#0a2a5e)!important;color:#fff!important;
  border:none!important;border-radius:8px!important;font-family:'Cairo',sans-serif!important;
  font-weight:700!important;font-size:.93rem!important;width:100%!important;padding:8px!important}
.seg-card{background:#fff;border:1.5px solid #d0e4f7;border-right:5px solid #0a2a5e;
  border-radius:8px;padding:12px 16px;margin-bottom:10px}
.seg-card h4{color:#0a2a5e;margin:0 0 6px;font-size:.9rem}
.tbadge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.75rem;font-weight:700;margin-bottom:4px}
.tp{background:#eaf4ff;color:#1a5fa8}
.tb{background:#fff3e0;color:#e65100}
.to{background:#e8f5e9;color:#2e7d32}
.section-title{color:#0a2a5e;font-size:1rem;font-weight:900;margin:16px 0 8px;
  border-bottom:2px solid #1a5fa8;padding-bottom:4px}
</style>""", unsafe_allow_html=True)

RLAT, RLON = 24.7136, 46.6753

# ══════════════════════════════
# دوال مساعدة
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

def get_price(line_type, diameter_mm=None, custom_price=None):
    """سعر المتر الواحد"""
    if custom_price and custom_price > 0:
        return float(custom_price)
    if line_type == "box_channel":
        return BOX_CHANNEL_PRICE
    if line_type == "open_channel":
        return OPEN_CHANNEL_PRICE
    # أنبوب
    if diameter_mm and diameter_mm in PIPE_PRICES:
        return float(PIPE_PRICES[diameter_mm])
    if diameter_mm:
        closest = min(PIPE_PRICES.keys(), key=lambda x: abs(x - diameter_mm))
        return float(PIPE_PRICES[closest])
    return float(PIPE_PRICES[1400])

def sanitize_props(props):
    import datetime
    clean = {}
    for k, v in props.items():
        if v is None: clean[str(k)] = None
        elif isinstance(v, (int, float, bool)): clean[str(k)] = v
        elif isinstance(v, str): clean[str(k)] = v
        elif isinstance(v, bytes):
            try: clean[str(k)] = v.decode("utf-8","ignore")
            except: clean[str(k)] = ""
        elif isinstance(v, (datetime.date, datetime.datetime)): clean[str(k)] = str(v)
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
        return [[lon, lat] for lon, lat in (tr.transform(x, y) for x, y in coords_tuple)]
    except:
        return [list(c) for c in coords_tuple]

@st.cache_data(show_spinner=False)
def load_geojson_cached(file_hash, text):
    try: gj = json.loads(text)
    except: return [], [], []
    crs_info = gj.get("crs",{}); epsg_file = None
    if crs_info:
        name = crs_info.get("properties",{}).get("name","")
        if "EPSG:" in name.upper():
            try: epsg_file = int(name.upper().split("EPSG:")[-1].strip().split()[0])
            except: pass
    feats, all_c, all_keys = [], [], set()
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
        all_c.extend(coords); all_keys.update(props.keys())
    return feats, all_c, list(all_keys)

@st.cache_data(show_spinner=False)
def load_shp_cached(file_hash, zb):
    try: import shapefile
    except: return [], [], []
    try:
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(BytesIO(zb)) as z: z.extractall(td)
            shp = next((os.path.join(r,f) for r,_,fs in os.walk(td) for f in fs if f.lower().endswith(".shp")),None)
            if not shp: return [], [], []
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
            feats, all_c, all_keys = [], [], set()
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
                all_c.extend(coords); all_keys.update(props.keys())
            return feats, all_c, list(all_keys)
    except: return [], [], []

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

# ══════════════════════════════
# دالة PDF محسّنة مع دعم العربية
# ══════════════════════════════
def ar(text):
    """تحويل النص العربي للعرض الصحيح في PDF"""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except:
        return str(text)

def gen_pdf(segments_data, stot, total_cost):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rlc
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # تسجيل خط يدعم العربية
    FONT_PATH  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FONTB_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        pdfmetrics.registerFont(TTFont("ArabicFont",  FONT_PATH))
        pdfmetrics.registerFont(TTFont("ArabicFontB", FONTB_PATH))
        FONT  = "ArabicFont"
        FONTB = "ArabicFontB"
    except:
        FONT  = "Helvetica"
        FONTB = "Helvetica-Bold"

    C = rlc.HexColor
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()

    def S(nm, **kw):
        return ParagraphStyle(nm, parent=styles["Normal"], fontName=FONT, **kw)
    def SB(nm, **kw):
        return ParagraphStyle(nm, parent=styles["Normal"], fontName=FONTB, **kw)

    story = []

    # ── رأس التقرير ──
    story.append(Paragraph(ar("تقرير تكلفة شبكات تصريف السيول"),
        SB("title", fontSize=16, textColor=C("#0a2a5e"), alignment=TA_CENTER, spaceAfter=4)))
    story.append(Paragraph("Eng. Ahmed Adam | Flood Drainage Networks 2025",
        S("sub", fontSize=9, textColor=C("#1a5fa8"), alignment=TA_CENTER, spaceAfter=10)))
    story.append(HRFlowable(width="100%", thickness=2, color=C("#1a5fa8"), spaceAfter=10))

    # ── ملخص ──
    sum_rows = [
        [ar("البيان"), ar("القيمة")],
        [ar("عدد العناصر"), str(len(segments_data))],
        [ar("مجموع الأطوال"), "%.2f m  /  %.3f km" % (stot, stot/1000)],
        [ar("التكلفة الإجمالية"), "%.2f SAR" % total_cost],
        [ar("بالمليون"), "%.4f M SAR" % (total_cost/1e6)],
    ]
    t1 = Table(sum_rows, colWidths=[7*cm, 10*cm])
    t1.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),C("#0a2a5e")),
        ("TEXTCOLOR",(0,0),(-1,0),rlc.white),
        ("FONTNAME",(0,0),(-1,0),FONTB),
        ("FONTNAME",(0,1),(-1,-1),FONT),
        ("FONTSIZE",(0,0),(-1,-1),10),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("BACKGROUND",(0,-2),(-1,-1),C("#eaf4ff")),
        ("BACKGROUND",(0,-1),(-1,-1),C("#1a5fa8")),
        ("TEXTCOLOR",(0,-1),(-1,-1),rlc.white),
        ("FONTNAME",(0,-1),(-1,-1),FONTB),
        ("FONTSIZE",(0,-1),(-1,-1),12),
        ("ROWBACKGROUNDS",(0,1),(-1,-3),[rlc.white,C("#f0f7ff")]),
        ("GRID",(0,0),(-1,-1),.5,C("#d0e4f7")),
        ("ROWHEIGHT",(0,0),(-1,-1),22),
    ]))
    story += [t1, Spacer(1, 14)]

    # ── تفاصيل العناصر ──
    story.append(Paragraph(ar("تفاصيل العناصر"),
        SB("h2", fontSize=11, textColor=C("#0a2a5e"), spaceAfter=6)))

    detail_rows = [[
        ar("م"), ar("النوع"), ar("القطر (ملم)"),
        ar("الطول (م)"), ar("سعر المتر"), ar("التكلفة (ريال)")
    ]]
    for s in segments_data:
        type_ar  = ar(LINE_TYPES.get(s["line_type"], s["line_type"]))
        dia_txt  = str(s["diameter_mm"]) if s.get("diameter_mm") else "-"
        detail_rows.append([
            s["label"],
            type_ar,
            dia_txt,
            "%.1f" % s["len"],
            "%.0f" % s["price_per_m"],
            "%.2f" % s["cost"],
        ])

    lt = Table(detail_rows, colWidths=[1.5*cm, 3.5*cm, 2.5*cm, 3*cm, 3*cm, 4.5*cm])
    lt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),C("#1a5fa8")),
        ("TEXTCOLOR",(0,0),(-1,0),rlc.white),
        ("FONTNAME",(0,0),(-1,0),FONTB),
        ("FONTNAME",(0,1),(-1,-1),FONT),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[rlc.white,C("#f0f7ff")]),
        ("GRID",(0,0),(-1,-1),.4,C("#d0e4f7")),
        ("ROWHEIGHT",(0,0),(-1,-1),18),
    ]))
    story += [lt, Spacer(1, 14)]

    # ── خريطة الموقع ──
    try:
        from staticmap import StaticMap, Line, CircleMarker
        from reportlab.platypus import Image as RLImg

        all_pts = [pt for s in segments_data for pt in s.get("coords",[])]
        if all_pts:
            lons = [p[0] for p in all_pts]; lats = [p[1] for p in all_pts]
            span = max(max(lons)-min(lons), (max(lats)-min(lats))*1.5)
            zoom = 17 if span==0 else max(10, min(18, int(math.log2(360.0/span)+math.log2(800/256)-0.5)))

            sm = StaticMap(800, 450,
                           url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                           padding_x=50, padding_y=40)
            LINE_COLORS = ["#c0392b","#2980b9","#16a085","#8e44ad","#d35400","#27ae60"]
            for idx, s in enumerate(segments_data):
                if not s.get("coords"): continue
                # الخط المرسوم والخط من الملف كلاهما باللون الأسود في التقرير
                col = "#222222"
                pts = [(c[0],c[1]) for c in s["coords"]]
                sm.add_line(Line(pts, col, 5))
                sm.add_marker(CircleMarker(pts[0],  "#27ae60", 10))
                sm.add_marker(CircleMarker(pts[-1], "#c0392b", 10))

            img = sm.render(zoom=zoom)
            ib = BytesIO(); img.save(ib,"PNG"); ib.seek(0)
            story.append(Paragraph(
                ar("خريطة الموقع") + " (OpenStreetMap) — Zoom %d" % zoom,
                SB("mh", fontSize=11, textColor=C("#0a2a5e"), spaceAfter=5)))
            story.append(RLImg(ib, width=17*cm, height=9.5*cm))
            story.append(Paragraph("© OpenStreetMap contributors",
                S("cap", fontSize=7, textColor=rlc.grey, alignment=TA_CENTER)))
    except Exception as e:
        story.append(Paragraph("Map not available: %s" % str(e),
            S("err", fontSize=8, textColor=rlc.orange, alignment=TA_CENTER)))

    story += [
        Spacer(1,10),
        HRFlowable(width="100%", thickness=1, color=C("#1a5fa8"), spaceAfter=5),
        Paragraph("Eng. Ahmed Adam | Flood Drainage Networks © 2025",
                  S("ft", fontSize=8, textColor=C("#888"), alignment=TA_CENTER))
    ]
    doc.build(story)
    return buf.getvalue()

# ══════════════════════════════
# Session State
# ══════════════════════════════
DEFAULTS = {
    "feats":[], "ac":[], "feats_json":"[]", "sel_set":"[]",
    "cost_result":None, "pdf_bytes":None, "_fhash":None,
    "props_keys":[],
    # meta الخطوط المختارة من الملف: {feat_i: {line_type, diameter_mm, custom_price}}
    "sel_feat_meta":{},
    # meta الخطوط المرسومة: list of {line_type, diameter_mm, custom_price}
    "drawn_meta":[],
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══ Sidebar ══
with st.sidebar:
    st.markdown('<div style="background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff;'
                'padding:12px 16px;text-align:center;margin:-1px -1px 12px">'
                '<b style="font-size:.97rem">🌊 حاسبة شبكات السيول</b><br>'
                '<small style="color:#b8d9f8">Eng. Ahmed Adam</small></div>', unsafe_allow_html=True)
    uc1, uc2 = st.columns([2,1])
    with uc1:
        st.markdown(f'<div style="font-size:.82rem;color:#0a2a5e;padding:4px 0">'
                    f'👤 <b>{st.session_state.get("current_user","")}</b></div>', unsafe_allow_html=True)
    with uc2:
        if st.button("خروج 🚪", key="logout_btn"):
            st.session_state["authenticated"] = False
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
                    f, c, pk = load_geojson_cached(fhash, raw.decode("utf-8","ignore"))
                else:
                    f, c, pk = load_shp_cached(fhash, raw)
            if f:
                st.session_state.feats = f
                st.session_state.ac = c
                st.session_state.feats_json = json.dumps(f, ensure_ascii=False)
                st.session_state.sel_set = "[]"
                st.session_state.cost_result = None
                st.session_state.pdf_bytes = None
                st.session_state._fhash = fhash
                st.session_state.props_keys = pk
                st.session_state.sel_feat_meta = {}
                st.success(f"✅ {len(f)} خط")
            else:
                st.warning("لم تُوجد خطوط صالحة")
    if st.session_state.feats:
        tl = sum(x["len"] for x in st.session_state.feats)
        st.caption(f"📊 {len(st.session_state.feats)} خط — {tl/1000:.2f} كم")

    st.markdown("---")
    st.markdown("**💲 الأسعار الإرشادية**")
    st.markdown('<div style="font-size:.78rem;color:#0a2a5e;font-weight:700;margin-bottom:4px">🔵 أنابيب حسب القطر</div>', unsafe_allow_html=True)
    for dia, price in PIPE_PRICES.items():
        st.markdown(f'<div class="pc"><b>{dia} ملم</b> <span style="float:left;color:#c0392b;font-weight:900">{price:,}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pc" style="border-right-color:#e65100"><b>🟠 قناة صندوقية</b><br><span style="color:#c0392b;font-weight:900">{int(BOX_CHANNEL_PRICE):,} ر/م</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pc" style="border-right-color:#2e7d32"><b>🟢 قناة مفتوحة</b><br><span style="color:#c0392b;font-weight:900">{int(OPEN_CHANNEL_PRICE):,} ر/م</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sig"><b>Eng: Ahmed Adam</b><br>شبكات تصريف السيول © 2025</div>', unsafe_allow_html=True)

# ══ Header ══
st.markdown("""<div class="hdr">
  <div><h1>🌊 حاسبة تكلفة شبكات تصريف السيول</h1>
  <p>تحليل الشبكات · حساب الأطوال · تقدير التكاليف</p></div>
  <div class="bdg">Eng: Ahmed Adam</div>
</div>""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🗺️ الشبكة والحساب", "📊 جدول البيانات"])

# ══════════════════════════════════════════
# TAB 1
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

    # ── الخريطة ──
    mc = list(map_center(st.session_state.ac)) if st.session_state.ac else [RLAT, RLON]
    mz = 13 if st.session_state.ac else 10
    m = folium.Map(location=mc, zoom_start=mz, tiles="OpenStreetMap", prefer_canvas=True)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صورة فضائية").add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    Fullscreen(position="topleft", title="تكبير", title_cancel="تصغير", force_separate_button=True).add_to(m)

    sel_set = set(json.loads(st.session_state.sel_set))

    def arrow_icon(bearing_deg, color):
        return folium.DivIcon(
            html=(f'<div style="transform:rotate({bearing_deg}deg);width:0;height:0;'
                  f'border-left:6px solid transparent;border-right:6px solid transparent;'
                  f'border-bottom:14px solid {color};filter:drop-shadow(0 1px 2px rgba(0,0,0,.4));"></div>'),
            icon_size=(12,14), icon_anchor=(6,7))

    def bearing(p1, p2):
        lat1, lat2 = math.radians(p1[1]), math.radians(p2[1])
        dlon = math.radians(p2[0]-p1[0])
        x = math.sin(dlon)*math.cos(lat2)
        y = math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
        return (math.degrees(math.atan2(x,y))+360)%360

    for f in feats:
        is_sel = f["i"] in sel_set
        line_color = "#e74c3c" if is_sel else "#222222"
        latlngs = [(c[1],c[0]) for c in f["coords"]]
        popup_html = (f"<div dir='rtl' style='font-family:Cairo,sans-serif;font-size:13px;min-width:160px'>"
                      f"<b style='color:#1a5fa8'>خط #{f['i']}</b><br>"
                      f"الطول: <b>{f['len']:,.1f} م</b></div>")
        folium.PolyLine(latlngs, color=line_color, weight=5 if is_sel else 3, opacity=0.9,
                        tooltip=f"خط #{f['i']} | {f['len']:,.0f} م",
                        popup=folium.Popup(popup_html, max_width=200)).add_to(m)
        if len(f["coords"]) >= 2:
            folium.CircleMarker(location=(f["coords"][0][1],f["coords"][0][0]),
                radius=5, color="#fff", weight=2, fill=True, fill_color="#27ae60",
                fill_opacity=1.0, tooltip="بداية الخط").add_to(m)
            folium.CircleMarker(location=(f["coords"][-1][1],f["coords"][-1][0]),
                radius=5, color="#fff", weight=2, fill=True, fill_color="#c0392b",
                fill_opacity=1.0, tooltip="نهاية الخط").add_to(m)
            n = len(f["coords"])
            if n >= 2:
                mid_idx = n//2
                p1 = f["coords"][max(0,mid_idx-1)]
                p2 = f["coords"][min(n-1,mid_idx+1)]
                mid = f["coords"][mid_idx]
                if p1 != p2:
                    folium.Marker(location=(mid[1],mid[0]),
                        icon=arrow_icon(bearing(p1,p2), line_color),
                        tooltip=f"اتجاه خط #{f['i']}").add_to(m)

    # أداة الرسم — اللون الأخضر
    Draw(draw_options={
        "polyline":{"shapeOptions":{"color":"#00aa00","weight":4,"opacity":.9}},
        "polygon":False,"circle":False,"rectangle":False,
        "circlemarker":False,"marker":False},
        edit_options={"edit":True,"remove":True}).add_to(m)

    map_data = st_folium(m, width="100%", height=430,
                          returned_objects=["all_drawings"], key="main_map")

    # ── قراءة الخطوط المرسومة ──
    raw_drawn = []
    if map_data and map_data.get("all_drawings"):
        for drw in map_data["all_drawings"]:
            g = drw.get("geometry") or {}
            if g.get("type") == "LineString":
                c = g.get("coordinates",[])
                if len(c) >= 2:
                    raw_drawn.append([[float(p[0]),float(p[1])] for p in c])

    # مزامنة drawn_meta
    cur_meta = st.session_state.drawn_meta
    if len(raw_drawn) != len(cur_meta):
        new_meta = []
        for i, _ in enumerate(raw_drawn):
            if i < len(cur_meta):
                new_meta.append(cur_meta[i])
            else:
                new_meta.append({"line_type":"pipe","diameter_mm":1400,"custom_price":0})
        st.session_state.drawn_meta = new_meta

    # ════════════════════════════════════════
    # قسم اختيار الخطوط من الملف
    # ════════════════════════════════════════
    if feats:
        st.markdown('<div class="section-title">📌 اختيار الخطوط من الملف</div>', unsafe_allow_html=True)
        ca1,ca2,_ = st.columns([2,2,4])
        with ca1:
            if st.button("✅ تحديد الكل", key="sel_all"):
                st.session_state.sel_set = json.dumps([f["i"] for f in feats])
                st.rerun()
        with ca2:
            if st.button("❌ إلغاء الكل", key="desel_all"):
                st.session_state.sel_set = "[]"
                st.rerun()

        cur_sel = set(json.loads(st.session_state.sel_set))
        opts = [f"خط #{f['i']}  ——  {f['len']:,.1f} م" for f in feats]
        cur_opts = [opts[i] for i,f in enumerate(feats) if f["i"] in cur_sel]
        sel = st.multiselect("ابحث واختر الخطوط:", opts, default=cur_opts,
                              placeholder="اكتب رقم الخط أو اختر...", key="sel_multi")
        new_sel = set(feats[opts.index(s)]["i"] for s in sel)
        if new_sel != cur_sel:
            st.session_state.sel_set = json.dumps(list(new_sel))
            for k in list(st.session_state.sel_feat_meta.keys()):
                if k not in new_sel:
                    del st.session_state.sel_feat_meta[k]
            st.rerun()

    sfeats = [f for f in feats if f["i"] in set(json.loads(st.session_state.sel_set))]

    # ════════════════════════════════════════
    # إعدادات الخطوط المختارة من الملف
    # ════════════════════════════════════════
    if sfeats:
        st.markdown('<div class="section-title">⚙️ إعدادات الخطوط المختارة من الملف</div>', unsafe_allow_html=True)
        props_keys = st.session_state.props_keys

        for f in sfeats:
            feat_i = f["i"]
            if feat_i not in st.session_state.sel_feat_meta:
                st.session_state.sel_feat_meta[feat_i] = {
                    "line_type":"pipe", "diameter_mm":1400, "custom_price":0}
            meta = st.session_state.sel_feat_meta[feat_i]

            with st.expander(f"🔧 خط #{feat_i}  —  {f['len']:,.1f} م", expanded=False):

                # ── الخطوة 1: نوع الخط ──
                st.markdown("**① نوع الخط:**")
                lt_choice = st.radio(
                    "نوع",
                    list(LINE_TYPES.values()),
                    index=list(LINE_TYPES.keys()).index(meta.get("line_type","pipe")),
                    key=f"lt_{feat_i}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                meta["line_type"] = [k for k,v in LINE_TYPES.items() if v == lt_choice][0]

                # ── الخطوة 2: القطر (فقط إذا أنبوب) ──
                if meta["line_type"] == "pipe":
                    st.markdown("**② القطر (ملم):**")
                    dia_col_opts = ["إدخال يدوي"] + [k for k in props_keys]
                    dc1, dc2 = st.columns([2,2])
                    with dc1:
                        dia_src = st.selectbox("مصدر القطر:",
                            dia_col_opts, key=f"diasrc_{feat_i}")
                    with dc2:
                        if dia_src == "إدخال يدوي":
                            dia_manual = st.selectbox(
                                "القطر (ملم):",
                                list(PIPE_PRICES.keys()),
                                index=list(PIPE_PRICES.keys()).index(
                                    meta.get("diameter_mm",1400)
                                    if meta.get("diameter_mm") in PIPE_PRICES else 1400),
                                key=f"dia_{feat_i}")
                            meta["diameter_mm"] = dia_manual
                        else:
                            # قراءة القطر من عمود الملف
                            dia_val = f["props"].get(dia_src)
                            try:
                                dia_from_file = int(float(dia_val))
                                closest = min(PIPE_PRICES.keys(), key=lambda x: abs(x-dia_from_file))
                                meta["diameter_mm"] = closest
                                st.markdown(
                                    f'<div class="ib" style="margin-top:22px">'
                                    f'📏 من الملف: <b>{dia_from_file}</b> ملم → معياري: <b>{closest}</b> ملم'
                                    f'</div>', unsafe_allow_html=True)
                            except:
                                st.warning("قيمة القطر في الملف غير صالحة — سيُستخدم 1400 ملم")
                                meta["diameter_mm"] = 1400
                else:
                    meta["diameter_mm"] = None

                # ── الخطوة 3: السعر ──
                st.markdown("**③ السعر (ريال/م):**")
                guide_price = get_price(meta["line_type"], meta.get("diameter_mm"), 0)
                pc1, pc2 = st.columns([2,2])
                with pc1:
                    price_mode = st.radio(
                        "مصدر السعر:",
                        ["إرشادي", "مخصص"],
                        key=f"prmode_{feat_i}",
                        horizontal=True,
                        label_visibility="collapsed")
                with pc2:
                    if price_mode == "مخصص":
                        cp = st.number_input("سعر مخصص:", min_value=0.0,
                            value=float(meta.get("custom_price") or guide_price),
                            step=100.0, format="%.0f", key=f"cp_{feat_i}")
                        meta["custom_price"] = cp
                        final_price = cp
                    else:
                        meta["custom_price"] = 0
                        final_price = guide_price
                        st.markdown(
                            f'<div class="mc" style="margin-top:4px">'
                            f'<div class="v" style="font-size:1.1rem">{guide_price:,.0f}</div>'
                            f'<div class="l">ريال/م (إرشادي)</div></div>',
                            unsafe_allow_html=True)

                st.markdown(
                    f'<div style="background:#eaf4ff;border-radius:6px;padding:7px 12px;'
                    f'margin-top:6px;font-size:.82rem;color:#0a2a5e">'
                    f'💰 التكلفة المتوقعة: <b style="color:#c0392b">'
                    f'{f["len"] * final_price:,.0f} ريال</b> '
                    f'({f["len"]:,.1f} م × {final_price:,.0f} ر/م)</div>',
                    unsafe_allow_html=True)

                st.session_state.sel_feat_meta[feat_i] = meta

    # ════════════════════════════════════════
    # إعدادات الخطوط المرسومة
    # ════════════════════════════════════════
    if raw_drawn:
        st.markdown('<div class="section-title">✏️ إعدادات الخطوط المرسومة</div>', unsafe_allow_html=True)

        for idx, seg in enumerate(raw_drawn):
            seg_len = length_m_wgs(seg)
            if idx >= len(st.session_state.drawn_meta):
                st.session_state.drawn_meta.append({"line_type":"pipe","diameter_mm":1400,"custom_price":0})
            meta_d = st.session_state.drawn_meta[idx]

            with st.expander(f"✏️ خط مرسوم #{idx+1}  —  {seg_len:,.1f} م", expanded=True):

                # ── نوع الخط ──
                st.markdown("**① نوع الخط:**")
                lt_d = st.radio(
                    "نوع",
                    list(LINE_TYPES.values()),
                    index=list(LINE_TYPES.keys()).index(meta_d.get("line_type","pipe")),
                    key=f"dlt_{idx}",
                    horizontal=True,
                    label_visibility="collapsed")
                meta_d["line_type"] = [k for k,v in LINE_TYPES.items() if v == lt_d][0]

                # ── القطر (إذا أنبوب) ──
                if meta_d["line_type"] == "pipe":
                    st.markdown("**② القطر (ملم):**")
                    dia_d = st.selectbox(
                        "القطر:",
                        list(PIPE_PRICES.keys()),
                        index=list(PIPE_PRICES.keys()).index(
                            meta_d.get("diameter_mm",1400)
                            if meta_d.get("diameter_mm") in PIPE_PRICES else 1400),
                        key=f"ddia_{idx}")
                    meta_d["diameter_mm"] = dia_d
                else:
                    meta_d["diameter_mm"] = None

                # ── السعر ──
                st.markdown("**③ السعر (ريال/م):**")
                guide_d = get_price(meta_d["line_type"], meta_d.get("diameter_mm"), 0)
                dp1, dp2 = st.columns([2,2])
                with dp1:
                    price_mode_d = st.radio(
                        "مصدر السعر:",
                        ["إرشادي", "مخصص"],
                        key=f"dprmode_{idx}",
                        horizontal=True,
                        label_visibility="collapsed")
                with dp2:
                    if price_mode_d == "مخصص":
                        cp_d = st.number_input("سعر مخصص:", min_value=0.0,
                            value=float(meta_d.get("custom_price") or guide_d),
                            step=100.0, format="%.0f", key=f"dcp_{idx}")
                        meta_d["custom_price"] = cp_d
                        final_d = cp_d
                    else:
                        meta_d["custom_price"] = 0
                        final_d = guide_d
                        st.markdown(
                            f'<div class="mc" style="margin-top:4px">'
                            f'<div class="v" style="font-size:1.1rem">{guide_d:,.0f}</div>'
                            f'<div class="l">ريال/م (إرشادي)</div></div>',
                            unsafe_allow_html=True)

                st.markdown(
                    f'<div style="background:#eaf4ff;border-radius:6px;padding:7px 12px;'
                    f'margin-top:6px;font-size:.82rem;color:#0a2a5e">'
                    f'💰 التكلفة المتوقعة: <b style="color:#c0392b">'
                    f'{seg_len * final_d:,.0f} ريال</b> '
                    f'({seg_len:,.1f} م × {final_d:,.0f} ر/م)</div>',
                    unsafe_allow_html=True)

                st.session_state.drawn_meta[idx] = meta_d

    # ════════════════════════════════════════
    # ملخص الاختيار
    # ════════════════════════════════════════
    if sfeats or raw_drawn:
        total_sel_len   = sum(f["len"] for f in sfeats)
        total_drawn_len = sum(length_m_wgs(s) for s in raw_drawn)
        stot = total_sel_len + total_drawn_len
        cs1,cs2,cs3,cs4 = st.columns(4)
        cs1.markdown(f'<div class="mc"><div class="v">{len(sfeats)}</div><div class="l">خطوط من ملف</div></div>',unsafe_allow_html=True)
        cs2.markdown(f'<div class="mc"><div class="v">{len(raw_drawn)}</div><div class="l">خطوط مرسومة</div></div>',unsafe_allow_html=True)
        cs3.markdown(f'<div class="mc"><div class="v">{stot:,.1f}</div><div class="l">مجموع الأطوال (م)</div></div>',unsafe_allow_html=True)
        cs4.markdown(f'<div class="mc"><div class="v">{stot/1000:.3f}</div><div class="l">مجموع الأطوال (كم)</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)

    # ════════════════════════════════════════
    # زر الحساب
    # ════════════════════════════════════════
    st.markdown('<div class="section-title">💰 حساب التكلفة</div>', unsafe_allow_html=True)

    if st.button("⚡ احسب التكلفة الآن", key="b_calc"):
        if not sfeats and not raw_drawn:
            st.warning("اختر خطاً من الملف أو ارسم خطاً على الخريطة")
        else:
            segments_data = []
            total_cost = 0.0
            total_len  = 0.0

            for f in sfeats:
                meta = st.session_state.sel_feat_meta.get(
                    f["i"], {"line_type":"pipe","diameter_mm":1400,"custom_price":0})
                ppm  = get_price(meta["line_type"], meta.get("diameter_mm"), meta.get("custom_price",0))
                cost = f["len"] * ppm
                total_cost += cost; total_len += f["len"]
                segments_data.append({
                    "label": f"#{f['i']}",
                    "len": f["len"],
                    "line_type": meta["line_type"],
                    "diameter_mm": meta.get("diameter_mm"),
                    "price_per_m": ppm,
                    "cost": cost,
                    "coords": f["coords"],
                    "is_drawn": False,
                })

            for idx, seg in enumerate(raw_drawn):
                seg_len = length_m_wgs(seg)
                meta_d  = st.session_state.drawn_meta[idx] if idx < len(st.session_state.drawn_meta) else {}
                ppm  = get_price(meta_d.get("line_type","pipe"), meta_d.get("diameter_mm"), meta_d.get("custom_price",0))
                cost = seg_len * ppm
                total_cost += cost; total_len += seg_len
                segments_data.append({
                    "label": f"✏{idx+1}",
                    "len": seg_len,
                    "line_type": meta_d.get("line_type","pipe"),
                    "diameter_mm": meta_d.get("diameter_mm"),
                    "price_per_m": ppm,
                    "cost": cost,
                    "coords": seg,
                    "is_drawn": True,
                })

            st.session_state.cost_result = {
                "segments_data": segments_data,
                "stot": total_len,
                "total_cost": total_cost,
            }
            st.session_state.pdf_bytes = None

    # ── نتيجة الحساب ──
    if st.session_state.cost_result:
        cr   = st.session_state.cost_result
        segs = cr["segments_data"]

        parts = [f"{s['label']} ({s['len']:,.0f}م)" for s in segs]
        st.markdown(f"""<div class="res">
{' | '.join(parts)}<br>
📏 مجموع الأطوال: <b>{cr['stot']:,.2f} م</b> ({cr['stot']/1000:.3f} كم)<br>
━━━━━━━━━━━━━━━━━<br>
💰 التكلفة الإجمالية: <b style="font-size:1.3rem">{cr['total_cost']:,.2f} ريال</b><br>
≈ <b>{cr['total_cost']/1e6:.3f} مليون ريال</b></div>""", unsafe_allow_html=True)

        st.markdown("<br>**تفاصيل كل عنصر:**", unsafe_allow_html=True)
        for s in segs:
            type_ar  = LINE_TYPES.get(s["line_type"],"—")
            dia_txt  = f"{s['diameter_mm']} ملم" if s.get("diameter_mm") else "—"
            badge_cls = {"pipe":"tp","box_channel":"tb","open_channel":"to"}.get(s["line_type"],"tp")
            icon = "✏️" if s["is_drawn"] else "📍"
            st.markdown(f"""<div class="seg-card">
<span class="tbadge {badge_cls}">{type_ar}</span>
<h4>{icon} {s['label']} — {s['len']:,.1f} م</h4>
القطر: <b>{dia_txt}</b> &nbsp;|&nbsp;
سعر المتر: <b>{s['price_per_m']:,.0f} ريال</b> &nbsp;|&nbsp;
<b style="color:#c0392b">التكلفة: {s['cost']:,.2f} ريال</b>
</div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        bp1, bp2 = st.columns(2)
        with bp1:
            if st.button("📄 إصدار تقرير PDF", key="gen_pdf"):
                with st.spinner("جاري إنشاء التقرير..."):
                    try:
                        st.session_state.pdf_bytes = gen_pdf(
                            cr["segments_data"], cr["stot"], cr["total_cost"])
                        st.success("✅ التقرير جاهز!")
                    except Exception as e:
                        st.error(f"خطأ في إنشاء التقرير: {e}")
        with bp2:
            if st.session_state.pdf_bytes:
                st.download_button("⬇️ تحميل التقرير PDF",
                    data=st.session_state.pdf_bytes,
                    file_name="flood_cost_report.pdf",
                    mime="application/pdf", key="dl_pdf")

    if not feats and not raw_drawn:
        st.markdown('<div class="ib">⬅️ ارفع ملف من القائمة الجانبية، أو ارسم خطاً على الخريطة لحساب التكلفة.</div>', unsafe_allow_html=True)

# ══ TAB 2 ══
with tab2:
    if not st.session_state.feats:
        st.markdown('<div class="ib">⬅️ ارفع ملف من القائمة الجانبية لعرض الجدول.</div>', unsafe_allow_html=True)
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
            df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            "flood_network.csv", "text/csv")

