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

    .checklist-item-popup { 
        background-color: #450a0a; padding: 10px; border-radius: 8px; 
        margin-bottom: 6px; border-right: 4px solid #ef4444; color: #fecaca !important;
        text-align: right !important;
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
        val = str(row.get(col, '')).strip()
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
                
    # إرجاع كمتغيرات عادية لتجنب خطأ الطول
    final_score = round(np.mean(scores)) if scores else 0
    final_missing = " | ".join(missing_items)
    return final_score, final_missing

SHEET_URL = "https://docs.google.com/spreadsheets/d/1nfOahkHuUnWdsh40f0E3WvIUqTC4phKUxraGSOKyuUs/export?format=csv"

@st.cache_data(ttl=20)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [col.strip().replace('\n', '') for col in df.columns]
    
    # التعامل الديناميكي مع الأعمدة
    sup_col1 = 'المراقب' if 'المراقب' in df.columns else df.columns[2]
    sup_col2 = 'المراقب .1' if 'المراقب .1' in df.columns else sup_col1
    id_col1 = 'رقم الشاخص' if 'رقم الشاخص' in df.columns else df.columns[5]
    id_col2 = 'رقم الشاخص .1' if 'رقم الشاخص .1' in df.columns else id_col1
    company_col = 'شركة' if 'شركة' in df.columns else df.columns[4]
    
    df['Supervisor_Final'] = df[sup_col2].fillna(df[sup_col1]).fillna("غير مسجل")
    df['Unified_ID'] = np.where(df[company_col].str.contains('ركين', na=False), df[id_col1], df[id_col2])
    df['Unified_ID'] = df['Unified_ID'].fillna("غير معرف").astype(str).str.strip()
    
    assistant_col = 'المعاون' if 'المعاون' in df.columns else df.columns[1]
    df['Assistant_Name'] = df[assistant_col].fillna("غير مسجل")
    
    if 'طابع زمني' in df.columns:
        df['temp_time'] = df['طابع زمني'].astype(str).str.replace('م', 'PM').str.replace('ص', 'AM')
        df['dt_object'] = pd.to_datetime(df['temp_time'], errors='coerce')
        df = df.sort_values(by='dt_object', ascending=False)
    
    # الاستخراج الديناميكي لأسئلة التقييم
    exclude_cols = ['طابع زمني', assistant_col, sup_col1, sup_col2, company_col, id_col1, id_col2, 'ملاحظات المراقب', 'temp_time', 'dt_object', 'Supervisor_Final', 'Unified_ID', 'Assistant_Name']
    checklist_cols = [c for c in df.columns if c not in exclude_cols]
    
    # 🌟 الإصلاح الجذري لمشكلة "Columns must be same length as key"
    scores_list = []
    missing_list = []
    for _, row in df.iterrows():
        s, m = analyze_readiness(row, checklist_cols)
        scores_list.append(s)
        missing_list.append(m)
        
    df['Overall_Score'] = scores_list
    df['Missing_Details'] = missing_list
    # 🌟 انتهاء الإصلاح
    
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
    
    notes = row.get('ملاحظات المراقب', '')
    display_notes = notes if pd.notna(notes) and str(notes).strip() != "" else 'لا توجد ملاحظات.'
    
    st.markdown(f"""
    <div class='observer-notes-box'>
        <div class='score-circle'>{score}%</div>
        <div>
            <p><b>المعاون:</b> {row['Assistant_Name']}</p>
            <p><b>المراقب:</b> {row['Supervisor_Final']}</p>
            <hr>
            <p><b>ملاحظات المراقب:</b></p>
            <p>{display_notes}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    missing_list = [item.strip() for item in str(row['Missing_Details']).split('|') if item.strip()]
    if missing_list:
        st.markdown("<h4>⚠️ النواقص</h4>", unsafe_allow_html=True)
        for item in missing_list:
            st.markdown(f"<div class='checklist-item-popup'>❌ {item}</div>", unsafe_allow_html=True)

# 4. داشبورد أداء المواقع 
def show_sites_dashboard(df_full, df_latest):
    st.markdown("<h2>📊 لوحة أداء المواقع</h2>", unsafe_allow_html=True)

    sites_stats = []
    company_col = 'شركة' if 'شركة' in df_latest.columns else df_latest.columns[4]
    
    for site_id in df_latest['Unified_ID'].unique():
        if site_id == "غير معرف":
            continue
        site_history = df_full[df_full['Unified_ID'] == site_id].copy()
        if 'dt_object' in site_history.columns:
            site_history = site_history.sort_values(by='dt_object', ascending=True)

        scores_over_time = site_history['Overall_Score'].tolist()
        if not scores_over_time:
            continue

        first_score = scores_over_time[0]
        latest_score = scores_over_time[-1]
        improvement = latest_score - first_score
        num_inspections = len(scores_over_time)
        avg_score = np.mean(scores_over_time)
        max_score = max(scores_over_time)
        min_score = min(scores_over_time)

        if improvement > 10:
            trend = "📈 تحسن كبير"
            trend_color = "#10b981"
        elif improvement > 0:
            trend = "🔼 تحسن طفيف"
            trend_color = "#3b82f6"
        elif improvement == 0:
            trend = "➖ ثابت"
            trend_color = "#9ca3af"
        elif improvement > -10:
            trend = "🔽 تراجع طفيف"
            trend_color = "#f59e0b"
        else:
            trend = "📉 تراجع كبير"
            trend_color = "#ef4444"

        latest_row = site_history.iloc[-1]
        sites_stats.append({
            'الموقع': site_id,
            'الشركة': latest_row.get(company_col, "غير محدد") if pd.notna(latest_row.get(company_col)) else "غير محدد",
            'المراقب': latest_row['Supervisor_Final'],
            'الأداء الحالي': latest_score,
            'أول تقييم': first_score,
            'مقدار التحسن': round(improvement, 1),
            'متوسط الأداء': round(avg_score, 1),
            'أعلى أداء': max_score,
            'أقل أداء': min_score,
            'عدد الزيارات': num_inspections,
            'حالة التقدم': trend,
            'لون': trend_color
        })

    stats_df = pd.DataFrame(sites_stats)
    if stats_df.empty:
        st.warning("لا توجد بيانات كافية لعرض أداء المواقع.")
        return

    stats_df = stats_df.sort_values('الأداء الحالي', ascending=False)

    total_sites = len(stats_df)
    avg_current = round(stats_df['الأداء الحالي'].mean(), 1)
    improved_sites = len(stats_df[stats_df['مقدار التحسن'] > 0])
    declined_sites = len(stats_df[stats_df['مقدار التحسن'] < 0])
    excellent_sites = len(stats_df[stats_df['الأداء الحالي'] >= 90])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total_sites}</div><div class="metric-label">إجمالي المواقع</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_current}%</div><div class="metric-label">متوسط الأداء العام</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#10b981">{improved_sites}</div><div class="metric-label">مواقع تحسنت</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#ef4444">{declined_sites}</div><div class="metric-label">مواقع تراجعت</div></div>', unsafe_allow_html=True)

    st.divider()

    st.markdown("<h3>🧠 تحليلات ذكية</h3>", unsafe_allow_html=True)
    insights_col1, insights_col2 = st.columns(2)

    with insights_col1:
        top_improved = stats_df.nlargest(1, 'مقدار التحسن').iloc[0] if not stats_df.empty else None
        if top_improved is not None and top_improved['مقدار التحسن'] > 0:
            st.markdown(f"""
            <div class='high-achievement'>
                <b>🏆 أكثر موقع تحسناً:</b> {top_improved['الموقع']}<br>
                ارتفع من <b>{top_improved['أول تقييم']}%</b> إلى <b>{top_improved['الأداء الحالي']}%</b>
                (تحسن +{top_improved['مقدار التحسن']}%)
            </div>
            """, unsafe_allow_html=True)

        best_now = stats_df.iloc[0]
        st.markdown(f"""
        <div class='high-achievement'>
            <b>⭐ أعلى موقع أداءً حالياً:</b> {best_now['الموقع']}<br>
            بنسبة إنجاز <b>{best_now['الأداء الحالي']}%</b> ({best_now['الشركة']})
        </div>
        """, unsafe_allow_html=True)

        excellence_rate = round((excellent_sites / total_sites * 100) if total_sites > 0 else 0, 1)
        st.markdown(f"""
        <div class='insight-box'>
            <b>📊 نسبة التميز:</b> {excellence_rate}% من المواقع تجاوزت 90%
            ({excellent_sites} من أصل {total_sites})
        </div>
        """, unsafe_allow_html=True)

    with insights_col2:
        top_declined = stats_df.nsmallest(1, 'مقدار التحسن').iloc[0] if not stats_df.empty else None
        if top_declined is not None and top_declined['مقدار التحسن'] < 0:
            st.markdown(f"""
            <div class='low-achievement'>
                <b>⚠️ أكثر موقع تراجعاً:</b> {top_declined['الموقع']}<br>
                انخفض من <b>{top_declined['أول تقييم']}%</b> إلى <b>{top_declined['الأداء الحالي']}%</b>
                (تراجع {top_declined['مقدار التحسن']}%)
            </div>
            """, unsafe_allow_html=True)

        worst_now = stats_df.iloc[-1]
        st.markdown(f"""
        <div class='low-achievement'>
            <b>🚨 أقل موقع أداءً حالياً:</b> {worst_now['الموقع']}<br>
            بنسبة إنجاز <b>{worst_now['الأداء الحالي']}%</b> - يحتاج لمتابعة عاجلة
        </div>
        """, unsafe_allow_html=True)

        avg_improvement = round(stats_df['مقدار التحسن'].mean(), 1)
        improvement_icon = "📈" if avg_improvement > 0 else "📉" if avg_improvement < 0 else "➖"
        st.markdown(f"""
        <div class='insight-box'>
            <b>{improvement_icon} متوسط معدل التحسن:</b> {avg_improvement}%
            عبر جميع المواقع منذ بداية المتابعة
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig = px.bar(
            stats_df, x='الموقع', y='الأداء الحالي',
            color='الأداء الحالي',
            color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'],
            title='الأداء الحالي لكل موقع',
            text='الأداء الحالي'
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white",
            xaxis=dict(autorange="reversed"),
            yaxis=dict(side="right"),
            title=dict(x=0.5, xanchor='center')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_chart2:
        improvement_df = stats_df.sort_values('مقدار التحسن', ascending=False)
        fig2 = px.bar(
            improvement_df, x='الموقع', y='مقدار التحسن',
            color='مقدار التحسن',
            color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'],
            color_continuous_midpoint=0,
            title='مقدار تحسن المواقع (مقارنة بأول تقييم)',
            text='مقدار التحسن'
        )
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white",
            xaxis=dict(autorange="reversed"),
            yaxis=dict(side="right"),
            title=dict(x=0.5, xanchor='center')
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<h3>📈 تطور أداء المواقع عبر الزمن</h3>", unsafe_allow_html=True)

    timeline_data = []
    for site_id in df_latest['Unified_ID'].unique():
        if site_id == "غير معرف":
            continue
        site_history = df_full[df_full['Unified_ID'] == site_id].copy()
        if 'dt_object' in site_history.columns:
            site_history = site_history.sort_values(by='dt_object', ascending=True)
        for idx, (_, r) in enumerate(site_history.iterrows(), start=1):
            timeline_data.append({
                'الموقع': site_id,
                'رقم الزيارة': idx,
                'النسبة': r['Overall_Score'],
                'التاريخ': r.get('طابع زمني', '-')
            })

    timeline_df = pd.DataFrame(timeline_data)
    if not timeline_df.empty:
        fig3 = px.line(
            timeline_df, x='رقم الزيارة', y='النسبة', color='الموقع',
            markers=True, title='تطور نسبة الإنجاز لكل موقع عبر الزيارات'
        )
        fig3.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white",
            xaxis=dict(side="top"),
            yaxis=dict(side="right"),
            title=dict(x=0.5, xanchor='center'),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3)
        )
        st.plotly_chart(fig3, use_container_width=True)

    col_chart3, col_chart4 = st.columns(2)
    with col_chart3:
        trend_counts = stats_df['حالة التقدم'].value_counts().reset_index()
        trend_counts.columns = ['الحالة', 'العدد']
        fig4 = px.pie(
            trend_counts, values='العدد', names='الحالة',
            title='توزيع المواقع حسب حالة التقدم',
            color_discrete_sequence=['#10b981', '#3b82f6', '#9ca3af', '#f59e0b', '#ef4444']
        )
        fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", title=dict(x=0.5, xanchor='center'))
        st.plotly_chart(fig4, use_container_width=True)

    with col_chart4:
        compare_df = stats_df.head(15).melt(
            id_vars=['الموقع'],
            value_vars=['أول تقييم', 'الأداء الحالي'],
            var_name='النوع', value_name='النسبة'
        )
        fig5 = px.bar(
            compare_df, x='الموقع', y='النسبة', color='النوع',
            barmode='group',
            title='مقارنة أول تقييم مقابل الأداء الحالي',
            color_discrete_map={'أول تقييم': '#9ca3af', 'الأداء الحالي': '#3b82f6'}
        )
        fig5.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white",
            xaxis=dict(autorange="reversed"),
            yaxis=dict(side="right"),
            title=dict(x=0.5, xanchor='center')
        )
        st.plotly_chart(fig5, use_container_width=True)

    st.markdown("<h3>📋 تقرير تفصيلي للمواقع</h3>", unsafe_allow_html=True)
    display_df = stats_df[['الموقع', 'الشركة', 'الأداء الحالي', 'أول تقييم',
                            'مقدار التحسن', 'متوسط الأداء', 'أعلى أداء', 'أقل أداء',
                            'عدد الزيارات', 'حالة التقدم']]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# 5. العرض الرئيسي
