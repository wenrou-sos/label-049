import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict

def create_passenger_heatmap(
    heatmap_data: pd.DataFrame,
    title: str = "公交客流热力图",
    colorscale: str = "Viridis"
) -> go.Figure:
    hour_labels = [f'{h:02d}:00' for h in heatmap_data.columns]
    
    custom_colorscale = [
        [0.0, '#f0f9e8'],
        [0.2, '#ccebc5'],
        [0.4, '#a8ddb5'],
        [0.6, '#4eb3d3'],
        [0.8, '#2b8cbe'],
        [1.0, '#08589e']
    ]
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=hour_labels,
        y=heatmap_data.index,
        colorscale=custom_colorscale,
        colorbar=dict(
            title=dict(
                text='客流人数',
                side='right',
                font=dict(size=12)
            ),
            tickfont=dict(size=10)
        ),
        hovertemplate=
        '<b>线路</b>: %{y}<br>' +
        '<b>时段</b>: %{x}<br>' +
        '<b>客流人数</b>: %{z:.0f}<br>' +
        '<extra></extra>',
        showscale=True
    ))
    
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2c3e50')
        ),
        xaxis=dict(
            title=dict(text='时段', font=dict(size=14, color='#34495e')),
            tickangle=45,
            tickfont=dict(size=10),
            gridcolor='rgba(0,0,0,0.1)',
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            title=dict(text='公交线路', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=10),
            gridcolor='rgba(0,0,0,0.1)',
            showgrid=True,
            zeroline=False
        ),
        height=max(500, len(heatmap_data) * 35),
        margin=dict(l=100, r=80, t=80, b=100),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Microsoft YaHei, Arial, sans-serif')
    )
    
    for i in range(len(heatmap_data.index)):
        for j in range(len(heatmap_data.columns)):
            value = heatmap_data.iloc[i, j]
            if value > 0:
                fig.add_annotation(
                    x=j,
                    y=i,
                    text=str(int(value)),
                    showarrow=False,
                    font=dict(
                        size=9,
                        color='white' if value > heatmap_data.values.max() * 0.5 else '#2c3e50'
                    )
                )
    
    return fig

def create_peak_comparison_chart(
    comparison_data: pd.DataFrame,
    selected_routes: List[str] = None
) -> go.Figure:
    display_data = comparison_data.copy()
    if selected_routes:
        display_data = display_data[display_data['线路名称'].isin(selected_routes)]
    
    display_data = display_data.sort_values('早高峰平均客流', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=display_data['线路名称'],
        x=display_data['早高峰平均客流'],
        name='早高峰',
        orientation='h',
        marker=dict(color='#e74c3c'),
        hovertemplate='<b>%{y}</b><br>早高峰平均客流: %{x:.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        y=display_data['线路名称'],
        x=display_data['晚高峰平均客流'],
        name='晚高峰',
        orientation='h',
        marker=dict(color='#f39c12'),
        hovertemplate='<b>%{y}</b><br>晚高峰平均客流: %{x:.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        y=display_data['线路名称'],
        x=display_data['平峰平均客流'],
        name='平峰',
        orientation='h',
        marker=dict(color='#3498db'),
        hovertemplate='<b>%{y}</b><br>平峰平均客流: %{x:.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='高峰与平峰时段客流对比',
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2c3e50')
        ),
        xaxis=dict(
            title=dict(text='平均客流人数', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=11),
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title=dict(text='公交线路', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=11)
        ),
        barmode='group',
        height=max(450, len(display_data) * 45),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=12)
        ),
        margin=dict(l=100, r=40, t=80, b=40),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Microsoft YaHei, Arial, sans-serif')
    )
    
    return fig

