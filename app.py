import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import shapefile
from shapely.geometry import shape
from pyproj import Geod

# --- إعدادات الصفحة الأساسية ---
st.set_page_config(
    page_title="حاسب تكاليف شبكات السيول",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- التنسيق الجمالي الاحترافي المخصص وقلب الـ Sidebar إلى اليمين كلياً ---
st.markdown("""
    <style>
        /* إعدادات الاتجاه العام للتطبيق من اليمين لليسار */
        html, body, [data-testid="stAppViewContainer"] {
            direction: RTL;
            text-align: right;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8fafc;
        }

        /* نقل الـ Sidebar بالكامل من اليسار إلى اليمين */
        [data-testid="stSidebarCollapsedControl"] {
            right: 20px;
            left: auto;
        }
        
        section[data-testid="stSidebar"] {
            right: 0;
            left: auto;
            border-left: 1px solid #e2e8f0;
            border-right: none;
            box-shadow: -4px 0 10px rgba(0,0,0,0.05);
            background-color: #ffffff !important;
            min-width: 420px !important;
            max-width: 420px !important;
        }
        
        /* ضبط إزاحة المحتوى الرئيسي ليتناسب مع وجود الـ Sidebar على اليمين */
        @media (min-width: 576px) {
            section[data-testid="stSidebar"] ~ [data-testid="stMain"] {
                margin-right: 420px;
                margin-left: 0px;
            }
        }

        /* تحسين مظهر النصوص والعناوين داخل الـ Sidebar */
        .sidebar-title {
            font-size: 22px !important;
            font-weight: 700;
            color: #1e3a8a;
            border-bottom: 2px solid #3b82f6;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        /* تصميم جميل وأنيق لبطاقة الأسعار الإرشادية */
        .guide-card {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            padding: 18px;
            border-radius: 12px;
            border-right: 6px solid #16a34a;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 25px;
        }
        .guide-card b {
            color: #14532d;
            font-size: 16px;
        }

        /* تحسين مظهر حاويات رفع الملفات والمدخلات */
        .stFileUploader, .stSelectbox, .stMultiSelect, .stNumberInput {
            margin-bottom: 15px;
        }
        
        /* تحسين مظهر المؤشرات الرقمية (Metrics) */
        div[data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: bold;
            color: #2563eb;
        }
        
        /* بطاقة الحقوق الثابتة أسفل يمين الشاشة */
        .premium-footer {
            position: fixed;
            bottom: 15px;
            right: 15px;
            font-size: 13px;
            font-weight: 600;
            color: #1e3a8a;
            background: #ffffff;
            padding: 8px 16px;
            border-radius: 30px;
            border: 1px solid #3b82f6;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
            z-index: 9999;
        }
        
        /* ضبط اتجاه تلميحات الادخال ونصوص المساعد الدلالي */
        div[data-testid="stMarkdownContainer"] p {
            text-align: right;
        }
    </style>
""", unsafe_allow_html=True)

# دالة لحساب طول الخط بالأمتار بدقة (WGS84)
def calculate_line_length(geometry):
    if geometry.geom_type == 'LineString':
        from pyproj import Geod
        geod = Geod(ellps="WGS84")
        return geod.geometry_length(geometry)
    elif geometry.geom_type == 'MultiLineString':
        from pyproj import Geod
        geod = Geod(ellps="WGS84")
        total_len = 0
        for part in geometry.geoms:
            total_len += geod.geometry_length(part)
        return total_len
    return 0

# --- القائمة الجانبية (Sidebar) في الجهة اليمنى ---
with st.sidebar:
    st.markdown('<p class="sidebar-title">⚙️ لوحة التحكم والإرشادات</p>', unsafe_allow_html=True)
    
    # بطاقة الأسعار الإرشادية التقديرية للمستخدم
    st.markdown('<div class="guide-card"><b>💰 الأسعار الإرشادية للمتر الطولي:</b><br><br>'
                '• أنابيب قطر 1400 ملم: <b>4,004 ريال</b><br>'
                '• قناة صندوقية (1.8x1.4): <b>9,336 ريال</b><br>'
                '• قناة مفتوحة (عرض 12م وعمق 1.5م): <b>13,052 ريال</b></div>', unsafe_allow_html=True)
    
    # رفع الملفات الهندسية باللغة العربية
    st.subheader("📂 رفع بيانات الشبكة")
    uploaded_file = st.file_uploader("اختر ملف شبكة السيول (GeoJSON أو Shapefile .shp)", type=['geojson', 'shp'])

    st.markdown("---")
    # حفظ حقوق الفكرة والمطور
    st.markdown("### 👤 إعداد وتطوير:")
    st.markdown("**Eng: Ahmed Adam**")
    st.caption("© 2026 جميع الحقوق محفوظة لمحرك التطبيق")

# --- محتوى التطبيق الرئيسي (الجهة اليسرى والوسطى) ---
st.title("🗺️ تطبيق حساب تكاليف شبكات السيول التفاعلي")
st.write("تطبيق ذكي مبسط ومصمم خصيصاً لتسهيل تحليل أطوال شبكات السيول وحساب تكاليفها التقديرية بدقة دون تعقيد.")

# إحداثيات الرياض والزوم البداية 18 المفضل لديك لتقريب دقيق جداً
RIYADH_LAT, RIYADH_LON = 24.7136, 46.6753
START_ZOOM = 18

network_lines = []

# 1. معالجة الملف المرفوع ودعم كامل للبيانات العربية والـ Shapefile
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.geojson'):
            file_content = uploaded_file.read().decode('utf-8')
            data = json.loads(file_content)
            for idx, feature in enumerate(data.get('features', [])):
                geom = shape(feature['geometry'])
                if geom.geom_type in ['LineString', 'MultiLineString']:
                    length = calculate_line_length(geom)
                    network_lines.append({'index': idx, 'geometry': geom, 'length': length})
                    
        elif uploaded_file.name.endswith('.shp'):
            with shapefile.Reader(shp=uploaded_file, encoding='utf-8') as sf:
                for idx, shape_record in enumerate(sf.shapeRecords()):
                    geom = shape(shape_record.shape.__geo_interface__)
                    if geom.geom_type in ['LineString', 'MultiLineString']:
                        length = calculate_line_length(geom)
                        network_lines.append({'index': idx, 'geometry': geom, 'length': length})
                        
        st.success(f"✅ تم تحميل {len(network_lines)} خط من الشبكة بنجاح!")
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف المرفوع: {e}")

# تقسيم واجهة العرض بالتوازي (توسيع عمود الخريطة وضبط المقاسات)
col1, col2 = st.columns([1, 2.5])

with col1:
    st.subheader("📊 حساب التكاليف للشبكة")
    
    if network_lines:
        available_indices = [item['index'] for item in network_lines]
        selected_indices = st.multiselect(
            "اختر أرقام الخطوط (Index):", 
            options=available_indices,
            help="تطابق الأرقام هنا مع رقم الـ Index الظاهر في الـ Popup الخاص بكل خط على الخريطة"
        )
        
        # حساب مجموع الأطوال
        total_selected_length = sum([item['length'] for item in network_lines if item['index'] in selected_indices])
        st.info(f"📏 مجموع أطوال الخطوط المختارة: **{total_selected_length:,.2f} متر**")
        
        price_option = st.selectbox("نوع السعر المستهدف للشبكة:", ["إدخال سعر مخصص", "أنبوب 1400 ملم", "قناة صندوقية", "قناة مفتوحة"])
        
        if price_option == "أنبوب 1400 ملم":
            unit_price = 4004
        elif price_option == "قناة صندوقية":
            unit_price = 9336
        elif price_option == "قناة مفتوحة":
            unit_price = 13052
        else:
            unit_price = st.number_input("أدخل سعر المتر المخصص (ريال):", min_value=0.0, value=1000.0, step=100.0)
            
        total_cost = total_selected_length * unit_price
        st.metric(label="💰 التكلفة الكلية للخطوط المحددة", value=f"{total_cost:,.2f} ريال")
    else:
        st.warning("يرجى رفع ملف GeoJSON أو Shapefile لتفعيل لوحة حساب خطوط الشبكة.")

    st.markdown("---")
    st.subheader("✏️ رسم مسار خط جديد")
    st.write("ارسم خطاً مخصصاً على الخريطة لحساب طوله وتكلفته:")
    
    new_price = st.number_input("أدخل سعر المتر للخط الجديد (ريال):", min_value=0.0, value=1000.0, key="new_p")

with col2:
    st.subheader("🗺️ الخريطة الجغرافية التفاعلية المتقدمة")
    
    # بناء الخريطة التفاعلية بزوم 18 الافتراضي لمدينة الرياض وبدون تحديد خلفية ثابتة لإتاحة التبديل
    m = folium.Map(location=[RIYADH_LAT, RIYADH_LON], zoom_start=START_ZOOM, control_scale=True, tiles=None)
    
    # 1. إضافة خرائط الأساس المتنوعة (Tile Layers) للتبديل الاحترافي
    folium.TileLayer('openstreetmap', name='الخريطة الافتراضية الطبوغرافية').add_to(m)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='قمر صناعي (Google)',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Hybrid',
        name='قمر صناعي مع الشوارع (Hybrid)',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer('cartodb dark_matter', name='الخريطة الداكنة الليلية').add_to(m)
    
    # إضافة أداة الرسم الحر للمسارات الجديدة
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
    
    # إضافة الخطوط الحالية إلى الخريطة التفاعلية مع ظهور رقم الـ index في الـ popup باللون الفسفوري الساطع/الأحمر لتناسب كل الخلفيات
    for line in network_lines:
        if line['geometry'].geom_type == 'LineString':
            coords = [(p[1], p[0]) for p in line['geometry'].coords]
            folium.PolyLine(
                locations=coords,
                color='#ef4444', # لون أحمر حيوي ممتاز يظهر بوضوح في الخريطة العادية والستلايت
                weight=5,
                opacity=0.9,
                popup=f"<div style='text-align:right; direction:rtl; font-family:sans-serif;'>📌 <b>رقم الخط (Index): {line['index']}</b><br>📏 الطول: {line['length']:.2f} متر</div>"
            ).add_to(m)
        elif line['geometry'].geom_type == 'MultiLineString':
            for part in line['geometry'].geoms:
                coords = [(p[1], p[0]) for p in part.coords]
                folium.PolyLine(
                    locations=coords,
                    color='#ef4444',
                    weight=5,
                    opacity=0.9,
                    popup=f"<div style='text-align:right; direction:rtl; font-family:sans-serif;'>📌 <b>رقم الخط (Index): {line['index']}</b><br>📏 الطول: {line['length']:.2f} متر</div>"
                ).add_to(m)
                
    # إضافة أداة تحكم الطبقات (المنبثقة للتبديل بين خرائط الأساس)
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
            
    # تشغيل وعرض الخريطة التفاعلية الكبيرة (تم زيادة الارتفاع إلى 750 بكسل للتوسعة)
    map_data = st_folium(m, width="100%", height=750)
    
    # معالجة بيانات الرسم المخصص للمستخدم
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
                st.success("📐 تم رصد مسار مرسوم حديثاً!")
                st.write(f"📏 طول الخط المرسوم: **{total_drawn_length:,.2f} متر**")
                st.metric(label="💰 تكلفة المسار المرسوم", value=f"{total_drawn_cost:,.2f} ريال")

# التوقيع والمظهر الاحترافي الثابت لحفظ فكرتك وحقوقك في أسفل يمين الشاشة
st.markdown(f'<div class="premium-footer">📐 فكرة وتطوير المهندس: <b>Ahmed Adam</b></div>', unsafe_allow_html=True)
