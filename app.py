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
    </style>
    """, unsafe_allow_html=True)

# =========================
# 2. معالجة البيانات
# =========================
def analyze_readiness(row, checklist_cols):
    scores = []
    missing_items = []
    for col in checklist_cols:
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
            elif any(p in val for p in ['نعم', 'مطابق', 'مكتمل', 'تم', 'يوجد', 'متوفر']):
                current_score = 100.0
            elif any(n in val for n in ['لا', 'غير', 'لم']):
                current_score = 0.0

        if current_score is not None:
            scores.append(current_score)
            if current_score < 100:
                missing_items.append(f"{col} ({int(current_score)}%)")

    return pd.Series([round(np.mean(scores)) if scores else 0, " | ".join(missing_items)])

SHEET_URL = "https://docs.google.com/spreadsheets/d/1pN31S92Xa4m-hilE-e56F9T6LuOhZLwPq6YWEnWP_xk/export?format=csv"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip().replace('\n', '') for col in df.columns]

    df['Supervisor_Final'] = df['المراقب .1'].fillna(df['المراقب']).fillna("غير مسجل")
    df['Unified_ID'] = np.where(df['شركة'].str.contains('ركين', na=False), df['رقم الشاخص'], df['رقم الشاخص .1'])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير معرف").astype(str).str.strip()

    df['temp_time'] = df['طابع زمني'].astype(str).str.replace('م', 'PM').str.replace('ص', 'AM')
    df['dt_object'] = pd.to_datetime(df['temp_time'], errors='coerce')
    df['date'] = df['dt_object'].dt.date

    checklist_cols = df.columns[7:37]
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)

    df_latest = df.drop_duplicates(subset=['Unified_ID'], keep='first')

    return df, df_latest

# =========================
# 📈 التقدم الزمني
# =========================
def show_time_progress(df_full):
    st.markdown("## 📈 التقدم الزمني للمخيمات")

    # 1. التقدم اليومي
    daily = df_full.groupby('date')['Overall_Score'].mean().reset_index()
    fig1 = px.line(daily, x='date', y='Overall_Score', markers=True, title='التقدم اليومي العام')
    fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', yaxis=dict(side="right"))
    st.plotly_chart(fig1, use_container_width=True)

    # 2. تقدم كل مخيم
    camp = df_full.groupby(['Unified_ID', 'date'])['Overall_Score'].mean().reset_index()

    selected = st.multiselect("اختر مخيمات", camp['Unified_ID'].unique())
    if selected:
        camp = camp[camp['Unified_ID'].isin(selected)]

    fig2 = px.line(camp, x='date', y='Overall_Score', color='Unified_ID', markers=True, title='تقدم كل مخيم')
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', yaxis=dict(side="right"))
    st.plotly_chart(fig2, use_container_width=True)

    # 3. سرعة الإنجاز
    daily['velocity'] = daily['Overall_Score'].diff()
    fig3 = px.bar(daily, x='date', y='velocity', title='سرعة الإنجاز')
    fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig3, use_container_width=True)

    # 4. التحسن
    improve = camp.sort_values('date').groupby('Unified_ID').agg(
        start=('Overall_Score', 'first'),
        end=('Overall_Score', 'last')
    ).reset_index()

    improve['change'] = improve['end'] - improve['start']

    fig4 = px.bar(improve, x='Unified_ID', y='change', title='تحسن المخيمات')
    fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', xaxis=dict(autorange="reversed"))
    st.plotly_chart(fig4, use_container_width=True)

# =========================
# 🚀 MAIN
# =========================
try:
    df_full, df_latest = load_data()

    st.markdown("# 🚀 لوحة متابعة قطاع المشاعر")

    page = st.radio(
        "اختر العرض:",
        ["📊 التحليل العام", "🏕️ خريطة المواقع", "👁️ أداء المراقبين", "📈 التقدم الزمني"],
        horizontal=True
    )

    st.divider()

    if page == "📈 التقدم الزمني":
        show_time_progress(df_full)

    elif page == "📊 التحليل العام":
        st.write(df_latest[['Unified_ID', 'Overall_Score']])

    elif page == "🏕️ خريطة المواقع":
        st.write("خريطة المواقع هنا")

    elif page == "👁️ أداء المراقبين":
        st.write("لوحة المراقبين هنا")

except Exception as e:
    st.error(f"⚠️ خطأ: {e}")
