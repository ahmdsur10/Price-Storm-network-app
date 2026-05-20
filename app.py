"""
نظام تحليل شبكات السيول
GIS Flood Network Analysis System
Developed by: Eng. Ahmed Adam
v5.0 — 2025 (Optimized)
"""

import streamlit as st
import folium
from folium.plugins import Draw, MeasureControl
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import json, os, tempfile, zipfile
from shapely.geometry import shape

# ══════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="نظام تحليل شبكات السيول",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
#  STYLES
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Tajawal', sans-serif !important;
    direction: rtl;
}
.main { background: #f0f4f8; }

/* ── Header ─────────────────────────────────────── */
.app-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 40%, #0d6efd 80%, #00b4d8 100%);
    border-radius: 18px;
    padding: 28px 40px;
    margin-bottom: 24px;
    text-align: center;
    color: white;
    box-shadow: 0 8px 32px rgba(13,110,253,.3);
}
.app-header h1 { font-size: 2.2rem; font-weight: 800; margin: 0; letter-spacing: 1px; }
.app-header p  { font-size: 1rem; opacity: .85; margin: 8px 0 0; }

/* ── Metric Cards ────────────────────────────────── */
.card {
    background: white;
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,.07);
    border-right: 5px solid #0d6efd;
    margin-bottom: 12px;
    direction: rtl;
}
.card.green  { border-right-color: #43a047; }
.card.orange { border-right-color: #fb8c00; }
.card .lbl { color: #6b7280; font-size: .84rem; font-weight: 500; }
.card .val { color: #1a3a5c; font-size: 1.6rem; font-weight: 800; margin-top: 2px; }
.card .unt { color: #0d6efd; font-size: .82rem; font-weight: 600; }
.card.green  .val { color: #1b5e20; } .card.green  .unt { color: #43a047; }
.card.orange .val { color: #e65100; } .card.orange .unt { color: #fb8c00; }

/* ── Result Box ──────────────────────────────────── */
.result {
    background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
    border: 2px solid #43a047;
    border-radius: 14px;
    padding: 20px 26px;
    text-align: center;
    margin-top: 14px;
    box-shadow: 0 4px 16px rgba(67,160,71,.15);
    direction: rtl;
}
.result .r-title { font-size: .95rem; color: #2e7d32; font-weight: 600; }
.result .r-value { font-size: 2.2rem; font-weight: 800; color: #1b5e20; margin-top: 6px; }
.result .r-sub   { font-size: .86rem; color: #388e3c; margin-top: 6px; line-height: 1.9; }

/* ── Info Box ────────────────────────────────────── */
.info-box {
    background: #e3f2fd;
    border: 1px solid #90caf9;
    border-radius: 10px;
    padding: 14px 18px;
    font-size: .92rem;
    color: #1565c0;
    line-height: 2;
    direction: rtl;
    text-align: right;
    margin: 10px 0;
}
.info-box b { color: #0d47a1; }

/* ── Price Guide ─────────────────────────────────── */
.price-guide {
    background: #fff8e1;
    border: 1px solid #ffe082;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 10px 0;
    direction: rtl;
    text-align: right;
}
.price-guide .pg-head {
    font-size: .97rem;
    font-weight: 800;
    color: #e65100;
    margin-bottom: 10px;
    padding-bottom: 7px;
    border-bottom: 1px dashed #ffcc80;
}
.price-guide .pg-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    border-bottom: 1px solid #fff3cd;
    font-size: .9rem;
}
.price-guide .pg-row:last-of-type { border-bottom: none; }
.price-guide .pg-name  { color: #5d4037; font-weight: 600; flex: 1; }
.price-guide .pg-badge {
    background: #e65100;
    color: white;
    border-radius: 8px;
    padding: 2px 11px;
    font-size: .82rem;
    font-weight: 700;
    white-space: nowrap;
}
.price-guide .pg-note {
    font-size: .76rem;
    color: #8d6e63;
    margin-top: 8px;
    line-height: 1.6;
}

/* ── Section Title ───────────────────────────────── */
.sec-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a3a5c;
    padding: 5px 0 9px;
    border-bottom: 2px solid #e2e8f0;
    margin-bottom: 14px;
    direction: rtl;
    text-align: right;
}

/* ── Sidebar ─────────────────────────────────────── */
section[data-testid="stSidebar"] {
    width: 360px !important;
    min-width: 360px !important;
}
section[data-testid="stSidebar"] > div:first-child {
    width: 360px !important;
    padding: 1.2rem 1rem !important;
}
section[data-testid="stSidebar"] .info-box   { font-size: .96rem !important; }
section[data-testid="stSidebar"] .price-guide { font-size: .92rem !important; }
section[data-testid="stSidebar"] label        { font-size: 1rem !important; }

/* ── Format Badges ───────────────────────────────── */
.badge {
    display: inline-block;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: .84rem;
    font-weight: 700;
    margin-left: 4px;
}
.badge.geo { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
.badge.shp { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }

/* ── Buttons ─────────────────────────────────────── */
div[data-testid="stButton"] > button {
    width: 100%;
    background: linear-gradient(135deg, #0d6efd, #0077b6);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 11px 18px;
    font-family: 'Tajawal', sans-serif !important;
    font-size: 1rem;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(13,110,253,.3);
    cursor: pointer;
    transition: all .2s;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(13,110,253,.42);
}

/* ── Tabs ────────────────────────────────────────── */
.stTabs [data-baseweb="tab"] {
    font-family: 'Tajawal', sans-serif !important;
    font-size: .97rem;
    font-weight: 600;
}

/* ── Developer Signature ─────────────────────────── */
.signature {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 50%, #0d6efd 100%);
    border-radius: 14px;
    padding: 18px 16px;
    margin-top: 18px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(13,110,253,.3);
    border: 1px solid rgba(255,255,255,.12);
}
.signature .sig-icon  { font-size: 2.4rem; display: block; margin-bottom: 6px; }
.signature .sig-by    { font-size: .72rem; color: rgba(255,255,255,.55); letter-spacing: 1.5px; text-transform: uppercase; }
.signature .sig-name  { font-size: 1.25rem; font-weight: 800; color: #fff; margin-top: 4px; letter-spacing: .5px; }
.signature .sig-sub   { font-size: .82rem; color: rgba(255,255,255,.65); margin-top: 4px; }
.signature .sig-hr    { border: 0; border-top: 1px solid rgba(255,255,255,.15); margin: 10px 0; }
.signature .sig-copy  { font-size: .72rem; color: rgba(255,255,255,.4); }

footer { visibility: hidden; }
input[type="number"] { text-align: right !important; direction: rtl !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════
RIYADH = [24.7136, 46.6753]
ZOOM_DEFAULT = 11   # شاشة الترحيب
ZOOM_DATA    = 18   # بعد رفع البيانات

PRICES = [
    ("أنابيب بقطر 1400 ملم",         4_004.0),
    ("قناة صندوقية (1.8 × 1.4) م",   9_336.0),
    ("قناة مفتوحة (12 × 1.5) م",    13_052.0),
]

# ══════════════════════════════════════════════════════════════
#  GEOMETRY HELPERS  (numpy vectorized — no GDAL)
# ══════════════════════════════════════════════════════════════

def _haversine_arr(coords: np.ndarray) -> float:
    """طول مسار من مصفوفة (N×2) [lon, lat] بالمتر"""
    if len(coords) < 2:
        return 0.0
    R   = 6_371_000.0
    lon = np.radians(coords[:, 0])
    lat = np.radians(coords[:, 1])
    dph = np.diff(lat)
    dlm = np.diff(lon)
    a   = (np.sin(dph / 2) ** 2
           + np.cos(lat[:-1]) * np.cos(lat[1:]) * np.sin(dlm / 2) ** 2)
    return float(R * 2 * np.sum(np.arctan2(np.sqrt(np.clip(a, 0, 1)),
                                            np.sqrt(np.clip(1 - a, 0, 1)))))


def length_from_geojson(geom: dict) -> float:
    """حساب طول هندسة GeoJSON بالمتر"""
    try:
        g = shape(geom)
        if g.geom_type == "LineString":
            return round(_haversine_arr(np.array(g.coords)), 2)
        if g.geom_type == "MultiLineString":
            return round(sum(_haversine_arr(np.array(p.coords)) for p in g.geoms), 2)
    except Exception:
        pass
    return 0.0


def length_from_coords(coords: list) -> float:
    """طول مسار من قائمة [[lon, lat], ...]"""
    return round(_haversine_arr(np.array(coords, dtype=float)), 2)


# ══════════════════════════════════════════════════════════════
#  FILE LOADING  (json + pyshp — no geopandas/fiona/GDAL)
# ══════════════════════════════════════════════════════════════

def _fc_to_df(fc: dict):
    """
    يحوّل FeatureCollection إلى DataFrame
    يُعيد (df, list_of_features) أو (None, None)
    """
    LINE_TYPES = {"LineString", "MultiLineString"}
    features = [
        f for f in fc.get("features", [])
        if f.get("geometry") and f["geometry"].get("type") in LINE_TYPES
    ]
    if not features:
        return None, None

    rows = []
    for i, feat in enumerate(features):
        props  = feat.get("properties") or {}
        length = length_from_geojson(feat["geometry"])
        row    = {"_idx": i, "length_m": length,
                  "_geom": json.dumps(feat["geometry"])}
        # تنظيف الخصائص
        for k, v in props.items():
            if isinstance(v, bytes):
                v = v.decode("utf-8", "ignore")
            row[str(k)] = v
        rows.append(row)

    df = pd.DataFrame(rows).set_index("_idx")
    df.index.name = "رقم"
    return df, features


@st.cache_data(show_spinner=False)
def load_geojson(data: bytes, name: str):
    try:
        fc = json.loads(data.decode("utf-8"))
        return _fc_to_df(fc)
    except Exception as e:
        st.error(f"❌ خطأ في قراءة GeoJSON: {e}")
        return None, None


@st.cache_data(show_spinner=False)
def load_shapefile_zip(data: bytes, name: str):
    try:
        import shapefile
    except ImportError:
        st.error("❌ مكتبة pyshp غير مثبتة في requirements.txt")
        return None, None

    with tempfile.TemporaryDirectory() as tmp:
        zp = os.path.join(tmp, "up.zip")
        with open(zp, "wb") as f:
            f.write(data)
        with zipfile.ZipFile(zp) as z:
            z.extractall(tmp)

        shps = [
            os.path.join(r, fn)
            for r, _, fs in os.walk(tmp)
            for fn in fs if fn.endswith(".shp")
        ]
        if not shps:
            st.error("❌ لم يُعثر على ملف .shp داخل الـ ZIP")
            return None, None

        try:
            sf = shapefile.Reader(shps[0], encoding="utf-8")
        except Exception:
            sf = shapefile.Reader(shps[0], encoding="cp1256")

        fields   = [f[0] for f in sf.fields[1:]]
        features = []
        for sr in sf.shapeRecords():
            geom  = sr.shape.__geo_interface__
            props = {
                k: (v.decode("utf-8", "ignore") if isinstance(v, bytes) else v)
                for k, v in zip(fields, sr.record)
            }
            features.append({"type": "Feature",
                              "geometry": geom,
                              "properties": props})

        fc = {"type": "FeatureCollection", "features": features}
        return _fc_to_df(fc)


def load_file(data: bytes, name: str):
    n = name.lower()
    if n.endswith((".geojson", ".json")):
        return load_geojson(data, name)
    if n.endswith(".zip"):
        return load_shapefile_zip(data, name)
    st.error("❌ صيغة غير مدعومة — ارفع GeoJSON أو ZIP")
    return None, None


# ══════════════════════════════════════════════════════════════
#  MAP BUILDER (CACHED FOR PERFORMANCE)
# ══════════════════════════════════════════════════════════════

def _label_col(df: pd.DataFrame):
    for c in ("name","Name","NAME","id","ID","FID","OBJECTID","label","LABEL"):
        if c in df.columns:
            return c
    return None


@st.cache_resource(ttl=3600)
def build_map(df=None, selected=None, draw=False, zoom=None):
    """
    بناء الخريطة مع تخزين مؤقت لتحسين الأداء.
    - df: DataFrame يحتوي على أعمدة (index, length_m, _geom)
    - selected: قائمة بالأرقام (index) للخطوط المحددة
    - draw: تفعيل أداة الرسم
    - zoom: مستوى التكبير (إن لم يُحدد يستخدم ZOOM_DATA)
    """
    sel = set(selected or [])
    z   = zoom if zoom is not None else ZOOM_DATA

    m = folium.Map(
        location=RIYADH, zoom_start=z,
        tiles=None, control_scale=True, prefer_canvas=True,
    )

    folium.TileLayer("OpenStreetMap",   name="خريطة الشارع", show=True).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صور جوية", show=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB", name="خريطة فاتحة", show=False,
    ).add_to(m)

    if df is not None and len(df) > 0:
        lc = _label_col(df)

        def _make_fc(rows, color, weight):
            fc = {"type": "FeatureCollection", "features": []}
            for idx, row in rows.iterrows():
                lbl = str(row[lc]) if lc else f"خط {idx}"
                fc["features"].append({
                    "type": "Feature",
                    "geometry": json.loads(row["_geom"]),
                    "properties": {
                        "رقم الخط": str(idx),
                        "الاسم":    lbl,
                        "الطول (م)": f"{row['length_m']:,.1f}",
                    },
                })
            return fc, color, weight

        # الخطوط العادية
        normal = df[~df.index.isin(sel)]
        if len(normal):
            fc_n, c_n, w_n = _make_fc(normal, "#0077b6", 2.5)
            folium.GeoJson(
                fc_n, name="شبكة السيول",
                style_function=lambda f, c=c_n, w=w_n:
                    {"color": c, "weight": w, "opacity": 0.85},
                tooltip=folium.GeoJsonTooltip(
                    fields=["رقم الخط", "الاسم", "الطول (م)"],
                    aliases=["رقم الخط:", "الاسم:", "الطول (م):"],
                    localize=True, sticky=False,
                    style="font-family:Tajawal,sans-serif;direction:rtl;font-size:13px;",
                ),
            ).add_to(m)

        # الخطوط المختارة
        if sel:
            sel_rows = df[df.index.isin(sel)]
            fc_s, c_s, w_s = _make_fc(sel_rows, "#e63946", 5)
            folium.GeoJson(
                fc_s, name="الخطوط المختارة",
                style_function=lambda f, c=c_s, w=w_s:
                    {"color": c, "weight": w, "opacity": 1.0},
                tooltip=folium.GeoJsonTooltip(
                    fields=["رقم الخط", "الاسم", "الطول (م)"],
                    aliases=["رقم الخط:", "الاسم:", "الطول (م):"],
                    localize=True, sticky=False,
                    style="font-family:Tajawal,sans-serif;direction:rtl;font-size:13px;",
                ),
            ).add_to(m)

        # fit_bounds على البيانات
        lats, lons = [], []
        for _, row in df.iterrows():
            try:
                b = shape(json.loads(row["_geom"])).bounds
                lats += [b[1], b[3]]; lons += [b[0], b[2]]
            except Exception:
                pass
        if lats:
            m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    if draw:
        Draw(
            draw_options={
                "polyline":     {"shapeOptions": {"color": "#ff6b35", "weight": 4}},
                "polygon":      False,
                "rectangle":    False,
                "circle":       False,
                "marker":       False,
                "circlemarker": False,
            },
            edit_options={"edit": True, "remove": True},
        ).add_to(m)

    MeasureControl(position="topleft", primary_length_unit="meters").add_to(m)
    folium.LayerControl(position="topright").add_to(m)
    return m


# ══════════════════════════════════════════════════════════════
#  SHARED WIDGETS
# ══════════════════════════════════════════════════════════════

def price_guide_html():
    return """
    <div class="price-guide">
        <div class="pg-head">💡 دليل الأسعار الإرشادية (ريال / متر)</div>
        <div class="pg-row">
            <span class="pg-name">أنابيب بقطر 1400 ملم</span>
            <span class="pg-badge">4,004 ﷼/م</span>
        </div>
        <div class="pg-row">
            <span class="pg-name">قناة صندوقية (1.8 × 1.4) م</span>
            <span class="pg-badge">9,336 ﷼/م</span>
        </div>
        <div class="pg-row">
            <span class="pg-name">قناة مفتوحة (12 × 1.5) م</span>
            <span class="pg-badge">13,052 ﷼/م</span>
        </div>
        <div class="pg-note">⚠️ الأسعار تقريبية للإرشاد — تختلف حسب الموقع والمواصفات</div>
    </div>"""


def quick_price_buttons(prefix: str):
    """أزرار تعبئة سريعة — تحفظ القيمة في session_state"""
    st.markdown(
        "<div style='direction:rtl;font-size:.88rem;font-weight:700;"
        "color:#374151;margin:8px 0 4px'>⚡ تعبئة سريعة:</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    for i, (col, (name, price)) in enumerate(zip(cols, PRICES)):
        short = ["أنابيب", "صندوقية", "مفتوحة"][i]
        if col.button(f"{short}\n{price:,.0f} ﷼", key=f"{prefix}_q{i}", help=name):
            st.session_state[f"{prefix}_price"] = price


def price_input(prefix: str, key: str) -> float:
    default = float(st.session_state.get(f"{prefix}_price", 100.0))
    return st.number_input(
        "💲 السعر لكل متر (ريال سعودي)",
        min_value=0.0, value=default, step=10.0,
        format="%.2f", key=key,
    )


# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sec-title">📁 رفع الملف</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="direction:rtl;font-size:.88rem;color:#374151;margin-bottom:8px">'
        'الصيغ المدعومة:<br>'
        '<span class="badge geo">GeoJSON</span>'
        '<span class="badge shp">ZIP — Shapefile</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "اختر الملف",
        type=["geojson", "json", "zip"],
        help="GeoJSON مباشرة · أو ZIP يحتوي على .shp .dbf .shx .prj",
    )

    st.markdown("---")
    st.markdown("""
    <div class="info-box">
    <b>💡 كيفية الاستخدام:</b><br>
    ① ارفع ملف GeoJSON أو ZIP<br>
    ② استعرض الخريطة التفاعلية<br>
    ③ اختر خطاً أو أكثر لحساب التكلفة<br>
    ④ أو ارسم خطاً جديداً على الخريطة
    </div>""", unsafe_allow_html=True)

    st.markdown(price_guide_html(), unsafe_allow_html=True)

    st.markdown("""
    <div class="signature">
        <span class="sig-icon">👷</span>
        <div class="sig-by">Developed by</div>
        <div class="sig-name">Eng: Ahmed Adam</div>
        <div class="sig-sub">🌊 نظام تحليل شبكات السيول</div>
        <hr class="sig-hr">
        <div class="sig-copy">GIS Flood Network System · v5.0<br>© 2025 — جميع الحقوق محفوظة</div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
    <h1>🌊 نظام تحليل شبكات السيول</h1>
    <p>تحليل شبكات تصريف السيول · حساب الأطوال · تقدير التكاليف</p>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  WELCOME SCREEN  (no file uploaded)
# ══════════════════════════════════════════════════════════════
if uploaded is None:
    col_info, col_map = st.columns([1, 2])

    with col_info:
        st.markdown("""
        <div style="background:white;border-radius:16px;padding:32px 22px;
                    box-shadow:0 2px 14px rgba(0,0,0,.08);direction:rtl">
            <div style="font-size:3rem;text-align:center">🗂️</div>
            <h3 style="color:#1a3a5c;text-align:center;margin:10px 0 8px;font-size:1.15rem">
                ابدأ برفع الملف
            </h3>
            <p style="color:#6b7280;font-size:.9rem;line-height:2">
                ارفع ملف <b>GeoJSON</b> مباشرةً<br>
                أو ملف <b>ZIP</b> يحتوي على Shapefile<br>
                من الشريط الجانبي لبدء التحليل
            </p>
            <div style="margin-top:14px;background:#f8fafc;border-radius:10px;
                        padding:13px;font-size:.85rem;color:#64748b;
                        border-right:3px solid #0d6efd">
                📌 <b>تحويل SHP إلى ZIP:</b><br>
                ① اختر مجلد الـ SHP كاملاً<br>
                ② كليك يمين ← ضغط / Compress<br>
                ③ ارفع ملف الـ ZIP الناتج
            </div>
        </div>""", unsafe_allow_html=True)

    with col_map:
        st_folium(
            build_map(zoom=ZOOM_DEFAULT),
            width="100%", height=450,
            returned_objects=[], key="map_welcome",
        )

# ══════════════════════════════════════════════════════════════
#  MAIN APP  (file uploaded)
# ══════════════════════════════════════════════════════════════
else:
    raw = uploaded.read()
    with st.spinner("⏳ جاري قراءة البيانات وحساب الأطوال..."):
        df, features = load_file(raw, uploaded.name)

    if df is not None:
        total_m  = float(df["length_m"].sum())
        n_lines  = len(df)
        avg_m    = float(df["length_m"].mean())
        max_m    = float(df["length_m"].max())

        # ── Stats Cards ────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="card"><div class="lbl">📏 عدد الخطوط</div>'
                    f'<div class="val">{n_lines:,}</div><div class="unt">خط</div></div>',
                    unsafe_allow_html=True)
        c2.markdown(f'<div class="card green"><div class="lbl">📐 الطول الإجمالي</div>'
                    f'<div class="val">{total_m/1000:.3f}</div>'
                    f'<div class="unt">كيلومتر ({total_m:,.0f} م)</div></div>',
                    unsafe_allow_html=True)
        c3.markdown(f'<div class="card"><div class="lbl">📊 متوسط الطول</div>'
                    f'<div class="val">{avg_m:.1f}</div><div class="unt">متر</div></div>',
                    unsafe_allow_html=True)
        c4.markdown(f'<div class="card orange"><div class="lbl">🔝 أطول خط</div>'
                    f'<div class="val">{max_m:,.1f}</div><div class="unt">متر</div></div>',
                    unsafe_allow_html=True)

        # ── Tabs ───────────────────────────────────────────
        tab1, tab2, tab3, tab4 = st.tabs([
            "🗺️ الخريطة التفاعلية",
            "💰 حساب تكلفة خطوط موجودة",
            "✏️ رسم خط جديد",
            "📊 جدول البيانات",
        ])

        # ════════════════════════════════════════════════════
        #  TAB 1 — Interactive Map (cached)
        # ════════════════════════════════════════════════════
        with tab1:
            st.markdown('<div class="sec-title">🗺️ خريطة شبكة السيول</div>',
                        unsafe_allow_html=True)
            st.markdown("""<div class="info-box">
            💡 مرّر الماوس على أي خط لعرض رقمه واسمه وطوله<br>
            غيّر نوع الخريطة من الزاوية العلوية اليمنى<br>
            استخدم أداة القياس 📐 في أعلى اليسار لقياس المسافات
            </div>""", unsafe_allow_html=True)
            with st.spinner("🗺️ جاري تحميل الخريطة..."):
                m1 = build_map(df)  # بدون draw
            st_folium(m1, width="100%", height=550,
                      returned_objects=[], key="map_t1")

        # ════════════════════════════════════════════════════
        #  TAB 2 — Cost Calculation (existing lines)
        # ════════════════════════════════════════════════════
        with tab2:
            st.markdown('<div class="sec-title">💰 حساب تكلفة خطوط من الشبكة</div>',
                        unsafe_allow_html=True)

            col_ctrl, col_map2 = st.columns([2, 3])

            with col_ctrl:
                st.markdown("""<div class="info-box">
                📋 <b>خطوات الحساب:</b><br>
                ① اختر خطاً أو أكثر من القائمة أدناه<br>
                ② تظهر الخطوط المختارة باللون الأحمر على الخريطة<br>
                ③ اختر نوع التصريف أو أدخل السعر يدوياً<br>
                ④ اضغط "احسب التكلفة الإجمالية"
                </div>""", unsafe_allow_html=True)

                st.markdown(price_guide_html(), unsafe_allow_html=True)
                quick_price_buttons("t2")

                st.markdown("---")
                st.markdown(
                    '<div style="direction:rtl;font-weight:700;color:#1a3a5c;'
                    'font-size:.95rem;margin-bottom:4px">📋 اختر الخطوط:</div>',
                    unsafe_allow_html=True,
                )

                lc = _label_col(df)
                opts = (
                    [f"{i} | {str(r[lc])[:30]}  ({r['length_m']:,.1f} م)"
                     for i, r in df.iterrows()]
                    if lc else
                    [f"خط {i}  ({r['length_m']:,.1f} م)"
                     for i, r in df.iterrows()]
                )

                chosen_labels = st.multiselect(
                    "يمكن اختيار خط واحد أو أكثر",
                    options=opts,
                    placeholder="اكتب للبحث أو انقر للاختيار...",
                    key="ms_t2",
                )

                # استخراج الأرقام من التسميات
                chosen_idx = []
                for lbl in chosen_labels:
                    try:
                        part = lbl.split("|")[0].strip() if "|" in lbl \
                               else lbl.replace("خط ", "").split(" ")[0]
                        chosen_idx.append(int(part.strip()))
                    except Exception:
                        pass

                if chosen_idx:
                    total_sel = float(df.loc[chosen_idx, "length_m"].sum())
                    st.markdown(
                        f'<div class="card green" style="margin-top:10px">'
                        f'<div class="lbl">✅ عدد الخطوط المختارة</div>'
                        f'<div class="val">{len(chosen_idx)}</div>'
                        f'<div class="unt">خط</div></div>'
                        f'<div class="card green">'
                        f'<div class="lbl">📐 مجموع الأطوال المختارة</div>'
                        f'<div class="val">{total_sel:,.1f}</div>'
                        f'<div class="unt">متر = {total_sel/1000:.3f} كم</div></div>',
                        unsafe_allow_html=True,
                    )
                    with st.expander("📋 تفاصيل الخطوط المختارة"):
                        for i in chosen_idx:
                            r   = df.loc[i]
                            lbl = str(r[lc]) if lc else f"خط {i}"
                            st.markdown(f"• **{lbl}** — {r['length_m']:,.1f} م")
                else:
                    total_sel = 0.0
                    st.markdown(
                        '<div style="text-align:center;padding:20px;color:#94a3b8;direction:rtl">'
                        '<div style="font-size:2rem">☝️</div>'
                        '<p style="margin:5px 0;font-size:.9rem">اختر خطاً أو أكثر من القائمة</p>'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                p2 = price_input("t2", "price_t2_inp")

                if st.button("🧮 احسب التكلفة الإجمالية", key="calc_t2"):
                    if total_sel > 0:
                        cost = total_sel * p2
                        detail = ""
                        if len(chosen_idx) > 1:
                            hr = '<hr style="border:0;border-top:1px solid #a5d6a7;margin:8px 0">'
                            rows_html = "".join(
                                f"• {str(df.loc[i, lc]) if lc else f'خط {i}'}: "
                                f"{df.loc[i,'length_m']:,.1f} م × {p2:,.2f}"
                                f" = {df.loc[i,'length_m']*p2:,.2f} ﷼<br>"
                                for i in chosen_idx
                            )
                            detail = hr + rows_html
                        st.markdown(
                            f'<div class="result">'
                            f'<div class="r-title">💵 التكلفة الإجمالية</div>'
                            f'<div class="r-value">{cost:,.2f} ﷼</div>'
                            f'<div class="r-sub">{total_sel:,.1f} م × {p2:,.2f} ﷼/م'
                            f' &nbsp;|&nbsp; {len(chosen_idx)} خط{detail}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.warning("⚠️ اختر خطاً واحداً على الأقل")

            with col_map2:
                with st.spinner("🗺️ جاري تحميل الخريطة..."):
                    m2 = build_map(df, selected=chosen_idx)  # بدون draw
                st_folium(m2, width="100%", height=570,
                          returned_objects=[], key="map_t2")

        # ════════════════════════════════════════════════════
        #  TAB 3 — Draw New Line (with draw)
        # ════════════════════════════════════════════════════
        with tab3:
            st.markdown('<div class="sec-title">✏️ ارسم خطاً جديداً على الخريطة</div>',
                        unsafe_allow_html=True)

            col_dm, col_dc = st.columns([3, 2])

            with col_dm:
                st.markdown("""<div class="info-box">
                📌 <b>خطوات الرسم:</b><br>
                ① انقر أيقونة <b>🖊</b> في أعلى يسار الخريطة<br>
                ② انقر على الخريطة نقطةً نقطةً لرسم المسار<br>
                ③ انقر <b>مرتين</b> على آخر نقطة لإنهاء الرسم<br>
                ④ يظهر الطول تلقائياً في اللوحة على اليسار<br>
                ⑤ أدخل السعر أو اختر نوع التصريف ثم احسب
                </div>""", unsafe_allow_html=True)
                with st.spinner("🗺️ جاري تحميل الخريطة..."):
                    m3 = build_map(df, draw=True)
                map_data = st_folium(
                    m3, width="100%", height=530,
                    returned_objects=["all_drawings"], key="map_t3",
                )

            with col_dc:
                st.markdown(price_guide_html(), unsafe_allow_html=True)
                quick_price_buttons("t3")
                st.markdown("---")

                drawings = (map_data or {}).get("all_drawings") or []
                drawn = [
                    d for d in drawings
                    if d.get("geometry", {}).get("type") == "LineString"
                    and len(d["geometry"].get("coordinates", [])) >= 2
                ]

                if drawn:
                    lengths     = [length_from_coords(d["geometry"]["coordinates"])
                                   for d in drawn]
                    drawn_total = sum(lengths)
                    st.markdown(
                        f'<div class="card green">'
                        f'<div class="lbl">✏️ عدد الخطوط المرسومة</div>'
                        f'<div class="val">{len(drawn)}</div>'
                        f'<div class="unt">خط</div></div>'
                        f'<div class="card green">'
                        f'<div class="lbl">📐 مجموع الأطوال المرسومة</div>'
                        f'<div class="val">{drawn_total:,.1f}</div>'
                        f'<div class="unt">متر = {drawn_total/1000:.3f} كم</div></div>',
                        unsafe_allow_html=True,
                    )
                    if len(lengths) > 1:
                        with st.expander("📋 تفاصيل الخطوط المرسومة"):
                            for i, ll in enumerate(lengths, 1):
                                st.markdown(f"• خط {i}: **{ll:,.1f} م**")
                else:
                    drawn_total = 0.0
                    st.markdown(
                        '<div style="text-align:center;padding:30px;color:#94a3b8;direction:rtl">'
                        '<div style="font-size:2.5rem">✏️</div>'
                        '<p style="margin:6px 0;font-size:.9rem">'
                        'ارسم خطاً على الخريطة<br>لظهور طوله هنا</p></div>',
                        unsafe_allow_html=True,
                    )

                p3 = price_input("t3", "price_t3_inp")

                if st.button("🧮 احسب تكلفة الخطوط المرسومة", key="calc_t3"):
                    if drawn_total > 0:
                        st.markdown(
                            f'<div class="result">'
                            f'<div class="r-title">💵 التكلفة الإجمالية</div>'
                            f'<div class="r-value">{drawn_total * p3:,.2f} ﷼</div>'
                            f'<div class="r-sub">'
                            f'{drawn_total:,.1f} م × {p3:,.2f} ﷼/م<br>'
                            f'({len(drawn)} خط مرسوم)</div></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.warning("⚠️ ارسم خطاً على الخريطة أولاً")

        # ════════════════════════════════════════════════════
        #  TAB 4 — Data Table
        # ════════════════════════════════════════════════════
        with tab4:
            st.markdown('<div class="sec-title">📊 جدول بيانات الشبكة الكاملة</div>',
                        unsafe_allow_html=True)
            st.markdown(
                f'<div class="card green" style="display:inline-block;min-width:280px">'
                f'<div class="lbl">📐 مجموع الأطوال الكلي</div>'
                f'<div class="val">{total_m:,.1f} م</div>'
                f'<div class="unt">= {total_m/1000:.3f} كيلومتر</div></div>',
                unsafe_allow_html=True,
            )

            show_cols = [c for c in df.columns if c not in ("_geom",)]
            df_show   = df[show_cols].copy()
            df_show["length_m"] = df_show["length_m"].round(2)
            st.dataframe(df_show, use_container_width=True, height=440)

            st.download_button(
                "⬇️ تحميل الجدول CSV",
                data=df_show.to_csv(index=True).encode("utf-8-sig"),
                file_name="flood_network.csv",
                mime="text/csv",
                key="dl_csv",
            )
