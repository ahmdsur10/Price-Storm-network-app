import streamlit as st
import json, math, os, tempfile, zipfile
from io import BytesIO

st.set_page_config(page_title="حاسبة شبكات السيول", page_icon="🌊",
                   layout="wide", initial_sidebar_state="expanded")

# ── CSS مرة واحدة فقط ──
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
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
# الدوال الأساسية — خفيفة وسريعة
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
    x, y = coords[0][0], coords[0][1]
    return abs(x) > 180 or abs(y) > 90

def map_center(coords):
    if not coords: return RLAT, RLON
    return sum(c[1] for c in coords)/len(coords), sum(c[0] for c in coords)/len(coords)

@st.cache_data(show_spinner=False)
def convert_to_wgs84_cached(coords_tuple, epsg):
    """تحويل مُخزّن في الكاش — لا يُعاد إلا عند ملف جديد"""
    from pyproj import Transformer
    try:
        tr = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
        return [[lon, lat] for x, y in coords_tuple for lon, lat in [tr.transform(x, y)]]
    except:
        return list(coords_tuple)

def parse_geom(geom):
    if not geom: return []
    t = geom.get("type",""); raw = geom.get("coordinates",[])
    pts = raw if t=="LineString" else [p for part in raw for p in part] if t=="MultiLineString" else []
    return [[float(c[0]),float(c[1])] for c in pts if isinstance(c,(list,tuple)) and len(c)>=2]

@st.cache_data(show_spinner=False)
def load_geojson_cached(text_hash, text):
    try: gj = json.loads(text)
    except: return [], []
    # اكتشاف CRS من الملف مرة واحدة
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
        props = f.get("properties") or {}
        if is_projected(coords):
            length = round(length_m_proj(coords), 2)
            epsg = epsg_file or 32637
            coords = convert_to_wgs84_cached(tuple(map(tuple,coords)), epsg)
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
            prj_path = shp.replace(".shp",".prj")
            epsg = None
            if os.path.exists(prj_path):
                try:
                    from pyproj import CRS
                    with open(prj_path,"r",errors="ignore") as pf: wkt = pf.read().strip()
                    ep = CRS.from_wkt(wkt).to_epsg()
                    if ep: epsg = ep
                except: pass
            sf = shapefile.Reader(shp)
            fnames = [f[0] for f in sf.fields[1:]]
            feats, all_c = [], []
            for i, sr in enumerate(sf.shapeRecords()):
                coords = [[float(p[0]),float(p[1])] for p in sr.shape.points if len(p)>=2]
                if len(coords) < 2: continue
                props = dict(zip(fnames, sr.record))
                if is_projected(coords):
                    length = round(length_m_proj(coords), 2)
                    coords = convert_to_wgs84_cached(tuple(map(tuple,coords)), epsg or 32637)
                else:
                    length = round(length_m_wgs(coords), 2)
                feats.append({"i":i,"len":length,"coords":coords,"props":props})
                all_c.extend(coords)
            return feats, all_c
    except: return [], []

