import io
import os
from datetime import datetime
from typing import List, Dict

import pandas as pd
import numpy as np
from plotly.graph_objects import Figure
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.visualizations import (
    create_passenger_heatmap, create_load_rate_ranking,
    create_peak_comparison_chart, create_hourly_trend
)

PAGE_W, PAGE_H = A4

def _register_fonts():
    font_names = ['SimSun', 'Microsoft YaHei', 'SimHei', 'STSong']
    font_paths = [
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\STSONG.TTF",
    ]
    for name, path in zip(font_names, font_paths):
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                return name
            except Exception:
                continue
    return 'Helvetica'


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.page_number = 0

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
        self.page_number += 1

    def save(self):
        num_pages = len(self._saved_page_states)
        for (page_num, state) in enumerate(self._saved_page_states, 1):
            self.__dict__.update(state)
            if page_num >= 2:
                self.draw_page_number(page_num, num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_num, total_count):
        self.setFont(_register_fonts() or 'Helvetica', 9)
        self.setFillColor(colors.grey)
        self.drawRightString(PAGE_W - 2 * cm, 1.5 * cm, f"第 {page_num} 页 / 共 {total_count} 页")
        self.drawString(2 * cm, 1.5 * cm, "公交客流数据可视化分析系统")


def _get_styles(font_name):
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CNTitle', fontName=font_name, fontSize=28, leading=40,
        textColor=colors.white, alignment=TA_CENTER, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'CNSubtitle', fontName=font_name, fontSize=14, leading=22,
        textColor=colors.Color(0.9, 0.95, 1.0), alignment=TA_CENTER, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'CNH1', fontName=font_name, fontSize=18, leading=28,
        textColor=colors.HexColor('#1e3c72'), spaceBefore=6, spaceAfter=12,
        alignment=TA_LEFT, borderPadding=(0, 0, 4, 0)
    ))
    styles.add(ParagraphStyle(
        'CNH2', fontName=font_name, fontSize=14, leading=22,
        textColor=colors.HexColor('#2a5298'), spaceBefore=10, spaceAfter=8,
        alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        'CNBody', fontName=font_name, fontSize=10.5, leading=18,
        textColor=colors.HexColor('#2c3e50'), alignment=TA_JUSTIFY, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'CNBullet', fontName=font_name, fontSize=10.5, leading=18,
        textColor=colors.HexColor('#2c3e50'), alignment=TA_LEFT, spaceAfter=4,
        leftIndent=16
    ))
    styles.add(ParagraphStyle(
        'CNCaption', fontName=font_name, fontSize=9, leading=14,
        textColor=colors.grey, alignment=TA_CENTER, spaceBefore=4, spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        'CNFooter', fontName=font_name, fontSize=8, leading=12,
        textColor=colors.grey, alignment=TA_CENTER
    ))
    return styles


def _fig_to_image(fig: Figure, width: float = 17 * cm, height: float = 10 * cm) -> Image:
    img_bytes = fig.to_image(format='png', width=int(width * 3.5), height=int(height * 3.5), scale=2)
    img = Image(io.BytesIO(img_bytes), width=width, height=height)
    return img


def _make_table(df: pd.DataFrame, font_name: str, max_rows: int = 10) -> Table:
    columns = list(df.columns)
    header = [Paragraph(str(c), ParagraphStyle('TblH', fontName=font_name, fontSize=9.5,
                                                textColor=colors.white, alignment=TA_CENTER, leading=14))
              for c in columns]
    data = [header]
    display_df = df.head(max_rows)
    for _, row in display_df.iterrows():
        r = []
        for c in columns:
            v = row[c]
            if isinstance(v, (float, np.floating)):
                if 0 < v < 1:
                    txt = f"{v * 100:.1f}%"
                else:
                    txt = f"{v:,.1f}"
            elif isinstance(v, (int, np.integer)):
                txt = f"{v:,}"
            else:
                txt = str(v)
            r.append(Paragraph(txt, ParagraphStyle('TblC', fontName=font_name, fontSize=9,
                                                   textColor=colors.HexColor('#2c3e50'),
                                                   alignment=TA_CENTER, leading=13)))
        data.append(r)

    col_w = (PAGE_W - 4 * cm) / len(columns)
    t = Table(data, colWidths=[col_w] * len(columns), hAlign='CENTER')
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#f8fbff'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dce6f2')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.2, colors.HexColor('#2a5298')),
    ])
    t.setStyle(style)
    return t


