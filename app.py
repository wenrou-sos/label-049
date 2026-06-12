import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import base64
from io import BytesIO

from src.data_processor import (
    load_data, filter_data, get_heatmap_data, get_route_analysis,
    get_peak_comparison, get_hourly_trend, get_district_analysis,
    generate_optimization_suggestions, get_unique_values
)
from src.visualizations import (
    create_passenger_heatmap, create_peak_comparison_chart,
    create_load_rate_ranking, create_hourly_trend,
    create_multi_route_comparison, create_district_pie,
    create_load_rate_distribution
)
from src.pdf_report import generate_pdf_report

st.set_page_config(
    page_title="公交客流数据可视化分析系统",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 600;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 0.85rem;
        color: #7f8c8d;
        font-weight: 500;
    }
    .metric-card p {
        margin: 0.5rem 0 0 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: #2c3e50;
    }
    .suggestion-card {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        border-left: 4px solid;
    }
    .suggestion-high {
        background: #fff5f5;
        border-color: #e74c3c;
    }
    .suggestion-medium {
        background: #fffbf0;
        border-color: #f39c12;
    }
    .suggestion-low {
        background: #f0f8ff;
        border-color: #3498db;
    }
    .section-header {
        padding: 0.8rem 0;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #ecf0f1;
    }
    .section-header h2 {
        margin: 0;
        font-size: 1.3rem;
        color: #2c3e50;
        font-weight: 600;
    }
    .stPlotlyChart {
        background: white;
        border-radius: 10px;
        padding: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .guide-box {
        background: #e8f4fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
    }
    .guide-box h4 {
        margin: 0 0 0.5rem 0;
        color: #2980b9;
        font-size: 1rem;
    }
    .guide-box ul {
        margin: 0;
        padding-left: 1.2rem;
        color: #34495e;
    }
    .guide-box li {
        margin-bottom: 0.3rem;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def get_download_link(df, filename, display_text):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="button-style">{display_text}</a>'

@st.cache_data(ttl=600)
def generate_report(df, route_analysis, suggestions, peak_comparison):
    report = f"""# 公交客流数据分析报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 一、整体概况
- 分析线路数: {df['线路名称'].nunique()} 条
- 覆盖区域: {df['所属区域'].nunique()} 个
- 统计天数: {df['日期'].nunique()} 天
- 总客流人次: {df['客流人数'].sum():,}

## 二、线路满载率分析
### TOP 5 最高满载率线路:
"""
    for _, row in route_analysis.head(5).iterrows():
        report += f"- {row['线路名称']}: {row['平均满载率']*100:.1f}% ({row['满载率等级']})\n"
    
    report += f"\n### TOP 5 最低满载率线路:\n"
    for _, row in route_analysis.tail(5).iloc[::-1].iterrows():
        report += f"- {row['线路名称']}: {row['平均满载率']*100:.1f}% ({row['满载率等级']})\n"
    
    report += f"\n## 三、高峰时段分析\n"
    peak_data = peak_comparison['comparison']
    report += f"- 早高峰平均客流: {peak_data['早高峰平均客流'].mean():.0f} 人/小时\n"
    report += f"- 晚高峰平均客流: {peak_data['晚高峰平均客流'].mean():.0f} 人/小时\n"
    report += f"- 平峰平均客流: {peak_data['平峰平均客流'].mean():.0f} 人/小时\n"
    report += f"- 高峰/平峰平均倍数: 早高峰 {peak_data['早高峰/平峰倍数'].mean():.2f}倍, 晚高峰 {peak_data['晚高峰/平峰倍数'].mean():.2f}倍\n"
    
    report += f"\n## 四、优化建议\n"
    for i, s in enumerate(suggestions[:10], 1):
        report += f"{i}. [{s['优先级']}] {s['线路']} - {s['建议']}\n"
        report += f"   问题: {s['问题']}\n\n"
    
    report += f"""
## 五、关键指标阈值说明
- 满载率 < 30%: 空载 - 建议减少运力
- 30% ≤ 满载率 < 50%: 低载 - 可优化调度
- 50% ≤ 满载率 < 70%: 正常 - 运力合理
- 70% ≤ 满载率 < 85%: 高载 - 关注高峰时段
- 满载率 ≥ 85%: 超载 - 建议增加运力
"""
    return report

def main():
    st.markdown("""
    <div class="main-header">
        <h1>🚌 公交客流数据可视化分析系统</h1>
        <p>基于 Python + Streamlit + Plotly 的智能公交调度决策支持平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    df = load_data()
    unique_vals = get_unique_values(df)
    
    with st.sidebar:
        st.markdown("### 🔍 数据筛选")
        
        st.markdown("#### 线路选择")
        select_all_routes = st.checkbox("全选线路", value=True)
        if select_all_routes:
            selected_routes = unique_vals['routes']
        else:
            selected_routes = st.multiselect(
                "选择公交线路",
                options=unique_vals['routes'],
                default=unique_vals['routes'][:5]
            )
        
        st.markdown("#### 区域筛选")
        select_all_districts = st.checkbox("全选区域", value=True)
        if select_all_districts:
            selected_districts = unique_vals['districts']
        else:
            selected_districts = st.multiselect(
                "选择区域",
                options=unique_vals['districts'],
                default=unique_vals['districts']
            )
        
        st.markdown("#### 时间范围")
        hour_range = st.slider(
            "选择时段范围",
            min_value=unique_vals['min_hour'],
            max_value=unique_vals['max_hour'],
            value=(unique_vals['min_hour'], unique_vals['max_hour']),
            format="%d:00"
        )
        
        st.markdown("#### 时段类型")
        peak_type = st.selectbox(
            "选择时段类型",
            options=['全部', '高峰', '早高峰', '晚高峰', '平峰'],
            index=0
        )
        
        st.markdown("#### 日期选择")
        select_all_dates = st.checkbox("全选日期", value=True)
        if select_all_dates:
            selected_dates = unique_vals['dates']
        else:
            selected_dates = st.multiselect(
                "选择日期",
                options=unique_vals['dates'],
                default=unique_vals['dates']
            )
        
        st.markdown("---")
        st.markdown("### ⚙️ 显示设置")
        heatmap_agg = st.selectbox(
            "热力图聚合方式",
            options=['mean', 'sum', 'max'],
            format_func=lambda x: {'mean': '平均值', 'sum': '总和', 'max': '最大值'}[x],
            index=0
        )
        
        show_numbers = st.checkbox("显示热力图数值", value=True)
        show_guide = st.checkbox("显示操作指引", value=True)
    
    filtered_df = filter_data(
        df,
        routes=selected_routes if not select_all_routes else None,
        districts=selected_districts if not select_all_districts else None,
        hours=hour_range,
        peak_type=peak_type,
        dates=selected_dates if not select_all_dates else None
    )
    
    if filtered_df.empty:
        st.warning("⚠️ 当前筛选条件下无数据，请调整筛选条件。")
        return
    
    if show_guide:
        st.markdown("""
        <div class="guide-box">
            <h4>📖 用户操作指引</h4>
            <ul>
                <li><strong>侧边栏筛选</strong>：可按线路、区域、时间范围、时段类型筛选数据</li>
                <li><strong>热力图交互</strong>：鼠标悬停查看具体数值，支持缩放和平移</li>
                <li><strong>图表交互</strong>：点击图例可隐藏/显示对应数据系列，支持下载为PNG图片</li>
                <li><strong>多线路对比</strong>：在下方选择多条线路进行对比分析</li>
                <li><strong>数据导出</strong>：可导出筛选后的数据和完整分析报告</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header"><h2>📊 核心指标概览</h2></div>', unsafe_allow_html=True)
    
    total_passengers = filtered_df['客流人数'].sum()
    avg_load_rate = filtered_df['满载率'].mean()
    peak_load_rate = filtered_df[filtered_df['是否高峰']]['满载率'].mean()
    unique_routes = filtered_df['线路名称'].nunique()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>总客流人次</h3>
            <p>{total_passengers:,}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #27ae60;">
            <h3>平均满载率</h3>
            <p>{avg_load_rate*100:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #e74c3c;">
            <h3>高峰满载率</h3>
            <p>{peak_load_rate*100:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #f39c12;">
            <h3>分析线路数</h3>
            <p>{unique_routes}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header"><h2>🔥 客流热力图</h2></div>', unsafe_allow_html=True)
    
    heatmap_data = get_heatmap_data(filtered_df, agg_type=heatmap_agg)
    heatmap_fig = create_passenger_heatmap(
        heatmap_data,
        title=f"公交客流热力图（按{('平均值', '总和', '最大值')[['mean', 'sum', 'max'].index(heatmap_agg)]}）"
    )
    
    if not show_numbers:
        heatmap_fig['layout']['annotations'] = []
    
    st.plotly_chart(heatmap_fig, width='stretch', config={'responsive': True})
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 客流趋势分析",
        "⚖️ 高峰/平峰对比",
        "🏆 线路满载率排名",
        "💡 优化建议"
    ])
    
    with tab1:
        st.markdown("#### 24小时客流趋势")
        hourly_data = get_hourly_trend(filtered_df)
        trend_fig = create_hourly_trend(hourly_data)
        st.plotly_chart(trend_fig, width='stretch')
        
        st.markdown("#### 多线路客流对比")
        compare_routes = st.multiselect(
            "选择要对比的线路（最多8条）",
            options=unique_vals['routes'],
            default=unique_vals['routes'][:4],
            key="compare_routes"
        )
        if len(compare_routes) > 0:
            compare_fig = create_multi_route_comparison(filtered_df, compare_routes[:8])
            st.plotly_chart(compare_fig, width='stretch')
        
        col_pie, col_box = st.columns(2)
        with col_pie:
            district_data = get_district_analysis(filtered_df)
            pie_fig = create_district_pie(district_data)
            st.plotly_chart(pie_fig, width='stretch')
        
        with col_box:
            route_analysis = get_route_analysis(filtered_df)
            box_fig = create_load_rate_distribution(route_analysis)
            st.plotly_chart(box_fig, width='stretch')
    
    with tab2:
        st.markdown("#### 高峰与平峰时段客流对比")
        peak_comparison = get_peak_comparison(filtered_df)
        peak_fig = create_peak_comparison_chart(peak_comparison['comparison'], selected_routes if len(selected_routes) <= 10 else None)
        st.plotly_chart(peak_fig, width='stretch')
        
        st.markdown("#### 详细对比数据")
        st.dataframe(
            peak_comparison['comparison'].style.format({
                '早高峰平均客流': '{:.0f}',
                '晚高峰平均客流': '{:.0f}',
                '平峰平均客流': '{:.0f}',
                '早高峰总客流': '{:,}',
                '晚高峰总客流': '{:,}',
                '平峰总客流': '{:,}',
                '早高峰/平峰倍数': '{:.2f}x',
                '晚高峰/平峰倍数': '{:.2f}x'
            }),
            width='stretch',
            hide_index=True
        )
        
        peak_summary = peak_comparison['comparison']
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("早高峰平均客流", f"{peak_summary['早高峰平均客流'].mean():.0f} 人", 
                     f"{peak_summary['早高峰/平峰倍数'].mean():.2f}x 平峰")
        with col_b:
            st.metric("晚高峰平均客流", f"{peak_summary['晚高峰平均客流'].mean():.0f} 人",
                     f"{peak_summary['晚高峰/平峰倍数'].mean():.2f}x 平峰")
        with col_c:
            st.metric("平峰平均客流", f"{peak_summary['平峰平均客流'].mean():.0f} 人")
    
    with tab3:
        st.markdown("#### 线路满载率排名（按平均满载率降序）")
        
        route_analysis = get_route_analysis(filtered_df)
        
        search_col, filter_col, _ = st.columns([2, 2, 2])
        with search_col:
            route_search = st.text_input("🔍 搜索线路", placeholder="输入线路号，如：1路")
        with filter_col:
            load_filter = st.multiselect(
                "📊 满载率等级筛选",
                options=['空载', '低载', '正常', '高载', '超载'],
                default=['空载', '低载', '正常', '高载', '超载']
            )
        
        display_analysis = route_analysis.copy()
        if route_search and route_search.strip():
            try:
                display_analysis = display_analysis[
                    display_analysis['线路名称'].str.contains(route_search.strip(), case=False, regex=False)
                ]
            except Exception:
                st.warning("⚠️ 搜索输入无效，请输入有效的线路名称")
                display_analysis = pd.DataFrame(columns=display_analysis.columns)
        
        if load_filter:
            display_analysis = display_analysis[display_analysis['满载率等级'].isin(load_filter)]
        
        if display_analysis.empty:
            st.info("ℹ️ 未找到符合条件的线路，请调整搜索或筛选条件")
        else:
            rank_fig = create_load_rate_ranking(display_analysis, top_n=len(display_analysis))
            st.plotly_chart(rank_fig, width='stretch')
            
            st.markdown("#### 详细线路数据")
            st.dataframe(
                display_analysis.style.format({
                    '总客流': '{:,}',
                    '平均客流': '{:.0f}',
                    '最大客流': '{:,}',
                    '平均满载率': '{:.1%}',
                    '最大满载率': '{:.1%}',
                    '运营班次': '{:,}'
                }),
                width='stretch',
                hide_index=True,
                column_config={
                    '满载率等级': st.column_config.Column(
                        '满载率等级',
                        width='small'
                    )
                }
            )
            
            selected_route_detail = st.selectbox(
                "📋 选择线路查看详细数据",
                options=display_analysis['线路名称'].tolist(),
                index=0
            )
            
            if selected_route_detail:
                route_detail_df = filtered_df[filtered_df['线路名称'] == selected_route_detail]
                st.markdown(f"#### {selected_route_detail} 详细客流数据")
                
                route_hourly = route_detail_df.groupby('时段')['客流人数'].agg(['mean', 'max', 'sum']).reset_index()
                route_hourly.columns = ['时段', '平均客流', '最大客流', '总客流']
                route_hourly['平均客流'] = route_hourly['平均客流'].round(0).astype(int)
                
                st.dataframe(
                    route_hourly.style.format({
                        '平均客流': '{:,}',
                        '最大客流': '{:,}',
                        '总客流': '{:,}'
                    }),
                    width='stretch',
                    hide_index=True
                )
    
    with tab4:
        st.markdown("#### 线路优化建议")
        
        suggestions = generate_optimization_suggestions(filtered_df)
        
        high_priority = [s for s in suggestions if s['优先级'] == '高']
        medium_priority = [s for s in suggestions if s['优先级'] == '中']
        low_priority = [s for s in suggestions if s['优先级'] == '低']
        
        col_h, col_m, col_l = st.columns(3)
        with col_h:
            st.markdown(f"<h3 style='color: #e74c3c; margin: 0;'>🔴 高优先级 ({len(high_priority)})</h3>", unsafe_allow_html=True)
        with col_m:
            st.markdown(f"<h3 style='color: #f39c12; margin: 0;'>🟡 中优先级 ({len(medium_priority)})</h3>", unsafe_allow_html=True)
        with col_l:
            st.markdown(f"<h3 style='color: #3498db; margin: 0;'>🔵 低优先级 ({len(low_priority)})</h3>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        for s in suggestions:
            priority_class = 'suggestion-high' if s['优先级'] == '高' else ('suggestion-medium' if s['优先级'] == '中' else 'suggestion-low')
            priority_icon = '🔴' if s['优先级'] == '高' else ('🟡' if s['优先级'] == '中' else '🔵')
            
            with st.expander(f"{priority_icon} [{s['优先级']}] {s['类型']} - {s['线路']}", expanded=s['优先级'] == '高'):
                st.markdown(f"""
                <div class="suggestion-card {priority_class}">
                    <h4 style="margin: 0 0 0.5rem 0; color: #2c3e50;">{s['建议']}</h4>
                    <p style="margin: 0.3rem 0; color: #7f8c8d;"><strong>问题描述:</strong> {s['问题']}</p>
                    <p style="margin: 0.3rem 0; color: #34495e;"><strong>详细数据:</strong> {s['详细数据']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("#### 满载率分级标准")
        standard_df = pd.DataFrame([
            {'等级': '空载', '满载率范围': '< 30%', '建议措施': '减少运营班次，优化线路布局'},
            {'等级': '低载', '满载率范围': '30% - 50%', '建议措施': '可适当减少班次，或调整发车频率'},
            {'等级': '正常', '满载率范围': '50% - 70%', '建议措施': '运力配置合理，保持现状'},
            {'等级': '高载', '满载率范围': '70% - 85%', '建议措施': '关注高峰时段，可适当增加班次'},
            {'等级': '超载', '满载率范围': '≥ 85%', '建议措施': '紧急增加运力，考虑区间车方案'},
        ])
        st.table(standard_df)
    
    hourly_data_export = get_hourly_trend(filtered_df)
    peak_comparison_export = get_peak_comparison(filtered_df)

    @st.cache_data(ttl=600)
    def get_pdf_report(df, route_analysis_df, suggestions_list, peak_comp,
                       heatmap_d, hourly_d, sel_routes):
        return generate_pdf_report(
            df, route_analysis_df, suggestions_list, peak_comp,
            heatmap_d, hourly_d, sel_routes
        )
    
    st.markdown('---')
    st.markdown('<div class="section-header"><h2>📥 数据导出</h2></div>', unsafe_allow_html=True)
    
    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
    
    with col_exp1:
        st.markdown("#### 筛选后数据")
        st.download_button(
            label="📊 导出CSV数据",
            data=filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
            file_name=f"公交客流数据_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
            width='stretch'
        )
    
    with col_exp2:
        st.markdown("#### Markdown报告")
        report = generate_report(filtered_df, route_analysis, suggestions, peak_comparison)
        st.download_button(
            label="� 导出分析报告",
            data=report.encode('utf-8'),
            file_name=f"公交客流分析报告_{datetime.now().strftime('%Y%m%d')}.md",
            mime='text/markdown',
            width='stretch'
        )
    
    with col_exp3:
        st.markdown("#### PDF分析报告")
        try:
            pdf_bytes = get_pdf_report(
                filtered_df, route_analysis, suggestions, peak_comparison_export,
                heatmap_data, hourly_data_export,
                selected_routes if len(selected_routes) <= 10 else None
            )
            st.download_button(
                label="📕 导出PDF报告",
                data=pdf_bytes,
                file_name=f"公交客流分析报告_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime='application/pdf',
                width='stretch'
            )
        except Exception as e:
            st.error(f"PDF生成失败: {str(e)}")
    
    with col_exp4:
        st.markdown("#### 热力图数据")
        st.download_button(
            label="🔥 导出热力图CSV",
            data=heatmap_data.to_csv(encoding='utf-8-sig').encode('utf-8-sig'),
            file_name=f"热力图数据_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
            width='stretch'
        )
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; padding: 1rem;">
        <p style="margin: 0;">© 2024 公交客流数据可视化分析系统 | 基于 Python + Streamlit + Plotly 构建</p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem;">数据更新周期: 每小时自动刷新 | 支持响应式布局，适配多端访问</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