@st.cache_data(show_spinner=False)
def build_map_html(feats_key, feats_json, center_lat, center_lon, sel_set_key):
    """بناء HTML الخريطة مرة واحدة ويُخزَّن في الكاش"""
    import folium
    feats = json.loads(feats_json)
    sel_set = set(json.loads(sel_set_key))
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14,
                   tiles="OpenStreetMap", prefer_canvas=True)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صورة فضائية").add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)

    # رسم الخطوط + Labels بـ GeoJson واحد أسرع بكثير من PolyLine منفردة
    features_geojson = []
    label_markers = []
    for f in feats:
        selected = f["i"] in sel_set
        color = "#e74c3c" if selected else "#1a5fa8"
        weight = 5 if selected else 3
        features_geojson.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": f["coords"]},
            "properties": {
                "idx": f["i"],
                "len_m": f["len"],
                "color": color,
                "weight": weight
            }
        })
        # Label فقط إذا كان المستخدم رفع ملف (لتوفير وقت)
        if f["coords"]:
            mid = f["coords"][len(f["coords"])//2]
            label_markers.append((mid[1], mid[0], f["i"]))

    # GeoJSON layer واحد بدل عشرات PolyLines
    folium.GeoJson(
        {"type":"FeatureCollection","features":features_geojson},
        style_function=lambda x: {
            "color": x["properties"]["color"],
            "weight": x["properties"]["weight"],
            "opacity": 0.92
        },
        tooltip=folium.GeoJsonTooltip(fields=["idx","len_m"],
                                       aliases=["خط #","الطول (م)"],
                                       localize=True),
        popup=folium.GeoJsonPopup(fields=["idx","len_m"],
                                   aliases=["خط #","الطول (م)"],
                                   max_width=200)
    ).add_to(m)

    # Labels مجمّعة كـ FeatureGroup
    if label_markers:
        fg = folium.FeatureGroup(name="labels", show=True)
        for lat, lon, idx in label_markers:
            folium.Marker(
                [lat, lon],
                icon=folium.DivIcon(
                    html=f'<div style="background:#1a5fa8;color:#fff;padding:1px 5px;border-radius:8px;font-size:10px;font-weight:bold;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.3)">{idx}</div>',
                    icon_size=(30,18), icon_anchor=(15,9)
                )
            ).add_to(fg)
        fg.add_to(m)

    return m._repr_html_()

@st.cache_data(show_spinner=False)
def make_df(feats_json):
    feats = json.loads(feats_json)
    rows = []
    for f in feats:
        r = {"رقم الخط":f["i"],"الطول (م)":f["len"],"الطول (كم)":round(f["len"]/1000,4)}
        r.update({str(k):v for k,v in f["props"].items()})
        rows.append(r)
    import pandas as pd
    return pd.DataFrame(rows)

def gen_pdf(sfeats, stot, cost, pr1):
    """توليد PDF خفيف بدون استيراد في بداية الملف"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    C = colors.HexColor

    def sty(name, **kw):
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    story = [
        Paragraph("Flood Network Cost Report", sty("t", fontSize=16, textColor=C("#0a2a5e"), alignment=TA_CENTER, spaceAfter=4)),
        Paragraph("Eng. Ahmed Adam | Flood Drainage Networks 2025", sty("s", fontSize=9, textColor=C("#1a5fa8"), alignment=TA_CENTER, spaceAfter=12)),
        HRFlowable(width="100%", thickness=2, color=C("#1a5fa8"), spaceAfter=10),
    ]

    # جدول الملخص
    sum_data = [
        ["Parameter","Value"],
        ["Lines Selected", str(len(sfeats))],
        ["Total Length","%.2f m  /  %.3f km" % (stot, stot/1000)],
        ["Price / Meter","%.2f SAR" % pr1],
        ["TOTAL COST","%.2f SAR" % cost],
        ["Millions","%.4f M SAR" % (cost/1e6)],
    ]
    st_tbl = Table(sum_data, colWidths=[7*cm,10*cm])
    st_tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),C("#0a2a5e")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,1),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),10),("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("BACKGROUND",(0,-2),(-1,-1),C("#eaf4ff")),
        ("BACKGROUND",(0,-1),(-1,-1),C("#1a5fa8")),("TEXTCOLOR",(0,-1),(-1,-1),colors.white),
        ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,-1),(-1,-1),12),
        ("ROWBACKGROUNDS",(0,1),(-1,-3),[colors.white,C("#f0f7ff")]),
        ("GRID",(0,0),(-1,-1),.5,C("#d0e4f7")),("ROWHEIGHT",(0,0),(-1,-1),22),
    ]))
    story += [st_tbl, Spacer(1,12)]

    # جدول الخطوط
    story.append(Paragraph("Line Details", sty("h", fontSize=11, textColor=C("#0a2a5e"), spaceAfter=5)))
    ld = [["Index","Length (m)","Length (km)","Cost (SAR)"]]
    for f in sfeats:
        ld.append([str(f["i"]), "%.2f"%f["len"], "%.4f"%(f["len"]/1000), "%.2f"%(f["len"]*pr1)])
    lt = Table(ld, colWidths=[3*cm,4.5*cm,4.5*cm,7*cm])
    lt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),C("#1a5fa8")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,1),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),9),("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,C("#f0f7ff")]),
        ("GRID",(0,0),(-1,-1),.4,C("#d0e4f7")),("ROWHEIGHT",(0,0),(-1,-1),18),
    ]))
    story += [lt, Spacer(1,12)]

    # خريطة ثابتة
    try:
        from staticmap import StaticMap, Line
        all_c = []
        for f in sfeats: all_c.extend(f["coords"])
        sm = StaticMap(580, 320, url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        COLS = ["#e74c3c","#e67e22","#2ecc71","#9b59b6","#1abc9c","#f39c12","#16a085","#8e44ad"]
        for idx, f in enumerate(sfeats):
            sm.add_line(Line([(c[0],c[1]) for c in f["coords"]], COLS[idx%len(COLS)], 4))
        img = sm.render(zoom=14)
        from io import BytesIO as _BIO
        from reportlab.platypus import Image as RLImg
        ib = _BIO(); img.save(ib,"PNG")
        ib.seek(0)
        story.append(Paragraph("Location Map (OpenStreetMap)", sty("mh", fontSize=11, textColor=C("#0a2a5e"), spaceAfter=5)))
        story.append(RLImg(ib, width=17*cm, height=9.2*cm))
        story.append(Paragraph("© OpenStreetMap contributors", sty("cap", fontSize=7, textColor=colors.grey, alignment=TA_CENTER)))
    except: pass

    story += [
        Spacer(1,10), HRFlowable(width="100%",thickness=1,color=C("#1a5fa8"),spaceAfter=5),
        Paragraph("Eng. Ahmed Adam | Flood Drainage Networks © 2025",
                  sty("ft",fontSize=8,textColor=C("#888"),alignment=TA_CENTER))
    ]
    doc.build(story)
    return buf.getvalue()

# ══ Session State ══
_defaults = {"feats":[],"ac":[],"sel_set":"[]","cost_result":None,"pdf_bytes":None,"feats_json":"[]"}
for k,v in _defaults.items():
    if k not in st.session_state: st.session_state[k]=v

# ══ Sidebar ══
with st.sidebar:
    st.markdown('<div style="background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff;padding:12px 16px;text-align:center;margin:-1px -1px 12px"><b style="font-size:.97rem">🌊 حاسبة شبكات السيول</b><br><small style="color:#b8d9f8">Eng. Ahmed Adam</small></div>', unsafe_allow_html=True)
    st.markdown("**📂 رفع بيانات الشبكة**")
    up = st.file_uploader("GeoJSON أو Shapefile (zip)", type=["geojson","json","zip"], label_visibility="collapsed")
    if up:
        raw = up.read(); ext = up.name.lower().rsplit(".",1)[-1]
        file_hash = hash(raw)
        if file_hash != st.session_state.get("_file_hash"):
            with st.spinner("جاري التحميل..."):
                if ext in ("geojson","json"):
                    f,c = load_geojson_cached(file_hash, raw.decode("utf-8","ignore"))
                else:
                    f,c = load_shp_cached(file_hash, raw)
            if f:
                st.session_state.feats = f
                st.session_state.ac = c
                st.session_state.feats_json = json.dumps(f, ensure_ascii=False)
                st.session_state.sel_set = "[]"
                st.session_state.cost_result = None
                st.session_state.pdf_bytes = None
                st.session_state._file_hash = file_hash
                st.success(f"✅ {len(f)} خط")
            else:
                st.warning("لم تُوجد خطوط صالحة")

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

tab1, tab2, tab3 = st.tabs(["🗺️ خطوط الشبكة","✏️ رسم خط جديد","📊 جدول البيانات"])

# ══ TAB 1 ══
with tab1:
    feats = st.session_state.feats
    if not feats:
        st.markdown('<div class="ib">⬅️ ارفع ملف GeoJSON أو Shapefile من القائمة الجانبية للبدء.</div>', unsafe_allow_html=True)

    if feats:
        tl = sum(x["len"] for x in feats)
        c1,c2,c3 = st.columns(3)
        c1.markdown(f'<div class="mc"><div class="v">{len(feats):,}</div><div class="l">عدد الخطوط</div></div>',unsafe_allow_html=True)
        c2.markdown(f'<div class="mc"><div class="v">{tl/1000:,.2f}</div><div class="l">إجمالي الطول (كم)</div></div>',unsafe_allow_html=True)
        c3.markdown(f'<div class="mc"><div class="v">{tl:,.0f}</div><div class="l">إجمالي الطول (م)</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)

    # ── الخريطة: مبنية بـ cache — لا تُعاد إلا عند تغيير الخطوط أو الاختيار ──
    mc = list(map_center(st.session_state.ac)) if st.session_state.ac else [RLAT, RLON]

    if feats:
        map_html = build_map_html(
            feats_key=hash(st.session_state.feats_json),
            feats_json=st.session_state.feats_json,
            center_lat=mc[0], center_lon=mc[1],
            sel_set_key=st.session_state.sel_set
        )
        st.components.v1.html(map_html, height=400, scrolling=False)
    else:
        import folium
        from streamlit_folium import st_folium
        m0 = folium.Map(location=[RLAT,RLON],zoom_start=10,tiles="OpenStreetMap")
        st_folium(m0,width="100%",height=350,returned_objects=[],key="m0")

    if feats:
        st.markdown("### 📌 اختيار الخطوط")
        st.markdown('<div class="ib">💡 اختر خطاً أو أكثر ثم احسب التكلفة مباشرة</div>',unsafe_allow_html=True)

        # ── أزرار سريعة ──
        ca1,ca2,_ = st.columns([2,2,4])
        with ca1:
            if st.button("✅ تحديد الكل",key="sel_all"):
                st.session_state.sel_set = json.dumps([f["i"] for f in feats])
                st.rerun()
        with ca2:
            if st.button("❌ إلغاء الكل",key="desel_all"):
                st.session_state.sel_set = "[]"
                st.rerun()

        sel_mode = st.radio("طريقة الاختيار:", ["🔍 بحث","☑️ Checkboxes"], horizontal=True, key="sel_mode")
        cur_sel = set(json.loads(st.session_state.sel_set))

        if sel_mode == "🔍 بحث":
            opts = [f"خط #{f['i']}  ——  {f['len']:,.1f} م" for f in feats]
            cur_opts = [opts[i] for i,f in enumerate(feats) if f["i"] in cur_sel]
            sel = st.multiselect("ابحث واختر:", opts, default=cur_opts,
                                  placeholder="اكتب رقم الخط أو اختر...", key="sel_multi")
            new_sel = set(feats[opts.index(s)]["i"] for s in sel)
            if new_sel != cur_sel:
                st.session_state.sel_set = json.dumps(list(new_sel))
                st.rerun()
        else:
            cols_n = 3
            new_sel = set()
            changed = False
            rows_chunks = [feats[i:i+cols_n] for i in range(0,len(feats),cols_n)]
            for chunk in rows_chunks:
                rcols = st.columns(cols_n)
                for ci,f in enumerate(chunk):
                    was = f["i"] in cur_sel
                    chk = rcols[ci].checkbox(f"#{f['i']}  {f['len']:,.0f}م", value=was, key=f"chk_{f['i']}")
                    if chk: new_sel.add(f["i"])
                    if chk != was: changed = True
            if changed:
                st.session_state.sel_set = json.dumps(list(new_sel))
                st.rerun()
            else:
                new_sel = cur_sel

        sfeats = [f for f in feats if f["i"] in new_sel]
        stot = sum(x["len"] for x in sfeats)

        if sfeats:
            c1,c2 = st.columns(2)
            c1.markdown(f'<div class="mc"><div class="v">{len(sfeats)}</div><div class="l">خطوط مختارة</div></div>',unsafe_allow_html=True)
            c2.markdown(f'<div class="mc"><div class="v">{stot:,.1f} م</div><div class="l">مجموع الأطوال</div></div>',unsafe_allow_html=True)
            st.markdown("<br>",unsafe_allow_html=True)

        st.markdown("### 💰 حساب التكلفة")

        # أسعار سريعة
        price_options = {
            "أنابيب 1400 ملم — 4,004": 4004.0,
            "قناة صندوقية 1.8×1.4 — 9,336": 9336.0,
            "قناة مفتوحة 12×1.5 — 13,052": 13052.0,
            "سعر مخصص": None
        }
        pc1,pc2 = st.columns([3,2])
        with pc1:
            price_choice = st.selectbox("نوع الشبكة:", list(price_options.keys()), key="price_choice")
        with pc2:
            if price_options[price_choice] is None:
                pr1 = st.number_input("سعر المتر (ريال):", min_value=0.0, value=4004.0,
                                       step=100.0, format="%.0f", key="pr1_custom")
            else:
                pr1 = price_options[price_choice]
                st.markdown(f'<div class="mc" style="margin-top:8px"><div class="v" style="font-size:1.1rem">{pr1:,.0f}</div><div class="l">ريال / متر</div></div>', unsafe_allow_html=True)

        if st.button("⚡ احسب التكلفة الآن", key="b1"):
            if not sfeats:
                st.warning("اختر خطاً أولاً")
            else:
                cost = stot * pr1
                st.session_state.cost_result = {"sfeats":sfeats,"stot":stot,"cost":cost,"pr1":pr1}
                st.session_state.pdf_bytes = None

        if st.session_state.cost_result:
            cr = st.session_state.cost_result
            info = " | ".join(f"خط #{f['i']} ({f['len']:,.0f}م)" for f in cr["sfeats"])
            st.markdown(f"""<div class="res">
{info}<br>📏 مجموع الأطوال: <b>{cr['stot']:,.2f} م</b> ({cr['stot']/1000:.3f} كم)<br>
💲 سعر المتر: <b>{cr['pr1']:,.0f} ريال</b><br>━━━━━━━━━━━━━━━━━<br>
💰 التكلفة الإجمالية: <b style="font-size:1.3rem">{cr['cost']:,.2f} ريال</b><br>
≈ <b>{cr['cost']/1e6:.3f} مليون ريال</b></div>""",unsafe_allow_html=True)

            st.markdown("<br>",unsafe_allow_html=True)
            pc1,pc2 = st.columns(2)
            with pc1:
                if st.button("📄 توليد PDF",key="gen_pdf"):
                    with st.spinner("جاري الإنشاء..."):
                        try:
                            st.session_state.pdf_bytes = gen_pdf(cr["sfeats"],cr["stot"],cr["cost"],cr["pr1"])
                            st.success("✅ جاهز!")
                        except Exception as e:
                            st.error(f"خطأ: {e}")
            with pc2:
                if st.session_state.pdf_bytes:
                    st.download_button("⬇️ تحميل PDF",
                        data=st.session_state.pdf_bytes,
                        file_name="flood_cost_report.pdf",
                        mime="application/pdf",key="dl_pdf")

# ══ TAB 2 ══
with tab2:
    import folium
    from folium.plugins import Draw
    from streamlit_folium import st_folium

    st.markdown("### ✏️ ارسم خطاً على الخريطة")
    st.markdown("""<div class="ib">
<b>📌 خطوات الرسم:</b> انقر أيقونة الخط في يسار الخريطة ← حدد النقاط ← انقر مرتين للإنهاء ← احسب
</div>""",unsafe_allow_html=True)

    mc2 = list(map_center(st.session_state.ac)) if st.session_state.ac else [RLAT,RLON]
    m2 = folium.Map(location=mc2, zoom_start=14, tiles="OpenStreetMap", prefer_canvas=True)

    # خطوط الملف بلون واضح — بدون labels لتخفيف الوزن في tab الرسم
    for f in st.session_state.feats:
        folium.PolyLine([(c[1],c[0]) for c in f["coords"]],
                        color="#1a5fa8",weight=3,opacity=0.8,
                        tooltip=f"خط #{f['i']}").add_to(m2)

    Draw(draw_options={
        "polyline":{"shapeOptions":{"color":"#e74c3c","weight":4,"opacity":.9}},
        "polygon":False,"circle":False,"rectangle":False,
        "circlemarker":False,"marker":False},
        edit_options={"edit":True,"remove":True}).add_to(m2)

    md2 = st_folium(m2, width="100%", height=440, returned_objects=["all_drawings"], key="m2")

    dlen = 0.0
    if md2 and md2.get("all_drawings"):
        for drw in md2["all_drawings"]:
            g = drw.get("geometry") or {}
            if g.get("type") == "LineString":
                c = g.get("coordinates",[])
                if len(c) >= 2: dlen += length_m_wgs(c)

    if dlen > 0:
        c1,c2 = st.columns(2)
        c1.markdown(f'<div class="mc"><div class="v">{dlen:,.2f}</div><div class="l">الطول (م)</div></div>',unsafe_allow_html=True)
        c2.markdown(f'<div class="mc"><div class="v">{dlen/1000:.3f}</div><div class="l">الطول (كم)</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)

        pr2 = st.number_input("سعر المتر (ريال):", min_value=0.0, value=4004.0,
                               step=100.0, format="%.0f", key="pr2")
        if st.button("⚡ احسب التكلفة",key="b2"):
            cost2 = dlen*pr2
            st.markdown(f"""<div class="res">
✏️ خط مرسوم يدوياً<br>📏 الطول: <b>{dlen:,.2f} م</b> ({dlen/1000:.3f} كم)<br>
💲 سعر المتر: <b>{pr2:,.0f} ريال</b><br>━━━━━━━━━━━━━━━━━<br>
💰 التكلفة: <b style="font-size:1.25rem">{cost2:,.2f} ريال</b><br>
≈ <b>{cost2/1e6:.3f} مليون ريال</b></div>""",unsafe_allow_html=True)
    else:
        st.markdown('<div class="ib">☝️ استخدم أداة الرسم في يسار الخريطة لرسم خط جديد.</div>',unsafe_allow_html=True)

# ══ TAB 3 ══
with tab3:
    if not st.session_state.feats:
        st.markdown('<div class="ib">⬅️ ارفع ملف من القائمة الجانبية لعرض الجدول.</div>',unsafe_allow_html=True)
    else:
        st.markdown(f"### 📋 بيانات الشبكة — {len(st.session_state.feats)} خط")
        search_idx = st.text_input("🔍 بحث برقم الخط:", placeholder="مثال: 0 أو 5", key="search_idx")

        df = make_df(st.session_state.feats_json)

        if search_idx.strip():
            try:
                idx_val = int(search_idx.strip())
                df_f = df[df["رقم الخط"] == idx_val]
                st.dataframe(df_f if not df_f.empty else df, use_container_width=True, height=200)
                if df_f.empty: st.warning(f"لا يوجد خط #{idx_val}")
            except:
                st.warning("أدخل رقماً صحيحاً")
        else:
            st.dataframe(df, use_container_width=True, height=500)

        st.download_button("⬇️ تحميل CSV",
            df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            "flood_network.csv","text/csv")
