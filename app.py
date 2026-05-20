import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import shapely.geometry as sg
from shapely.geometry import LineString, mapping
from pyproj import Geod
import numpy as np

# ------------------------------------------------------------
# تنسيق الصفحة وتوسيع الشريط الجانبي
# ------------------------------------------------------------
st.set_page_config(page_title="حساب تكلفة شبكات السيول", layout="wide")

st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            min-width: 380px !important;
            width: 380px !important;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f0f2f6;
            text-align: center;
            padding: 5px;
            font-size: 14px;
            color: #333;
            border-top: 1px solid #ddd;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# دوال مساعدة
# ------------------------------------------------------------
@st.cache_data
def load_geojson(file) -> pd.DataFrame:
    data = json.load(file)
    features = data.get("features", [])
    records = []
    geod = Geod(ellps="WGS84")
    for feat in features:
        geom = feat.get("geometry")
        if geom and geom["type"] == "LineString":
            coords = geom["coordinates"]
            line = LineString(coords)
            _, _, dist = geod.inv(line.coords[:-1], line.coords[1:])
            length_m = sum(dist)
            records.append({
                "index": len(records),
                "geometry": line,
                "length_m": length_m
            })
    df = pd.DataFrame(records)
    if not df.empty:
        df["index_1based"] = df.index + 1
    return df

def compute_line_length(line_geom: LineString) -> float:
    geod = Geod(ellps="WGS84")
    coords = list(line_geom.coords)
    _, _, dist = geod.inv(coords[:-1], coords[1:])
    return sum(dist)

# ------------------------------------------------------------
# حالة الجلسة
# ------------------------------------------------------------
if "gdf" not in st.session_state:
    st.session_state.gdf = pd.DataFrame()
if "drawn_line" not in st.session_state:
    st.session_state.drawn_line = None
if "map_center" not in st.session_state:
    st.session_state.map_center = [24.7136, 46.6753]
if "zoom_start" not in st.session_state:
    st.session_state.zoom_start = 18

# ------------------------------------------------------------
# الشريط الجانبي
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📁 رفع الملف الخام")
    uploaded_file = st.file_uploader("اختر ملف GeoJSON (خطوط شبكة السيول)", type=["geojson"])
    
    st.markdown("---")
    st.markdown("## 💰 إعدادات التكلفة")
    st.info("**الأسعار الإرشادية (ريال / متر طولي):**\n"
            "- أنابيب بقطر 1400 مم: 4,004 ريال\n"
            "- قناة صندوقية (1.8x1.4 م): 9,336 ريال\n"
            "- قناة مفتوحة (عرض 12 م، عمق 1.5 م): 13,052 ريال")
    
    price_option = st.radio(
        "اختر طريقة تحديد السعر:",
        ["سعر مسبق (من القائمة)", "إدخال يدوي"]
    )
    
    if price_option == "سعر مسبق (من القائمة)":
        price_type = st.selectbox(
            "نوع القطعة",
            ["أنابيب قطر 1400 مم (4004 ريال/م)", 
             "قناة صندوقية 1.8x1.4 م (9336 ريال/م)",
             "قناة مفتوحة 12x1.5 م (13052 ريال/م)"]
        )
        price_per_meter = {
            "أنابيب قطر 1400 مم (4004 ريال/م)": 4004,
            "قناة صندوقية 1.8x1.4 م (9336 ريال/م)": 9336,
            "قناة مفتوحة 12x1.5 م (13052 ريال/م)": 13052
        }[price_type]
    else:
        price_per_meter = st.number_input("السعر لكل متر (ريال)", min_value=0.0, value=5000.0, step=100.0)
    
    st.markdown("---")
    st.markdown("## 🖊️ رسم خط جديد")
    st.markdown("استخدم أداة الرسم على الخريطة (أيقونة الخط 📏)، ثم سيظهر طوله وتكلفته أدناه.")
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; font-size: 16px;'>✍️ <strong>Eng: Ahmed Adam</strong><br>© جميع الحقوق محفوظة</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# تحميل الملف
# ------------------------------------------------------------
if uploaded_file is not None:
    try:
        st.session_state.gdf = load_geojson(uploaded_file)
        st.success(f"تم تحميل {len(st.session_state.gdf)} خط بنجاح")
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {e}")
        st.session_state.gdf = pd.DataFrame()

