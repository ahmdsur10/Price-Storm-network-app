import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import Draw, MeasureControl
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import os, tempfile, zipfile, json, math

# ══════════════════════════════════════════════════════════════════
#  إعدادات الصفحة
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="نظام تحليل شبكات السيول",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════
#  CSS — اتجاه RTL صريح على جميع العناصر
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

/* --- إعادة ضبط الاتجاه بشكل شامل --- */
html, body { direction: rtl; }
[class*="css"], .stMarkdown, .stTextInput, .stNumberInput,
.stSelectbox, .stMultiSelect, .stFileUploader,
div[data-testid="stSidebar"], div[data-testid="stAppViewContainer"],
div[data-testid="stVerticalBlock"], div[data-testid="column"],
p, span, label, div, li, ul, ol, h1, h2, h3, h4 {
    font-family: 'Tajawal', sans-serif !important;
    direction: rtl;
    text-align: right;
}
/* مدخلات الأرقام */
input[type="number"] { text-align: right !important; direction: rtl !important; }

.main { background: #f0f4f8; }

/* --- هيدر --- */
.hero-header {
    background: linear-gradient(135deg,#1a3a5c 0%,#0d6efd 60%,#00b4d8 100%);
    border-radius: 16px; padding: 26px 36px; margin-bottom: 22px;
    color: white; text-align: center;
    box-shadow: 0 8px 32px rgba(13,110,253,.25);
}
.hero-header h1 { font-size:2.1rem; font-weight:800; margin:0; direction:rtl; }
.hero-header p  { font-size:1rem; opacity:.88; margin:7px 0 0; }

/* --- بطاقات الإحصائيات --- */
.mc { background:white; border-radius:14px; padding:16px 20px;
      box-shadow:0 2px 10px rgba(0,0,0,.07);
      border-right:5px solid #0d6efd; margin-bottom:12px; direction:rtl; }
.mc .lb { color:#6b7280; font-size:.85rem; font-weight:500; }
.mc .vl { color:#1a3a5c; font-size:1.55rem; font-weight:800; margin-top:3px; }
.mc .un { color:#0d6efd; font-size:.82rem; font-weight:600; }
.mc.g  { border-right-color:#43a047; }
.mc.g .vl { color:#1b5e20; } .mc.g .un { color:#43a047; }
.mc.o  { border-right-color:#fb8c00; }
.mc.o .vl { color:#e65100; } .mc.o .un { color:#fb8c00; }

/* --- نتيجة الحساب --- */
.result-box {
    background: linear-gradient(135deg,#e8f5e9,#c8e6c9);
    border:2px solid #43a047; border-radius:14px;
    padding:20px 24px; text-align:center; margin-top:14px;
    box-shadow:0 4px 14px rgba(67,160,71,.15); direction:rtl;
}
.result-box .rt { font-size:.95rem; color:#2e7d32; font-weight:600; }
.result-box .rv { font-size:2.1rem; font-weight:800; color:#1b5e20; margin-top:5px; }
.result-box .rs { font-size:.86rem; color:#388e3c; margin-top:5px; line-height:1.9; }

/* --- صندوق المعلومات (RTL صريح) --- */
.info-box {
    background:#e3f2fd; border:1px solid #90caf9; border-radius:10px;
    padding:14px 18px; font-size:.91rem; color:#1565c0;
    margin:9px 0; line-height:2; direction:rtl; text-align:right;
}
.info-box b { color:#0d47a1; }

/* --- صندوق دليل الأسعار --- */
.price-guide {
    background:#fff8e1; border:1px solid #ffe082; border-radius:12px;
    padding:14px 18px; margin:10px 0; direction:rtl; text-align:right;
    font-size:.88rem; color:#4e342e; line-height:2.1;
}
.price-guide .pg-title {
    font-size:.97rem; font-weight:800; color:#e65100;
    margin-bottom:8px; border-bottom:1px dashed #ffcc80; padding-bottom:6px;
}
.price-guide .pg-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:4px 0; border-bottom:1px solid #fff3cd;
}
.price-guide .pg-row:last-child { border-bottom:none; }
.price-guide .pg-name { color:#5d4037; font-weight:600; flex:1; }
.price-guide .pg-price {
    background:#e65100; color:white; border-radius:8px;
    padding:2px 10px; font-weight:700; font-size:.84rem; white-space:nowrap;
}

/* --- عنوان القسم --- */
.sec-title {
    font-size:1.1rem; font-weight:700; color:#1a3a5c;
    padding:5px 0 9px; border-bottom:2px solid #e2e8f0;
    margin-bottom:12px; direction:rtl; text-align:right;
}

/* --- شارات الصيغ --- */
.bdg-s { display:inline-block; background:#e8f5e9; color:#2e7d32;
    border:1px solid #a5d6a7; border-radius:20px; padding:2px 11px;
    font-size:.8rem; font-weight:700; margin-left:4px; }
.bdg-g { display:inline-block; background:#e3f2fd; color:#1565c0;
    border:1px solid #90caf9; border-radius:20px; padding:2px 11px;
    font-size:.8rem; font-weight:700; margin-left:4px; }

/* --- أزرار --- */
div[data-testid="stButton"]>button {
    width:100%; background:linear-gradient(135deg,#0d6efd,#0077b6);
    color:white; border:none; border-radius:10px; padding:11px 18px;
    font-family:'Tajawal',sans-serif; font-size:1rem; font-weight:700;
    cursor:pointer; box-shadow:0 4px 10px rgba(13,110,253,.3);
    direction:rtl;
}
div[data-testid="stButton"]>button:hover {
    transform:translateY(-1px); box-shadow:0 6px 16px rgba(13,110,253,.42);
}

/* --- تبويبات --- */
.stTabs [data-baseweb="tab"] {
    font-family:'Tajawal',sans-serif !important;
    font-size:.97rem; font-weight:600; direction:rtl;
}

/* --- قوائم الاختيار --- */
div[data-testid="stMultiSelect"] span,
div[data-testid="stSelectbox"] span { direction:rtl; text-align:right; }

/* --- تسميات المدخلات --- */
div[data-testid="stNumberInput"] label,
div[data-testid="stFileUploader"] label,
div[data-testid="stMultiSelect"] label,
div[data-testid="stSelectbox"] label { direction:rtl; text-align:right; }

footer { visibility:hidden; }

/* ══════════════════════════════════════════
   تكبير الشريط الجانبي
   ══════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    width: 360px !important;
    min-width: 360px !important;
}
section[data-testid="stSidebar"] > div:first-child {
    width: 360px !important;
    padding: 1.2rem 1.1rem !important;
}
/* توسيع محتوى الصفحة الرئيسية تلقائياً */
.main .block-container { padding-right: 1.5rem !important; }

/* --- تكبير خطوط الشريط الجانبي --- */
section[data-testid="stSidebar"] .sec-title  { font-size:1.18rem !important; }
section[data-testid="stSidebar"] .info-box   { font-size:.96rem !important; line-height:2.15 !important; padding:15px 18px !important; }
section[data-testid="stSidebar"] .price-guide { font-size:.93rem !important; line-height:2.2 !important; }
section[data-testid="stSidebar"] .price-guide .pg-title { font-size:1.02rem !important; }
section[data-testid="stSidebar"] .price-guide .pg-price { font-size:.9rem !important; padding:3px 12px !important; }
section[data-testid="stSidebar"] label       { font-size:1rem !important; }
section[data-testid="stSidebar"] .bdg-g,
section[data-testid="stSidebar"] .bdg-s      { font-size:.9rem !important; padding:3px 14px !important; }

/* --- توقيع المطوّر --- */
.dev-signature {
    background: linear-gradient(135deg,#0d1b2a 0%,#1a3a5c 50%,#0d6efd 100%);
    border-radius: 14px; padding: 18px 16px; margin-top: 16px;
    text-align: center; direction: rtl;
    box-shadow: 0 6px 20px rgba(13,110,253,.3);
    border: 1px solid rgba(255,255,255,.12);
    position: relative; overflow: hidden;
}
.dev-signature::before {
    content: ""; position:absolute; top:-40px; right:-40px;
    width:120px; height:120px; border-radius:50%;
    background:rgba(255,255,255,.04);
}
.dev-signature .dev-avatar {
    font-size:2.4rem; margin-bottom:8px; display:block;
}
.dev-signature .dev-label {
    font-size:.72rem; color:rgba(255,255,255,.55);
    letter-spacing:1.5px; text-transform:uppercase;
    margin-bottom:5px; font-family:'Tajawal',sans-serif;
}
.dev-signature .dev-name {
    font-size:1.25rem; font-weight:800; color:#ffffff;
    letter-spacing:.5px; font-family:'Tajawal',sans-serif;
    text-shadow: 0 2px 8px rgba(0,0,0,.3);
}
.dev-signature .dev-title-line {
    font-size:.82rem; color:rgba(255,255,255,.65);
    margin-top:5px; font-family:'Tajawal',sans-serif;
}
.dev-signature .dev-divider {
    border:0; border-top:1px solid rgba(255,255,255,.15);
    margin:10px 0;
}
.dev-signature .dev-copy {
    font-size:.72rem; color:rgba(255,255,255,.4);
    font-family:'Tajawal',sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  ثوابت
# ══════════════════════════════════════════════════════════════════
RIYADH_LAT  = 24.7136
RIYADH_LON  = 46.6753
RIYADH_ZOOM = 18          # zoom افتراضي — مدينة الرياض

# دليل الأسعار الإرشادية
PRICE_GUIDE = [
    {"name": "أنابيب بقطر 1400 ملم",              "price": 4004.0},
    {"name": "قناة صندوقية (1.8 × 1.4) م",         "price": 9336.0},
    {"name": "قناة مفتوحة عرض 12م / عمق 1.5م",    "price": 13052.0},
]

# ══════════════════════════════════════════════════════════════════
#  حساب الأطوال — numpy vectorized
# ══════════════════════════════════════════════════════════════════

def _seg_lengths_np(coords_arr: np.ndarray) -> float:
    if len(coords_arr) < 2:
        return 0.0
    R   = 6_371_000.0
    lon = np.radians(coords_arr[:, 0])
    lat = np.radians(coords_arr[:, 1])
    dph = np.diff(lat);  dlm = np.diff(lon)
    ph1 = lat[:-1];      ph2 = lat[1:]
    a   = np.sin(dph/2)**2 + np.cos(ph1)*np.cos(ph2)*np.sin(dlm/2)**2
    a   = np.clip(a, 0, 1)
    return float(R * 2 * np.sum(np.arctan2(np.sqrt(a), np.sqrt(1-a))))


def calc_length_fast(geom) -> float:
    try:
        if geom is None: return 0.0
        if geom.geom_type == "MultiLineString":
            return round(sum(_seg_lengths_np(np.array(p.coords)) for p in geom.geoms), 2)
        if geom.geom_type == "LineString":
            return round(_seg_lengths_np(np.array(geom.coords)), 2)
        return 0.0
    except Exception:
        return 0.0


def haversine_coords(coords: list) -> float:
    return round(_seg_lengths_np(np.array(coords, dtype=float)), 2)


# ══════════════════════════════════════════════════════════════════
#  تحميل الملف — مخزَّن في الكاش
# ══════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def load_file(file_bytes: bytes, file_name: str):
    name = file_name.lower()
    try:
        if name.endswith((".geojson", ".json")):
            import io
            gdf = gpd.read_file(io.BytesIO(file_bytes))
        elif name.endswith(".zip"):
            with tempfile.TemporaryDirectory() as tmp:
                zp = os.path.join(tmp, "up.zip")
                with open(zp, "wb") as f: f.write(file_bytes)
                with zipfile.ZipFile(zp) as z: z.extractall(tmp)
                shps = [os.path.join(r, fn)
                        for r, _, fs in os.walk(tmp) for fn in fs if fn.endswith(".shp")]
                if not shps:
                    st.error("❌ لا يوجد ملف .shp داخل الـ ZIP")
                    return None
                gdf = gpd.read_file(shps[0])
        else:
            st.error("❌ صيغة غير مدعومة")
            return None
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الملف: {e}")
        return None

    if gdf.crs is None:          gdf = gdf.set_crs(epsg=4326)
    elif gdf.crs.to_epsg() != 4326: gdf = gdf.to_crs(epsg=4326)

    gdf = gdf[gdf.geometry.apply(
        lambda g: g is not None and g.geom_type in ("LineString","MultiLineString")
    )].reset_index(drop=True)

    if len(gdf) == 0:
        st.error("❌ الملف لا يحتوي على معالم خطية"); return None

    gdf["length_m"]  = gdf.geometry.apply(calc_length_fast)
    gdf["_geojson"]  = gdf.geometry.apply(lambda g: json.dumps(g.__geo_interface__))
    gdf.attrs["bounds"] = gdf.total_bounds.tolist()
    return gdf


def get_label_col(gdf):
    for c in ("name","Name","NAME","id","ID","FID","OBJECTID","label","LABEL"):
        if c in gdf.columns: return c
    return None


# ══════════════════════════════════════════════════════════════════
#  بناء الخريطة
#  default_riyadh=True  → يبدأ على الرياض ثم fit_bounds على البيانات
# ══════════════════════════════════════════════════════════════════

def build_map(gdf=None, selected_indices=None, draw_tools=False, zoom_start=None):
    sel = set(selected_indices or [])
    z   = zoom_start if zoom_start is not None else RIYADH_ZOOM

    # الوضع الافتراضي دائماً الرياض أولاً
    m = folium.Map(
        location=[RIYADH_LAT, RIYADH_LON],
        zoom_start=z,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )

    folium.TileLayer("OpenStreetMap", name="خريطة الشارع", show=True).add_to(m)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صور جوية", show=False
    ).add_to(m)
    folium.TileLayer(
        "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB", name="خريطة فاتحة", show=False
    ).add_to(m)

    if gdf is not None and len(gdf) > 0:
        label_col = get_label_col(gdf)

        # ── الخطوط العادية (طبقة FeatureCollection واحدة) ──────
        normal = gdf[~gdf.index.isin(sel)]
        if len(normal) > 0:
            fc = {"type":"FeatureCollection","features":[]}
            for idx, row in normal.iterrows():
                lbl = str(row[label_col]) if label_col else f"خط {idx}"
                fc["features"].append({
                    "type":"Feature",
                    "geometry": json.loads(row["_geojson"]),
                    "properties":{"idx": str(idx), "label":lbl,"length":f"{row['length_m']:,.1f}"}
                })
            folium.GeoJson(
                fc, name="شبكة السيول",
                style_function=lambda f: {"color":"#0077b6","weight":2.5,"opacity":0.85},
                tooltip=folium.GeoJsonTooltip(
                    fields=["idx","label","length"],
                    aliases=["رقم الخط:","الاسم:","الطول (م):"],
                    localize=True, sticky=False,
                    style="font-family:Tajawal,sans-serif;direction:rtl;font-size:13px;"
                )
            ).add_to(m)

        # ── الخطوط المختارة (أحمر) ─────────────────────────────
        if sel:
            sel_rows = gdf[gdf.index.isin(sel)]
            fc_s = {"type":"FeatureCollection","features":[]}
            for idx, row in sel_rows.iterrows():
                lbl = str(row[label_col]) if label_col else f"خط {idx}"
                fc_s["features"].append({
                    "type":"Feature",
                    "geometry": json.loads(row["_geojson"]),
                    "properties":{"idx": str(idx), "label":lbl,"length":f"{row['length_m']:,.1f}"}
                })
            folium.GeoJson(
                fc_s, name="الخطوط المختارة",
                style_function=lambda f: {"color":"#e63946","weight":5,"opacity":1.0},
                tooltip=folium.GeoJsonTooltip(
                    fields=["idx","label","length"],
                    aliases=["رقم الخط:","الاسم:","الطول (م):"],
                    localize=True, sticky=False,
                    style="font-family:Tajawal,sans-serif;direction:rtl;font-size:13px;"
                )
            ).add_to(m)

        # fit_bounds على منطقة البيانات
        b = gdf.attrs.get("bounds")
        if b:
            m.fit_bounds([[b[1],b[0]],[b[3],b[2]]])

    if draw_tools:
        Draw(
            draw_options={
                "polyline": {"shapeOptions":{"color":"#ff6b35","weight":4}},
                "polygon":False,"rectangle":False,
                "circle":False,"marker":False,"circlemarker":False,
            },
            edit_options={"edit":True,"remove":True}
        ).add_to(m)

    MeasureControl(position="topleft", primary_length_unit="meters").add_to(m)
    folium.LayerControl(position="topright").add_to(m)
    return m


# ══════════════════════════════════════════════════════════════════
#  مكوّن: دليل الأسعار الإرشادية
# ══════════════════════════════════════════════════════════════════

def price_guide_widget(key_prefix="pg"):
    """
    يعرض جدول الأسعار الإرشادية وأزرار تعبئة سريعة،
    ويُعيد السعر المختار (float) أو None.
    """
    rows_html = ""
    for p in PRICE_GUIDE:
        rows_html += f"""
        <div class="pg-row">
            <span class="pg-name">{p['name']}</span>
            <span class="pg-price">{p['price']:,.0f} ﷼/م</span>
        </div>"""

    st.markdown(f"""
    <div class="price-guide">
        <div class="pg-title">💡 دليل الأسعار الإرشادية التقريبية</div>
        {rows_html}
        <div style='font-size:.78rem;color:#8d6e63;margin-top:8px'>
        ⚠️ الأسعار تقريبية للإرشاد فقط — تختلف حسب الموقع والمواصفات
        </div>
    </div>
    """, unsafe_allow_html=True)

    # أزرار التعبئة السريعة
    st.markdown("<div style='direction:rtl;font-size:.88rem;font-weight:600;color:#374151;margin-bottom:4px'>⚡ تعبئة سريعة:</div>",
                unsafe_allow_html=True)

    chosen = None
    cols = st.columns(len(PRICE_GUIDE))
    for i, (p, col) in enumerate(zip(PRICE_GUIDE, cols)):
        short = p["name"].split(" ")[0] + " " + p["name"].split(" ")[1] \
                if len(p["name"].split(" ")) > 1 else p["name"][:12]
        if col.button(f"{p['price']:,.0f} ﷼", key=f"{key_prefix}_btn_{i}",
                      help=p["name"]):
            chosen = p["price"]
    return chosen


# ══════════════════════════════════════════════════════════════════
#  الواجهة الرئيسية
# ══════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero-header">
    <h1>🌊 نظام تحليل شبكات السيول</h1>
    <p>تحليل شبكات تصريف السيول · حساب الأطوال · تقدير التكاليف</p>
</div>
""", unsafe_allow_html=True)

# ─── الشريط الجانبي ───────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sec-title">📁 رفع الملف</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:.86rem;color:#374151;margin-bottom:8px;direction:rtl'>
        الصيغ المدعومة:<br>
        <span class="bdg-g">GeoJSON</span>
        <span class="bdg-s">ZIP (Shapefile)</span>
    </div>""", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "اختر الملف",
        type=["geojson","json","zip"],
        help="ارفع GeoJSON مباشرة أو ZIP يحتوي على .shp/.dbf/.shx/.prj"
    )

    st.markdown("---")

    st.markdown("""
    <div class="info-box">
    <b>💡 كيفية الاستخدام:</b><br>
    ① ارفع ملف GeoJSON أو ZIP<br>
    ② استعرض الخريطة التفاعلية<br>
    ③ اختر خطاً أو أكثر لحساب التكلفة<br>
    ④ أو ارسم خطاً جديداً على الخريطة
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="price-guide" style="margin-top:12px">
        <div class="pg-title">💡 الأسعار الإرشادية (ريال / متر)</div>
        <div class="pg-row">
            <span class="pg-name">أنابيب بقطر 1400 ملم</span>
            <span class="pg-price">4,004 ﷼/م</span>
        </div>
        <div class="pg-row">
            <span class="pg-name">قناة صندوقية (1.8 × 1.4) م</span>
            <span class="pg-price">9,336 ﷼/م</span>
        </div>
        <div class="pg-row">
            <span class="pg-name">قناة مفتوحة (12 × 1.5) م</span>
            <span class="pg-price">13,052 ﷼/م</span>
        </div>
        <div style='font-size:.76rem;color:#8d6e63;margin-top:7px;line-height:1.6'>
        ⚠️ الأسعار تقريبية للإرشاد — تختلف حسب الموقع والمواصفات
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="dev-signature">
        <span class="dev-avatar">👷</span>
        <div class="dev-label">Developed by</div>
        <div class="dev-name">Eng: Ahmed Adam</div>
        <div class="dev-title-line">🌊 نظام تحليل شبكات السيول</div>
        <hr class="dev-divider">
        <div class="dev-copy">GIS Flood Network System &nbsp;·&nbsp; v4.0<br>© 2025 — جميع الحقوق محفوظة</div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  شاشة الترحيب — بدون ملف
# ══════════════════════════════════════════════════════════════════
if uploaded is None:
    m_default = build_map(zoom_start=11)   # خريطة الرياض فارغة — zoom مدينة
    col_info, col_map = st.columns([1, 2])

    with col_info:
        st.markdown("""
        <div style='background:white;border-radius:16px;padding:30px 20px;
                    box-shadow:0 2px 14px rgba(0,0,0,.08);text-align:right;direction:rtl'>
            <div style='font-size:3rem;text-align:center'>🗂️</div>
            <h3 style='color:#1a3a5c;margin:10px 0 8px;font-size:1.15rem;text-align:center'>
                ابدأ برفع الملف
            </h3>
            <p style='color:#6b7280;font-size:.9rem;line-height:2;text-align:right'>
                ارفع ملف <b>GeoJSON</b> مباشرةً<br>
                أو ملف <b>ZIP</b> يحتوي على Shapefile<br>
                من الشريط الجانبي لبدء التحليل
            </p>
            <div style='margin-top:14px;background:#f8fafc;border-radius:10px;
                        padding:12px;font-size:.84rem;color:#64748b;direction:rtl;text-align:right;
                        border-right:3px solid #0d6efd'>
                📌 <b>كيف تحوّل Shapefile إلى ZIP؟</b><br>
                ① اختر مجلد الـ SHP كاملاً<br>
                ② كليك يمين ← ضغط / Compress<br>
                ③ ارفع ملف الـ ZIP الناتج
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_map:
        st_folium(m_default, width="100%", height=450,
                  returned_objects=[], key="map_default")

# ══════════════════════════════════════════════════════════════════
#  بعد رفع الملف
# ══════════════════════════════════════════════════════════════════
else:
    file_bytes = uploaded.read()
    with st.spinner("⏳ جاري قراءة البيانات وحساب الأطوال..."):
        gdf = load_file(file_bytes, uploaded.name)

    if gdf is not None:
        total_length = float(gdf["length_m"].sum())
        n_lines      = len(gdf)
        avg_len      = float(gdf["length_m"].mean())
        max_len      = float(gdf["length_m"].max())

        # ── بطاقات الإحصائيات ─────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="mc">
                <div class="lb">📏 عدد الخطوط</div>
                <div class="vl">{n_lines:,}</div>
                <div class="un">خط</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="mc g">
                <div class="lb">📐 الطول الإجمالي</div>
                <div class="vl">{total_length/1000:.3f}</div>
                <div class="un">كيلومتر ({total_length:,.0f} م)</div></div>""",
                unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="mc">
                <div class="lb">📊 متوسط الطول</div>
                <div class="vl">{avg_len:.1f}</div>
                <div class="un">متر</div></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="mc o">
                <div class="lb">🔝 أطول خط</div>
                <div class="vl">{max_len:,.1f}</div>
                <div class="un">متر</div></div>""", unsafe_allow_html=True)

        # ── التبويبات ──────────────────────────────────────────
        tab1, tab2, tab3, tab4 = st.tabs([
            "🗺️ الخريطة التفاعلية",
            "💰 حساب تكلفة خطوط موجودة",
            "✏️ رسم خط جديد",
            "📊 جدول البيانات"
        ])

        # ════════════════════════════════════════════════════════
        #  تبويب 1 — الخريطة
        # ════════════════════════════════════════════════════════
        with tab1:
            st.markdown('<div class="sec-title">🗺️ خريطة شبكة السيول</div>',
                        unsafe_allow_html=True)
            st.markdown("""
            <div class="info-box">
            💡 <b>كيفية الاستخدام:</b><br>
            مرّر الماوس على أي خط لعرض اسمه وطوله<br>
            غيّر نوع الخريطة من الزاوية العلوية اليمنى<br>
            استخدم أداة القياس 📐 في أعلى اليسار لقياس المسافات
            </div>""", unsafe_allow_html=True)

            with st.spinner("🗺️ جاري تحميل الخريطة..."):
                m1 = build_map(gdf)
            st_folium(m1, width="100%", height=540,
                      returned_objects=[], key="map_overview")

        # ════════════════════════════════════════════════════════
        #  تبويب 2 — تكلفة خطوط موجودة
        # ════════════════════════════════════════════════════════
        with tab2:
            st.markdown('<div class="sec-title">💰 حساب تكلفة خطوط من الشبكة</div>',
                        unsafe_allow_html=True)

            col_ctrl, col_map2 = st.columns([2, 3])

            with col_ctrl:
                # ── إرشادات (RTL) ──
                st.markdown("""
                <div class="info-box">
                📋 <b>خطوات الحساب:</b><br>
                ① اختر خطاً أو أكثر من القائمة أدناه<br>
                ② تظهر الخطوط باللون الأحمر على الخريطة<br>
                ③ اختر نوع التصريف أو أدخل السعر يدوياً<br>
                ④ اضغط "احسب التكلفة الإجمالية"
                </div>
                """, unsafe_allow_html=True)

                # ── دليل الأسعار ──
                st.markdown("""
                <div class="price-guide">
                    <div class="pg-title">💡 دليل الأسعار الإرشادية (ريال/متر)</div>
                    <div class="pg-row">
                        <span class="pg-name">أنابيب بقطر 1400 ملم</span>
                        <span class="pg-price">4,004 ﷼</span>
                    </div>
                    <div class="pg-row">
                        <span class="pg-name">قناة صندوقية (1.8 × 1.4) م</span>
                        <span class="pg-price">9,336 ﷼</span>
                    </div>
                    <div class="pg-row">
                        <span class="pg-name">قناة مفتوحة (12 × 1.5) م</span>
                        <span class="pg-price">13,052 ﷼</span>
                    </div>
                    <div style='font-size:.75rem;color:#8d6e63;margin-top:6px'>
                    ⚠️ الأسعار تقريبية للإرشاد — تختلف حسب الموقع والمواصفات
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ── تعبئة سريعة ──
                st.markdown("""<div style='direction:rtl;font-size:.88rem;
                    font-weight:700;color:#374151;margin:8px 0 4px'>
                    ⚡ تعبئة سريعة بسعر نوع التصريف:</div>""",
                    unsafe_allow_html=True)

                qc1, qc2, qc3 = st.columns(3)
                quick_price_t2 = None
                if qc1.button("أنابيب\n4,004 ﷼", key="qp_t2_0",
                               help="أنابيب بقطر 1400 ملم — 4,004 ﷼/م"):
                    quick_price_t2 = 4004.0
                if qc2.button("صندوقية\n9,336 ﷼", key="qp_t2_1",
                               help="قناة صندوقية (1.8×1.4)م — 9,336 ﷼/م"):
                    quick_price_t2 = 9336.0
                if qc3.button("مفتوحة\n13,052 ﷼", key="qp_t2_2",
                               help="قناة مفتوحة (12×1.5)م — 13,052 ﷼/م"):
                    quick_price_t2 = 13052.0

                # تحديث session_state عند الضغط
                if quick_price_t2 is not None:
                    st.session_state["price_t2"] = quick_price_t2

                st.markdown("---")
                st.markdown("""<div style='direction:rtl;font-weight:700;color:#1a3a5c;
                    font-size:.95rem;margin-bottom:4px'>📋 اختر الخطوط:</div>""",
                    unsafe_allow_html=True)

                label_col = get_label_col(gdf)
                if label_col:
                    options_list = [
                        f"{idx} | {str(row[label_col])[:28]}  ({row['length_m']:,.1f} م)"
                        for idx, row in gdf.iterrows()
                    ]
                else:
                    options_list = [
                        f"خط {idx}  ({row['length_m']:,.1f} م)"
                        for idx, row in gdf.iterrows()
                    ]

                selected_labels = st.multiselect(
                    "يمكن اختيار خط واحد أو أكثر",
                    options=options_list,
                    placeholder="اكتب للبحث أو انقر للاختيار...",
                    key="multi_lines"
                )

                # استخراج الـ indices
                selected_indices = []
                for lbl in selected_labels:
                    try:
                        part = lbl.split("|")[0].strip() if "|" in lbl \
                               else lbl.replace("خط ","").split(" ")[0]
                        selected_indices.append(int(part.strip()))
                    except Exception:
                        pass

                if selected_indices:
                    sel_gdf   = gdf.loc[selected_indices]
                    total_sel = float(sel_gdf["length_m"].sum())
                    n_sel     = len(selected_indices)
                    st.markdown(f"""
                    <div class="mc g" style="margin-top:10px">
                        <div class="lb">✅ عدد الخطوط المختارة</div>
                        <div class="vl">{n_sel}</div>
                        <div class="un">خط</div>
                    </div>
                    <div class="mc g">
                        <div class="lb">📐 مجموع الأطوال المختارة</div>
                        <div class="vl">{total_sel:,.1f}</div>
                        <div class="un">متر = {total_sel/1000:.3f} كم</div>
                    </div>""", unsafe_allow_html=True)

                    with st.expander("📋 تفاصيل الخطوط المختارة"):
                        for i in selected_indices:
                            r   = gdf.loc[i]
                            lbl = str(r[label_col]) if label_col else f"خط {i}"
                            st.markdown(f"• **{lbl}** — {r['length_m']:,.1f} م")
                else:
                    total_sel = 0.0
                    n_sel     = 0
                    st.markdown("""
                    <div style='text-align:center;padding:18px;color:#94a3b8;direction:rtl'>
                        <div style='font-size:1.8rem'>☝️</div>
                        <p style='margin:4px 0;font-size:.9rem'>اختر خطاً أو أكثر من القائمة</p>
                    </div>""", unsafe_allow_html=True)

                # حقل السعر
                default_price_t2 = st.session_state.get("price_t2", 100.0)
                price = st.number_input(
                    "💲 أدخل السعر لكل متر (ريال سعودي)",
                    min_value=0.0,
                    value=float(default_price_t2),
                    step=10.0,
                    format="%.2f",
                    key="price_t2_input"
                )

                if st.button("🧮 احسب التكلفة الإجمالية", key="calc_t2"):
                    if total_sel > 0:
                        cost = total_sel * price
                        breakdown = ""
                        if n_sel > 1:
                            for i in selected_indices:
                                r   = gdf.loc[i]
                                lbl = str(r[label_col]) if label_col else f"خط {i}"
                                breakdown += (
                                    f"• {lbl}: {r['length_m']:,.1f} م"
                                    f" × {price:,.2f} = {r['length_m']*price:,.2f} ﷼<br>"
                                )
                        hr = '<hr style="border:0;border-top:1px solid #a5d6a7;margin:8px 0">'
                        st.markdown(f"""
                        <div class="result-box">
                            <div class="rt">💵 التكلفة الإجمالية</div>
                            <div class="rv">{cost:,.2f} ﷼</div>
                            <div class="rs">
                                {total_sel:,.1f} م × {price:,.2f} ﷼/م
                                &nbsp;|&nbsp; {n_sel} خط
                                {(hr+breakdown) if breakdown else ""}
                            </div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ اختر خطاً واحداً على الأقل")

            with col_map2:
                with st.spinner("🗺️ جاري تحميل الخريطة..."):
                    m2 = build_map(gdf, selected_indices=selected_indices)
                st_folium(m2, width="100%", height=560,
                          returned_objects=[], key="map_t2")

        # ════════════════════════════════════════════════════════
        #  تبويب 3 — رسم خط جديد
        # ════════════════════════════════════════════════════════
        with tab3:
            st.markdown('<div class="sec-title">✏️ ارسم خطاً جديداً على الخريطة</div>',
                        unsafe_allow_html=True)

            col_dm, col_dc = st.columns([3, 2])

            with col_dm:
                # إرشادات فوق الخريطة
                st.markdown("""
                <div class="info-box">
                📌 <b>خطوات الرسم:</b><br>
                ① انقر على أيقونة <b>🖊 الخط</b> في أعلى يسار الخريطة<br>
                ② انقر على الخريطة نقطةً نقطةً لرسم المسار<br>
                ③ انقر <b>مرتين</b> على آخر نقطة لإنهاء الرسم<br>
                ④ يظهر الطول تلقائياً في اللوحة على اليسار<br>
                ⑤ أدخل السعر أو اختر نوع التصريف ثم احسب
                </div>
                """, unsafe_allow_html=True)

                with st.spinner("🗺️ جاري تحميل الخريطة..."):
                    m3 = build_map(gdf, draw_tools=True)
                map_data = st_folium(
                    m3, width="100%", height=520,
                    returned_objects=["all_drawings"],
                    key="map_draw"
                )

            with col_dc:
                # ── دليل الأسعار ──
                st.markdown("""
                <div class="price-guide">
                    <div class="pg-title">💡 دليل الأسعار الإرشادية (ريال/متر)</div>
                    <div class="pg-row">
                        <span class="pg-name">أنابيب بقطر 1400 ملم</span>
                        <span class="pg-price">4,004 ﷼</span>
                    </div>
                    <div class="pg-row">
                        <span class="pg-name">قناة صندوقية (1.8 × 1.4) م</span>
                        <span class="pg-price">9,336 ﷼</span>
                    </div>
                    <div class="pg-row">
                        <span class="pg-name">قناة مفتوحة (12 × 1.5) م</span>
                        <span class="pg-price">13,052 ﷼</span>
                    </div>
                    <div style='font-size:.75rem;color:#8d6e63;margin-top:6px'>
                    ⚠️ الأسعار تقريبية للإرشاد — تختلف حسب الموقع
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # تعبئة سريعة
                st.markdown("""<div style='direction:rtl;font-size:.88rem;
                    font-weight:700;color:#374151;margin:8px 0 4px'>
                    ⚡ تعبئة سريعة:</div>""", unsafe_allow_html=True)

                dc1, dc2, dc3 = st.columns(3)
                quick_price_t3 = None
                if dc1.button("أنابيب\n4,004 ﷼", key="qp_t3_0",
                               help="أنابيب بقطر 1400 ملم — 4,004 ﷼/م"):
                    quick_price_t3 = 4004.0
                if dc2.button("صندوقية\n9,336 ﷼", key="qp_t3_1",
                               help="قناة صندوقية (1.8×1.4)م — 9,336 ﷼/م"):
                    quick_price_t3 = 9336.0
                if dc3.button("مفتوحة\n13,052 ﷼", key="qp_t3_2",
                               help="قناة مفتوحة (12×1.5)م — 13,052 ﷼/م"):
                    quick_price_t3 = 13052.0

                if quick_price_t3 is not None:
                    st.session_state["price_t3"] = quick_price_t3

                st.markdown("---")

                # نتيجة الطول المرسوم
                drawings    = (map_data or {}).get("all_drawings") or []
                drawn_lines = [
                    d for d in drawings
                    if d.get("geometry",{}).get("type") == "LineString"
                    and len(d["geometry"].get("coordinates",[])) >= 2
                ]

                if drawn_lines:
                    line_lengths = [
                        haversine_coords(d["geometry"]["coordinates"])
                        for d in drawn_lines
                    ]
                    drawn_total = sum(line_lengths)
                    st.markdown(f"""
                    <div class="mc g">
                        <div class="lb">✏️ عدد الخطوط المرسومة</div>
                        <div class="vl">{len(drawn_lines)}</div>
                        <div class="un">خط</div>
                    </div>
                    <div class="mc g">
                        <div class="lb">📐 مجموع الأطوال المرسومة</div>
                        <div class="vl">{drawn_total:,.1f}</div>
                        <div class="un">متر = {drawn_total/1000:.3f} كم</div>
                    </div>""", unsafe_allow_html=True)

                    if len(line_lengths) > 1:
                        with st.expander("📋 تفاصيل الخطوط المرسومة"):
                            for i, ll in enumerate(line_lengths, 1):
                                st.markdown(f"• خط {i}: **{ll:,.1f} م**")
                else:
                    drawn_total = 0.0
                    st.markdown("""
                    <div style='text-align:center;padding:28px;color:#94a3b8;direction:rtl'>
                        <div style='font-size:2.2rem'>✏️</div>
                        <p style='margin:6px 0;font-size:.9rem'>
                            ارسم خطاً على الخريطة<br>لظهور طوله هنا
                        </p>
                    </div>""", unsafe_allow_html=True)

                # حقل السعر
                default_price_t3 = st.session_state.get("price_t3", 100.0)
                price_draw = st.number_input(
                    "💲 أدخل السعر لكل متر (ريال سعودي)",
                    min_value=0.0,
                    value=float(default_price_t3),
                    step=10.0,
                    format="%.2f",
                    key="price_t3_input"
                )

                if st.button("🧮 احسب تكلفة الخطوط المرسومة", key="calc_t3"):
                    if drawn_total > 0:
                        cost_draw = drawn_total * price_draw
                        st.markdown(f"""
                        <div class="result-box">
                            <div class="rt">💵 التكلفة الإجمالية</div>
                            <div class="rv">{cost_draw:,.2f} ﷼</div>
                            <div class="rs">
                                {drawn_total:,.1f} م × {price_draw:,.2f} ﷼/م<br>
                                ({len(drawn_lines)} خط مرسوم)
                            </div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ ارسم خطاً على الخريطة أولاً")

        # ════════════════════════════════════════════════════════
        #  تبويب 4 — جدول البيانات
        # ════════════════════════════════════════════════════════
        with tab4:
            st.markdown('<div class="sec-title">📊 جدول بيانات الشبكة الكاملة</div>',
                        unsafe_allow_html=True)

            st.markdown(f"""
            <div class="mc g" style="display:inline-block;min-width:280px">
                <div class="lb">📐 مجموع الأطوال الكلي</div>
                <div class="vl">{total_length:,.1f} م</div>
                <div class="un">= {total_length/1000:.3f} كيلومتر</div>
            </div>""", unsafe_allow_html=True)

            display_cols = [c for c in gdf.columns if c not in ("geometry","_geojson")]
            df_show = gdf[display_cols].copy()
            df_show["length_m"] = df_show["length_m"].round(2)
            df_show.index.name  = "رقم"

            st.dataframe(df_show, use_container_width=True, height=430)

            csv = df_show.to_csv(index=True).encode("utf-8-sig")
            st.download_button(
                label="⬇️ تحميل الجدول CSV",
                data=csv,
                file_name="flood_network.csv",
                mime="text/csv",
                key="dl_csv"
            )
