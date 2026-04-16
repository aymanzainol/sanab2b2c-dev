import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import json
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# 1. إعدادات الصفحة والتنسيق
# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="لوحة قطاع المشاعر 2026 🚀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');

    .stApp { 
        background-color: #0e1117; 
        color: #ffffff; 
        direction: rtl !important; 
    }

    h1, h2, h3, h4, h5, h6, .stMarkdown, p, span, label {
        text-align: right !important;
        direction: rtl !important;
        font-family: 'Cairo', sans-serif !important;
    }

    div.stButton { display: flex; justify-content: flex-start; align-items: center; margin-bottom: 12px; }
    .stButton > button {
        width: 185px !important;
        height: 110px !important;
        border-radius: 15px !important; 
        background-color: #1f2937 !important;
        border: 2px solid #374151 !important; 
        color: white !important;
        display: flex !important; 
        flex-direction: column !important;
        justify-content: center !important; 
        align-items: center !important;
        text-align: center !important; 
    }
    .stButton > button:hover { border-color: #3b82f6 !important; transform: scale(1.05); }

    .observer-notes-box {
        background-color: #1e1e1e; padding: 20px; border-radius: 15px;
        border-right: 6px solid #eab308; position: relative;
        margin-bottom: 20px; color: #e5e7eb !important;
        text-align: right !important;
    }

    .score-circle {
        position: absolute; left: 20px; top: 20px;
        width: 75px; height: 75px; border-radius: 50%;
        background: #111827; border: 4px solid #eab308;
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; font-size: 1.2rem; color: #eab308;
    }

    .checklist-item-popup { 
        background-color: #450a0a; padding: 10px; border-radius: 8px; 
        margin-bottom: 6px; border-right: 4px solid #ef4444; color: #fecaca !important;
        text-align: right !important;
    }

    /* ── تنسيقات صفحة الإدخال ── */
    .form-card {
        background-color: #1f2937;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        border: 1px solid #374151;
    }
    .section-title {
        font-family: 'Cairo', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #93c5fd;
        border-bottom: 1px solid #374151;
        padding-bottom: 8px;
        margin-bottom: 16px;
        text-align: right;
    }
    .company-sana   { border-right: 5px solid #b91c1c !important; }
    .company-rakeen { border-right: 5px solid #92400e !important; }

    .success-banner {
        background: linear-gradient(135deg, #065f46, #047857);
        border-radius: 12px; padding: 20px;
        text-align: center; font-size: 1.3rem;
        font-weight: bold; color: white;
        margin: 20px 0;
    }
    .stSelectbox > div { direction: rtl !important; }
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 2. إعدادات الاتصال
# ──────────────────────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1pN31S92Xa4m-hilE-e56F9T6LuOhZLwPq6YWEnWP_xk/export?format=csv"

# ضع رابط Apps Script Web App هنا بعد نشره
# (راجع ملف apps_script.js للتعليمات)
APPS_SCRIPT_URL = st.secrets.get("APPS_SCRIPT_URL", "")


# ──────────────────────────────────────────────────────────────
# 3. معالجة البيانات
# ──────────────────────────────────────────────────────────────
def analyze_readiness(row, checklist_cols):
    scores, missing_items = [], []
    for col in checklist_cols:
        val = str(row[col]).strip()
        if not val or val.lower() == 'nan' or val == "":
            continue
        current_score = None
        if "عدد" in col:
            try:
                num_val = float(val.replace('%', ''))
                current_score = 100.0 if num_val >= 1 else 0.0
            except:
                pass
        if current_score is None:
            if '%' in val:
                try:
                    current_score = float(val.replace('%', ''))
                except:
                    pass
            elif any(p in val for p in ['نعم', 'مطابق', 'مكتمل', 'تم', 'يوجد', 'متوفر', 'جاهز', 'صح', '100']):
                current_score = 100.0
            elif any(n in val for n in ['لا', 'غير', 'لم', 'ناقص', 'خطأ', '0']):
                current_score = 0.0
        if current_score is not None:
            scores.append(current_score)
            if current_score < 100:
                missing_items.append(f"{col} ({int(current_score)}%)")
    return pd.Series([round(np.mean(scores)) if scores else 0, " | ".join(missing_items)])


@st.cache_data(ttl=20)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip() for col in df.columns]
    df['Unified_ID'] = np.where(
        df['شركة'].str.contains('ركين', na=False),
        df.iloc[:, 5], df.iloc[:, 6]
    )
    df['Unified_ID']      = df['Unified_ID'].fillna("غير معرف").astype(str).str.strip()
    df['Assistant_Name']  = df.iloc[:, 1].fillna("غير مسجل")
    df['Supervisor_Name'] = np.where(
        df['شركة'].str.contains('ركين', na=False),
        df.iloc[:, 2], df.iloc[:, 3]
    )
    df['Supervisor_Name'] = df['Supervisor_Name'].fillna("غير مسجل")

    if 'طابع زمني' in df.columns:
        df['temp_time'] = df['طابع زمني'].astype(str).str.replace('م', 'PM').str.replace('ص', 'AM')
        df['dt_object'] = pd.to_datetime(df['temp_time'], errors='coerce')
        df = df.sort_values(by='dt_object', ascending=False)

    checklist_cols = df.columns[7:37]
    df[['Overall_Score', 'Missing_Details']] = df.apply(
        lambda row: analyze_readiness(row, checklist_cols), axis=1
    )
    df_latest = df.drop_duplicates(subset=['Unified_ID'], keep='first')
    return df, df_latest, checklist_cols


# ──────────────────────────────────────────────────────────────
# 4. النافذة المنبثقة للتفاصيل
# ──────────────────────────────────────────────────────────────
@st.dialog("تفاصيل جاهزية الموقع 🏕️")
def show_tent_details(tent_id, full_df):
    tent_history = full_df[full_df['Unified_ID'] == tent_id].copy()
    st.markdown(f"<h2 style='text-align: right;'>موقع: {tent_id}</h2>", unsafe_allow_html=True)

    history_options = tent_history['طابع زمني'].tolist()
    selected_time   = st.selectbox("🕒 عرض تقرير تاريخ:", history_options)
    row   = tent_history[tent_history['طابع زمني'] == selected_time].iloc[0]
    score = int(row['Overall_Score'])

    st.markdown(f"""
    <div class='observer-notes-box'>
        <div class='score-circle'>{score}%</div>
        <div class='notes-content'>
            <b>المعاون:</b> {row['Assistant_Name']}<br>
            <b>المراقب:</b> {row['Supervisor_Name']}
            <hr style='border: 0; border-top: 1px solid #374151; margin: 10px 0;'>
            <b>ملاحظات المراقب:</b><br>
            {row['ملاحظات المراقب'] if pd.notna(row['ملاحظات المراقب']) and str(row['ملاحظات المراقب']).strip() != "" else 'لا توجد ملاحظات.'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    missing_list = [item.strip() for item in str(row['Missing_Details']).split('|') if item.strip()]
    if missing_list:
        st.markdown("<h3 style='text-align: right;'>⚠️ النواقص</h3>", unsafe_allow_html=True)
        for item in missing_list:
            st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 5. صفحة إدخال بيانات المراقب (الجديدة)
# ──────────────────────────────────────────────────────────────
def observer_entry_page(checklist_cols, df_latest):

    st.markdown("<h2 style='text-align:right;'>📝 إدخال تقرير المراقب</h2>", unsafe_allow_html=True)

    # ── اختيار الشركة ──
    company_choice = st.radio(
        "اختر الشركة:",
        ["🔴 سنا", "🟤 ركين"],
        horizontal=True
    )
    is_sana   = "سنا"   in company_choice
    company   = "سنا"   if is_sana else "ركين"
    card_cls  = "company-sana" if is_sana else "company-rakeen"
    icon      = "🔴" if is_sana else "🟤"

    # المواقع المتاحة لتلك الشركة
    existing_ids = sorted(
        df_latest[df_latest['شركة'].str.contains(company, na=False)]['Unified_ID'].tolist()
    )

    st.markdown(f"<div class='form-card {card_cls}'>", unsafe_allow_html=True)

    # ── بيانات أساسية ──
    st.markdown("<div class='section-title'>📋 البيانات الأساسية</div>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        site_id_mode = st.radio("رقم الموقع:", ["اختيار موجود", "إدخال جديد"], horizontal=True, key="site_mode")
    with col_b:
        if site_id_mode == "اختيار موجود":
            site_id = st.selectbox("رقم الموقع:", existing_ids, key="site_select")
        else:
            site_id = st.text_input("رقم الموقع الجديد:", key="site_new", placeholder="مثال: T-201")
    with col_c:
        supervisor_name = st.text_input("اسم المراقب:", key="sup_name", placeholder="الاسم الكامل")

    assistant_name = st.text_input("اسم المعاون:", key="asst_name", placeholder="الاسم الكامل")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── قائمة التحقق ──
    st.markdown("<div class='form-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>✅ قائمة التحقق</div>", unsafe_allow_html=True)

    checklist_responses = {}
    cols_per_row = 2
    col_list     = list(checklist_cols)
    
    for i in range(0, len(col_list), cols_per_row):
        row_cols = st.columns(cols_per_row)
        for j, col_name in enumerate(col_list[i : i + cols_per_row]):
            with row_cols[j]:
                if "عدد" in col_name:
                    checklist_responses[col_name] = st.number_input(
                        col_name, min_value=0, step=1, key=f"chk_{col_name}"
                    )
                else:
                    checklist_responses[col_name] = st.selectbox(
                        col_name,
                        options=["نعم", "لا", "جزئي"],
                        key=f"chk_{col_name}"
                    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── ملاحظات ──
    st.markdown("<div class='form-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📝 ملاحظات المراقب</div>", unsafe_allow_html=True)
    observer_notes = st.text_area("ملاحظاتك:", height=120, key="obs_notes",
                                  placeholder="أي ملاحظات إضافية على الموقع...")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── إرسال ──
    st.markdown("<br>", unsafe_allow_html=True)
    submit_btn = st.button(f"{icon} إرسال تقرير موقع {site_id}", use_container_width=True, type="primary")

    if submit_btn:
        # التحقق من الحقول الإلزامية
        if not site_id or not supervisor_name or not assistant_name:
            st.error("⚠️ يرجى تعبئة رقم الموقع واسم المراقب واسم المعاون.")
            return

        # بناء الصف بنفس ترتيب أعمدة الـ Sheet
        timestamp = datetime.now().strftime("%Y/%m/%d %I:%M:%S %p")

        # الأعمدة: [timestamp, assistant, sup_rakeen, sup_sana, company, id_rakeen, id_sana, ...checklist, notes]
        row_data = [
            timestamp,                                    # col 0 – طابع زمني
            assistant_name,                               # col 1 – المعاون
            supervisor_name if not is_sana else "",       # col 2 – مراقب ركين
            supervisor_name if is_sana     else "",       # col 3 – مراقب سنا
            company,                                      # col 4 – الشركة
            site_id if not is_sana else "",               # col 5 – رقم ركين
            site_id if is_sana     else "",               # col 6 – رقم سنا
        ]

        for col_name in col_list:
            row_data.append(str(checklist_responses.get(col_name, "")))

        row_data.append(observer_notes)                  # ملاحظات المراقب

        # ── إرسال للـ Apps Script ──
        if not APPS_SCRIPT_URL:
            st.warning("⚠️ لم يتم ضبط APPS_SCRIPT_URL في الـ secrets بعد.")
            with st.expander("📋 البيانات الجاهزة (يمكن نسخها يدوياً)"):
                st.json(row_data)
            return

        try:
            with st.spinner("جاري الإرسال..."):
                resp = requests.post(
                    APPS_SCRIPT_URL,
                    data=json.dumps({"row": row_data}),
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
            if resp.status_code == 200:
                st.markdown(
                    f"<div class='success-banner'>✅ تم إرسال تقرير الموقع {site_id} بنجاح!</div>",
                    unsafe_allow_html=True
                )
                # مسح cache لتحديث البيانات
                st.cache_data.clear()
            else:
                st.error(f"❌ فشل الإرسال. الكود: {resp.status_code}")
        except Exception as ex:
            st.error(f"❌ خطأ في الاتصال: {ex}")


# ──────────────────────────────────────────────────────────────
# 6. العرض الرئيسي
# ──────────────────────────────────────────────────────────────
try:
    df_full, df_latest, checklist_cols = load_data()

    st.markdown("<h1 style='text-align: right;'>🚀 لوحة متابعة قطاع المشاعر</h1>", unsafe_allow_html=True)

    page = st.radio(
        "اختر العرض:",
        ["📊 التحليل العام", "🏕️ خريطة المواقع", "📝 إدخال تقرير المراقب"],
        horizontal=True
    )

    st.divider()

    # ── صفحة التحليل ──
    if page == "📊 التحليل العام":
        st.markdown("<h2 style='text-align: right;'>📊 الإحصائيات العامة للمخيمات</h2>", unsafe_allow_html=True)

        for company, color in [("سنا", "#b91c1c"), ("ركين", "#8b5e3c")]:
            sub_df = df_latest[df_latest['شركة'].str.contains(company, na=False)]
            st.markdown(
                f"<h3 style='text-align: right;'>{'🔴' if company=='سنا' else '🟤'} شركة {company}</h3>",
                unsafe_allow_html=True
            )
            if not sub_df.empty:
                c1, c2 = st.columns([1, 4])
                avg = round(sub_df['Overall_Score'].mean())
                c1.metric("متوسط الإنجاز", f"{avg}%")
                fig = px.bar(
                    sub_df, x='Unified_ID', y='Overall_Score',
                    color_discrete_sequence=[color], text='Overall_Score'
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color="white",
                    xaxis_title="رقم الموقع",
                    yaxis_title="نسبة الجاهزية (%)"
                )
                c2.plotly_chart(fig, use_container_width=True)

    # ── صفحة الخريطة ──
    elif page == "🏕️ خريطة المواقع":
        st.markdown("<h2 style='text-align: right;'>🏕️ خريطة المواقع</h2>", unsafe_allow_html=True)
        df_sorted = df_latest.sort_values(by=['شركة', 'Unified_ID'])
        grid_cols = st.columns(6)
        for idx, (_, row) in enumerate(df_sorted.iterrows()):
            icon = "🔴" if "سنا" in str(row['شركة']) else "🟤"
            with grid_cols[idx % 6]:
                label = f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%"
                if st.button(label, key=f"btn_{row['Unified_ID']}"):
                    show_tent_details(row['Unified_ID'], df_full)

    # ── صفحة الإدخال ──
    elif page == "📝 إدخال تقرير المراقب":
        observer_entry_page(checklist_cols, df_latest)

except Exception as e:
    st.error(f"⚠️ خطأ: {e}")
