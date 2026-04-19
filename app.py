import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# 1. إعدادات الصفحة والتنسيق الجمالي
st.set_page_config(page_title="جاهزية مخيمات عرفات 2026", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    .stApp { background-color: #0e1117; color: #ffffff; direction: rtl !important; }
    h1, h2, h3, h4, .stMarkdown, p, span, label { 
        text-align: right !important; 
        direction: rtl !important; 
        font-family: 'Cairo', sans-serif !important; 
    }

    /* تنسيق أزرار المربعات (Tiles) */
    div.stButton > button {
        width: 100% !important;
        height: 110px !important;
        border-radius: 15px !important; 
        background: linear-gradient(145deg, #1f2937, #111827) !important;
        border: 2px solid #374151 !important; 
        color: white !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    div.stButton > button:hover { 
        border-color: #3b82f6 !important; 
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    }

    .score-badge {
        font-size: 0.9rem;
        background: #374151;
        padding: 2px 8px;
        border-radius: 10px;
        margin-top: 5px;
    }

    /* بطاقات الإحصائيات */
    .metric-card {
        background: #1f2937;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #374151;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-value { font-size: 2.5rem; font-weight: bold; color: #3b82f6; }
    
    /* صندوق تفاصيل الموقع */
    .details-box {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 15px;
        border-right: 8px solid #3b82f6;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. معالجة البيانات وتحليل الجاهزية
def analyze_readiness(row, checklist_cols):
    scores = []
    missing_items = []
    for col in checklist_cols:
        val = str(row.get(col, '')).strip()
        if not val or val.lower() == 'nan' or val == "": continue
        
        current_score = None
        # منطق التقييم: نعم أو رقم 1 يعني 100%، لا أو 0 يعني 0%
        if any(p in val for p in ['نعم', 'مطابق', 'مكتمل', 'تم', '1.0', '1']): current_score = 100.0
        elif any(n in val for n in ['لا', 'غير', 'لم', 'ناقص', '0.0', '0']): current_score = 0.0
        
        if current_score is not None:
            scores.append(current_score)
            if current_score < 100: missing_items.append(col)
                
    final_score = round(np.mean(scores)) if scores else 0
    final_missing = " | ".join(missing_items)
    return final_score, final_missing

# رابط الملف (تأكد من أنه متاح للجميع للعرض)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nfOahkHuUnWdsh40f0E3WvIUqTC4phKUxraGSOKyuUs/export?format=csv"

@st.cache_data(ttl=30)
def load_and_clean_data():
    df = pd.read_csv(SHEET_URL)
    # تنظيف أسماء الأعمدة من المسافات الزائدة
    df.columns = [" ".join(col.split()) for col in df.columns]
    
    # 🌟 منطق التسمية المطلوب (F لسنا و G لركين)
    def create_unified_id(row):
        company = str(row.get('شركة', '')).lower()
        id_sana = str(row.get('رقم الشاخص', ''))
        id_rakeen = str(row.get('رقم الشاخص 2', ''))
        
        if 'سنا' in company and id_sana != 'nan':
            return f"F-{id_sana}"
        elif 'ركين' in company and id_rakeen != 'nan':
            return f"G-{id_rakeen}"
        return "غير معرف"

    df['Unified_ID'] = df.apply(create_unified_id, axis=1)
    df['Supervisor_Final'] = df['المراقب 2'].fillna(df['المراقب']).fillna("غير مسجل")
    
    # معالجة الوقت
    if 'طابع زمني' in df.columns:
        df['dt_object'] = pd.to_datetime(df['طابع زمني'], errors='coerce')
        df = df.sort_values(by='dt_object', ascending=False)
    
    # تحديد أعمدة الأسئلة (التي سيتم حساب النسبة بناءً عليها)
    exclude = ['طابع زمني', 'المعاون', 'المراقب', 'المراقب 2', 'شركة', 'رقم الشاخص', 'رقم الشاخص 2', 'ملاحظات المراقب', 'Unified_ID', 'Supervisor_Final', 'dt_object']
    checklist_cols = [c for c in df.columns if c not in exclude]
    
    # حساب النتائج
    results = df.apply(lambda r: analyze_readiness(r, checklist_cols), axis=1)
    df['Overall_Score'], df['Missing_Details'] = zip(*results)
    
    # أخذ أحدث تقييم لكل موقع فقط
    df_latest = df.drop_duplicates(subset=['Unified_ID'], keep='first')
    return df, df_latest

# 3. نافذة منبثقة لتفاصيل المخيم
@st.dialog("تفاصيل جاهزية المخيم 🏕️")
def show_tent_info(tent_id, full_df):
    history = full_df[full_df['Unified_ID'] == tent_id].copy()
    latest = history.iloc[0]
    
    st.markdown(f"### تفاصيل الموقع: {tent_id}")
    
    st.markdown(f"""
    <div class='details-box'>
        <h2 style='color:#eab308; margin:0;'>{int(latest['Overall_Score'])}%</h2>
        <p><b>الشركة:</b> {latest['شركة']}</p>
        <p><b>المراقب:</b> {latest['Supervisor_Final']}</p>
        <p><b>آخر تحديث:</b> {latest['طابع زمني']}</p>
        <hr>
        <p><b>ملاحظات المراقب:</b><br>{latest['ملاحظات المراقب'] if pd.notna(latest['ملاحظات المراقب']) else 'لا توجد ملاحظات'}</p>
    </div>
    """, unsafe_allow_html=True)

    missing = str(latest['Missing_Details']).split('|')
    if missing and missing[0] != "":
        st.error("⚠️ قائمة النواقص:")
        for item in missing:
            st.write(f"❌ {item.strip()}")
    else:
        st.success("✅ الموقع مكتمل الجاهزية")

# 4. بناء الواجهة الرئيسية
try:
    df_all, df_latest = load_and_clean_data()
    
    st.title("📊 لوحة متابعة جاهزية مخيمات عرفات")
    st.info("يتم تحديث البيانات تلقائياً من Google Sheets")

    # بطاقات الإحصائيات العلوية
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df_latest)}</div><div>إجمالي المواقع</div></div>', unsafe_allow_html=True)
    with m2:
        avg = round(df_latest['Overall_Score'].mean())
        st.markdown(f'<div class="metric-card"><div class="metric-value">{avg}%</div><div>متوسط الجاهزية العام</div></div>', unsafe_allow_html=True)
    with m3:
        ready = len(df_latest[df_latest['Overall_Score'] >= 90])
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#10b981">{ready}</div><div>مواقع جاهزة (+90%)</div></div>', unsafe_allow_html=True)
    with m4:
        low = len(df_latest[df_latest['Overall_Score'] < 50])
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#ef4444">{low}</div><div>مواقع متأخرة (-50%)</div></div>', unsafe_allow_html=True)

    # التبويبات
    tab1, tab2 = st.tabs(["🏕️ خريطة المواقع (Tiles)", "📈 التحليل البياني"])

    with tab1:
        search = st.text_input("🔍 ابحث عن رقم شاخص (مثال: 518):", "")
        
        # تقسيم العرض حسب الشركة
        for company_label, prefix in [("شركة سنا (F)", "F-"), ("شركة ركين (G)", "G-")]:
            st.subheader(company_label)
            sub_df = df_latest[df_latest['Unified_ID'].str.startswith(prefix)].sort_values('Unified_ID')
            
            if search:
                sub_df = sub_df[sub_df['Unified_ID'].str.contains(search)]

            if not sub_df.empty:
                cols = st.columns(6) # 6 مربعات في الصف الواحد
                for idx, (_, row) in enumerate(sub_df.iterrows()):
                    with cols[idx % 6]:
                        # لون الزر بناءً على النسبة
                        score = row['Overall_Score']
                        color = "#10b981" if score >= 90 else "#f59e0b" if score >= 50 else "#ef4444"
                        
                        btn_text = f"{row['Unified_ID']}\n{int(score)}%"
                        if st.button(btn_text, key=f"btn_{row['Unified_ID']}"):
                            show_tent_info(row['Unified_ID'], df_all)
            else:
                st.write("لا توجد بيانات لهذه الشركة حالياً.")

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            fig1 = px.histogram(df_latest, x='Overall_Score', nbins=10, title="توزيع مستويات الجاهزية",
                               labels={'Overall_Score': 'نسبة الجاهزية'}, color_discrete_sequence=['#3b82f6'])
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_b:
            fig2 = px.box(df_latest, x='شركة', y='Overall_Score', title="مقارنة أداء الشركات",
                         color='شركة', color_discrete_map={'سنا (مشارق الذهبية)': '#b91c1c', 'ركين (مشارق المتميزة)': '#1e3a8a'})
            st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"خطأ في التحميل: {e}")
    st.write("تأكد من أن الملف المرفوع يحتوي على الأعمدة المطلوبة.")
