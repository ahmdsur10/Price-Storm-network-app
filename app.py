import streamlit as st
import folium
from folium.plugins import Draw, MeasureControl
from streamlit_folium import st_folium

import pandas as pd
import numpy as np
import tempfile
import zipfile
import os

import orjson as json

from shapely.geometry import shape, mapping
import shapefile

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Flood Network System",
    page_icon="🌊",
    layout="wide"
)

RIYADH = [24.7136, 46.6753]

# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #f5f7fa;
}

.block-container {
    padding-top: 1rem;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================

def simplify_geometry(geom, tolerance=0.00001):
    try:
        g = shape(geom)
        simp = g.simplify(tolerance, preserve_topology=True)
        return mapping(simp)
    except:
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
            return sum(haversine(x.coords) for x in g.geoms)

    except:
        return 0

    return 0


# =========================================================
# LOAD FILE
# =========================================================

@st.cache_data(show_spinner=False)
def load_geojson(data):

    fc = json.loads(data)

    rows = []

    for i, feat in enumerate(fc["features"]):

        geom = feat["geometry"]

        if geom["type"] not in ["LineString", "MultiLineString"]:
            continue

        geom = simplify_geometry(geom)

        rows.append({
            "id": i,
            "geometry": geom,
            "length_m": round(line_length(geom), 2)
        })

    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def load_shp_zip(data):

    with tempfile.TemporaryDirectory() as tmp:

        zpath = os.path.join(tmp, "file.zip")

        with open(zpath, "wb") as f:
            f.write(data)

        with zipfile.ZipFile(zpath) as z:
            z.extractall(tmp)

        shp = None

        for root, _, files in os.walk(tmp):
            for f in files:
                if f.endswith(".shp"):
                    shp = os.path.join(root, f)

        if shp is None:
            return None

        sf = shapefile.Reader(shp)

        rows = []

        for i, sr in enumerate(sf.shapeRecords()):

            geom = sr.shape.__geo_interface__

            if geom["type"] not in ["LineString", "MultiLineString"]:
                continue

            geom = simplify_geometry(geom)

            rows.append({
                "id": i,
                "geometry": geom,
                "length_m": round(line_length(geom), 2)
            })

        return pd.DataFrame(rows)


def load_data(uploaded):

    data = uploaded.read()

    name = uploaded.name.lower()

    if name.endswith(".geojson") or name.endswith(".json"):
        return load_geojson(data)

    if name.endswith(".zip"):
        return load_shp_zip(data)

    return None


# =========================================================
# MAP
# =========================================================

@st.cache_resource(show_spinner=False)
def create_base_map():

    m = folium.Map(
        location=RIYADH,
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite"
    ).add_to(m)

    MeasureControl().add_to(m)

    folium.LayerControl().add_to(m)

    return m


def build_map(df, selected=None, draw=False):

    m = create_base_map()

    if df is not None and len(df) > 0:

        features = []

        selected = selected or []

        for _, row in df.iterrows():

            color = "#ff0000" if row["id"] in selected else "#0077b6"

            weight = 5 if row["id"] in selected else 2

            features.append({
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {
                    "style": {
                        "color": color,
                        "weight": weight
                    }
                }
            })

        folium.GeoJson(
            {
                "type": "FeatureCollection",
                "features": features
            },
            style_function=lambda x: x["properties"]["style"]
        ).add_to(m)

    if draw:

        Draw(
            draw_options={
                "polyline": True,
                "polygon": False,
                "rectangle": False,
                "circle": False,
                "marker": False,
                "circlemarker": False
            }
        ).add_to(m)

    return m


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📁 Upload")

uploaded = st.sidebar.file_uploader(
    "Upload GeoJSON or ZIP",
    type=["geojson", "json", "zip"]
)

price = st.sidebar.number_input(
    "Price per meter",
    min_value=0.0,
    value=100.0
)

# =========================================================
# MAIN
# =========================================================

st.title("🌊 Flood Network Analysis System")

if uploaded is None:

    st.info("Upload file to start")

    empty_map = create_base_map()

    st_folium(
        empty_map,
        height=500,
        width=None,
        use_container_width=True,
        returned_objects=[]
    )

    st.stop()

# =========================================================
# LOAD
# =========================================================

with st.spinner("Loading data..."):

    if "df" not in st.session_state:
        st.session_state.df = load_data(uploaded)

df = st.session_state.df

if df is None:

    st.error("Invalid file")

    st.stop()

# =========================================================
# STATS
# =========================================================

total_length = df["length_m"].sum()

col1, col2, col3 = st.columns(3)

col1.metric(
    "Lines",
    f"{len(df):,}"
)

col2.metric(
    "Total Length",
    f"{total_length/1000:.2f} km"
)

col3.metric(
    "Average",
    f"{df['length_m'].mean():.2f} m"
)

# =========================================================
# SELECT
# =========================================================

selected = st.multiselect(
    "Select lines",
    options=df["id"].tolist()
)

selected_length = 0

if selected:

    selected_length = df[
        df["id"].isin(selected)
    ]["length_m"].sum()

# =========================================================
# COST
# =========================================================

cost = selected_length * price

st.success(
    f"Total Cost = {cost:,.2f} SAR"
)

# =========================================================
# MAP
# =========================================================

map_obj = build_map(
    df,
    selected=selected,
    draw=True
)

map_data = st_folium(
    map_obj,
    height=650,
    width=None,
    use_container_width=True,
    returned_objects=["all_drawings"]
)

# =========================================================
# DRAWINGS
# =========================================================

drawings = (map_data or {}).get("all_drawings") or []

if drawings:

    lengths = []

    for d in drawings:

        geom = d["geometry"]

        if geom["type"] == "LineString":

            lengths.append(
                line_length(geom)
            )

    if lengths:

        total_draw = sum(lengths)

        st.info(
            f"Drawn Length = {total_draw:,.2f} m"
        )

        st.success(
            f"Drawn Cost = {total_draw * price:,.2f} SAR"
        )

# =========================================================
# TABLE
# =========================================================

st.subheader("Data")

show_df = df.copy()

show_df["geometry"] = show_df["geometry"].astype(str)

st.dataframe(
    show_df,
    use_container_width=True
)
