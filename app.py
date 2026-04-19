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

    .metric-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #374151;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #3b82f6;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #9ca3af;
        margin-top: 5px;
    }
    
    .high-achievement {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
        border-radius: 12px;
        padding: 15px;
        border-right: 4px solid #10b981;
        margin-bottom: 10px;
    }
    
    .low-achievement {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        border-radius: 12px;
        padding: 15px;
        border-right: 4px solid #ef4444;
        margin-bottom: 10px;
    }

    .insight-box {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        border-radius: 12px;
        padding: 15px;
        border-right: 4px solid #3b82f6;
        margin-bottom: 10px;
        color: #dbeafe !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. معالجة البيانات
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

# الرابط الجديد المحدث (بصيغة CSV لضمان القراءة الصحيحة)
RAW_URL = "https://docs.google.com/spreadsheets/d/1nfOahkHuUnWdsh40f0E3WvIUqTC4phKUxraGSOKyuUs/edit?usp=sharing"
SHEET_URL = RAW_URL.replace("/edit?usp=sharing", "/export?format=csv")

@st.cache_data(ttl=20)
def load_data():
    # استخدام mangle_dupe_cols للتعامل مع أي تكرار مفاجئ في الأسماء
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip().replace('\n', '') for col in df.columns]
    
    # منطق مرن للتعرف على الأعمدة حتى لو تغيرت أسماؤها
    moraqeb_cols = [c for c in df.columns if 'المراقب' in c]
    df['Supervisor_Final'] = df[moraqeb_cols[0]].fillna("غير مسجل") if moraqeb_cols else "غير مسجل"
    
    shaخص_cols = [c for c in df.columns if 'رقم الشاخص' in c]
    df['Unified_ID'] = df[shaخص_cols[0]].fillna("غير معرف") if shaخص_cols else "غير معرف"
    df['Unified_ID'] = df['Unified_ID'].astype(str).str.strip()
    
    df['Assistant_Name'] = df['المعاون'].fillna("غير مسجل") if 'المعاون' in df.columns else "غير مسجل"
    
    if 'طابع زمني' in df.columns:
        df['temp_time'] = df['طابع زمني'].astype(str).str.replace('م', 'PM').str.replace('ص', 'AM')
        df['dt_object'] = pd.to_datetime(df['temp_time'], errors='coerce')
        df = df.sort_values(by='dt_object', ascending=False)
    
    checklist_cols = df.columns[7:37] if len(df.columns) > 7 else []
    df[['Overall_Score', 'Missing_Details']] = df.apply(lambda row: analyze_readiness(row, checklist_cols), axis=1)
    df_latest = df.drop_duplicates(subset=['Unified_ID'], keep='first')
    return df, df_latest, checklist_cols

# 3. النافذة المنبثقة
@st.dialog("تفاصيل جاهزية الموقع 🏕️")
def show_tent_details(tent_id, full_df):
    tent_history = full_df[full_df['Unified_ID'] == tent_id].copy()
    st.markdown(f"<h3>موقع: {tent_id}</h3>", unsafe_allow_html=True)
    history_options = tent_history['طابع زمني'].tolist()
    selected_time = st.selectbox("🕒 عرض تقرير تاريخ:", history_options)
    row = tent_history[tent_history['طابع زمني'] == selected_time].iloc[0]
    score = int(row['Overall_Score'])
    
    st.markdown(f"""
    <div class='observer-notes-box'>
        <div class='score-circle'>{score}%</div>
        <div>
            <p><b>المعاون:</b> {row['Assistant_Name']}</p>
            <p><b>المراقب:</b> {row['Supervisor_Final']}</p>
            <hr>
            <p><b>ملاحظات المراقب:</b></p>
            <p>{row['ملاحظات المراقب'] if 'ملاحظات المراقب' in row and pd.notna(row['ملاحظات المراقب']) else 'لا توجد ملاحظات.'}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 4. داشبورد أداء المواقع
def show_sites_dashboard(df_full, df_latest):
    st.markdown("<h2>📊 لوحة أداء المواقع</h2>", unsafe_allow_html=True)
    sites_stats = []
    for site_id in df_latest['Unified_ID'].unique():
        if site_id == "غير معرف": continue
        site_history = df_full[df_full['Unified_ID'] == site_id].copy()
        if 'dt_object' in site_history.columns:
            site_history = site_history.sort_values(by='dt_object', ascending=True)

        scores = site_history['Overall_Score'].tolist()
        if not scores: continue
        
        improvement = scores[-1] - scores[0]
        latest_row = site_history.iloc[-1]
        
        sites_stats.append({
            'الموقع': site_id,
            'الأداء الحالي': scores[-1],
            'مقدار التحسن': round(improvement, 1),
            'عدد الزيارات': len(scores),
            'حالة التقدم': "📈 تحسن" if improvement > 0 else "📉 تراجع" if improvement < 0 else "➖ ثابت"
        })

    stats_df = pd.DataFrame(sites_stats).sort_values('الأداء الحالي', ascending=False)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي المواقع", len(stats_df))
    c2.metric("متوسط الأداء العام", f"{round(stats_df['الأداء الحالي'].mean(), 1)}%")
    c3.metric("مواقع تحسنت", len(stats_df[stats_df['مقدار التحسن'] > 0]))

    st.divider()
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig = px.bar(stats_df, x='الموقع', y='الأداء الحالي', color='الأداء الحالي', title='الأداء الحالي لكل موقع')
        fig.update_layout(xaxis=dict(autorange="reversed"), yaxis=dict(side="right"), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    with col_chart2:
        fig2 = px.bar(stats_df, x='الموقع', y='مقدار التحسن', color='مقدار التحسن', title='مقدار التحسن')
        fig2.update_layout(xaxis=dict(autorange="reversed"), yaxis=dict(side="right"), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

# 5. العرض الرئيسي
try:
    df_full, df_latest, checklist_cols = load_data()
    st.markdown("<h1>🚀 لوحة متابعة قطاع المشاعر</h1>", unsafe_allow_html=True)
    page = st.radio("اختر العرض:", ["📊 التحليل العام", "🏕️ خريطة المواقع", "🏗️ أداء المواقع"], horizontal=True)
    st.divider()

    if page == "📊 التحليل العام":
        st.subheader("إحصائيات جاهزية الشركات")
        # منطق عرض الشركات (سنا / ركين)
        for company in df_latest['شركة'].unique() if 'شركة' in df_latest.columns else []:
            sub_df = df_latest[df_latest['شركة'] == company]
            st.write(f"### شركة {company}")
            fig = px.bar(sub_df, x='Unified_ID', y='Overall_Score', text='Overall_Score')
            fig.update_layout(xaxis=dict(autorange="reversed"), yaxis=dict(side="right"))
            st.plotly_chart(fig, use_container_width=True)

    elif page == "🏕️ خريطة المواقع":
        cols = st.columns(6) 
        for idx, (_, row) in enumerate(df_latest.iterrows()):
            with cols[idx % 6]:
                if st.button(f"{row['Unified_ID']}\n{row['Overall_Score']}%", key=f"btn_{row['Unified_ID']}"):
                    show_tent_details(row['Unified_ID'], df_full)

    elif page == "🏗️ أداء المواقع":
        show_sites_dashboard(df_full, df_latest)

except Exception as e:
    st.error(f"⚠️ خطأ في قراءة البيانات: {e}")
