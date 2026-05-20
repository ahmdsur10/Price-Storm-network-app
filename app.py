"""
نظام تحليل شبكات السيول
GIS Flood Network Analysis System
Developed by: Eng. Ahmed Adam
v6.0 — Ultra Fast
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
#  STYLES (نفس التصميم الأصلي)
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Tajawal', sans-serif !important; direction: rtl; }
.main { background: #f0f4f8; }
.app-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 40%, #0d6efd 80%, #00b4d8 100%);
    border-radius: 18px; padding: 28px 40px; margin-bottom: 24px; text-align: center;
    color: white; box-shadow: 0 8px 32px rgba(13,110,253,.3);
}
.app-header h1 { font-size: 2.2rem; font-weight: 800; margin: 0; }
.app-header p  { font-size: 1rem; opacity: .85; margin: 8px 0 0; }
.card {
    background: white; border-radius: 14px; padding: 16px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,.07); border-right: 5px solid #0d6efd;
    margin-bottom: 12px; direction: rtl;
}
.card.green  { border-right-color: #43a047; }
.card.orange { border-right-color: #fb8c00; }
.card .lbl { color: #6b7280; font-size: .84rem; font-weight: 500; }
.card .val { color: #1a3a5c; font-size: 1.6rem; font-weight: 800; margin-top: 2px; }
.card .unt { color: #0d6efd; font-size: .82rem; font-weight: 600; }
.card.green  .val { color: #1b5e20; } .card.green  .unt { color: #43a047; }
.card.orange .val { color: #e65100; } .card.orange .unt { color: #fb8c00; }
.result {
    background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
    border: 2px solid #43a047; border-radius: 14px; padding: 20px 26px;
    text-align: center; margin-top: 14px; direction: rtl;
}
.result .r-title { font-size: .95rem; color: #2e7d32; font-weight: 600; }
.result .r-value { font-size: 2.2rem; font-weight: 800; color: #1b5e20; }
.result .r-sub   { font-size: .86rem; color: #388e3c; margin-top: 6px; }
.info-box {
    background: #e3f2fd; border: 1px solid #90caf9; border-radius: 10px;
    padding: 14px 18px; font-size: .92rem; color: #1565c0; direction: rtl;
}
.price-guide {
    background: #fff8e1; border: 1px solid #ffe082; border-radius: 12px;
    padding: 14px 18px; margin: 10px 0; direction: rtl;
}
.price-guide .pg-head { font-size: .97rem; font-weight: 800; color: #e65100; margin-bottom: 10px; border-bottom: 1px dashed #ffcc80; }
.price-guide .pg-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #fff3cd; }
.price-guide .pg-name  { color: #5d4037; font-weight: 600; }
.price-guide .pg-badge { background: #e65100; color: white; border-radius: 8px; padding: 2px 11px; font-size: .82rem; font-weight: 700; }
.sec-title { font-size: 1.1rem; font-weight: 700; color: #1a3a5c; border-bottom: 2px solid #e2e8f0; margin-bottom: 14px; }
section[data-testid="stSidebar"] { width: 360px !important; min-width: 360px !important; }
.badge { display: inline-block; border-radius: 20px; padding: 2px 12px; font-size: .84rem; font-weight: 700; margin-left: 4px; }
.badge.geo { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
.badge.shp { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
div[data-testid="stButton"] > button {
    width: 100%; background: linear-gradient(135deg, #0d6efd, #0077b6);
    color: white; border: none; border-radius: 10px; padding: 11px 18px;
    font-family: 'Tajawal', sans-serif; font-weight: 700;
}
.signature {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 50%, #0d6efd 100%);
    border-radius: 14px; padding: 18px 16px; margin-top: 18px; text-align: center;
}
.signature .sig-name { font-size: 1.25rem; font-weight: 800; color: #fff; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════
RIYADH = [24.7136, 46.6753]
ZOOM_DEFAULT = 11
ZOOM_DATA = 18
PRICES = [
    ("أنابيب بقطر 1400 ملم", 4004.0),
    ("قناة صندوقية (1.8 × 1.4) م", 9336.0),
    ("قناة مفتوحة (12 × 1.5) م", 13052.0),
]

# ══════════════════════════════════════════════════════════════
#  GEOMETRY HELPERS (سريعة جداً)
# ══════════════════════════════════════════════════════════════
def _haversine_arr(coords: np.ndarray) -> float:
    if len(coords) < 2:
        return 0.0
    R = 6_371_000.0
    lon = np.radians(coords[:, 0])
    lat = np.radians(coords[:, 1])
    dph = np.diff(lat)
    dlm = np.diff(lon)
    a = (np.sin(dph/2)**2 + np.cos(lat[:-1]) * np.cos(lat[1:]) * np.sin(dlm/2)**2)
    return float(R * 2 * np.sum(np.arctan2(np.sqrt(np.clip(a,0,1)), np.sqrt(np.clip(1-a,0,1)))))

def length_from_geojson(geom: dict) -> float:
    try:
        g = shape(geom)
        if g.geom_type == "LineString":
            return round(_haversine_arr(np.array(g.coords)), 2)
        if g.geom_type == "MultiLineString":
            return round(sum(_haversine_arr(np.array(p.coords)) for p in g.geoms), 2)
    except:
        pass
    return 0.0

def length_from_coords(coords: list) -> float:
    return round(_haversine_arr(np.array(coords, dtype=float)), 2)

# ══════════════════════════════════════════════════════════════
#  FILE LOADING (مُحسّن وسريع)
# ══════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_geojson(data: bytes):
    try:
        fc = json.loads(data.decode("utf-8"))
        features = [f for f in fc.get("features", []) if f.get("geometry") and f["geometry"].get("type") in ("LineString","MultiLineString")]
        if not features:
            return None
        rows = []
        for i, feat in enumerate(features):
            length = length_from_geojson(feat["geometry"])
            rows.append({
                "رقم": i,
                "length_m": length,
                "_geom": json.dumps(feat["geometry"]),
                **{k: (v.decode("utf-8","ignore") if isinstance(v,bytes) else v) for k,v in feat.get("properties",{}).items()}
            })
        df = pd.DataFrame(rows).set_index("رقم")
        return df
    except Exception as e:
        st.error(f"خطأ في GeoJSON: {e}")
        return None

@st.cache_data(show_spinner=False)
def load_shapefile_zip(data: bytes):
    try:
        import shapefile
    except ImportError:
        st.error("مكتبة pyshp غير مثبتة")
        return None
    with tempfile.TemporaryDirectory() as tmp:
        zp = os.path.join(tmp, "up.zip")
        with open(zp, "wb") as f:
            f.write(data)
        with zipfile.ZipFile(zp) as z:
            z.extractall(tmp)
        shps = [os.path.join(r,fn) for r,_,fs in os.walk(tmp) for fn in fs if fn.endswith(".shp")]
        if not shps:
            st.error("لا يوجد ملف .shp")
            return None
        sf = shapefile.Reader(shps[0], encoding="utf-8") if "utf" in str(sf.encoding).lower() else shapefile.Reader(shps[0], encoding="cp1256")
        fields = [f[0] for f in sf.fields[1:]]
        features = []
        for sr in sf.shapeRecords():
            geom = sr.shape.__geo_interface__
            props = {k: (v.decode("utf-8","ignore") if isinstance(v,bytes) else v) for k,v in zip(fields, sr.record)}
            features.append({"type":"Feature","geometry":geom,"properties":props})
        fc = {"type":"FeatureCollection","features":features}
        return load_geojson(json.dumps(fc).encode("utf-8"))
    return None

def load_file(data: bytes, name: str):
    name = name.lower()
    if name.endswith((".geojson", ".json")):
        return load_geojson(data)
    if name.endswith(".zip"):
        return load_shapefile_zip(data)
    st.error("صيغة غير مدعومة")
    return None

# ══════════════════════════════════════════════════════════════
#  MAP BUILDER (مخزّن مؤقتاً لسرعة فائقة)
# ══════════════════════════════════════════════════════════════
def _label_col(df):
    for c in ("name","Name","NAME","id","ID","FID","OBJECTID","label"):
        if c in df.columns:
            return c
    return None

@st.cache_resource(ttl=3600, hash_funcs={pd.DataFrame: lambda df: df["_geom"].sum() if len(df) else 0})
def build_map(df=None, selected=None, draw=False, zoom=None):
    sel = set(selected or [])
    z = zoom if zoom is not None else ZOOM_DATA
    m = folium.Map(location=RIYADH, zoom_start=z, tiles=None, control_scale=True, prefer_canvas=True)
    folium.TileLayer("OpenStreetMap", name="خريطة الشارع", show=True).add_to(m)
    folium.TileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", name="صور جوية", show=False).add_to(m)
    folium.TileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", attr="CartoDB", name="خريطة فاتحة", show=False).add_to(m)
    if df is not None and len(df):
        lc = _label_col(df)
        def _make_fc(rows, color, weight):
            fc = {"type":"FeatureCollection","features":[]}
            for idx, row in rows.iterrows():
                lbl = str(row[lc]) if lc else f"خط {idx}"
                fc["features"].append({
                    "type":"Feature",
                    "geometry": json.loads(row["_geom"]),
                    "properties": {"رقم الخط": str(idx), "الاسم": lbl, "الطول (م)": f"{row['length_m']:,.1f}"}
                })
            return fc, color, weight
        normal = df[~df.index.isin(sel)]
        if len(normal):
            fc_n, c_n, w_n = _make_fc(normal, "#0077b6", 2.5)
            folium.GeoJson(fc_n, name="شبكة السيول", style_function=lambda f, c=c_n, w=w_n: {"color":c,"weight":w,"opacity":0.85},
                tooltip=folium.GeoJsonTooltip(fields=["رقم الخط","الاسم","الطول (م)"], aliases=["رقم الخط:","الاسم:","الطول (م):"], localize=True, sticky=False, style="font-family:Tajawal;direction:rtl;font-size:13px;")).add_to(m)
        if sel:
            sel_rows = df[df.index.isin(sel)]
            fc_s, c_s, w_s = _make_fc(sel_rows, "#e63946", 5)
            folium.GeoJson(fc_s, name="الخطوط المختارة", style_function=lambda f, c=c_s, w=w_s: {"color":c,"weight":w,"opacity":1.0},
                tooltip=folium.GeoJsonTooltip(fields=["رقم الخط","الاسم","الطول (م)"], aliases=["رقم الخط:","الاسم:","الطول (م):"], localize=True, sticky=False, style="font-family:Tajawal;direction:rtl;font-size:13px;")).add_to(m)
        lats, lons = [], []
        for _, row in df.iterrows():
            try:
                b = shape(json.loads(row["_geom"])).bounds
                lats += [b[1], b[3]]; lons += [b[0], b[2]]
            except:
                pass
        if lats:
            m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
    if draw:
        Draw(draw_options={"polyline":{"shapeOptions":{"color":"#ff6b35","weight":4}},"polygon":False,"rectangle":False,"circle":False,"marker":False,"circlemarker":False}, edit_options={"edit":True,"remove":True}).add_to(m)
    MeasureControl(position="topleft", primary_length_unit="meters").add_to(m)
    folium.LayerControl(position="topright").add_to(m)
    return m

# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sec-title">📁 رفع الملف</div>', unsafe_allow_html=True)
    st.markdown('<div style="direction:rtl;margin-bottom:8px">الصيغ المدعومة:<br><span class="badge geo">GeoJSON</span> <span class="badge shp">ZIP — Shapefile</span></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("اختر الملف", type=["geojson","json","zip"], help="GeoJSON أو ZIP يحتوي على SHP")
    st.markdown("---")
    st.markdown('<div class="info-box"><b>💡 كيفية الاستخدام:</b><br>① ارفع ملف<br>② استعرض الخريطة<br>③ اختر خطوطاً لحساب التكلفة<br>④ أو ارسم خطاً جديداً</div>', unsafe_allow_html=True)
    st.markdown('<div class="price-guide"><div class="pg-head">💡 دليل الأسعار (ريال/م)</div><div class="pg-row"><span class="pg-name">أنابيب 1400 ملم</span><span class="pg-badge">4,004</span></div><div class="pg-row"><span class="pg-name">قناة صندوقية 1.8×1.4</span><span class="pg-badge">9,336</span></div><div class="pg-row"><span class="pg-name">قناة مفتوحة 12×1.5</span><span class="pg-badge">13,052</span></div><div class="pg-note">⚠️ أسعار إرشادية</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="signature"><div class="sig-name">👷 Eng: Ahmed Adam</div><div style="font-size:.8rem;color:#ccc">نظام تحليل شبكات السيول v6.0</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="app-header"><h1>🌊 نظام تحليل شبكات السيول</h1><p>تحليل شبكات تصريف السيول · حساب الأطوال · تقدير التكاليف</p></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  WELCOME
# ══════════════════════════════════════════════════════════════
if uploaded is None:
    col_info, col_map = st.columns([1,2])
    with col_info:
        st.markdown('<div style="background:white;border-radius:16px;padding:32px 22px;box-shadow:0 2px 14px rgba(0,0,0,.08);direction:rtl"><div style="font-size:3rem;text-align:center">🗂️</div><h3 style="color:#1a3a5c;text-align:center">ابدأ برفع الملف</h3><p style="color:#6b7280;font-size:.9rem;line-height:2">ارفع ملف <b>GeoJSON</b> أو <b>ZIP</b> من الشريط الجانبي</p><div style="background:#f8fafc;border-radius:10px;padding:13px;border-right:3px solid #0d6efd">📌 تحويل SHP إلى ZIP: ضغط المجلد بالكامل</div></div>', unsafe_allow_html=True)
    with col_map:
        st_folium(build_map(zoom=ZOOM_DEFAULT), width="100%", height=450, returned_objects=[], key="welcome_map")
    st.stop()

# ══════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════
with st.spinner("⏳ جاري تحميل البيانات وحساب الأطوال..."):
    df = load_file(uploaded.read(), uploaded.name)
if df is None or df.empty:
    st.error("فشل تحميل الملف أو لا يحتوي على خطوط")
    st.stop()

# إحصائيات سريعة
total_m = df["length_m"].sum()
n_lines = len(df)
avg_m = df["length_m"].mean()
max_m = df["length_m"].max()
c1,c2,c3,c4 = st.columns(4)
c1.markdown(f'<div class="card"><div class="lbl">📏 عدد الخطوط</div><div class="val">{n_lines:,}</div><div class="unt">خط</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card green"><div class="lbl">📐 الطول الإجمالي</div><div class="val">{total_m/1000:.3f}</div><div class="unt">كم ({total_m:,.0f} م)</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="card"><div class="lbl">📊 متوسط الطول</div><div class="val">{avg_m:.1f}</div><div class="unt">متر</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="card orange"><div class="lbl">🔝 أطول خط</div><div class="val">{max_m:,.1f}</div><div class="unt">متر</div></div>', unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ الخريطة التفاعلية", "💰 حساب تكلفة خطوط موجودة", "✏️ رسم خط جديد", "📊 جدول البيانات"])

# TAB 1 – خريطة فقط (بدون رسم، سريعة)
with tab1:
    st.markdown('<div class="sec-title">🗺️ خريطة شبكة السيول</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">💡 مرّر الماوس على أي خط لعرض البيانات | غيّر نوع الخريطة من الزاوية اليمنى</div>', unsafe_allow_html=True)
    with st.spinner("جاري تحميل الخريطة..."):
        m1 = build_map(df)
    st_folium(m1, width="100%", height=550, returned_objects=[], key="map_t1")

# TAB 2 – حساب تكلفة الخطوط المختارة
with tab2:
    st.markdown('<div class="sec-title">💰 حساب تكلفة خطوط من الشبكة</div>', unsafe_allow_html=True)
    col_ctrl, col_map2 = st.columns([2,3])
    with col_ctrl:
        st.markdown('<div class="info-box">📋 اختر خطاً أو أكثر من القائمة، ثم حدد السعر واضغط احسب</div>', unsafe_allow_html=True)
        lc = _label_col(df)
        opts = [f"{i} | {str(df.loc[i, lc])[:30]} ({df.loc[i,'length_m']:.1f} م)" if lc else f"خط {i} ({df.loc[i,'length_m']:.1f} م)" for i in df.index]
        chosen_labels = st.multiselect("اختر الخطوط", options=opts, key="ms_t2")
        chosen_idx = []
        for lbl in chosen_labels:
            try:
                idx = int(lbl.split("|")[0].strip() if "|" in lbl else lbl.split(" ")[1])
                chosen_idx.append(idx)
            except:
                pass
        if chosen_idx:
            total_sel = df.loc[chosen_idx, "length_m"].sum()
            st.markdown(f'<div class="card green"><div class="lbl">✅ عدد الخطوط</div><div class="val">{len(chosen_idx)}</div></div><div class="card green"><div class="lbl">📐 مجموع الأطوال</div><div class="val">{total_sel:,.1f} م</div><div class="unt">= {total_sel/1000:.3f} كم</div></div>', unsafe_allow_html=True)
        else:
            total_sel = 0.0
        # السعر
        price_option = st.radio("السعر لكل متر", ["اختر من القائمة", "إدخال يدوي"], key="price_opt_t2")
        if price_option == "اختر من القائمة":
            price_type = st.selectbox("نوع القطعة", ["أنابيب 1400 مم (4004)", "قناة صندوقية (9336)", "قناة مفتوحة (13052)"])
            price_per_m = {"أنابيب 1400 مم (4004)":4004, "قناة صندوقية (9336)":9336, "قناة مفتوحة (13052)":13052}[price_type]
        else:
            price_per_m = st.number_input("السعر (ريال/م)", min_value=0.0, value=100.0, step=10.0)
        if st.button("🧮 احسب التكلفة الإجمالية", key="calc_t2"):
            if total_sel > 0:
                cost = total_sel * price_per_m
                st.markdown(f'<div class="result"><div class="r-title">💵 التكلفة الإجمالية</div><div class="r-value">{cost:,.2f} ﷼</div><div class="r-sub">{total_sel:,.1f} م × {price_per_m:,.2f} ﷼/م</div></div>', unsafe_allow_html=True)
            else:
                st.warning("اختر خطاً واحداً على الأقل")
    with col_map2:
        with st.spinner("جاري تحميل الخريطة..."):
            m2 = build_map(df, selected=chosen_idx)
        st_folium(m2, width="100%", height=570, returned_objects=[], key="map_t2")

# TAB 3 – رسم خط جديد (مع أداة الرسم)
with tab3:
    st.markdown('<div class="sec-title">✏️ ارسم خطاً جديداً على الخريطة</div>', unsafe_allow_html=True)
    col_draw, col_price = st.columns([3,2])
    with col_draw:
        st.markdown('<div class="info-box">📌 اضغط أيقونة 🖊 في أعلى اليسار، ثم انقر على الخريطة نقطة نقطة، وانقر مرتين لإنهاء الرسم</div>', unsafe_allow_html=True)
        with st.spinner("جاري تحميل خريطة الرسم..."):
            m3 = build_map(df, draw=True)
        map_data = st_folium(m3, width="100%", height=530, returned_objects=["all_drawings"], key="map_t3")
    with col_price:
        st.markdown('<div class="price-guide"><div class="pg-head">💡 الأسعار الإرشادية</div><div class="pg-row"><span class="pg-name">أنابيب 1400 مم</span><span class="pg-badge">4,004</span></div><div class="pg-row"><span class="pg-name">قناة صندوقية</span><span class="pg-badge">9,336</span></div><div class="pg-row"><span class="pg-name">قناة مفتوحة</span><span class="pg-badge">13,052</span></div></div>', unsafe_allow_html=True)
        drawings = (map_data or {}).get("all_drawings") or []
        drawn = [d for d in drawings if d.get("geometry",{}).get("type")=="LineString" and len(d["geometry"].get("coordinates",[]))>=2]
        if drawn:
            lengths = [length_from_coords(d["geometry"]["coordinates"]) for d in drawn]
            drawn_total = sum(lengths)
            st.markdown(f'<div class="card green"><div class="lbl">✏️ عدد الخطوط المرسومة</div><div class="val">{len(drawn)}</div></div><div class="card green"><div class="lbl">📐 مجموع الأطوال</div><div class="val">{drawn_total:,.1f} م</div></div>', unsafe_allow_html=True)
        else:
            drawn_total = 0.0
            st.markdown('<div style="text-align:center;padding:30px;color:#94a3b8">✏️ ارسم خطاً على الخريطة</div>', unsafe_allow_html=True)
        price_opt3 = st.radio("السعر لكل متر", ["اختر من القائمة", "إدخال يدوي"], key="price_opt_t3")
        if price_opt3 == "اختر من القائمة":
            pt = st.selectbox("نوع القطعة", ["أنابيب 1400 مم (4004)", "قناة صندوقية (9336)", "قناة مفتوحة (13052)"], key="pt_t3")
            price3 = {"أنابيب 1400 مم (4004)":4004, "قناة صندوقية (9336)":9336, "قناة مفتوحة (13052)":13052}[pt]
        else:
            price3 = st.number_input("السعر (ريال/م)", min_value=0.0, value=100.0, step=10.0, key="price3")
        if st.button("🧮 احسب تكلفة الخطوط المرسومة", key="calc_t3"):
            if drawn_total > 0:
                st.markdown(f'<div class="result"><div class="r-title">💵 التكلفة الإجمالية</div><div class="r-value">{drawn_total * price3:,.2f} ﷼</div><div class="r-sub">{drawn_total:,.1f} م × {price3:,.2f} ﷼/م</div></div>', unsafe_allow_html=True)
            else:
                st.warning("ارسم خطاً أولاً")

# TAB 4 – جدول البيانات
with tab4:
    st.markdown('<div class="sec-title">📊 جدول بيانات الشبكة الكاملة</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card green" style="display:inline-block"><div class="lbl">📐 مجموع الأطوال الكلي</div><div class="val">{total_m:,.1f} م</div><div class="unt">= {total_m/1000:.3f} كم</div></div>', unsafe_allow_html=True)
    show_cols = [c for c in df.columns if c != "_geom"]
    df_show = df[show_cols].copy()
    df_show["length_m"] = df_show["length_m"].round(2)
    st.dataframe(df_show, use_container_width=True, height=440)
    st.download_button("⬇️ تحميل CSV", data=df_show.to_csv(index=True).encode("utf-8-sig"), file_name="flood_network.csv", mime="text/csv")
