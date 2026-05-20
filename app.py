"""
🌊 نظام تحليل شبكات السيول — النسخة المحسنة الاحترافية
Optimized GIS Flood Network System
Developed by: Eng. Ahmed Adam

✔ سريع جداً
✔ يحافظ على التنسيق الأصلي
✔ يدعم GeoJSON + SHP ZIP
✔ يمنع الانهيار والأخطاء
✔ محسن لـ Streamlit Cloud
"""

# =========================================================
# IMPORTS
# =========================================================

import streamlit as st
import folium

from folium.plugins import Draw, MeasureControl
from streamlit_folium import st_folium

import pandas as pd
import numpy as np

import tempfile
import zipfile
import os

import shapefile
import orjson as json

from shapely.geometry import shape, mapping

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="نظام تحليل شبكات السيول",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Tajawal', sans-serif !important;
    direction: rtl;
}

.main {
    background: #f0f4f8;
}

.app-header {
    background: linear-gradient(135deg,#0d1b2a,#0d6efd);
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 18px;
    text-align: center;
    color: white;
}

.card {
    background: white;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 2px 10px rgba(0,0,0,.08);
    margin-bottom: 10px;
    border-right: 5px solid #0d6efd;
}

.card .lbl {
    color: #64748b;
    font-size: .85rem;
}

.card .val {
    color: #1e293b;
    font-size: 1.7rem;
    font-weight: 800;
}

.result {
    background: linear-gradient(135deg,#e8f5e9,#c8e6c9);
    border-radius: 14px;
    padding: 24px;
    text-align: center;
    border: 2px solid #43a047;
}

.result .r-title {
    font-size: 1rem;
    color: #2e7d32;
}

.result .r-value {
    font-size: 2rem;
    font-weight: 800;
    color: #1b5e20;
}

.sec-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a3a5c;
    margin-bottom: 10px;
}

.info-box {
    background: #e3f2fd;
    padding: 14px;
    border-radius: 10px;
    color: #1565c0;
    margin-bottom: 10px;
}

div[data-testid="stButton"] > button {
    width: 100%;
    border-radius: 10px;
    border: none;
    background: linear-gradient(135deg,#0d6efd,#0077b6);
    color: white;
    font-weight: 700;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# CONSTANTS
# =========================================================

RIYADH = [24.7136, 46.6753]

PRICES = [
    ("أنابيب 1400 ملم", 4004.0),
    ("قناة صندوقية", 9336.0),
    ("قناة مفتوحة", 13052.0),
]

# =========================================================
# GEOMETRY HELPERS
# =========================================================

def simplify_geometry(geom, tolerance=0.00001):

    try:

        g = shape(geom)

        simp = g.simplify(
            tolerance,
            preserve_topology=True
        )

        return mapping(simp)

    except Exception:
        return geom


def haversine(coords):

    if len(coords) < 2:
        return 0

    R = 6371000

    coords = np.array(coords)

    lon = np.radians(coords[:, 0])
    lat = np.radians(coords[:, 1])

    dlon = np.diff(lon)
    dlat = np.diff(lat)

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat[:-1])
        * np.cos(lat[1:])
        * np.sin(dlon / 2) ** 2
    )

    return float(
        R * 2 * np.sum(
            np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        )
    )


def line_length(geom):

    try:

        g = shape(geom)

        if g.geom_type == "LineString":
            return haversine(g.coords)

        if g.geom_type == "MultiLineString":
            return sum(
                haversine(x.coords)
                for x in g.geoms
            )

    except Exception:
        return 0

    return 0

# =========================================================
# DATAFRAME BUILDER
# =========================================================

def _fc_to_df(fc):

    rows = []

    features = fc.get("features", [])

    for i, feat in enumerate(features):

        try:

            geom = feat.get("geometry")

            if geom is None:
                continue

            geom_type = geom.get("type")

            if geom_type not in [
                "LineString",
                "MultiLineString"
            ]:
                continue

            geom = simplify_geometry(geom)

            props = feat.get("properties") or {}

            row = {
                "_idx": i,
                "length_m": round(
                    line_length(geom),
                    2
                ),
                "_geom": json.dumps(geom).decode()
            }

            for k, v in props.items():

                if isinstance(v, bytes):
                    v = v.decode(
                        "utf-8",
                        "ignore"
                    )

                row[str(k)] = v

            rows.append(row)

        except Exception:
            continue

    if len(rows) == 0:

        return pd.DataFrame(
            columns=["length_m", "_geom"]
        )

    df = pd.DataFrame(rows)

    df = df.set_index("_idx")

    return df

# =========================================================
# FILE LOADERS
# =========================================================

@st.cache_data(show_spinner=False)
def load_geojson(data):

    try:

        fc = json.loads(data)

        return _fc_to_df(fc)

    except Exception as e:

        st.error(f"خطأ GeoJSON: {e}")

        return pd.DataFrame(
            columns=["length_m", "_geom"]
        )


@st.cache_data(show_spinner=False)
def load_shapefile_zip(data):

    try:

        with tempfile.TemporaryDirectory() as tmp:

            zp = os.path.join(
                tmp,
                "file.zip"
            )

            with open(zp, "wb") as f:
                f.write(data)

            with zipfile.ZipFile(zp) as z:
                z.extractall(tmp)

            shp_path = None

            for root, _, files in os.walk(tmp):

                for f in files:

                    if f.endswith(".shp"):

                        shp_path = os.path.join(
                            root,
                            f
                        )

            if shp_path is None:

                st.error("لا يوجد SHP")

                return pd.DataFrame(
                    columns=["length_m", "_geom"]
                )

            try:

                sf = shapefile.Reader(
                    shp_path,
                    encoding="utf-8"
                )

            except Exception:

                sf = shapefile.Reader(
                    shp_path,
                    encoding="cp1256"
                )

            fields = [
                f[0]
                for f in sf.fields[1:]
            ]

            features = []

            for sr in sf.shapeRecords():

                try:

                    geom = sr.shape.__geo_interface__

                    props = {
                        k: v
                        for k, v in zip(
                            fields,
                            sr.record
                        )
                    }

                    features.append({
                        "type": "Feature",
                        "geometry": geom,
                        "properties": props
                    })

                except Exception:
                    continue

            fc = {
                "type": "FeatureCollection",
                "features": features
            }

            return _fc_to_df(fc)

    except Exception as e:

        st.error(f"خطأ SHP: {e}")

        return pd.DataFrame(
            columns=["length_m", "_geom"]
        )

# =========================================================
# FILE HANDLER
# =========================================================

def load_file(uploaded):

    uploaded.seek(0)

    data = uploaded.read()

    name = uploaded.name.lower()

    if name.endswith((".geojson", ".json")):
        return load_geojson(data)

    if name.endswith(".zip"):
        return load_shapefile_zip(data)

    return pd.DataFrame(
        columns=["length_m", "_geom"]
    )

# =========================================================
# MAP
# =========================================================

@st.cache_resource(show_spinner=False)
def create_base_map():

    m = folium.Map(
        location=RIYADH,
        zoom_start=12,
        control_scale=True,
        prefer_canvas=True,
        tiles="Cartodb Positron"
    )

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Street"
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite"
    ).add_to(m)

    MeasureControl().add_to(m)

    return m