def create_load_rate_ranking(
    route_analysis: pd.DataFrame,
    top_n: int = 15
) -> go.Figure:
    display_data = route_analysis.head(top_n).copy()
    display_data = display_data.sort_values('平均满载率', ascending=True)
    
    color_map = {
        '空载': '#3498db',
        '低载': '#2ecc71',
        '正常': '#f1c40f',
        '高载': '#e67e22',
        '超载': '#e74c3c'
    }
    
    colors = [color_map.get(level, '#95a5a6') for level in display_data['满载率等级']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=display_data['线路名称'],
        x=display_data['平均满载率'] * 100,
        orientation='h',
        marker=dict(color=colors),
        text=[f'{v*100:.1f}%' for v in display_data['平均满载率']],
        textposition='outside',
        customdata=list(zip(
            display_data['所属区域'],
            display_data['车辆容量'],
            display_data['平均客流'],
            display_data['最大满载率'] * 100
        )),
        hovertemplate=
        '<b>%{y}</b><br>' +
        '平均满载率: %{x:.1f}%<br>' +
        '所属区域: %{customdata[0]}<br>' +
        '车辆容量: %{customdata[1]} 人<br>' +
        '平均客流: %{customdata[2]:.0f} 人<br>' +
        '最大满载率: %{customdata[3]:.1f}%<br>' +
        '<extra></extra>'
    ))
    
    fig.add_shape(
        type='line',
        x0=85, y0=0, x1=85, y1=len(display_data),
        line=dict(color='#e74c3c', width=2, dash='dash'),
        xref='x', yref='y'
    )
    fig.add_annotation(
        x=85, y=len(display_data) - 0.5,
        text='超载警戒线 (85%)',
        showarrow=False,
        xanchor='left',
        font=dict(color='#e74c3c', size=10)
    )
    
    fig.update_layout(
        title=dict(
            text='公交线路满载率排名',
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2c3e50')
        ),
        xaxis=dict(
            title=dict(text='平均满载率 (%)', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=11),
            gridcolor='rgba(0,0,0,0.1)',
            range=[0, max(100, display_data['平均满载率'].max() * 110)]
        ),
        yaxis=dict(
            title=dict(text='公交线路', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=11)
        ),
        height=max(450, len(display_data) * 45),
        margin=dict(l=100, r=80, t=80, b=40),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Microsoft YaHei, Arial, sans-serif')
    )
    
    return fig

def create_hourly_trend(
    hourly_data: pd.DataFrame,
    selected_routes: List[str] = None
) -> go.Figure:
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hourly_data['时段'].apply(lambda x: f'{x:02d}:00'),
        y=hourly_data['平均客流'],
        mode='lines+markers',
        name='平均客流',
        line=dict(color='#3498db', width=3),
        marker=dict(size=8, color='#2980b9'),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.15)',
        hovertemplate=
        '<b>时段</b>: %{x}<br>' +
        '<b>平均客流</b>: %{y:.0f}<br>' +
        '<extra></extra>'
    ))
    
    peak_hours = ['07:00', '08:00', '09:00', '17:00', '18:00', '19:00']
    peak_mask = hourly_data['时段'].apply(lambda x: f'{x:02d}:00').isin(peak_hours)
    peak_data = hourly_data[peak_mask]
    
    fig.add_trace(go.Scatter(
        x=peak_data['时段'].apply(lambda x: f'{x:02d}:00'),
        y=peak_data['平均客流'],
        mode='markers',
        name='高峰时段',
        marker=dict(size=12, color='#e74c3c', symbol='star'),
        hovertemplate=
        '<b>高峰时段</b>: %{x}<br>' +
        '<b>平均客流</b>: %{y:.0f}<br>' +
        '<extra></extra>'
    ))
    
    fig.add_vrect(
        x0=5.5, x1=9.5,
        fillcolor='#e74c3c', opacity=0.1,
        layer='below', line_width=0,
        annotation_text='早高峰',
        annotation_position='top left'
    )
    fig.add_vrect(
        x0=15.5, x1=19.5,
        fillcolor='#e74c3c', opacity=0.1,
        layer='below', line_width=0,
        annotation_text='晚高峰',
        annotation_position='top left'
    )
    
    fig.update_layout(
        title=dict(
            text='24小时客流趋势图',
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2c3e50')
        ),
        xaxis=dict(
            title=dict(text='时段', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=10),
            tickangle=45,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title=dict(text='平均客流人数', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=11),
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        height=500,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=12)
        ),
        margin=dict(l=60, r=40, t=80, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Microsoft YaHei, Arial, sans-serif'),
        hovermode='x unified'
    )
    
    return fig

