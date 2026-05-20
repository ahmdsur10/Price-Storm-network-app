import streamlit as st
import pandas as pd
import folium
import json
import tempfile
import zipfile
import os

from shapely.geometry import shape, LineString
from streamlit_folium import st_folium
from folium.plugins import Draw

st.set_page_config(
    page_title="Storm Network Cost Calculator",
    layout="wide"
)

# ======================================================
# STYLE
# ======================================================

st.markdown("""
<style>
[data-testid="stSidebar"] {
    width: 420px;
}

.main-title {
    font-size:40px;
    font-weight:bold;
    color:#0B5394;
}

.footer {
    text-align:center;
    font-size:16px;
    color:gray;
    margin-top:20px;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================

st.sidebar.title("💰 حساب تكلفة شبكات السيول")

st.sidebar.markdown("""
## 📌 أسعار استرشادية

- انابيب بقطة 1400 ملم  
💵 4004 ريال / متر

- قناة صندوقية (1.8 × 1.4)  
💵 9336 ريال / متر

- قناة مفتوحة عرض 12م وعمق 1.5م  
💵 13052 ريال / متر
""")

st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "📂 ارفع ملف GIS",
    type=["geojson", "zip"]
)

price_per_meter = st.sidebar.number_input(
    "💵 سعر المتر",
    min_value=0.0,
    value=4004.0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 👨‍💻 Developed by")
st.sidebar.markdown("## Eng: Ahmed Adam")

# ======================================================
# MAP
# ======================================================

m = folium.Map(
    location=[24.7136, 46.6753],
    zoom_start=18,
    control_scale=True
)

Draw(
    export=True,
    draw_options={
        "polyline": True,
        "polygon": False,
        "circle": False,
        "rectangle": False,
        "marker": False,
        "circlemarker": False
    }
).add_to(m)

selected_lengths = []

# ======================================================
# READ GEOJSON
# ======================================================

if uploaded_file:

    features = []

    if uploaded_file.name.endswith(".geojson"):

        geojson_data = json.load(uploaded_file)
        features = geojson_data["features"]

    elif uploaded_file.name.endswith(".zip"):

        with tempfile.TemporaryDirectory() as tmpdir:

            zip_path = os.path.join(tmpdir, uploaded_file.name)

            with open(zip_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdir)

            shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]

            if shp_files:
                import pyogrio

                shp_path = os.path.join(tmpdir, shp_files[0])

                gdf = pyogrio.read_dataframe(shp_path)

                geojson_data = json.loads(gdf.to_json())

                features = geojson_data["features"]

    # ======================================================
    # DRAW FEATURES
    # ======================================================

    for idx, feature in enumerate(features):

        geom = shape(feature["geometry"])

        if isinstance(geom, LineString):

            length = geom.length

            selected_lengths.append(length)

            coords = [[y, x] for x, y in geom.coords]

            popup_text = f"""
            <b>رقم الخط:</b> {idx}<br>
            <b>الطول:</b> {round(length,2)} متر
            """

            folium.PolyLine(
                coords,
                color="blue",
                weight=5,
                popup=popup_text
            ).add_to(m)

# ======================================================
# SHOW MAP
# ======================================================

st.markdown('<p class="main-title">💰 Storm Network Cost Calculator</p>', unsafe_allow_html=True)

map_data = st_folium(
    m,
    width=None,
    height=700
)

# ======================================================
# DRAWN LINE COST
# ======================================================

if map_data and map_data.get("all_drawings"):

    drawings = map_data["all_drawings"]

    for drawing in drawings:

        if drawing["geometry"]["type"] == "LineString":

            coords = drawing["geometry"]["coordinates"]

            line = LineString(coords)

            draw_length = line.length

            draw_cost = draw_length * price_per_meter

            st.success(f"""
            📏 طول الخط المرسوم: {round(draw_length,2)} متر

            💰 التكلفة: {round(draw_cost,2)} ريال
            """)

# ======================================================
# NETWORK COST
# ======================================================

if len(selected_lengths) > 0:

    total_length = sum(selected_lengths)

    total_cost = total_length * price_per_meter

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "📏 إجمالي الأطوال",
            f"{round(total_length,2)} متر"
        )

    with col2:
        st.metric(
            "💰 التكلفة الإجمالية",
            f"{round(total_cost,2)} ريال"
        )

# ======================================================
# FOOTER
# ======================================================

st.markdown("""
<div class='footer'>
Developed by Eng: Ahmed Adam
</div>
""", unsafe_allow_html=True)