try:
    df_full, df_latest, checklist_cols = load_data()
    st.markdown("<h1>🚀 لوحة متابعة قطاع المشاعر</h1>", unsafe_allow_html=True)
    page = st.radio("اختر العرض:", ["📊 التحليل العام", "🏕️ خريطة المواقع", "🏗️ أداء المواقع"], horizontal=True)
    st.divider()

    company_col = 'شركة' if 'شركة' in df_latest.columns else df_latest.columns[4]

    if page == "📊 التحليل العام":
        for company, color in [("سنا", "#b91c1c"), ("ركين", "#8b5e3c")]:
            sub_df = df_latest[df_latest[company_col].astype(str).str.contains(company, na=False)]
            st.markdown(f"<h2>{'🔴' if company=='سنا' else '🟤'} شركة {company}</h2>", unsafe_allow_html=True)
            if not sub_df.empty:
                c1, c2 = st.columns([1, 4])
                avg = round(sub_df['Overall_Score'].mean())
                c1.metric("متوسط الإنجاز", f"{avg}%")
                fig = px.bar(sub_df, x='Unified_ID', y='Overall_Score', color_discrete_sequence=[color], text='Overall_Score')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", 
                                  xaxis=dict(autorange="reversed"), yaxis=dict(side="right"))
                c2.plotly_chart(fig, use_container_width=True)

    elif page == "🏕️ خريطة المواقع":
        df_sorted = df_latest.sort_values(by=[company_col, 'Unified_ID'])
        grid_cols = st.columns(6) 
        for idx, (_, row) in enumerate(df_sorted.iterrows()):
            icon = "🔴" if "سنا" in str(row.get(company_col, '')) else "🟤"
            with grid_cols[idx % 6]:
                if st.button(f"{icon} {row['Unified_ID']}\n{row['Overall_Score']}%", key=f"btn_{row['Unified_ID']}"):
                    show_tent_details(row['Unified_ID'], df_full)

    elif page == "🏗️ أداء المواقع":
        show_sites_dashboard(df_full, df_latest)

except Exception as e:
    st.error(f"⚠️ خطأ: {e}")
