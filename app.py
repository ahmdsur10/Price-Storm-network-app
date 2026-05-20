import streamlit as st
import folium
from folium.plugins import Draw, MeasureControl
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import json
import tempfile
import zipfile
import time
from shapely.geometry import shape

st.set_page_config(page_title="نظام تحليل شبكات السيول", layout="wide")

# ─── التصميم (نفس السابق، مختصر قليلاً للوضوح) ──────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; }
.app-header {
    background: linear-gradient(135deg, #0d1b2a, #1a3a5c, #0d6efd);
    border-radius: 18px; padding: 28px 40px; margin-bottom: 24px; text-align: center; color: white;
}
.card {
    background: white; border-radius: 14px; padding: 16px 20px; margin-bottom: 12px;
    border-right: 5px solid #0d6efd; box-shadow: 0 2px 12px rgba(0,0,0,.07);
}
.card.green { border-right-color: #43a047; }
.card .val { font-size: 1.6rem; font-weight: 800; color: #1a3a5c; }
.info-box { background: #e3f2fd; border-radius: 10px; padding: 14px; margin: 10px 0; }
.price-guide { background: #fff8e1; border-radius: 12px; padding: 14px; margin: 10px 0; }
.sec-title { font-size: 1.1rem; font-weight: 700; border-bottom: 2px solid #e2e8f0; margin-bottom: 14px; }
section[data-testid="stSidebar"] { width: 360px !important; }
div[data-testid="stButton"] button { width: 100%; background: linear-gradient(135deg,#0d6efd,#0077b6); color: white; border: none; border-radius: 10px; padding: 10px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

RIYADH = [24.7136, 46.6753]
PRICES = {"أنابيب 1400 مم": 4004, "قناة صندوقية": 9336, "قناة مفتوحة": 13052}

# ─── دوال حساب الأطوال (سريعة) ────────────────────────────────────────
def haversine_length(coords):
    if len(coords) < 2: return 0.0
    R = 6371000
    lon = np.radians([c[0] for c in coords])
    lat = np.radians([c[1] for c in coords])
    dlon = np.diff(lon)
    dlat = np.diff(lat)
    a = np.sin(dlat/2)**2 + np.cos(lat[:-1]) * np.cos(lat[1:]) * np.sin(dlon/2)**2
    return float(R * 2 * np.sum(np.arctan2(np.sqrt(a), np.sqrt(1-a))))

def length_from_geojson(geom):
    try:
        g = shape(geom)
        if g.geom_type == "LineString":
            return round(haversine_length(list(g.coords)), 2)
        if g.geom_type == "MultiLineString":
            return round(sum(haversine_length(list(p.coords)) for p in g.geoms), 2)
    except:
        return 0.0

# ─── رفع الملف (بدون geopandas) ───────────────────────────────────────
@st.cache_data
def load_geojson(data):
    fc = json.loads(data)
    features = [f for f in fc.get("features",[]) if f.get("geometry") and f["geometry"]["type"] in ("LineString","MultiLineString")]
    rows = []
    for i, f in enumerate(features):
        rows.append({
            "index": i,
            "length_m": length_from_geojson(f["geometry"]),
            "_geom": json.dumps(f["geometry"]),
            **{k: (v if not isinstance(v,bytes) else v.decode()) for k,v in f.get("properties",{}).items()}
        })
    return pd.DataFrame(rows).set_index("index")

@st.cache_data
def load_shapefile_zip(data):
    import shapefile
    with tempfile.TemporaryDirectory() as tmp:
        zp = os.path.join(tmp, "up.zip")
        with open(zp, "wb") as f: f.write(data)
        with zipfile.ZipFile(zp) as z: z.extractall(tmp)
        shp = next((os.path.join(r,fn) for r,_,fs in os.walk(tmp) for fn in fs if fn.endswith(".shp")), None)
        if not shp: return None
        sf = shapefile.Reader(shp, encoding="utf-8")
        features = []
        fields = [f[0] for f in sf.fields[1:]]
        for sr in sf.shapeRecords():
            geom = sr.shape.__geo_interface__
            props = {k: (v.decode() if isinstance(v,bytes) else v) for k,v in zip(fields, sr.record)}
            features.append({"type":"Feature","geometry":geom,"properties":props})
        return load_geojson(json.dumps({"type":"FeatureCollection","features":features}).encode())
    return None

def load_file(data, name):
    name = name.lower()
    if name.endswith((".geojson", ".json")):
        return load_geojson(data.decode())
    if name.endswith(".zip"):
        return load_shapefile_zip(data)
    return None

# ─── دوال بناء الخريطة (دون caching معقد) ─────────────────────────────
def build_map(df, selected_indices=None, enable_draw=False, zoom_start=18):
    m = folium.Map(location=RIYADH, zoom_start=zoom_start, tiles="OpenStreetMap", control_scale=True)
    if df is not None and len(df):
        selected = set(selected_indices or [])
        for idx, row in df.iterrows():
            color = "#e63946" if idx in selected else "#0077b6"
            weight = 5 if idx in selected else 2.5
            popup_text = f"رقم الخط: {idx}<br>الطول: {row['length_m']:.1f} م"
            geojson_data = json.loads(row["_geom"])
            folium.GeoJson(
                geojson_data,
                style_function=lambda x, c=color, w=weight: {"color": c, "weight": w, "opacity": 0.8},
                popup=folium.Popup(popup_text, max_width=200),
            ).add_to(m)
        # ضبط الإطار على البيانات
        try:
            bounds = []
            for _, row in df.iterrows():
                b = shape(json.loads(row["_geom"])).bounds
                bounds.append([b[1], b[0]]); bounds.append([b[3], b[2]])
            if bounds:
                m.fit_bounds(bounds)
        except:
            pass
    if enable_draw:
        Draw(draw_options={"polyline": {"shapeOptions": {"color": "#ff6b35", "weight": 4}}, "polygon": False, "rectangle": False, "circle": False, "marker": False}).add_to(m)
        MeasureControl(position="topleft", primary_length_unit="meters").add_to(m)
    return m

# ─── الشريط الجانبي ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📁 رفع الملف")
    uploaded = st.file_uploader("اختر GeoJSON أو ZIP (Shapefile)", type=["geojson","json","zip"])
    st.markdown("---")
    st.markdown('<div class="info-box">💡 الأسعار الإرشادية:<br>أنابيب 1400 مم: 4,004 ريال/م<br>قناة صندوقية: 9,336 ريال/م<br>قناة مفتوحة: 13,052 ريال/م</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; margin-top:20px;"><b>Eng: Ahmed Adam</b><br>نظام تحليل شبكات السيول</div>', unsafe_allow_html=True)

# ─── رأس الصفحة ──────────────────────────────────────────────────────
st.markdown('<div class="app-header"><h1>🌊 نظام تحليل شبكات السيول</h1><p>تحليل شبكات تصريف السيول · حساب الأطوال · تقدير التكاليف</p></div>', unsafe_allow_html=True)

if uploaded is None:
    st.info("📂 يرجى رفع ملف GeoJSON أو ZIP من القائمة الجانبية")
    m = folium.Map(location=RIYADH, zoom_start=11)
    st_folium(m, width="100%", height=500, key="welcome")
    st.stop()

# ─── تحميل البيانات ───────────────────────────────────────────────────
with st.spinner("جاري تحميل البيانات وحساب الأطوال..."):
    df = load_file(uploaded.read(), uploaded.name)
    time.sleep(0.5)  # تأخير صغير لضمان استقرار Streamlit
if df is None or df.empty:
    st.error("الملف لا يحتوي على خطوط صالحة")
    st.stop()

total_m = df["length_m"].sum()
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="card"><div class="val">{len(df)}</div><div>عدد الخطوط</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card green"><div class="val">{total_m/1000:.2f} كم</div><div>الطول الإجمالي</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="card"><div class="val">{df["length_m"].mean():.0f} م</div><div>متوسط الطول</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="card"><div class="val">{df["length_m"].max():.0f} م</div><div>أطول خط</div></div>', unsafe_allow_html=True)

# ─── التبويبات ────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ الخريطة التفاعلية", "💰 حساب التكلفة (شبكة)", "✏️ رسم خط جديد", "📊 جدول البيانات"])

# تبويب 1: خريطة بدون رسم
with tab1:
    st.markdown('<div class="sec-title">استعراض شبكة السيول</div>', unsafe_allow_html=True)
    m1 = build_map(df, zoom_start=18)
    st_folium(m1, width="100%", height=550, key="map_tab1")

# تبويب 2: اختيار خطوط وحساب التكلفة
with tab2:
    st.markdown('<div class="sec-title">اختر خطوطاً لحساب التكلفة</div>', unsafe_allow_html=True)
    col_left, col_right = st.columns([2,3])
    with col_left:
        indices = df.index.tolist()
        selected = st.multiselect("اختر رقم/أرقام الخطوط", indices, format_func=lambda x: f"خط {x}  ({df.loc[x,'length_m']:.1f} م)")
        if selected:
            total_len = df.loc[selected, "length_m"].sum()
            st.markdown(f'<div class="card green"><div class="val">{total_len:,.1f} م</div><div>مجموع الأطوال المختارة</div></div>', unsafe_allow_html=True)
        # إدخال السعر
        price_source = st.radio("السعر لكل متر", ["اختر من القائمة", "إدخال يدوي"])
        if price_source == "اختر من القائمة":
            price_type = st.selectbox("نوع التصريف", list(PRICES.keys()))
            price = PRICES[price_type]
        else:
            price = st.number_input("السعر (ريال/م)", min_value=0.0, value=100.0, step=10.0)
        if st.button("احسب التكلفة", key="calc_t2") and selected:
            cost = total_len * price
            st.markdown(f'<div class="card" style="background:#e8f5e9; border-right-color:#43a047;"><div class="val">{cost:,.2f} ﷼</div><div>التكلفة الإجمالية</div></div>', unsafe_allow_html=True)
    with col_right:
        m2 = build_map(df, selected_indices=selected)
        st_folium(m2, width="100%", height=550, key="map_tab2")

# تبويب 3: رسم خط جديد
with tab3:
    st.markdown('<div class="sec-title">ارسم خطاً على الخريطة</div>', unsafe_allow_html=True)
    col_draw, col_info = st.columns([3,2])
    with col_draw:
        m3 = build_map(df, enable_draw=True)
        output = st_folium(m3, width="100%", height=550, returned_objects=["all_drawings"], key="map_tab3")
    with col_info:
        st.markdown("### تعليمات الرسم")
        st.markdown("1. اضغط أيقونة 🖊 أعلى اليسار\n2. انقر على الخريطة لتحديد نقاط المسار\n3. انقر مرتين لإنهاء الرسم")
        drawings = output.get("all_drawings", []) if output else []
        lines = [d for d in drawings if d.get("geometry", {}).get("type") == "LineString" and len(d["geometry"]["coordinates"]) >= 2]
        if lines:
            total_len_draw = sum(haversine_length(d["geometry"]["coordinates"]) for d in lines)
            st.metric("الطول المرسوم", f"{total_len_draw:.1f} متر")
            price_source2 = st.radio("السعر لكل متر", ["اختر من القائمة", "إدخال يدوي"], key="price_opt3")
            if price_source2 == "اختر من القائمة":
                pt = st.selectbox("نوع التصريف", list(PRICES.keys()), key="pt3")
                price2 = PRICES[pt]
            else:
                price2 = st.number_input("السعر (ريال/م)", min_value=0.0, value=100.0, step=10.0, key="price3")
            if st.button("احسب التكلفة", key="calc_t3"):
                st.markdown(f'<div class="card" style="background:#e8f5e9;"><div class="val">{total_len_draw * price2:,.2f} ﷼</div><div>تكلفة الخط المرسوم</div></div>', unsafe_allow_html=True)
        else:
            st.info("ارسم خطاً على الخريطة ليظهر طوله هنا")

# تبويب 4: جدول البيانات
with tab4:
    st.markdown('<div class="sec-title">جميع الخطوط</div>', unsafe_allow_html=True)
    df_display = df[["length_m"] + [c for c in df.columns if c not in ["_geom","length_m"]]].copy()
    df_display.columns = ["الطول (م)"] + [c for c in df_display.columns if c != "الطول (م)"]
    st.dataframe(df_display, use_container_width=True, height=400)
    csv = df_display.to_csv(index=True).encode("utf-8-sig")
    st.download_button("تحميل CSV", csv, "flood_network.csv", "text/csv")