def _draw_cover(c, doc):
    font_name = _register_fonts()
    w, h = PAGE_W, PAGE_H

    c.setFillColor(colors.HexColor('#1e3c72'))
    c.rect(0, h * 0.55, w, h * 0.45, fill=1, stroke=0)

    c.setFillColor(colors.HexColor('#2a5298'))
    c.rect(0, 0, w, h * 0.15, fill=1, stroke=0)

    c.setFillColor(colors.HexColor('#3498db'))
    c.circle(w - 3 * cm, h - 3 * cm, 2.5 * cm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#f39c12'))
    c.circle(w - 8 * cm, h - 7 * cm, 1.5 * cm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#2ecc71'))
    c.circle(3 * cm, h * 0.45, 1.2 * cm, fill=1, stroke=0)

    c.setFont(font_name, 32)
    c.setFillColor(colors.white)
    c.drawCentredString(w / 2, h * 0.78, "公交客流数据分析报告")

    c.setFont(font_name, 14)
    c.setFillColor(colors.Color(0.85, 0.92, 1.0))
    c.drawCentredString(w / 2, h * 0.72, "BUS PASSENGER FLOW ANALYSIS REPORT")

    c.setStrokeColor(colors.Color(0.7, 0.85, 1.0))
    c.setLineWidth(1.5)
    c.line(w * 0.3, h * 0.68, w * 0.7, h * 0.68)

    c.setFont(font_name, 12)
    c.setFillColor(colors.Color(0.9, 0.95, 1.0))
    c.drawCentredString(w / 2, h * 0.63, "基于 Python + Streamlit + Plotly 的智能公交调度决策支持平台")

    now = datetime.now().strftime('%Y年%m月%d日')
    c.setFont(font_name, 11)
    c.setFillColor(colors.white)
    c.drawCentredString(w / 2, h * 0.59, f"报告生成日期：{now}")

    info_items = [
        ("📊", "数据可视化", "多维度客流热力图与趋势分析"),
        ("⚖️", "高峰对比", "高峰/平峰时段客流智能对比"),
        ("🏆", "满载排名", "线路满载率排序与分级评估"),
        ("💡", "优化建议", "基于数据的线路调度决策建议"),
    ]
    y = h * 0.40
    for icon, title, desc in info_items:
        c.setFont(font_name, 12)
        c.setFillColor(colors.HexColor('#1e3c72'))
        c.drawString(3 * cm, y, f"{icon}  {title}")
        c.setFont(font_name, 10)
        c.setFillColor(colors.HexColor('#7f8c8d'))
        c.drawString(3 * cm + 3.2 * cm, y, desc)
        y -= 0.9 * cm

    c.setFont(font_name, 14)
    c.setFillColor(colors.white)
    c.drawCentredString(w / 2, h * 0.08, "公交客流数据可视化分析系统")
    c.setFont(font_name, 10)
    c.drawCentredString(w / 2, h * 0.05, "© Public Transport Data Analysis Platform")

    c.showPage()


def generate_pdf_report(
    df: pd.DataFrame,
    route_analysis: pd.DataFrame,
    peak_comparison: Dict,
    suggestions: List[Dict],
    heatmap_agg: str = 'mean'
) -> bytes:
    font_name = _register_fonts()
    styles = _get_styles(font_name)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2.5 * cm,
        title="公交客流数据分析报告",
        author="公交客流数据可视化分析系统"
    )

    story = []
    from src.data_processor import get_heatmap_data, get_hourly_trend

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("一、整体概况", styles['CNH1']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2a5298'), spaceBefore=0, spaceAfter=10))

    total_passengers = df['客流人数'].sum()
    avg_load = df['满载率'].mean()
    peak_load = df[df['是否高峰']]['满载率'].mean()
    unique_routes = df['线路名称'].nunique()
    unique_districts = df['所属区域'].nunique()
    unique_days = df['日期'].nunique()

    kpi_data = [
        ['指标名称', '数值', '指标名称', '数值'],
        ['分析线路数', f'{unique_routes} 条', '覆盖区域数', f'{unique_districts} 个'],
        ['统计天数', f'{unique_days} 天', '总客流人次', f'{total_passengers:,}'],
        ['平均满载率', f'{avg_load * 100:.1f}%', '高峰满载率', f'{peak_load * 100:.1f}%'],
    ]
    kpi_table = Table(kpi_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm], hAlign='CENTER')
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f7ff'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dce6f2')),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph("24小时客流趋势", styles['CNH2']))
    hourly_data = get_hourly_trend(df)
    trend_fig = create_hourly_trend(hourly_data)
    trend_fig.update_layout(title=None, margin=dict(l=50, r=30, t=30, b=50))
    story.append(_fig_to_image(trend_fig, width=17 * cm, height=9 * cm))
    story.append(Paragraph("图1：24小时客流趋势（高峰时段高亮标注）", styles['CNCaption']))

    story.append(PageBreak())

    story.append(Paragraph("二、客流热力图分析", styles['CNH1']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2a5298'), spaceBefore=0, spaceAfter=10))

    heatmap_data = get_heatmap_data(df, agg_type=heatmap_agg)
    agg_name = {'mean': '平均值', 'sum': '总和', 'max': '最大值'}.get(heatmap_agg, '平均值')
    heatmap_fig = create_passenger_heatmap(heatmap_data, title=f"公交客流热力图（按{agg_name}）")
    heatmap_fig.update_layout(
        title=None,
        height=max(500, len(heatmap_data) * 30),
        margin=dict(l=80, r=40, t=30, b=80),
        annotations=[]
    )
    img_h = min(13 * cm, max(7 * cm, len(heatmap_data) * 0.55 * cm))
    story.append(_fig_to_image(heatmap_fig, width=17 * cm, height=img_h))
    story.append(Paragraph(f"图2：线路×时段客流热力图（{agg_name}）", styles['CNCaption']))

    story.append(Paragraph("热力图说明：", styles['CNH2']))
    heatmap_desc = [
        f"共展示 {len(heatmap_data)} 条公交线路 × {len(heatmap_data.columns)} 个时段的客流分布。",
        "颜色越深表示客流密度越高，颜色越浅表示客流越低。",
        f"聚合方式采用：{agg_name}。",
    ]
    for d in heatmap_desc:
        story.append(Paragraph(f"• {d}", styles['CNBullet']))
    story.append(Spacer(1, 0.5 * cm))

    story.append(PageBreak())

    story.append(Paragraph("三、线路满载率分析", styles['CNH1']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2a5298'), spaceBefore=0, spaceAfter=10))

    rank_fig = create_load_rate_ranking(route_analysis, top_n=min(15, len(route_analysis)))
    rank_fig.update_layout(title=None, margin=dict(l=80, r=60, t=30, b=50))
    rank_h = min(12 * cm, max(7 * cm, len(route_analysis.head(15)) * 0.55 * cm))
    story.append(_fig_to_image(rank_fig, width=17 * cm, height=rank_h))
    story.append(Paragraph("图3：公交线路满载率排名（按平均满载率降序）", styles['CNCaption']))

    story.append(Paragraph("TOP 5 最高满载率线路", styles['CNH2']))
    top5 = route_analysis.head(5)[['线路名称', '平均满载率', '最大满载率', '满载率等级', '所属区域', '总客流']]
    story.append(_make_table(top5, font_name))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("TOP 5 最低满载率线路", styles['CNH2']))
    bottom5 = route_analysis.tail(5).iloc[::-1][['线路名称', '平均满载率', '最大满载率', '满载率等级', '所属区域', '总客流']]
    story.append(_make_table(bottom5, font_name))
    story.append(Spacer(1, 0.5 * cm))

    story.append(PageBreak())

    story.append(Paragraph("四、高峰与平峰对比分析", styles['CNH1']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2a5298'), spaceBefore=0, spaceAfter=10))

    peak_data = peak_comparison['comparison']
    peak_fig = create_peak_comparison_chart(peak_data)
    peak_fig.update_layout(title=None, margin=dict(l=80, r=30, t=30, b=50))
    peak_h = min(11 * cm, max(7 * cm, len(peak_data) * 0.55 * cm))
    story.append(_fig_to_image(peak_fig, width=17 * cm, height=peak_h))
    story.append(Paragraph("图4：高峰与平峰时段客流对比（按线路）", styles['CNCaption']))

    story.append(Paragraph("高峰时段关键指标汇总", styles['CNH2']))
    avg_morning = peak_data['早高峰平均客流'].mean()
    avg_evening = peak_data['晚高峰平均客流'].mean()
    avg_off = peak_data['平峰平均客流'].mean()
    morning_ratio = peak_data['早高峰/平峰倍数'].mean()
    evening_ratio = peak_data['晚高峰/平峰倍数'].mean()

    peak_summary_data = [
        ['时段类型', '平均客流 (人/小时)', '相比平峰倍数'],
        ['早高峰 (7:00-9:00)', f'{avg_morning:.0f}', f'{morning_ratio:.2f}x'],
        ['晚高峰 (17:00-19:00)', f'{avg_evening:.0f}', f'{evening_ratio:.2f}x'],
        ['平峰时段', f'{avg_off:.0f}', '1.00x'],
    ]
    pst = Table(peak_summary_data, colWidths=[6 * cm, 5.5 * cm, 5.5 * cm], hAlign='CENTER')
    pst.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fde8e8')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fff5e6')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#e8f4fd')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dce6f2')),
    ]))
    story.append(pst)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("高峰/平峰对比明细数据", styles['CNH2']))
    detail_df = peak_data[['线路名称', '早高峰平均客流', '晚高峰平均客流', '平峰平均客流',
                           '早高峰/平峰倍数', '晚高峰/平峰倍数']].head(10)
    story.append(_make_table(detail_df, font_name, max_rows=10))

    story.append(PageBreak())

    story.append(Paragraph("五、线路优化建议", styles['CNH1']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2a5298'), spaceBefore=0, spaceAfter=10))

    high_s = [s for s in suggestions if s['优先级'] == '高']
    med_s = [s for s in suggestions if s['优先级'] == '中']
    low_s = [s for s in suggestions if s['优先级'] == '低']

    story.append(Paragraph(f"🔴 高优先级建议（共 {len(high_s)} 条）", styles['CNH2']))
    for i, s in enumerate(high_s[:5], 1):
        story.append(KeepTogether([
            Paragraph(f"<b>建议 {i}：{s['类型']} — {s['线路']}</b>",
                      ParagraphStyle('RecH', fontName=font_name, fontSize=11,
                                     textColor=colors.HexColor('#c0392b'), leading=18, spaceBefore=4)),
            Paragraph(f"<b>问题：</b>{s['问题']}", styles['CNBullet']),
            Paragraph(f"<b>建议：</b>{s['建议']}", styles['CNBullet']),
            Paragraph(f"<b>数据：</b>{s['详细数据']}",
                      ParagraphStyle('RecD', fontName=font_name, fontSize=9.5,
                                     textColor=colors.HexColor('#7f8c8d'), leading=15,
                                     leftIndent=16, spaceAfter=6)),
        ]))

    story.append(Paragraph(f"🟡 中优先级建议（共 {len(med_s)} 条）", styles['CNH2']))
    for i, s in enumerate(med_s[:5], 1):
        story.append(KeepTogether([
            Paragraph(f"<b>建议 {i}：{s['类型']} — {s['线路']}</b>",
                      ParagraphStyle('RecM', fontName=font_name, fontSize=11,
                                     textColor=colors.HexColor('#d68910'), leading=18, spaceBefore=3)),
            Paragraph(f"<b>问题：</b>{s['问题']}", styles['CNBullet']),
            Paragraph(f"<b>建议：</b>{s['建议']}", styles['CNBullet']),
        ]))

    if low_s:
        story.append(Paragraph(f"🔵 低优先级建议（共 {len(low_s)} 条）", styles['CNH2']))
        for i, s in enumerate(low_s[:3], 1):
            story.append(Paragraph(
                f"{i}. [{s['类型']}] {s['线路']}：{s['建议']}",
                styles['CNBullet']
            ))

    story.append(PageBreak())

    story.append(Paragraph("六、关键指标阈值说明", styles['CNH1']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2a5298'), spaceBefore=0, spaceAfter=10))

    standard_data = [
        ['满载率等级', '满载率范围', '建议措施', '状态指示'],
        ['空载', '< 30%', '减少运营班次，优化线路布局', '运力过剩'],
        ['低载', '30% - 50%', '可适当减少班次，或调整发车频率', '运力偏松'],
        ['正常', '50% - 70%', '运力配置合理，保持现状', '运力合理'],
        ['高载', '70% - 85%', '关注高峰时段，可适当增加班次', '运力偏紧'],
        ['超载', '≥ 85%', '紧急增加运力，考虑区间车方案', '超载风险'],
    ]
    std_table = Table(standard_data, colWidths=[3 * cm, 3.5 * cm, 6.5 * cm, 4 * cm], hAlign='CENTER')
    std_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e8f4fd')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#eafaf1')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#fef9e7')),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#fef5e7')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#fde8e8')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dce6f2')),
    ]))
    story.append(std_table)
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph("报告说明", styles['CNH2']))
    notes = [
        "本报告基于系统采集的公交客流数据自动生成，所有数据仅供参考。",
        f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "满载率计算方式：实际客流人数 / 车辆核定容量 × 100%。",
        "高峰时段定义：早高峰 7:00-9:00，晚高峰 17:00-19:00。",
    ]
    for n in notes:
        story.append(Paragraph(f"• {n}", styles['CNBullet']))

    story.append(Spacer(1, 2 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph("© 公交客流数据可视化分析系统  |  Powered by Python + Streamlit + Plotly", styles['CNFooter']))

    def on_first_page(canv, doc_obj):
        _draw_cover(canv, doc_obj)

    def on_later_pages(canv, doc_obj):
        pass

    doc.build(story, canvasmaker=NumberedCanvas)

    return buf.getvalue()