if st.session_state.gdf.empty:
    st.info("📂 يرجى رفع ملف GeoJSON من الشريط الجانبي لعرض الخطوط وحساب التكاليف.")
    m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.zoom_start)
    st_folium(m, width="100%", height=500)
    st.stop()

# ------------------------------------------------------------
# بناء الخريطة التفاعلية
# ------------------------------------------------------------
gdf = st.session_state.gdf
m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.zoom_start)

for idx, row in gdf.iterrows():
    line_geom = row["geometry"]
    popup_text = f"<b>رقم الخط: {row['index_1based']}</b><br>الطول: {row['length_m']:.2f} متر"
    geojson_data = mapping(line_geom)
    folium.GeoJson(
        geojson_data,
        name=f"line_{idx}",
        popup=folium.Popup(popup_text, max_width=300),
        style_function=lambda feature, col=row['length_m']: {"color": "blue", "weight": 3, "opacity": 0.7}
    ).add_to(m)

draw_control = folium.plugins.Draw(
    draw_options={
        "polyline": {"shapeOptions": {"color": "red", "weight": 4}},
        "rectangle": False,
        "circle": False,
        "polygon": False,
        "marker": False,
        "circlemarker": False
    },
    edit_options={"edit": False}
)
m.add_child(draw_control)

map_output = st_folium(m, width="100%", height=550, key="main_map")

if map_output and map_output.get("last_active_drawing"):
    drawing = map_output["last_active_drawing"]
    if drawing and drawing.get("geometry") and drawing["geometry"]["type"] == "LineString":
        coords = drawing["geometry"]["coordinates"]
        if len(coords) >= 2:
            new_line = LineString(coords)
            length_m = compute_line_length(new_line)
            st.session_state.drawn_line = (new_line, length_m)
        else:
            st.session_state.drawn_line = None
else:
    pass

if st.session_state.drawn_line is not None:
    drawn_geom, drawn_len = st.session_state.drawn_line
    st.markdown("---")
    st.subheader("📏 الخط المرسوم حديثاً")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("الطول (متر)", f"{drawn_len:.2f}")
    with col2:
        cost_drawn = drawn_len * price_per_meter
        st.metric("التكلفة التقديرية (ريال)", f"{cost_drawn:,.2f}")
    if st.button("🗑️ مسح الخط المرسوم"):
        st.session_state.drawn_line = None
        st.rerun()

# ------------------------------------------------------------
# اختيار متعدد للخطوط
# ------------------------------------------------------------
st.markdown("---")
st.subheader("🔍 اختيار خطوط من الشبكة لحساب التكلفة الإجمالية")

line_numbers = gdf["index_1based"].tolist()
selected_nums = st.multiselect(
    "اختر رقم/أرقام الخطوط (يمكنك اختيار أكثر من خط)",
    options=line_numbers,
    format_func=lambda x: f"الخط رقم {x}"
)

if selected_nums:
    selected_rows = gdf[gdf["index_1based"].isin(selected_nums)]
    total_length = selected_rows["length_m"].sum()
    total_cost = total_length * price_per_meter
    st.info(f"**عدد الخطوط المختارة:** {len(selected_nums)}")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("📏 إجمالي الطول (متر)", f"{total_length:,.2f}")
    with col_b:
        st.metric("💰 التكلفة الكلية (ريال)", f"{total_cost:,.2f}")
    with st.expander("تفاصيل الأطوال لكل خط"):
        detail_df = selected_rows[["index_1based", "length_m"]].copy()
        detail_df.columns = ["رقم الخط", "الطول (متر)"]
        st.dataframe(detail_df, use_container_width=True)
else:
    st.caption("✏️ اختر خطاً واحداً أو أكثر من القائمة أعلاه")

st.markdown(
    "<div class='footer'>تطبيق حساب تكاليف شبكات السيول – تصميم وتطوير المهندس: أحمد آدم</div>",
    unsafe_allow_html=True
)
