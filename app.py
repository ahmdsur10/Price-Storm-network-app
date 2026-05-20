import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import shapefile
from shapely.geometry import shape, LineString
from pyproj import Geod

# --- إعدادات الصفحة والتصميم ---
st.set_page_config(
    page_title="Stormwater Cost Estimator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص واجهة المستخدم وزيادة عرض الـ Sidebar بالـ CSS
st.markdown("""
    <style>
        /* تكبير عرض القائمة الجانبية وتوضيح الخطوط */
        [data-testid="stSidebar"] {
            min-width: 450px;
            max-width: 450px;
        }
        .sidebar-title {
            font-size: 24px !important;
            font-weight: bold;
            color: #1E3A8A;
            margin-bottom: 20px;
        }
        .guide-box {
            background-color: #f0f4f8;
            padding: 15px;
            border-radius: 8px;
            border-right: 5px solid #1E3A8A;
            margin-bottom: 20px;
        }
        .footer-text {
            position: fixed;
            bottom: 10px;
            left: 10px;
            font-size: 14px;
            color: #555;
            background-color: rgba(255,255,255,0.8);
            padding: 5px 10px;
            border-radius: 5px;
            z-index: 100;
        }
    </style>
""", unsafe_allow_name_escaped=True)

# دالة لحساب طول الخط بالأمتار بدقة (WGS84)
def calculate_line_length(geometry):
    if geometry.geom_type == 'LineString':
        geod = Geod(ellps="WGS84")
        return geod.geometry_length(geometry)
    return 0

# --- القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.markdown('<p class="sidebar-title">⚙️ لوحة التحكم والإرشادات</p>', unsafe_allow_html=True)
    
    # أسعار إرشادية للمستخدم
    st.markdown('<div class="guide-box"><b>💰 الأسعار الإرشادية للمتر الطولي:</b><br>'
                '• أنابيب قطر 1400 ملم: <b>4,004 ريال</b><br>'
                '• قناة صندوقية (1.8x1.4): <b>9,336 ريال</b><br>'
                '• قناة مفتوحة (عرض 12م وعمق 1.5م): <b>13,052 ريال</b></div>', unsafe_allow_html=True)
    
    # رفع الملفات
    st.subheader("📂 رفع بيانات الشبكة")
    uploaded_file = st.file_uploader("اختر ملف شبكة السيول (GeoJSON أو Shapefile .shp)", type=['geojson', 'shp'])

    st.markdown("---")
    # تذييل لحفظ الحقوق والفكرة
    st.markdown("### 👤 إعداد وتطوير:")
    st.markdown("**Eng: Ahmed Adam**")
    st.caption("© 2026 جميع الحقوق محفوظة لمحرك التطبيق")

# --- محتوى التطبيق الرئيسي ---
st.title("🗺️ تطبيق حساب تكاليف شبكات السيول التفاعلي")
st.write("تطبيق ذكي مبسط لتحليل أطوال شبكات السيول وحساب تكاليفها التقديرية بدقة.")

# إحداثيات الرياض الافتراضية
RIYADH_LAT, RIYADH_LON = 24.7136, 46.6753
START_ZOOM = 18

# متغيرات لتخزين الخطوط المحملة
network_lines = []

# 1. معالجة الملف المرفوع وتحويله إلى خطوط Shapely خفيفة
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.geojson'):
            # قراءة GeoJSON ميكانيكياً
            data = json.load(uploaded_file)
            for idx, feature in enumerate(data.get('features', [])):
                geom = shape(feature['geometry'])
                if geom.geom_type in ['LineString', 'MultiLineString']:
                    length = calculate_line_length(geom)
                    network_lines.append({'index': idx, 'geometry': geom, 'length': length})
                    
        elif uploaded_file.name.endswith('.shp'):
            # قراءة Shapefile عبر pyshp الخفيفة بدون مشاكل gdal
            # نكتب الملف مؤقتاً في الذاكرة للقراءة
            with shapefile.Reader(shp=uploaded_file) as sf:
                for idx, shape_record in enumerate(sf.shapeRecords()):
                    geom = shape(shape_record.shape.__geo_interface__)
                    if geom.geom_type in ['LineString', 'MultiLineString']:
                        length = calculate_line_length(geom)
                        network_lines.append({'index': idx, 'geometry': geom, 'length': length})
                        
        st.success(f"✅ تم تحميل {len(network_lines)} خط من الشبكة بنجاح!")
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")

# تقسيم الواجهة إلى جزأين (التحليل والخريطة)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 حساب التكاليف للشبكة الحالية")
    
    if network_lines:
        # اختيار متعدد للخطوط بناءً على الـ Index المطلوب
        available_indices = [item['index'] for item in network_lines]
        selected_indices = st.multiselect(
            "اختر أرقام الخطوط (Index) المراد حساب تكلفتها:", 
            options=available_indices,
            help="يمكنك البحث عن رقم الخط المكتوب في الخريطة واختياره هنا"
        )
        
        # حساب مجموع الأطوال المحددة
        total_selected_length = sum([item['length'] for item in network_lines if item['index'] in selected_indices])
        st.info(f"📏 مجموع أطوال الخطوط المختارة: **{total_selected_length:,.2f} متر**")
        
        # إدخال السعر مخصص أو اختيار سعر إرشادي
        price_option = st.selectbox("نوع السعر:", ["إدخال سعر مخصص", "أنبوب 1400 ملم", "قناة صندوقية", "قناة مفتوحة"])
        
        if price_option == "أنبوب 1400 ملم":
            unit_price = 4004
        elif price_option == "قناة صندوقية":
            unit_price = 9336
        elif price_option == "قناة مفتوحة":
            unit_price = 13052
        else:
            unit_price = st.number_input("أدخل سعر المتر الطولي (ريال):", min_value=0.0, value=1000.0, step=100.0)
            
        total_cost = total_selected_length * unit_price
        st.metric(label="💰 التكلفة الإجمالية للخطوط المختارة", value=f"{total_cost:,.2f} ريال")
    else:
        st.warning("الرجاء رفع ملف GeoJSON أو Shapefile لتفعيل خيارات اختيار الخطوط الحالية.")

    st.markdown("---")
    st.subheader("✏️ حساب تكلفة خط جديد (رسم مخصص)")
    st.write("استخدم أداة الرسم في الخريطة (لوحة الرسم يسار الخريطة) لرسم مسار جديد:")
    
    new_price = st.number_input("أدخل سعر المتر للخط الجديد (ريال):", min_value=0.0, value=1000.0, key="new_p")

with col2:
    st.subheader("🗺️ الخريطة التفاعلية")
    
    # بناء خريطة Folium مخصصة
    m = folium.Map(location=[RIYADH_LAT, RIYADH_LON], zoom_start=START_ZOOM, control_scale=True)
    
    # إضافة أداة الرسم الحر للخطوط المخصصة
    from folium.plugins import Draw
    Draw(
        export=False,
        position='topleft',
        draw_options={
            'polyline': True,
            'polygon': False,
            'circle': False,
            'rectangle': False,
            'marker': False,
            'circlemarker': False
        }
    ).add_to(m)
    
    # عرض خطوط الشبكة المرفوعة على الخريطة
    for line in network_lines:
        # تحويل الإحداثيات لشكل يفهمه folium (Lat, Lon) بدلاً من (Lon, Lat)
        if line['geometry'].geom_type == 'LineString':
            coords = [(p[1], p[0]) for p in line['geometry'].coords]
            folium.PolyLine(
                locations=coords,
                color='blue',
                weight=4,
                opacity=0.8,
                popup=f"📌 <b>رقم الخط (Index): {line['index']}</b><br>📏 الطول: {line['length']:.2f} متر"
            ).add_to(m)
            
    # عرض الخريطة في Streamlit والتقاط بيانات التفاعل ورسم المستخدم
    map_data = st_folium(m, width="100%", height=600)
    
    # معالجة الخطوط المرسومة حديثاً من قِبل المستخدم وحساب طولها وتكلفتها
    if map_data and map_data.get('all_drawings'):
        drawings = map_data['all_drawings']
        drawn_lengths = []
        
        for drawing in drawings:
            if drawing['geometry']['type'] == 'LineString':
                geom_drawn = shape(drawing['geometry'])
                drawn_lengths.append(calculate_line_length(geom_drawn))
        
        if drawn_lengths:
            total_drawn_length = sum(drawn_lengths)
            total_drawn_cost = total_drawn_length * new_price
            
            with col1:
                st.success("📐 تم رصد خط مرسوم على الخريطة!")
                st.write(f"📏 طول الخط المرسوم: **{total_drawn_length:,.2f} متر**")
                st.metric(label="💰 تكلفة الخط المرسوم", value=f"{total_drawn_cost:,.2f} ريال")

# إضافة توقيع ثابت أسفل الشاشة لحفظ الحقوق
st.markdown(f'<div class="footer-text">📐 فكرة وتطوير المهندس: <b>Ahmed Adam</b></div>', unsafe_allow_html=True)
