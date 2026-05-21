"""
نظام تحليل شبكات السيول
Eng. Ahmed Adam — v6.0 — 2025
"""
import streamlit as st, folium, json, os, tempfile, zipfile
import numpy as np, pandas as pd
from folium.plugins import Draw, MeasureControl
from streamlit_folium import st_folium
from shapely.geometry import shape

# ── Page ──────────────────────────────────────────────────────
st.set_page_config(page_title="شبكات السيول", page_icon="🌊",
                   layout="wide", initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap');
*{font-family:'Tajawal',sans-serif!important;direction:rtl}
.main{background:#f0f4f8}

.hdr{background:linear-gradient(135deg,#1a3a5c,#0d6efd,#00b4d8);
     border-radius:14px;padding:20px 30px;text-align:center;
     color:#fff;box-shadow:0 6px 24px rgba(13,110,253,.3);margin-bottom:18px}
.hdr h1{font-size:1.9rem;font-weight:800;margin:0}
.hdr p{font-size:.92rem;opacity:.85;margin:6px 0 0}

.card{background:#fff;border-radius:12px;padding:14px 18px;
      box-shadow:0 2px 8px rgba(0,0,0,.07);border-right:5px solid #0d6efd;
      margin-bottom:10px}
.card.g{border-right-color:#43a047}
.card.o{border-right-color:#fb8c00}
.card .lb{color:#6b7280;font-size:.82rem}
.card .vl{color:#1a3a5c;font-size:1.5rem;font-weight:800}
.card.g .vl{color:#1b5e20} .card.o .vl{color:#e65100}
.card .un{color:#0d6efd;font-size:.8rem;font-weight:600}
.card.g .un{color:#43a047} .card.o .un{color:#fb8c00}

.result{background:linear-gradient(135deg,#e8f5e9,#c8e6c9);
        border:2px solid #43a047;border-radius:12px;
        padding:18px 22px;text-align:center;margin-top:12px}
.result .rv{font-size:2rem;font-weight:800;color:#1b5e20}
.result .rs{font-size:.84rem;color:#388e3c;margin-top:4px;line-height:1.8}

.ibox{background:#e3f2fd;border:1px solid #90caf9;border-radius:10px;
      padding:12px 16px;font-size:.88rem;color:#1565c0;line-height:1.9;margin:8px 0}

.pguide{background:#fff8e1;border:1px solid #ffe082;border-radius:10px;
        padding:12px 16px;margin:8px 0;font-size:.86rem}
.pguide .ph{font-size:.92rem;font-weight:800;color:#e65100;
            border-bottom:1px dashed #ffcc80;padding-bottom:6px;margin-bottom:8px}
.pguide .pr{display:flex;justify-content:space-between;
            align-items:center;padding:4px 0;border-bottom:1px solid #fff3cd}
.pguide .pr:last-of-type{border:none}
.pguide .pn{color:#5d4037;font-weight:600;flex:1;font-size:.84rem}
.pguide .pb{background:#e65100;color:#fff;border-radius:6px;
            padding:2px 9px;font-size:.78rem;font-weight:700}

.stitle{font-size:1.05rem;font-weight:700;color:#1a3a5c;
        border-bottom:2px solid #e2e8f0;padding-bottom:8px;margin-bottom:12px}

section[data-testid="stSidebar"]{width:340px!important;min-width:340px!important}
section[data-testid="stSidebar"]>div:first-child{width:340px!important;padding:1rem!important}

.sig{background:linear-gradient(135deg,#0d1b2a,#1a3a5c,#0d6efd);
     border-radius:12px;padding:16px;margin-top:14px;text-align:center;
     box-shadow:0 4px 16px rgba(13,110,253,.25)}
.sig .sn{font-size:1.15rem;font-weight:800;color:#fff;margin-top:4px}
.sig .ss{font-size:.78rem;color:rgba(255,255,255,.6);margin-top:3px}
.sig hr{border:0;border-top:1px solid rgba(255,255,255,.15);margin:8px 0}

div[data-testid="stButton"]>button{
  width:100%;background:linear-gradient(135deg,#0d6efd,#0077b6);
  color:#fff;border:none;border-radius:10px;padding:11px;
  font-size:1rem;font-weight:700;box-shadow:0 4px 10px rgba(13,110,253,.3)}
footer{visibility:hidden}
</style>""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────
RIYADH = [24.7136, 46.6753]
PRICES = [
    ("أنابيب بقطر 1400 ملم",       4_004.0),
    ("قناة صندوقية (1.8×1.4) م",   9_336.0),
    ("قناة مفتوحة (12×1.5) م",    13_052.0),
]

# ── Helpers ───────────────────────────────────────────────────
def haversine(coords):
    if len(coords) < 2: return 0.0
    a = np.array(coords, dtype=float)
    R = 6_371_000.0
    lo, la = np.radians(a[:,0]), np.radians(a[:,1])
    dph, dlm = np.diff(la), np.diff(lo)
    x = np.sin(dph/2)**2 + np.cos(la[:-1])*np.cos(la[1:])*np.sin(dlm/2)**2
    return float(R*2*np.sum(np.arctan2(np.sqrt(np.clip(x,0,1)),
                                        np.sqrt(np.clip(1-x,0,1)))))

def geom_length(g):
    try:
        s = shape(g)
        if s.geom_type == "LineString":    return round(haversine(list(s.coords)),2)
        if s.geom_type == "MultiLineString": return round(sum(haversine(list(p.coords)) for p in s.geoms),2)
    except: pass
    return 0.0

def label_col(df):
    for c in ("name","Name","NAME","id","ID","FID","OBJECTID"):
        if c in df.columns: return c
    return None

# ── File Loading ──────────────────────────────────────────────
def fc_to_df(fc):
    ok = {"LineString","MultiLineString"}
    feats = [f for f in fc.get("features",[])
             if f.get("geometry") and f["geometry"].get("type") in ok]
    if not feats: return None
    rows = []
    for i,f in enumerate(feats):
        p = f.get("properties") or {}
        r = {"_i":i,"length_m":geom_length(f["geometry"]),"_g":json.dumps(f["geometry"])}
        r.update({k:(v.decode("utf-8","ignore") if isinstance(v,bytes) else v) for k,v in p.items()})
        rows.append(r)
    df = pd.DataFrame(rows).set_index("_i")
    df.index.name = "رقم"
    return df

@st.cache_data(show_spinner=False)
def load_file(data, name):
    n = name.lower()
    try:
        if n.endswith((".geojson",".json")):
            return fc_to_df(json.loads(data.decode("utf-8")))
        if n.endswith(".zip"):
            import shapefile
            with tempfile.TemporaryDirectory() as tmp:
                zp = os.path.join(tmp,"u.zip")
                open(zp,"wb").write(data)
                zipfile.ZipFile(zp).extractall(tmp)
                shps=[os.path.join(r,f) for r,_,fs in os.walk(tmp) for f in fs if f.endswith(".shp")]
                if not shps: st.error("❌ لا يوجد .shp في الـ ZIP"); return None
                try:    sf=shapefile.Reader(shps[0],encoding="utf-8")
                except: sf=shapefile.Reader(shps[0],encoding="cp1256")
                flds=[f[0] for f in sf.fields[1:]]
                feats=[{"type":"Feature",
                        "geometry":sr.shape.__geo_interface__,
                        "properties":{k:(v.decode("utf-8","ignore") if isinstance(v,bytes) else v)
                                      for k,v in zip(flds,sr.record)}}
                       for sr in sf.shapeRecords()]
                return fc_to_df({"type":"FeatureCollection","features":feats})
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
    return None

# ── Map Builder ───────────────────────────────────────────────
def make_map(df=None, sel=None, draw=False, zoom=18):
    sel = set(sel or [])
    m = folium.Map(location=RIYADH, zoom_start=zoom, tiles=None,
                   control_scale=True, prefer_canvas=True)
    folium.TileLayer("OpenStreetMap",  name="شارع",  show=True).add_to(m)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="جوي", show=False).add_to(m)

    if df is not None and len(df):
        lc = label_col(df)

        def _fc(rows, color, w):
            return {"type":"FeatureCollection","features":[{
                "type":"Feature",
                "geometry":json.loads(r["_g"]),
                "properties":{"رقم":str(i)}
                } for i,r in rows.iterrows()]}

        normal = df[~df.index.isin(sel)]
        if len(normal):
            folium.GeoJson(_fc(normal,"#0077b6",2.5),name="الشبكة",
                style_function=lambda f:{"color":"#0077b6","weight":2.5,"opacity":.85},
                tooltip=folium.GeoJsonTooltip(
                    fields=["رقم"],aliases=["رقم الخط:"],
                    sticky=False,style="font-family:Tajawal;direction:rtl;font-size:14px;font-weight:700"
                )).add_to(m)
        if sel:
            folium.GeoJson(_fc(df[df.index.isin(sel)],"#e63946",5),name="مختار",
                style_function=lambda f:{"color":"#e63946","weight":5,"opacity":1},
                tooltip=folium.GeoJsonTooltip(
                    fields=["رقم"],aliases=["رقم الخط:"],
                    sticky=False,style="font-family:Tajawal;direction:rtl;font-size:14px;font-weight:700"
                )).add_to(m)

        # fit bounds
        pts=[]
        for _,r in df.iterrows():
            try:
                b=shape(json.loads(r["_g"])).bounds
                pts+=[[b[1],b[0]],[b[3],b[2]]]
            except: pass
        if pts: m.fit_bounds([[min(p[0] for p in pts),min(p[1] for p in pts)],
                               [max(p[0] for p in pts),max(p[1] for p in pts)]])

    if draw:
        Draw(draw_options={"polyline":{"shapeOptions":{"color":"#ff6b35","weight":4}},
             "polygon":False,"rectangle":False,"circle":False,
             "marker":False,"circlemarker":False},
             edit_options={"edit":True,"remove":True}).add_to(m)
    MeasureControl(position="topleft",primary_length_unit="meters").add_to(m)
    folium.LayerControl(position="topright").add_to(m)
    return m

# ── Price Widgets ─────────────────────────────────────────────
PGUIDE_HTML = """
<div class="pguide">
  <div class="ph">💡 الأسعار الإرشادية (ريال / متر)</div>
  <div class="pr"><span class="pn">أنابيب Ø 1400 ملم</span><span class="pb">4,004 ﷼</span></div>
  <div class="pr"><span class="pn">قناة صندوقية (1.8×1.4)م</span><span class="pb">9,336 ﷼</span></div>
  <div class="pr"><span class="pn">قناة مفتوحة (12×1.5)م</span><span class="pb">13,052 ﷼</span></div>
  <div style="font-size:.74rem;color:#8d6e63;margin-top:6px">
  ⚠️ أسعار إرشادية تقريبية — تختلف حسب الموقع والمواصفات
  </div>
</div>"""

def quick_btns(prefix):
    cols = st.columns(3)
    labels = ["أنابيب","صندوقية","مفتوحة"]
    for i,(col,(name,price)) in enumerate(zip(cols,PRICES)):
        if col.button(f"{labels[i]}\n{price:,.0f}﷼", key=f"{prefix}q{i}", help=name):
            st.session_state[f"{prefix}p"] = price

def price_inp(prefix, key):
    return st.number_input("💲 السعر / متر (ريال)",
        min_value=0.0, value=float(st.session_state.get(f"{prefix}p",100)),
        step=10.0, format="%.0f", key=key)

# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="stitle">📁 رفع الملف</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("GeoJSON أو ZIP (Shapefile)",
                                type=["geojson","json","zip"])
    st.markdown("---")
    st.markdown("""<div class="ibox">
    <b>💡 طريقة الاستخدام:</b><br>
    ① ارفع ملف GeoJSON أو ZIP<br>
    ② استعرض الخريطة<br>
    ③ اختر الخطوط واحسب التكلفة<br>
    ④ أو ارسم خطاً جديداً
    </div>""", unsafe_allow_html=True)
    st.markdown(PGUIDE_HTML, unsafe_allow_html=True)
    st.markdown("""
    <div class="sig">
      <div style="font-size:2rem">👷</div>
      <div class="sn">Eng: Ahmed Adam</div>
      <div class="ss">🌊 نظام تحليل شبكات السيول</div>
      <hr>
      <div class="ss">GIS Flood Network · v6.0 · © 2025</div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="hdr">
  <h1>🌊 نظام تحليل شبكات السيول</h1>
  <p>حساب الأطوال · تقدير التكاليف · نتائج سريعة</p>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  NO FILE — Welcome
# ══════════════════════════════════════════════════════════════
if not uploaded:
    c1,c2 = st.columns([1,2])
    with c1:
        st.markdown("""
        <div style="background:#fff;border-radius:14px;padding:28px 20px;
                    box-shadow:0 2px 12px rgba(0,0,0,.08)">
          <div style="font-size:2.8rem;text-align:center">🗂️</div>
          <h3 style="color:#1a3a5c;text-align:center;font-size:1.1rem;margin:10px 0 8px">
            ارفع الملف للبدء</h3>
          <div class="ibox">
          ارفع <b>GeoJSON</b> مباشرة<br>
          أو <b>ZIP</b> يحتوي Shapefile<br>
          من الشريط الجانبي
          </div>
          <div style="background:#f8fafc;border-radius:9px;padding:11px;
                      font-size:.83rem;color:#64748b;border-right:3px solid #0d6efd;margin-top:10px">
          📌 <b>SHP → ZIP:</b><br>
          اختر المجلد ← كليك يمين ← ضغط
          </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st_folium(make_map(zoom=11), width="100%", height=420,
                  returned_objects=[], key="m0")

# ══════════════════════════════════════════════════════════════
#  FILE LOADED
# ══════════════════════════════════════════════════════════════
else:
    raw = uploaded.read()
    with st.spinner("⏳ جاري قراءة البيانات..."):
        df = load_file(raw, uploaded.name)

    if df is None:
        st.stop()

    total_m = float(df["length_m"].sum())
    n       = len(df)

    # Stats
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="card"><div class="lb">عدد الخطوط</div>'
                f'<div class="vl">{n:,}</div><div class="un">خط</div></div>',
                unsafe_allow_html=True)
    c2.markdown(f'<div class="card g"><div class="lb">الطول الإجمالي</div>'
                f'<div class="vl">{total_m/1000:.2f}</div>'
                f'<div class="un">كم ({total_m:,.0f} م)</div></div>',
                unsafe_allow_html=True)
    c3.markdown(f'<div class="card"><div class="lb">متوسط الطول</div>'
                f'<div class="vl">{df["length_m"].mean():.0f}</div>'
                f'<div class="un">متر</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="card o"><div class="lb">أطول خط</div>'
                f'<div class="vl">{df["length_m"].max():,.0f}</div>'
                f'<div class="un">متر</div></div>', unsafe_allow_html=True)

    t1,t2,t3,t4 = st.tabs([
        "🗺️ الخريطة","💰 حساب التكلفة","✏️ رسم خط جديد","📊 الجدول"])

    # ── Tab 1: Map ────────────────────────────────────────────
    with t1:
        st.markdown('<div class="stitle">🗺️ خريطة شبكة السيول</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="ibox">مرّر على أي خط لعرض رقمه وطوله · '
                    'غيّر نوع الخريطة من أعلى اليمين</div>', unsafe_allow_html=True)
        st_folium(make_map(df), width="100%", height=530,
                  returned_objects=[], key="m1")

    # ── Tab 2: Cost ───────────────────────────────────────────
    with t2:
        st.markdown('<div class="stitle">💰 حساب تكلفة خطوط من الشبكة</div>',
                    unsafe_allow_html=True)
        cc, cm = st.columns([2,3])

        with cc:
            st.markdown('<div class="ibox">① اختر الخطوط<br>② اختر السعر أو أدخله<br>'
                        '③ اضغط احسب</div>', unsafe_allow_html=True)
            st.markdown(PGUIDE_HTML, unsafe_allow_html=True)
            quick_btns("t2")
            st.markdown("---")

            lc = label_col(df)
            opts = ([f"{i} | {str(r[lc])[:25]} ({r['length_m']:,.0f}م)" for i,r in df.iterrows()]
                    if lc else [f"خط {i} ({r['length_m']:,.0f}م)" for i,r in df.iterrows()])

            sel_lbl = st.multiselect("اختر الخطوط:", opts,
                                     placeholder="ابحث أو اختر...", key="ms2")
            sel_idx = []
            for lb in sel_lbl:
                try:
                    sel_idx.append(int(lb.split("|")[0].strip() if "|" in lb
                                       else lb.replace("خط ","").split(" ")[0]))
                except: pass

            if sel_idx:
                ts = float(df.loc[sel_idx,"length_m"].sum())
                st.markdown(f'<div class="card g">'
                            f'<div class="lb">✅ {len(sel_idx)} خط مختار</div>'
                            f'<div class="vl">{ts:,.0f}</div>'
                            f'<div class="un">متر = {ts/1000:.2f} كم</div></div>',
                            unsafe_allow_html=True)
            else:
                ts = 0.0

            p2 = price_inp("t2","pi2")
            if st.button("🧮 احسب التكلفة", key="cb2"):
                if ts > 0:
                    cost = ts * p2
                    detail = ""
                    if len(sel_idx) > 1:
                        hr = '<hr style="border:0;border-top:1px solid #a5d6a7;margin:6px 0">'
                        detail = hr + "".join(
                            f"• خط {i}: {df.loc[i,'length_m']:,.0f}م × {p2:,.0f} = "
                            f"{df.loc[i,'length_m']*p2:,.0f} ﷼<br>"
                            for i in sel_idx)
                    st.markdown(f'<div class="result">'
                                f'<div class="rv">{cost:,.0f} ﷼</div>'
                                f'<div class="rs">{ts:,.0f}م × {p2:,.0f} ﷼/م'
                                f' | {len(sel_idx)} خط{detail}</div></div>',
                                unsafe_allow_html=True)
                else:
                    st.warning("⚠️ اختر خطاً واحداً على الأقل")

        with cm:
            st_folium(make_map(df, sel=sel_idx), width="100%", height=540,
                      returned_objects=[], key="m2")

    # ── Tab 3: Draw ───────────────────────────────────────────
    with t3:
        st.markdown('<div class="stitle">✏️ ارسم خطاً جديداً</div>',
                    unsafe_allow_html=True)
        dm, dc = st.columns([3,2])

        with dm:
            st.markdown('<div class="ibox">'
                        '① انقر 🖊 في أعلى يسار الخريطة<br>'
                        '② انقر لإضافة نقاط · انقر مرتين للإنهاء<br>'
                        '③ يظهر الطول تلقائياً</div>', unsafe_allow_html=True)
            md = st_folium(make_map(df, draw=True), width="100%", height=500,
                           returned_objects=["all_drawings"], key="m3")

        with dc:
            st.markdown(PGUIDE_HTML, unsafe_allow_html=True)
            quick_btns("t3")
            st.markdown("---")

            drw = [d for d in ((md or {}).get("all_drawings") or [])
                   if d.get("geometry",{}).get("type")=="LineString"
                   and len(d["geometry"].get("coordinates",[]))>=2]

            if drw:
                lens = [haversine(d["geometry"]["coordinates"]) for d in drw]
                dt   = sum(lens)
                st.markdown(f'<div class="card g">'
                            f'<div class="lb">✏️ {len(drw)} خط مرسوم</div>'
                            f'<div class="vl">{dt:,.0f}</div>'
                            f'<div class="un">متر = {dt/1000:.2f} كم</div></div>',
                            unsafe_allow_html=True)
                if len(lens)>1:
                    with st.expander("تفاصيل الخطوط المرسومة"):
                        for i,l in enumerate(lens,1):
                            st.markdown(f"• خط {i}: **{l:,.0f} م**")
            else:
                dt = 0.0
                st.markdown('<div style="text-align:center;padding:24px;color:#94a3b8">'
                            '<div style="font-size:2rem">✏️</div>'
                            '<p>ارسم خطاً لظهور طوله</p></div>',
                            unsafe_allow_html=True)

            p3 = price_inp("t3","pi3")
            if st.button("🧮 احسب التكلفة", key="cb3"):
                if dt > 0:
                    st.markdown(f'<div class="result">'
                                f'<div class="rv">{dt*p3:,.0f} ﷼</div>'
                                f'<div class="rs">{dt:,.0f}م × {p3:,.0f} ﷼/م'
                                f' | {len(drw)} خط</div></div>',
                                unsafe_allow_html=True)
                else:
                    st.warning("⚠️ ارسم خطاً أولاً")

    # ── Tab 4: Table ─────────────────────────────────────────
    with t4:
        st.markdown('<div class="stitle">📊 جدول البيانات</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="card g" style="display:inline-block;min-width:260px">'
                    f'<div class="lb">مجموع الأطوال</div>'
                    f'<div class="vl">{total_m:,.0f} م</div>'
                    f'<div class="un">= {total_m/1000:.2f} كم</div></div>',
                    unsafe_allow_html=True)
        show = df[[c for c in df.columns if c!="_g"]].copy()
        show["length_m"] = show["length_m"].round(0).astype(int)
        st.dataframe(show, use_container_width=True, height=420)
        st.download_button("⬇️ تحميل CSV",
            data=show.to_csv(index=True).encode("utf-8-sig"),
            file_name="flood_network.csv", mime="text/csv", key="dl")