def create_multi_route_comparison(
    df: pd.DataFrame,
    selected_routes: List[str]
) -> go.Figure:
    route_data = df[df['线路名称'].isin(selected_routes)]
    grouped = route_data.groupby(['时段', '线路名称'])['客流人数'].mean().reset_index()
    
    fig = go.Figure()
    
    color_palette = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
    
    for i, route in enumerate(selected_routes):
        route_df = grouped[grouped['线路名称'] == route]
        color = color_palette[i % len(color_palette)]
        
        fig.add_trace(go.Scatter(
            x=route_df['时段'].apply(lambda x: f'{x:02d}:00'),
            y=route_df['客流人数'],
            mode='lines+markers',
            name=route,
            line=dict(width=3, color=color),
            marker=dict(size=6, color=color),
            hovertemplate=
            f'<b>{route}</b><br>' +
            '<b>时段</b>: %{x}<br>' +
            '<b>客流</b>: %{y:.0f}<br>' +
            '<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text='多线路客流对比分析',
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2c3e50')
        ),
        xaxis=dict(
            title=dict(text='时段', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=10),
            tickangle=45,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title=dict(text='平均客流人数', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=11),
            gridcolor='rgba(0,0,0,0.1)'
        ),
        height=500,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=12)
        ),
        margin=dict(l=60, r=40, t=80, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Microsoft YaHei, Arial, sans-serif'),
        hovermode='x unified'
    )
    
    return fig

def create_district_pie(district_data: pd.DataFrame) -> go.Figure:
    fig = go.Figure(data=[go.Pie(
        labels=district_data['区域'],
        values=district_data['总客流'],
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
        marker=dict(
            colors=['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'],
            line=dict(color='white', width=2)
        ),
        hovertemplate=
        '<b>%{label}</b><br>' +
        '总客流: %{value:,}<br>' +
        '占比: %{percent}<br>' +
        '<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(
            text='各区域客流分布',
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2c3e50')
        ),
        height=450,
        margin=dict(l=40, r=40, t=80, b=40),
        paper_bgcolor='white',
        font=dict(family='Microsoft YaHei, Arial, sans-serif'),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.1,
            xanchor='center',
            x=0.5
        )
    )
    
    return fig

def create_load_rate_distribution(route_analysis: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        x=route_analysis['平均满载率'] * 100,
        name='满载率分布',
        marker=dict(color='#3498db'),
        boxpoints='all',
        jitter=0.3,
        pointpos=-1.8,
        text=route_analysis['线路名称'],
        hovertemplate=
        '<b>%{text}</b><br>' +
        '满载率: %{x:.1f}%<br>' +
        '<extra></extra>'
    ))
    
    fig.add_shape(
        type='line',
        x0=85, y0=-1, x1=85, y1=1,
        line=dict(color='#e74c3c', width=2, dash='dash'),
        xref='x', yref='paper'
    )
    fig.add_annotation(
        x=85, y=0.95,
        text='超载警戒线 (85%)',
        showarrow=False,
        xanchor='left',
        font=dict(color='#e74c3c', size=10)
    )
    
    fig.update_layout(
        title=dict(
            text='线路满载率分布',
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2c3e50')
        ),
        xaxis=dict(
            title=dict(text='满载率 (%)', font=dict(size=14, color='#34495e')),
            tickfont=dict(size=11),
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=False
        ),
        yaxis=dict(showticklabels=False),
        height=350,
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Microsoft YaHei, Arial, sans-serif')
    )
    
    return fig
