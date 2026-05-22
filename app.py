import streamlit as st
import json, math, os, tempfile, zipfile, io, base64
from io import BytesIO
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import urllib.request
import urllib.parse

st.set_page_config(page_title="حاسبة شبكات السيول", page_icon="🌊",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
html,body,[class*="css"],.stApp{font-family:'Cairo',sans-serif!important;direction:rtl}
[data-testid="stSidebar"]{min-width:340px!important;max-width:380px!important;background:#f7f9fc!important}
.hdr{background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff;padding:16px 22px;border-radius:12px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between}
.hdr h1{margin:0;font-size:1.35rem;font-weight:900}
.hdr p{margin:2px 0 0;font-size:.82rem;color:#b8d9f8}
.hdr .bdg{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);padding:5px 14px;border-radius:16px;font-size:.78rem;font-weight:700;white-space:nowrap}
.mc{background:#fff;border-radius:10px;padding:12px 16px;box-shadow:0 2px 8px rgba(0,0,0,.07);border-top:4px solid #1a5fa8;text-align:center}
.mc .v{font-size:1.45rem;font-weight:900;color:#0a2a5e}
.mc .l{font-size:.78rem;color:#6b7a99;margin-top:2px}
.res{background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff!important;padding:18px 22px;border-radius:12px;font-size:1.05rem;font-weight:700;text-align:center;box-shadow:0 4px 16px rgba(26,95,168,.3);margin-top:10px;line-height:2}
.ib{background:#eaf4ff;border-right:4px solid #1a5fa8;border-radius:7px;padding:10px 14px;font-size:.85rem;color:#0a2a5e;margin-bottom:8px;direction:rtl;line-height:1.8}
.pc{background:#fff;border:1.5px solid #d0e4f7;border-right:5px solid #1a5fa8;border-radius:7px;padding:9px 13px;margin-bottom:7px;font-size:.84rem;color:#1a2a3a}
.pc b{color:#0a2a5e}.pc small{color:#888}.pc span{color:#c0392b;font-weight:900;font-size:.9rem}
.sig{background:#0a2a5e;color:#a8d0f0!important;text-align:center;padding:10px;border-radius:8px;margin-top:12px;font-size:.8rem}
.sig b{color:#fff!important}
.stButton>button{background:linear-gradient(135deg,#1a5fa8,#0a2a5e)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-family:'Cairo',sans-serif!important;font-weight:700!important;font-size:.95rem!important;width:100%!important;padding:9px!important}
</style>
""", unsafe_allow_html=True)

RLAT, RLON = 24.7136, 46.6753

# ── حساب الأطوال ──
def hav(lon1, lat1, lon2, lat2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def length_m_wgs(coords_wgs):
    """حساب الطول بالمتر من إحداثيات WGS84 [lon, lat]"""
    t = 0.0
    for i in range(len(coords_wgs)-1):
        try:
            t += hav(float(coords_wgs[i][0]), float(coords_wgs[i][1]),
                     float(coords_wgs[i+1][0]), float(coords_wgs[i+1][1]))
        except:
            pass
    return t

def length_m_projected(coords_proj):
    """حساب الطول بالمتر من إحداثيات مسقطة (x,y بالمتر)"""
    t = 0.0
    for i in range(len(coords_proj)-1):
        dx = float(coords_proj[i+1][0]) - float(coords_proj[i][0])
        dy = float(coords_proj[i+1][1]) - float(coords_proj[i][1])
        t += math.sqrt(dx**2 + dy**2)
    return t

def is_projected(coords):
    """تحديد إذا كانت الإحداثيات مسقطة أم جغرافية"""
    if not coords:
        return False
    x, y = float(coords[0][0]), float(coords[0][1])
    # الإحداثيات الجغرافية WGS84: lon بين -180 و 180، lat بين -90 و 90
    if abs(x) > 180 or abs(y) > 90:
        return True
    return False

def convert_projected_to_wgs84(coords, crs_wkt=None, epsg=None):
    """تحويل إحداثيات مسقطة إلى WGS84"""
    try:
        from pyproj import Transformer, CRS
        if epsg:
            transformer = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
        elif crs_wkt:
            src_crs = CRS.from_wkt(crs_wkt)
            transformer = Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
        else:
            # محاولة تخمين النظام — UTM zone 37N (شائع في السعودية)
            transformer = Transformer.from_crs("EPSG:32637", "EPSG:4326", always_xy=True)
        converted = []
        for c in coords:
            lon, lat = transformer.transform(float(c[0]), float(c[1]))
            converted.append([lon, lat])
        return converted
    except Exception as e:
        st.warning(f"تعذّر التحويل تلقائياً: {e}")
        return coords

def center(coords):
    v = [(float(c[0]), float(c[1])) for c in coords if len(c) >= 2]
    if not v:
        return RLAT, RLON
    return sum(c[1] for c in v)/len(v), sum(c[0] for c in v)/len(v)

def parse_geom(geom):
    if not geom:
        return []
    t = geom.get("type", "")
    raw = geom.get("coordinates", [])
    pts = (raw if t == "LineString"
           else [p for part in raw for p in part] if t == "MultiLineString"
           else [])
    return [[float(c[0]), float(c[1])] for c in pts if isinstance(c, (list, tuple)) and len(c) >= 2]

def load_geojson(text):
    try:
        gj = json.loads(text)
    except:
        st.error("خطأ في قراءة الملف")
        return [], []
    feats, all_c = [], []
    for i, f in enumerate(gj.get("features", [])):
        if not isinstance(f, dict):
            continue
        coords = parse_geom(f.get("geometry") or {})
        if len(coords) < 2:
            continue
        props = f.get("properties") or {}

        # اكتشاف وتحويل الإحداثيات المسقطة
        if is_projected(coords):
            crs_info = gj.get("crs", {})
            epsg = None
            wkt = None
            if crs_info:
                props_crs = crs_info.get("properties", {})
                name = props_crs.get("name", "")
                if "EPSG:" in name.upper():
                    try:
                        epsg = int(name.upper().split("EPSG:")[-1].strip().split()[0])
                    except:
                        pass
            # حساب الطول قبل التحويل (أدق)
            length = round(length_m_projected(coords), 2)
            coords = convert_projected_to_wgs84(coords, crs_wkt=wkt, epsg=epsg)
        else:
            length = round(length_m_wgs(coords), 2)

        feats.append({"i": i, "lbl": f"خط #{i}", "len": length, "coords": coords, "props": props})
        all_c.extend(coords)
    return feats, all_c

def load_shp(zb):
    try:
        import shapefile
    except:
        st.error("مكتبة pyshp غير متاحة")
        return [], []
    try:
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(BytesIO(zb)) as z:
                z.extractall(td)
            shp = next((os.path.join(r, f) for r, _, fs in os.walk(td)
                        for f in fs if f.lower().endswith(".shp")), None)
            if not shp:
                st.error("لم يُعثر على .shp")
                return [], []

            # قراءة ملف .prj لمعرفة نظام الإحداثيات
            prj_path = shp.replace(".shp", ".prj")
            crs_wkt = None
            epsg = None
            if os.path.exists(prj_path):
                with open(prj_path, "r", errors="ignore") as pf:
                    crs_wkt = pf.read().strip()
                # محاولة استخراج EPSG من WKT
                try:
                    from pyproj import CRS
                    crs_obj = CRS.from_wkt(crs_wkt)
                    epsg_auth = crs_obj.to_epsg()
                    if epsg_auth:
                        epsg = epsg_auth
                except:
                    pass

            sf = shapefile.Reader(shp)
            fnames = [f[0] for f in sf.fields[1:]]
            feats, all_c = [], []
            projected_detected = False

            for i, sr in enumerate(sf.shapeRecords()):
                coords = [[float(p[0]), float(p[1])] for p in sr.shape.points if len(p) >= 2]
                if len(coords) < 2:
                    continue
                props = dict(zip(fnames, sr.record))

                # اكتشاف وتحويل الإحداثيات المسقطة
                if is_projected(coords):
                    if not projected_detected:
                        projected_detected = True
                        if epsg:
                            st.info(f"📐 تم اكتشاف نظام إحداثيات مسقط (EPSG:{epsg}) — سيتم التحويل إلى WGS84")
                        else:
                            st.info("📐 تم اكتشاف نظام إحداثيات مسقط — سيتم التحويل إلى WGS84 (UTM 37N افتراضي)")
                    # حساب الطول قبل التحويل (أدق)
                    length = round(length_m_projected(coords), 2)
                    coords = convert_projected_to_wgs84(coords, crs_wkt=crs_wkt, epsg=epsg)
                else:
                    length = round(length_m_wgs(coords), 2)

                feats.append({"i": i, "lbl": f"خط #{i}", "len": length, "coords": coords, "props": props})
                all_c.extend(coords)
            return feats, all_c
    except Exception as e:
        st.error(f"خطأ: {e}")
        return [], []

# ── توليد خريطة ثابتة Static Map ──
def get_static_map_url(coords_list, width=600, height=400):
    """إنشاء رابط خريطة ثابتة من OpenStreetMap عبر Staticmap"""
    if not coords_list:
        return None
    # استخدام staticmap API
    path_str = "|".join(f"{lat},{lon}" for lon, lat in coords_list)
    # نستخدم openstreetmap tiles مع geoapify static maps
    lats = [c[1] for c in coords_list]
    lons = [c[0] for c in coords_list]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    return center_lat, center_lon

def fetch_osm_tile(lat, lon, zoom=14):
    """تحميل tile من OpenStreetMap"""
    n = 2**zoom
    x_tile = int((lon + 180) / 360 * n)
    y_tile = int((1 - math.log(math.tan(math.radians(lat)) + 1/math.cos(math.radians(lat))) / math.pi) / 2 * n)
    url = f"https://tile.openstreetmap.org/{zoom}/{x_tile}/{y_tile}.png"
    return url, x_tile, y_tile

def generate_pdf_report(sfeats, stot, cost, pr1):
    """توليد تقرير PDF مع خريطة ثابتة"""
    buf = BytesIO()

    # ── إنشاء خريطة Folium وتحويلها لصورة ──
    map_img_bytes = None
    try:
        import selenium
        has_selenium = True
    except:
        has_selenium = False

    # إنشاء خريطة folium وحفظها كـ HTML ثم PNG
    all_coords = []
    for f in sfeats:
        all_coords.extend(f["coords"])

    if all_coords:
        clat, clon = center(all_coords)
    else:
        clat, clon = RLAT, RLON

    # ── بناء صورة الخريطة باستخدام staticmap ──
    try:
        from staticmap import StaticMap, Line, CircleMarker
        m = StaticMap(600, 350, url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        COLORS = ["#e74c3c", "#e67e22", "#2ecc71", "#9b59b6", "#1abc9c",
                  "#f39c12", "#d35400", "#c0392b", "#16a085", "#8e44ad"]
        for idx, f in enumerate(sfeats):
            line_coords = [(c[0], c[1]) for c in f["coords"]]
            color = COLORS[idx % len(COLORS)]
            line = Line(line_coords, color, 4)
            m.add_line(line)
            # علامة بداية
            if f["coords"]:
                mid_idx = len(f["coords"]) // 2
                mc_pt = CircleMarker((f["coords"][mid_idx][0], f["coords"][mid_idx][1]), color, 8)
                m.add_marker(mc_pt)
        map_img = m.render(zoom=14)
        img_buf = BytesIO()
        map_img.save(img_buf, format="PNG")
        map_img_bytes = img_buf.getvalue()
    except Exception as e:
        # Fallback: بناء خريطة HTML وحفظها
        map_img_bytes = None

    # ── بناء PDF بـ ReportLab ──
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    # ستايلات مخصصة (بدون خط عربي مدمج — نستخدم Helvetica مع النصوص الإنجليزية)
    title_style = ParagraphStyle("title", parent=styles["Title"],
                                 fontSize=16, textColor=colors.HexColor("#0a2a5e"),
                                 alignment=TA_CENTER, spaceAfter=8)
    sub_style = ParagraphStyle("sub", parent=styles["Normal"],
                               fontSize=10, textColor=colors.HexColor("#1a5fa8"),
                               alignment=TA_CENTER, spaceAfter=14)
    label_style = ParagraphStyle("label", parent=styles["Normal"],
                                 fontSize=9, textColor=colors.HexColor("#555555"),
                                 alignment=TA_LEFT)
    result_style = ParagraphStyle("result", parent=styles["Normal"],
                                  fontSize=12, textColor=colors.HexColor("#0a2a5e"),
                                  alignment=TA_CENTER, spaceAfter=6)

    story = []

    # ── رأس التقرير ──
    story.append(Paragraph("Flood Network Cost Report", title_style))
    story.append(Paragraph("Eng. Ahmed Adam | Flood Drainage Networks Calculator 2025", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a5fa8"), spaceAfter=12))

    # ── ملخص النتائج ──
    summary_data = [
        ["Parameter", "Value"],
        ["Number of Lines", f"{len(sfeats)}"],
        ["Total Length (m)", f"{stot:,.2f} m"],
        ["Total Length (km)", f"{stot/1000:.3f} km"],
        ["Price per Meter", f"{pr1:,.2f} SAR"],
        ["TOTAL COST", f"{cost:,.2f} SAR"],
        ["Total Cost (Millions)", f"{cost/1e6:.3f} M SAR"],
    ]
    summary_table = Table(summary_data, colWidths=[7*cm, 10*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a2a5e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -2), (-1, -1), colors.HexColor("#eaf4ff")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#1a5fa8")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -3), [colors.white, colors.HexColor("#f0f7ff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0e4f7")),
        ("ROWHEIGHT", (0, 0), (-1, -1), 22),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # ── جدول الخطوط ──
    story.append(Paragraph("Line Details:", ParagraphStyle("h2", parent=styles["Heading2"],
                                                            fontSize=12, textColor=colors.HexColor("#0a2a5e"),
                                                            spaceAfter=6)))
    line_data = [["Index", "Line Name", "Length (m)", "Length (km)", "Cost (SAR)"]]
    for f in sfeats:
        lc = f["len"] * pr1
        line_data.append([str(f["i"]), f["lbl"],
                          f"{f['len']:,.2f}", f"{f['len']/1000:.4f}", f"{lc:,.2f}"])
    line_table = Table(line_data, colWidths=[2*cm, 4*cm, 4*cm, 4*cm, 5*cm])
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5fa8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f7ff")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0e4f7")),
        ("ROWHEIGHT", (0, 0), (-1, -1), 18),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 14))

    # ── صورة الخريطة ──
    if map_img_bytes:
        story.append(Paragraph("Location Map (OpenStreetMap):", ParagraphStyle("h2", parent=styles["Heading2"],
                                                                                 fontSize=12, textColor=colors.HexColor("#0a2a5e"),
                                                                                 spaceAfter=6)))
        img_stream = BytesIO(map_img_bytes)
        rl_img = RLImage(img_stream, width=17*cm, height=9.5*cm)
        story.append(rl_img)
        story.append(Spacer(1, 8))
        story.append(Paragraph("Map tiles © OpenStreetMap contributors",
                                ParagraphStyle("caption", parent=styles["Normal"],
                                               fontSize=7, textColor=colors.grey, alignment=TA_CENTER)))
    else:
        # إنشاء خريطة HTML كبديل
        story.append(Paragraph("Map could not be rendered (staticmap not available).",
                                ParagraphStyle("note", parent=styles["Normal"],
                                               fontSize=9, textColor=colors.orange, alignment=TA_CENTER)))
        # إضافة إحداثيات كبديل
        coords_info = []
        for f in sfeats:
            if f["coords"]:
                lat, lon = center(f["coords"])
                coords_info.append(f"Line #{f['i']}: lat={lat:.5f}, lon={lon:.5f}")
        if coords_info:
            story.append(Paragraph("Line Centers: " + " | ".join(coords_info),
                                    ParagraphStyle("coords", parent=styles["Normal"],
                                                   fontSize=8, textColor=colors.HexColor("#555"))))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a5fa8"), spaceAfter=6))
    story.append(Paragraph("Eng. Ahmed Adam | Flood Drainage Networks © 2025",
                            ParagraphStyle("footer", parent=styles["Normal"],
                                           fontSize=8, textColor=colors.HexColor("#888"), alignment=TA_CENTER)))

    doc.build(story)
    return buf.getvalue()

# ── Session ──
for k, v in [("feats", []), ("ac", []), ("cost_result", None), ("sel_indices", [])]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ──
with st.sidebar:
    st.markdown('<div style="background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff;padding:14px 18px;text-align:center;margin:-1px -1px 14px"><b style="font-size:1rem">🌊 حاسبة شبكات السيول</b><br><small style="color:#b8d9f8">Eng. Ahmed Adam</small></div>', unsafe_allow_html=True)

    st.markdown("**📂 رفع بيانات الشبكة**")
    up = st.file_uploader("GeoJSON أو Shapefile (zip)", type=["geojson", "json", "zip"], label_visibility="collapsed")
    if up:
        raw = up.read()
        ext = up.name.lower().rsplit(".", 1)[-1]
        with st.spinner("جاري التحميل..."):
            if ext in ("geojson", "json"):
                f, c = load_geojson(raw.decode("utf-8", "ignore"))
            else:
                f, c = load_shp(raw)
        if f:
            st.session_state.feats = f
            st.session_state.ac = c
            st.session_state.sel_indices = []
            st.session_state.cost_result = None
            st.success(f"✅ {len(f)} خط")
        else:
            st.warning("لم تُوجد خطوط صالحة في الملف")

    if st.session_state.feats:
        tl = sum(x["len"] for x in st.session_state.feats)
        st.caption(f"📊 {len(st.session_state.feats)} خط — إجمالي {tl/1000:.2f} كم")

    st.markdown("---")
    st.markdown("**💲 أسعار إرشادية**")
    st.markdown("""
<div class="pc"><b>🔵 أنابيب — قطر 1400 ملم</b><br><span>4,004 ريال / متر</span></div>
<div class="pc"><b>🟠 قناة صندوقية — 1.8 × 1.4 م</b><br><span>9,336 ريال / متر</span></div>
<div class="pc"><b>🟢 قناة مفتوحة — عرض 12م / عمق 1.5م</b><br><span>13,052 ريال / متر</span></div>
<div class="sig"><b>Eng: Ahmed Adam</b><br>شبكات تصريف السيول © 2025</div>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="hdr">
  <div><h1>🌊 حاسبة تكلفة شبكات تصريف السيول</h1>
  <p>تحليل الشبكات · حساب الأطوال · تقدير التكاليف</p></div>
  <div class="bdg">Eng: Ahmed Adam</div>
</div>""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🗺️ خطوط الشبكة", "✏️ رسم خط جديد", "📊 جدول البيانات"])

# ══ TAB 1 ══
with tab1:
    feats = st.session_state.feats
    if not feats:
        st.markdown('<div class="ib">⬅️ ارفع ملف GeoJSON أو Shapefile من القائمة الجانبية للبدء.</div>', unsafe_allow_html=True)

    if feats:
        tl = sum(x["len"] for x in feats)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="mc"><div class="v">{len(feats):,}</div><div class="l">عدد الخطوط</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="mc"><div class="v">{tl/1000:,.2f}</div><div class="l">إجمالي الطول (كم)</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="mc"><div class="v">{tl:,.0f}</div><div class="l">إجمالي الطول (م)</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── الخريطة ──
    mc = list(center(st.session_state.ac)) if st.session_state.ac else [RLAT, RLON]
    m1 = folium.Map(location=mc, zoom_start=14, tiles="OpenStreetMap", prefer_canvas=True)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صورة فضائية").add_to(m1)
    folium.LayerControl(collapsed=True).add_to(m1)

    selected_set = set(st.session_state.sel_indices)

    for f in feats:
        cll = [(c[1], c[0]) for c in f["coords"]]
        is_selected = f["i"] in selected_set
        line_color = "#e74c3c" if is_selected else "#1a5fa8"
        line_weight = 5 if is_selected else 3

        # Popup مبسط: فقط الطول والـ Index
        popup_html = f"""<div dir='rtl' style='font-family:Cairo,sans-serif;font-size:13px;min-width:160px'>
<b style='color:#1a5fa8;font-size:15px'>خط #{f['i']}</b><br>
<b>الطول:</b> {f['len']:,.1f} م<br>
<small style='color:#888'>({f['len']/1000:.3f} كم)</small>
</div>"""

        # Label (DivIcon) في منتصف الخط
        if cll:
            mid = cll[len(cll)//2]
            folium.Marker(
                location=mid,
                icon=folium.DivIcon(
                    html=f'<div style="background:#1a5fa8;color:#fff;padding:2px 6px;border-radius:10px;font-size:10px;font-weight:bold;font-family:Cairo,sans-serif;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,.3)">{f["i"]}</div>',
                    icon_size=(36, 20),
                    icon_anchor=(18, 10)
                )
            ).add_to(m1)

        folium.PolyLine(cll, color=line_color, weight=line_weight, opacity=0.92,
                        tooltip=f"خط #{f['i']} | {f['len']:,.0f} م",
                        popup=folium.Popup(popup_html, max_width=220)).add_to(m1)

    st_folium(m1, width="100%", height=420, returned_objects=[], key="m1")

    if feats:
        st.markdown("### 📌 اختيار الخطوط")
        st.markdown('<div class="ib">💡 اختر خطاً أو أكثر — رقم الخط مطابق لـ Index في الجدول</div>', unsafe_allow_html=True)

        # ── Select All / Clear All ──
        ca1, ca2, ca3 = st.columns([2, 2, 4])
        with ca1:
            if st.button("✅ تحديد الكل", key="sel_all"):
                st.session_state.sel_indices = [f["i"] for f in feats]
                st.rerun()
        with ca2:
            if st.button("❌ إلغاء الكل", key="desel_all"):
                st.session_state.sel_indices = []
                st.rerun()

        # ── خيار Checkboxes أو Multiselect ──
        sel_mode = st.radio("طريقة الاختيار:", ["🔍 بحث (Multiselect)", "☑️ Checkboxes"],
                             horizontal=True, key="sel_mode")

        if sel_mode == "🔍 بحث (Multiselect)":
            opts = [f"خط #{f['i']}  ——  {f['len']:,.1f} م" for f in feats]
            # تحويل sel_indices الحالية إلى قائمة opts
            current_opts = [opts[f["i"]] for f in feats if f["i"] in set(st.session_state.sel_indices) and f["i"] < len(opts)]
            sel = st.multiselect("ابحث واختر:", opts,
                                  default=current_opts,
                                  placeholder="اكتب رقم الخط أو اختر...", key="sel_multi")
            new_indices = []
            for s in sel:
                idx = opts.index(s)
                new_indices.append(feats[idx]["i"])
            if set(new_indices) != set(st.session_state.sel_indices):
                st.session_state.sel_indices = new_indices
                st.rerun()

        else:  # Checkboxes
            st.markdown("---")
            # شبكة checkboxes بعمودين
            cols_per_row = 2
            feat_chunks = [feats[i:i+cols_per_row] for i in range(0, len(feats), cols_per_row)]
            new_indices = list(st.session_state.sel_indices)
            changed = False
            for chunk in feat_chunks:
                row_cols = st.columns(cols_per_row)
                for ci, f in enumerate(chunk):
                    is_checked = f["i"] in set(new_indices)
                    checked = row_cols[ci].checkbox(
                        f"خط #{f['i']}  ({f['len']:,.0f} م)",
                        value=is_checked,
                        key=f"chk_{f['i']}"
                    )
                    if checked and f["i"] not in new_indices:
                        new_indices.append(f["i"])
                        changed = True
                    elif not checked and f["i"] in new_indices:
                        new_indices.remove(f["i"])
                        changed = True
            if changed:
                st.session_state.sel_indices = new_indices

        # ── الخطوط المختارة ──
        sfeats = [f for f in feats if f["i"] in set(st.session_state.sel_indices)]
        stot = sum(x["len"] for x in sfeats)

        if sfeats:
            c1, c2 = st.columns(2)
            c1.markdown(f'<div class="mc"><div class="v">{len(sfeats)}</div><div class="l">خطوط مختارة</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="mc"><div class="v">{stot:,.1f} م</div><div class="l">مجموع الأطوال</div></div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### 💰 حساب التكلفة")
        cp, cb = st.columns([3, 1])
        with cp:
            pr1 = st.number_input("سعر المتر (ريال):", min_value=0.0, value=4004.0,
                                   step=100.0, format="%.2f", key="pr1",
                                   help="إرشادية: أنابيب 4,004 | صندوقية 9,336 | مفتوحة 13,052")
        with cb:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("احسب 💰", key="b1"):
                if not sfeats:
                    st.warning("اختر خطاً أولاً")
                else:
                    cost = stot * pr1
                    st.session_state.cost_result = {
                        "sfeats": sfeats, "stot": stot, "cost": cost, "pr1": pr1
                    }

        # ── نتيجة الحساب + PDF ──
        if st.session_state.cost_result:
            cr = st.session_state.cost_result
            info = " | ".join(f"خط #{f['i']} ({f['len']:,.0f}م)" for f in cr["sfeats"])
            st.markdown(f"""<div class="res">
{info}<br>📏 مجموع الأطوال: <b>{cr['stot']:,.2f} م</b> ({cr['stot']/1000:.3f} كم)<br>
💲 سعر المتر: <b>{cr['pr1']:,.2f} ريال</b><br>━━━━━━━━━━━━━━━━━<br>
💰 التكلفة الإجمالية: <b style="font-size:1.25rem">{cr['cost']:,.2f} ريال</b><br>
≈ <b>{cr['cost']/1e6:.3f} مليون ريال</b></div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            pdf_col1, pdf_col2 = st.columns(2)
            with pdf_col1:
                if st.button("📄 توليد تقرير PDF", key="gen_pdf"):
                    with st.spinner("جاري إنشاء التقرير..."):
                        try:
                            pdf_bytes = generate_pdf_report(
                                cr["sfeats"], cr["stot"], cr["cost"], cr["pr1"]
                            )
                            st.session_state.pdf_bytes = pdf_bytes
                            st.success("✅ التقرير جاهز للتحميل!")
                        except Exception as e:
                            st.error(f"خطأ في إنشاء PDF: {e}")

            with pdf_col2:
                if hasattr(st.session_state, "pdf_bytes") and st.session_state.pdf_bytes:
                    st.download_button(
                        label="⬇️ تحميل PDF",
                        data=st.session_state.pdf_bytes,
                        file_name="flood_network_cost_report.pdf",
                        mime="application/pdf",
                        key="dl_pdf"
                    )

# ══ TAB 2 ══
with tab2:
    st.markdown("### ✏️ ارسم خطاً على الخريطة")
    st.markdown("""<div class="ib" style="text-align:right">
<b>📌 خطوات الرسم:</b><br>
<b>١.</b> انقر أيقونة <b>رسم الخط</b> في يسار الخريطة<br>
<b>٢.</b> انقر لتحديد نقاط المسار<br>
<b>٣.</b> انقر <b>مرتين</b> لإنهاء الرسم<br>
<b>٤.</b> أدخل السعر ثم اضغط احسب
</div>""", unsafe_allow_html=True)

    mc2 = list(center(st.session_state.ac)) if st.session_state.ac else [RLAT, RLON]
    m2 = folium.Map(location=mc2, zoom_start=14, tiles="OpenStreetMap", prefer_canvas=True)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صورة فضائية").add_to(m2)

    # خطوط الملف بلون واضح في تبويب الرسم
    for f in st.session_state.feats:
        cll2 = [(c[1], c[0]) for c in f["coords"]]
        folium.PolyLine(cll2, color="#1a5fa8", weight=3, opacity=0.85,
                        tooltip=f"خط #{f['i']}").add_to(m2)
        # Labels في تبويب الرسم أيضاً
        if cll2:
            mid2 = cll2[len(cll2)//2]
            folium.Marker(
                location=mid2,
                icon=folium.DivIcon(
                    html=f'<div style="background:#1a5fa8;color:#fff;padding:1px 5px;border-radius:8px;font-size:9px;font-weight:bold;opacity:0.8">{f["i"]}</div>',
                    icon_size=(30, 16),
                    icon_anchor=(15, 8)
                )
            ).add_to(m2)

    Draw(draw_options={
        "polyline": {"shapeOptions": {"color": "#e74c3c", "weight": 4, "opacity": .9}},
        "polygon": False, "circle": False, "rectangle": False,
        "circlemarker": False, "marker": False},
        edit_options={"edit": True, "remove": True}).add_to(m2)
    folium.LayerControl(collapsed=True).add_to(m2)

    md2 = st_folium(m2, width="100%", height=460, key="m2")

    dlen = 0.0
    if md2 and md2.get("all_drawings"):
        for drw in md2["all_drawings"]:
            g = drw.get("geometry") or {}
            if g.get("type") == "LineString":
                c = g.get("coordinates", [])
                if len(c) >= 2:
                    dlen += length_m_wgs(c)

    if dlen > 0:
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="mc"><div class="v">{dlen:,.2f}</div><div class="l">الطول (م)</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="mc"><div class="v">{dlen/1000:.3f}</div><div class="l">الطول (كم)</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        cp2, cb2 = st.columns([3, 1])
        with cp2:
            pr2 = st.number_input("سعر المتر (ريال):", min_value=0.0, value=4004.0,
                                   step=100.0, format="%.2f", key="pr2",
                                   help="إرشادية: أنابيب 4,004 | صندوقية 9,336 | مفتوحة 13,052")
        with cb2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("احسب 💰", key="b2"):
                cost2 = dlen * pr2
                st.markdown(f"""<div class="res">
✏️ خط مرسوم يدوياً<br>📏 الطول: <b>{dlen:,.2f} م</b> ({dlen/1000:.3f} كم)<br>
💲 سعر المتر: <b>{pr2:,.2f} ريال</b><br>━━━━━━━━━━━━━━━━━<br>
💰 التكلفة: <b style="font-size:1.25rem">{cost2:,.2f} ريال</b><br>
≈ <b>{cost2/1e6:.3f} مليون ريال</b></div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="ib">☝️ استخدم أداة الرسم في يسار الخريطة لرسم خط جديد.</div>', unsafe_allow_html=True)

# ══ TAB 3 ══
with tab3:
    feats = st.session_state.feats
    if not feats:
        st.markdown('<div class="ib">⬅️ ارفع ملف من القائمة الجانبية لعرض الجدول.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"### 📋 بيانات الشبكة — {len(feats)} خط")

        # ── بحث بالـ Index ──
        search_idx = st.text_input("🔍 بحث برقم الخط (Index):", placeholder="أدخل رقم الخط مثل: 0 أو 5", key="search_idx")

        rows = []
        for f in feats:
            r = {"رقم الخط (Index)": f["i"], "الطول (م)": f["len"], "الطول (كم)": round(f["len"]/1000, 4)}
            # إضافة جميع الخصائص
            r.update({str(k): v for k, v in f["props"].items()})
            rows.append(r)

        df = pd.DataFrame(rows)

        # تطبيق الفلتر
        if search_idx.strip():
            try:
                idx_val = int(search_idx.strip())
                df_filtered = df[df["رقم الخط (Index)"] == idx_val]
                if df_filtered.empty:
                    st.warning(f"لا يوجد خط بالرقم {idx_val}")
                else:
                    st.dataframe(df_filtered, use_container_width=True, height=200)
            except ValueError:
                st.warning("يرجى إدخال رقم صحيح")
        else:
            st.dataframe(df, use_container_width=True, height=500)

        st.download_button("⬇️ تحميل CSV",
                            df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                            "flood_network.csv", "text/csv")
