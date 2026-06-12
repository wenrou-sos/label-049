import pandas as pd
import numpy as np
import streamlit as st
import os
from typing import List, Tuple, Dict

@st.cache_data(ttl=3600, show_spinner="正在加载数据...")
def load_data() -> pd.DataFrame:
    csv_path = 'data/bus_passenger_data.csv'
    xlsx_path = 'data/bus_passenger_data.xlsx'
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
    elif os.path.exists(xlsx_path):
        df = pd.read_excel(xlsx_path)
    else:
        from src.data_generator import generate_bus_data
        df = generate_bus_data()
    
    df['时段标签'] = df['时段'].apply(lambda x: f'{x:02d}:00-{x+1:02d}:00')
    return df

@st.cache_data(ttl=1800)
def filter_data(
    df: pd.DataFrame,
    routes: List[str] = None,
    districts: List[str] = None,
    hours: Tuple[int, int] = None,
    peak_type: str = None,
    dates: List[str] = None
) -> pd.DataFrame:
    filtered = df.copy()
    
    if routes is not None:
        filtered = filtered[filtered['线路名称'].isin(routes)]
    if districts is not None:
        filtered = filtered[filtered['所属区域'].isin(districts)]
    if hours:
        filtered = filtered[(filtered['时段'] >= hours[0]) & (filtered['时段'] <= hours[1])]
    if peak_type and peak_type != '全部':
        if peak_type == '高峰':
            filtered = filtered[filtered['是否高峰']]
        elif peak_type == '早高峰':
            filtered = filtered[filtered['时段类型'] == '早高峰']
        elif peak_type == '晚高峰':
            filtered = filtered[filtered['时段类型'] == '晚高峰']
        elif peak_type == '平峰':
            filtered = filtered[filtered['时段类型'] == '平峰']
    if dates is not None:
        filtered = filtered[filtered['日期'].isin(dates)]
    
    return filtered

@st.cache_data(ttl=1800)
def get_heatmap_data(df: pd.DataFrame, agg_type: str = 'mean') -> pd.DataFrame:
    pivot_table = df.pivot_table(
        index='线路名称',
        columns='时段',
        values='客流人数',
        aggfunc=agg_type,
        fill_value=0
    )
    
    route_order = sorted(pivot_table.index, key=lambda x: int(''.join(filter(str.isdigit, x))))
    pivot_table = pivot_table.reindex(route_order)
    
    return pivot_table

@st.cache_data(ttl=1800)
def get_route_analysis(df: pd.DataFrame) -> pd.DataFrame:
    route_stats = df.groupby('线路名称').agg({
        '客流人数': ['sum', 'mean', 'max'],
        '满载率': ['mean', 'max'],
        '所属区域': 'first',
        '车辆容量': 'first',
        '运营班次': 'sum'
    }).reset_index()
    
    route_stats.columns = ['线路名称', '总客流', '平均客流', '最大客流', 
                           '平均满载率', '最大满载率', '所属区域', '车辆容量', '运营班次']
    
    route_stats['平均满载率'] = route_stats['平均满载率'].round(3)
    route_stats['最大满载率'] = route_stats['最大满载率'].round(3)
    route_stats['平均客流'] = route_stats['平均客流'].round(1)
    
    route_stats = route_stats.sort_values('平均满载率', ascending=False)
    route_stats['满载率等级'] = pd.cut(
        route_stats['平均满载率'],
        bins=[0, 0.3, 0.5, 0.7, 0.9, 2.0],
        labels=['空载', '低载', '正常', '高载', '超载']
    )
    
    return route_stats

