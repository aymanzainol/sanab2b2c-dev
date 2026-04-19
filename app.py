import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. إعدادات الصفحة والتنسيق
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
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف معالجة البيانات
def analyze_readiness(row, checklist_cols):
    scores = []
    missing_items = []
    for col in checklist_cols:
        if col not in row: continue
        val = str(row[col]).strip()
        if not val or val.lower() == 'nan' or val == "": continue
        current_score = None
        if "عدد" in col:
            try:
                num_val = float(val.replace('%', ''))
                current_score = 100.0 if num_val >= 1 else 0.0
            except: pass
        if current_score is None:
            if '%' in val:
                try: current_score = float(val.replace('%', ''))
                except: pass
            elif any(p in val for p in ['نعم', 'مطابق', 'مكتمل', 'تم', 'يوجد', 'متوفر', 'جاهز', 'صح', '100']): current_score = 100.0
            elif any(n in val for n in ['لا', 'غير', 'لم', 'ناقص', 'خطأ', '0']): current_score = 0.0
        if current_score is not None:
            scores.append(current_score)
            if current_score < 100: 
                missing_items.append(f"{col} ({int(current_score)}%)")
    return pd.Series([round(np.mean(scores)) if scores else 0, " | ".join(missing_items)])

# الرابط الخاص بك (تأكد أنه رابط Google Sheet وليس Form للتشغيل الفعلي)
SHEET_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeLc_hzu18NMzwAdVAm5Rk2qk4oBmNnh4Z4P8F8g05LOLnCBw/viewform?usp=sharing&ouid=104994008626485786659"

@st.cache_data(ttl=20)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip().replace('\n', '') for col in df.columns]
    
    # حل مشكلة "المراقب .1" - البحث عن أي عمود يحتوي على كلمة مراقب
    moraqeb_cols = [c for c in df.columns if 'المراقب' in c]
    if moraqeb_cols:
        df['Supervisor_Final'] = df[moraqeb_cols[0]].fillna("غير مسجل")
        if len(moraqeb_cols) > 1: # إذا وجد أكثر من عمود للمراقب، قم بدمجهم
            for col in moraqeb_cols[1:]:
                df['Supervisor_Final'] = df['Supervisor_Final'].fillna(df[col])
    else:
        df['Supervisor_Final'] = "غير مسجل"

    # حل مرن لرقم الشاخص
    shaخص_cols = [c for c in df.columns if 'رقم الشاخص' in c]
    if shaخص_cols:
        df['Unified_ID'] = df[shaخص_cols[0]].fillna("غير معرف")
        if len(shaخص_cols) > 1:
            for col in shaخص_cols[1:]:
                df['Unified_ID'] = df['Unified_ID'].fillna(df[col])
    else:
        df['Unified_ID'] = "غير معرف"
        
    df['Unified_ID'] = df['Unified_ID'].astype(str).str.strip()
    df['Assistant_Name'] = df['المعاون'].fillna("غير مسجل") if 'المعاون' in df.columns else "غير مسجل"
    
    if 'طابع زمني' in df.columns:
        df['temp_time'] = df['طابع زمني'].astype(str).str.replace('م', 'PM').str.replace('ص', 'AM')
        df['dt_object'] = pd.to_datetime(df['temp_time'], errors='coerce')
        df = df.sort_values(by='dt_object', ascending=False)
    
    # تحديد أعمدة التشيك ليست (أول 30 عمود بعد البيانات الأساسية)
    checklist_cols = df.columns[7:37] if len(df.columns) > 7 else []
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    df_latest = df.drop_duplicates(subset=['Unified_ID'], keep='first')
    return df, df_latest, checklist_cols

# 3. واجهة العرض (تم اختصارها لضمان العمل)
try:
    df_full, df_latest, checklist_cols = load_data()
    st.markdown("<h1>🚀 لوحة متابعة قطاع المشاعر</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 التحليل العام", "🏕️ خريطة المواقع", "🏗️ أداء المواقع"])

    with tab1:
        st.subheader("إحصائيات عامة")
        avg_total = round(df_latest['Overall_Score'].mean())
        st.metric("متوسط الجاهزية الكلي", f"{avg_total}%")
        
        fig = px.histogram(df_latest, x='Overall_Score', nbins=10, title="توزيع درجات الجاهزية", color_discrete_sequence=['#3b82f6'])
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("المواقع الحالية")
        cols = st.columns(6)
        for idx, row in df_latest.iterrows():
            with cols[idx % 6]:
                st.button(f"{row['Unified_ID']}\n{row['Overall_Score']}%", key=f"site_{idx}")

    with tab3:
        st.subheader("أداء المشرفين")
        sup_perf = df_latest.groupby('Supervisor_Final')['Overall_Score'].mean().sort_values(ascending=False).reset_index()
        st.table(sup_perf)

except Exception as e:
    st.error(f"حدث خطأ في قراءة البيانات: {e}")
    st.info("نصيحة: تأكد من أن الرابط المستخدم هو رابط Google Sheet بصيغة CSV وليس رابط Form.")
