import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import shapefile
from shapely.geometry import shape, LineString
from pyproj import Geod

# --- إعدادات الصفحة والتصميم ---
st.set_page_config(
    page_title="حاسب تكاليف شبكات السيول",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص واجهة المستخدم لدعم العربية (RTL) وزيادة عرض الـ Sidebar
st.markdown("""
    <style>
        /* تحويل اتجاه التطبيق بالكامل من اليمين إلى اليسار */
        .main .block-container, div[data-testid="stSidebarUserContent"] {
            direction: RTL;
            text-align: right;
        }
        
        /* ضبط عناصر التحكم والقوائم المنسدلة لتتناسب مع اليمين */
        div[role="listbox"], .stSelectbox, .stMultiSelect, .stNumberInput {
            direction: RTL;
            text-align: right;
        }
        
        /* تكبير عرض القائمة الجانبية وتعديل مكانها المخصص للـ RTL */
        [data-testid="stSidebar"] {
            min-width: 450px;
            max-width: 450px;
            direction: RTL;
        }
        
        /* تنسيق العنوان الجانبي */
        .sidebar-title {
            font-size: 24px !important;
            font-weight: bold;
            color: #1E3A8A;
            margin-bottom: 20px;
        }
        
        /* صندوق الإرشادات والأسعار */
        .guide-box {
            background-color: #f0f4f8;
            padding: 15px;
            border-radius: 8px;
            border-right: 5px solid #1E3A8A;
            margin-bottom: 20px;
            direction: RTL;
        }
        
        /* توقيع ثابت أسفل الشاشة جهة اليمين */
        .footer-text {
            position: fixed;
            bottom: 10px;
            right: 10px;
            font-size: 14px;
            color: #555;
            background-color: rgba(255,255,255,0.9);
            padding: 5px 15px;
            border-radius: 5px;
            border: 1px solid #ddd;
            z-index: 100;
            direction: RTL;
        }
        
        /* محاذاة التلميحات المساعدة */
        div[data-testid="stMarkdownContainer"] {
            text-align: right;
        }
    </style>
""", unsafe_allow_html=True)

# دالة لحساب طول الخط بالأمتار بدقة (WGS84)
def calculate_line_length(geometry):
    if geometry.geom_type == 'LineString':
        geod = Geod(ellps="WGS84")
        return geod.geometry_length(geometry)
    elif geometry.geom_type == 'MultiLineString':
        geod = Geod(ellps="WGS84")
        total_len = 0
        for part in geometry.geoms:
            total_len += geod.geometry_length(part)
        return total_len
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
    # تذييل لحفظ الحقوق والفكرة داخل القائمة الجانبية
    st.markdown("### 👤 إعداد وتطوير:")
    st.markdown("**Eng: Ahmed Adam**")
    st.caption("© 2026 جميع الحقوق محفوظة لمحرك التطبيق")

# --- محتوى التطبيق الرئيسي ---
st.title("🗺️ تطبيق حساب تكاليف شبكات السيول التفاعلي")
st.write("تطبيق ذكي مبسط لتحليل أطوال شبكات السيول وحساب تكاليفها التقديرية بدقة وسرعة عالية.")

# إحداثيات الرياض الافتراضية والزوم المطلوب
RIYADH_LAT, RIYADH_LON = 24.7136, 46.6753
START_ZOOM = 18

# متغيرات لتخزين الخطوط المحملة في الذاكرة
network_lines = []

# 1. معالجة الملف المرفوع (دعم كامل للملفات والبيانات باللغة العربية)
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.geojson'):
            # استخدام ترميز utf-8 لضمان قراءة النصوص العربية دون مشاكل رموز غريبة
            file_content = uploaded_file.read().decode('utf-8')
            data = json.loads(file_content)
            for idx, feature in enumerate(data.get('features', [])):
                geom = shape(feature['geometry'])
                if geom.geom_type in ['LineString', 'MultiLineString']:
                    length = calculate_line_length(geom)
                    network_lines.append({'index': idx, 'geometry': geom, 'length': length})
                    
        elif uploaded_file.name.endswith('.shp'):
            # استخدام مكتبة pyshp الخفيفة والنقية لقراءة ملفات الـ Shapefile مباشرة
            # نقوم بقراءة الملف وتمرير ترميز اللغة العربية utf-8 لبيانات الجدول المصاحب إن وُجد
            with shapefile.Reader(shp=uploaded_file, encoding='utf-8') as sf:
                for idx, shape_record in enumerate(sf.shapeRecords()):
                    geom = shape(shape_record.shape.__geo_interface__)
                    if geom.geom_type in ['LineString', 'MultiLineString']:
                        length = calculate_line_length(geom)
                        network_lines.append({'index': idx, 'geometry': geom, 'length': length})
                        
        st.success(f"✅ تم تحميل {len(network_lines)} خط من الشبكة المرفوعة بنجاح!")
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")

# تقسيم واجهة العرض (عمود التحكم يمين، وعمود الخريطة يسار لتناسب الـ RTL)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 حساب التكاليف للشبكة الحالية")
    
    if network_lines:
        available_indices = [item['index'] for item in network_lines]
        selected_indices = st.multiselect(
            "اختر أرقام الخطوط (Index) المراد حساب تكلفتها:", 
            options=available_indices,
            help="يمكنك كتابة رقم الـ Index أو اختيار عدة خطوط معاً مباشرة وسيقوم التطبيق بحساب مجموع الأطوال تلقائياً"
        )
        
        # حساب مجموع الأطوال المحددة
        total_selected_length = sum([item['length'] for item in network_lines if item['index'] in selected_indices])
        st.info(f"📏 مجموع أطوال الخطوط المختارة: **{total_selected_length:,.2f} متر**")
        
        price_option = st.selectbox("نوع السعر المستهدف:", ["إدخال سعر مخصص", "أنبوب 1400 ملم", "قناة صندوقية", "قناة مفتوحة"])
        
        if price_option == "أنبوب 1400 ملم":
            unit_price = 4004
        elif price_option == "قناة صندوقية":
            unit_price = 9336
        elif price_option == "قناة مفتوحة":
            unit_price = 13052
        else:
            unit_price = st.number_input("أدخل سعر المتر الطولي المخصص (ريال):", min_value=0.0, value=1000.0, step=100.0)
            
        total_cost = total_selected_length * unit_price
        st.metric(label="💰 التكلفة الإجمالية للخطوط المختارة", value=f"{total_cost:,.2f} ريال")
    else:
        st.warning("الرجاء رفع ملف هندسي (GeoJSON / Shapefile) لتفعيل لوحة اختيار وحساب تكاليف الخطوط.")

    st.markdown("---")
    st.subheader("✏️ حساب تكلفة خط جديد (رسم يدوي)")
    st.write("استخدم أداة الرسم الموجودة أعلى يسار الخريطة لرسم مسار خط مخصص:")
    
    new_price = st.number_input("أدخل سعر المتر الطولي للخط المرسوم الجديد (ريال):", min_value=0.0, value=1000.0, key="new_p")

with col2:
    st.subheader("🗺️ الخريطة التفاعلية (منطقة الرياض)")
    
    # إنشاء الخريطة والبدء بزوم 18 كما طلبت في الرياض
    m = folium.Map(location=[RIYADH_LAT, RIYADH_LON], zoom_start=START_ZOOM, control_scale=True)
    
    # إضافة أداة الرسم للتطبيق
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
    
    # إسقاط خطوط الشبكة على الخريطة
    for line in network_lines:
        if line['geometry'].geom_type == 'LineString':
            coords = [(p[1], p[0]) for p in line['geometry'].coords]
            folium.PolyLine(
                locations=coords,
                color='blue',
                weight=4,
                opacity=0.8,
                popup=f"<div style='text-align:right; direction:rtl;'>📌 <b>رقم الخط (Index): {line['index']}</b><br>📏 الطول: {line['length']:.2f} متر</div>"
            ).add_to(m)
        elif line['geometry'].geom_type == 'MultiLineString':
            for part in line['geometry'].geoms:
                coords = [(p[1], p[0]) for p in part.coords]
                folium.PolyLine(
                    locations=coords,
                    color='blue',
                    weight=4,
                    opacity=0.8,
                    popup=f"<div style='text-align:right; direction:rtl;'>📌 <b>رقم الخط (Index): {line['index']}</b><br>📏 الطول: {line['length']:.2f} متر</div>"
                ).add_to(m)
            
    # تشغيل الخريطة التفاعلية وعرضها
    map_data = st_folium(m, width="100%", height=650)
    
    # التحقق من وجود رسم مخصص جديد من المستخدم
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
                st.success("📐 تم رصد خط مرسوم على الخريطة بنجاح!")
                st.write(f"📏 طول المسار المرسوم: **{total_drawn_length:,.2f} متر**")
                st.metric(label="💰 التكلفة المقدرة للمسار المرسوم", value=f"{total_drawn_cost:,.2f} ريال")

# إضافة التوقيع المرئي الثابت لحفظ الفكرة والحقوق أسفل يمين الشاشة
st.markdown(f'<div class="footer-text">📐 فكرة وتطوير المهندس: <b>Ahmed Adam</b></div>', unsafe_allow_html=True)