def build_map(df=None, selected=None, draw=False):

    m = create_base_map()

    selected = set(selected or [])

    if df is not None and len(df) > 0:

        features = []

        for idx, row in df.iterrows():

            try:

                color = (
                    "#e63946"
                    if idx in selected
                    else "#0077b6"
                )

                weight = (
                    5
                    if idx in selected
                    else 2
                )

                features.append({
                    "type": "Feature",
                    "geometry": json.loads(
                        row["_geom"]
                    ),
                    "properties": {
                        "style": {
                            "color": color,
                            "weight": weight,
                            "opacity": 0.8
                        }
                    }
                })

            except Exception:
                continue

        folium.GeoJson(
            {
                "type": "FeatureCollection",
                "features": features
            },
            style_function=lambda x:
                x["properties"]["style"],
            zoom_on_click=False
        ).add_to(m)

    if draw:

        Draw(
            draw_options={
                "polyline": {
                    "shapeOptions": {
                        "color": "#ff6b35",
                        "weight": 4
                    }
                },
                "polygon": False,
                "rectangle": False,
                "circle": False,
                "marker": False,
                "circlemarker": False,
            }
        ).add_to(m)

    folium.LayerControl().add_to(m)

    return m

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="sec-title">📁 رفع الملف</div>',
        unsafe_allow_html=True
    )

    uploaded = st.file_uploader(
        "اختر ملف GeoJSON أو ZIP",
        type=["geojson", "json", "zip"]
    )

    st.markdown("---")

    price = st.number_input(
        "💲 السعر لكل متر",
        min_value=0.0,
        value=100.0,
        step=10.0
    )

# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="app-header">
<h1>🌊 نظام تحليل شبكات السيول</h1>
<p>تحليل الشبكات · حساب الأطوال · تقدير التكاليف</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# EMPTY STATE
# =========================================================

if uploaded is None:

    st.info("📁 ارفع ملف لبدء التحليل")

    empty_map = create_base_map()

    st_folium(
        empty_map,
        height=550,
        use_container_width=True,
        returned_objects=[]
    )

    st.stop()

# =========================================================
# LOAD DATA
# =========================================================

with st.spinner("⏳ جاري قراءة البيانات..."):

    if "df_cache" not in st.session_state:

        st.session_state.df_cache = load_file(
            uploaded
        )

df = st.session_state.df_cache

# =========================================================
# VALIDATION
# =========================================================

if len(df) == 0:

    st.warning(
        "⚠️ الملف لا يحتوي على خطوط صالحة"
    )

    st.stop()

# =========================================================
# STATS
# =========================================================

total_m = float(
    df["length_m"].sum()
)

avg_m = float(
    df["length_m"].mean()
)

max_m = float(
    df["length_m"].max()
)

c1, c2, c3, c4 = st.columns(4)

c1.markdown(
    f"""
    <div class="card">
    <div class="lbl">📏 عدد الخطوط</div>
    <div class="val">{len(df):,}</div>
    </div>
    """,
    unsafe_allow_html=True
)

c2.markdown(
    f"""
    <div class="card">
    <div class="lbl">📐 الطول الكلي</div>
    <div class="val">{total_m/1000:.2f} كم</div>
    </div>
    """,
    unsafe_allow_html=True
)

c3.markdown(
    f"""
    <div class="card">
    <div class="lbl">📊 المتوسط</div>
    <div class="val">{avg_m:.1f} م</div>
    </div>
    """,
    unsafe_allow_html=True
)

c4.markdown(
    f"""
    <div class="card">
    <div class="lbl">🔝 أطول خط</div>
    <div class="val">{max_m:.1f} م</div>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3 = st.tabs([
    "🗺️ الخريطة",
    "💰 الحساب",
    "📊 البيانات"
])

# =========================================================
# TAB 1
# =========================================================

with tab1:

    st.markdown(
        '<div class="sec-title">🗺️ الخريطة التفاعلية</div>',
        unsafe_allow_html=True
    )

    selected = st.multiselect(
        "اختر الخطوط",
        options=df.index.tolist()
    )

    map_obj = build_map(
        df,
        selected=selected,
        draw=True
    )

    map_data = st_folium(
        map_obj,
        height=650,
        use_container_width=True,
        returned_objects=["all_drawings"]
    )

# =========================================================
# TAB 2
# =========================================================

with tab2:

    selected_length = 0

    if selected:

        selected_length = float(
            df.loc[
                selected,
                "length_m"
            ].sum()
        )

    cost = selected_length * price

    st.markdown(
        f"""
        <div class="result">
        <div class="r-title">💵 التكلفة الإجمالية</div>
        <div class="r-value">{cost:,.2f} ﷼</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    drawings = (
        map_data or {}
    ).get("all_drawings") or []

    if drawings:

        lengths = []

        for d in drawings:

            try:

                geom = d["geometry"]

                if geom["type"] == "LineString":

                    lengths.append(
                        line_length(geom)
                    )

            except Exception:
                continue

        if lengths:

            draw_total = sum(lengths)

            draw_cost = draw_total * price

            st.markdown("---")

            st.markdown(
                f"""
                <div class="result">
                <div class="r-title">✏️ تكلفة الخطوط المرسومة</div>
                <div class="r-value">{draw_cost:,.2f} ﷼</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# =========================================================
# TAB 3
# =========================================================

with tab3:

    st.markdown(
        '<div class="sec-title">📊 جدول البيانات</div>',
        unsafe_allow_html=True
    )

    show_df = df.copy()

    show_df["_geom"] = "Geometry"

    st.dataframe(
        show_df,
        use_container_width=True,
        height=500
    )

    st.download_button(
        "⬇️ تحميل CSV",
        data=show_df.to_csv().encode(
            "utf-8-sig"
        ),
        file_name="flood_network.csv",
        mime="text/csv"
    )