@st.cache_data(ttl=1800)
def get_peak_comparison(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    peak_data = df[df['时段类型'] == '早高峰']
    off_peak_data = df[df['时段类型'] == '平峰']
    evening_peak_data = df[df['时段类型'] == '晚高峰']
    
    peak_stats = peak_data.groupby('线路名称')['客流人数'].agg(['mean', 'sum']).reset_index()
    peak_stats.columns = ['线路名称', '早高峰平均客流', '早高峰总客流']
    
    evening_stats = evening_peak_data.groupby('线路名称')['客流人数'].agg(['mean', 'sum']).reset_index()
    evening_stats.columns = ['线路名称', '晚高峰平均客流', '晚高峰总客流']
    
    off_peak_stats = off_peak_data.groupby('线路名称')['客流人数'].agg(['mean', 'sum']).reset_index()
    off_peak_stats.columns = ['线路名称', '平峰平均客流', '平峰总客流']
    
    comparison = peak_stats.merge(evening_stats, on='线路名称').merge(off_peak_stats, on='线路名称')
    
    comparison['早高峰/平峰倍数'] = (comparison['早高峰平均客流'] / comparison['平峰平均客流']).round(2)
    comparison['晚高峰/平峰倍数'] = (comparison['晚高峰平均客流'] / comparison['平峰平均客流']).round(2)
    
    return {
        'comparison': comparison,
        'peak_data': peak_data,
        'off_peak_data': off_peak_data,
        'evening_peak_data': evening_peak_data
    }

@st.cache_data(ttl=1800)
def get_hourly_trend(df: pd.DataFrame, routes: List[str] = None) -> pd.DataFrame:
    if routes:
        df = df[df['线路名称'].isin(routes)]
    
    hourly = df.groupby('时段')['客流人数'].agg(['mean', 'sum', 'count']).reset_index()
    hourly.columns = ['时段', '平均客流', '总客流', '记录数']
    hourly['平均客流'] = hourly['平均客流'].round(1)
    
    return hourly

@st.cache_data(ttl=1800)
def get_district_analysis(df: pd.DataFrame) -> pd.DataFrame:
    district_stats = df.groupby('所属区域').agg({
        '客流人数': ['sum', 'mean', 'count'],
        '满载率': ['mean', 'max'],
        '线路名称': 'nunique'
    }).reset_index()
    
    district_stats.columns = ['区域', '总客流', '平均客流', '记录数', '平均满载率', '最大满载率', '线路数']
    district_stats['平均满载率'] = district_stats['平均满载率'].round(3)
    district_stats['最大满载率'] = district_stats['最大满载率'].round(3)
    district_stats['平均客流'] = district_stats['平均客流'].round(1)
    
    return district_stats.sort_values('总客流', ascending=False)

@st.cache_data(ttl=1800)
def generate_optimization_suggestions(df: pd.DataFrame) -> List[Dict]:
    route_analysis = get_route_analysis(df)
    suggestions = []
    
    overloaded = route_analysis[route_analysis['平均满载率'] > 0.85]
    for _, row in overloaded.iterrows():
        suggestions.append({
            '类型': '运力增加建议',
            '优先级': '高',
            '线路': row['线路名称'],
            '问题': f'平均满载率达到 {row["平均满载率"]:.1%}，存在超载风险',
            '建议': f'建议在高峰时段增加 {max(2, int((row["平均满载率"] - 0.7) * 10))} 个运营班次',
            '详细数据': f'区域: {row["所属区域"]}, 最大满载率: {row["最大满载率"]:.1%}, 日均客流: {row["总客流"]:,}'
        })
    
    underloaded = route_analysis[route_analysis['平均满载率'] < 0.3]
    for _, row in underloaded.iterrows():
        suggestions.append({
            '类型': '运力优化建议',
            '优先级': '中',
            '线路': row['线路名称'],
            '问题': f'平均满载率仅 {row["平均满载率"]:.1%}，运力过剩',
            '建议': f'建议在平峰时段减少 {max(1, int((0.4 - row["平均满载率"]) * 10))} 个运营班次',
            '详细数据': f'区域: {row["所属区域"]}, 日均客流: {row["总客流"]:,}'
        })
    
    peak_comparison = get_peak_comparison(df)['comparison']
    high_peak_routes = peak_comparison[peak_comparison['早高峰/平峰倍数'] > 2.5]
    for _, row in high_peak_routes.head(5).iterrows():
        suggestions.append({
            '类型': '高峰调度建议',
            '优先级': '中',
            '线路': row['线路名称'],
            '问题': f'早高峰客流是平峰的 {row["早高峰/平峰倍数"]} 倍，波动性大',
            '建议': '建议实施高峰时段区间车或大站快车策略',
            '详细数据': f'早高峰平均客流: {row["早高峰平均客流"]:.0f}, 平峰平均客流: {row["平峰平均客流"]:.0f}'
        })
    
    suggestions.sort(key=lambda x: 0 if x['优先级'] == '高' else (1 if x['优先级'] == '中' else 2))
    
    return suggestions

def get_unique_values(df: pd.DataFrame) -> Dict:
    return {
        'routes': sorted(df['线路名称'].unique(), key=lambda x: int(''.join(filter(str.isdigit, x)))),
        'districts': sorted(df['所属区域'].unique()),
        'hours': sorted(df['时段'].unique()),
        'dates': sorted(df['日期'].unique()),
        'min_hour': df['时段'].min(),
        'max_hour': df['时段'].max()
    }
