import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime
from io import BytesIO
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, Line


FONT_DIR = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')

def _register_chinese_fonts():
    font_registered = {'yahei': False, 'yahei_bold': False, 'simhei': False}

    yahei_path = os.path.join(FONT_DIR, 'msyh.ttc')
    if os.path.exists(yahei_path):
        try:
            pdfmetrics.registerFont(TTFont('MicrosoftYaHei', yahei_path, subfontIndex=0))
            font_registered['yahei'] = True
        except Exception:
            pass

    yahei_bold_path = os.path.join(FONT_DIR, 'msyhbd.ttc')
    if os.path.exists(yahei_bold_path):
        try:
            pdfmetrics.registerFont(TTFont('MicrosoftYaHeiBold', yahei_bold_path, subfontIndex=0))
            font_registered['yahei_bold'] = True
        except Exception:
            pass

    simhei_path = os.path.join(FONT_DIR, 'simhei.ttf')
    if os.path.exists(simhei_path):
        try:
            pdfmetrics.registerFont(TTFont('SimHei', simhei_path))
            font_registered['simhei'] = True
        except Exception:
            pass

    if font_registered['yahei']:
        return 'MicrosoftYaHei', 'MicrosoftYaHeiBold' if font_registered['yahei_bold'] else 'MicrosoftYaHei'
    elif font_registered['simhei']:
        return 'SimHei', 'SimHei'
    else:
        return 'Helvetica', 'Helvetica-Bold'


FONT_NAME, FONT_BOLD = _register_chinese_fonts()


def _setup_matplotlib_font():
    candidates = [
        os.path.join(FONT_DIR, 'msyh.ttc'),
        os.path.join(FONT_DIR, 'simhei.ttf'),
        os.path.join(FONT_DIR, 'simsun.ttc'),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                fm.fontManager.addfont(path)
                prop = fm.FontProperties(fname=path)
                return prop.get_name()
            except Exception:
                continue
    return None


_MPL_FONT = _setup_matplotlib_font()
plt.rcParams['axes.unicode_minus'] = False
if _MPL_FONT:
    plt.rcParams['font.sans-serif'] = [_MPL_FONT] + plt.rcParams.get('font.sans-serif', [])

PRIMARY_COLOR = HexColor('#1e3c72')
SECONDARY_COLOR = HexColor('#2a5298')
ACCENT_BLUE = HexColor('#3498db')
ACCENT_GREEN = HexColor('#27ae60')
ACCENT_RED = HexColor('#e74c3c')
ACCENT_ORANGE = HexColor('#f39c12')
LIGHT_GRAY = HexColor('#ecf0f1')
TEXT_DARK = HexColor('#2c3e50')
TEXT_GRAY = HexColor('#7f8c8d')
BG_LIGHT = HexColor('#f8f9fa')


class PDFReportTemplate(BaseDocTemplate):
    def __init__(self, buffer, **kwargs):
        super().__init__(buffer, **kwargs)
        self.page_count = 0

        content_frame = Frame(
            2 * cm, 2 * cm,
            A4[0] - 4 * cm, A4[1] - 4.5 * cm,
            id='content'
        )

        cover_frame = Frame(
            0, 0, A4[0], A4[1],
            id='cover', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0
        )

        self.addPageTemplates([
            PageTemplate(id='Cover', frames=[cover_frame], onPage=self._cover_page),
            PageTemplate(id='Content', frames=[content_frame], onPage=self._content_page),
        ])

    def _cover_page(self, canvas, doc):
        pass

    def _content_page(self, canvas, doc):
        self.page_count += 1
        canvas.saveState()

        canvas.setFillColor(PRIMARY_COLOR)
        canvas.rect(0, A4[1] - 1.2 * cm, A4[0], 1.2 * cm, fill=True, stroke=False)

        canvas.setFillColor(white)
        canvas.setFont(FONT_NAME, 8)
        canvas.drawString(2 * cm, A4[1] - 0.9 * cm, '公交客流数据可视化分析系统')

        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 0.9 * cm,
                               datetime.now().strftime('%Y-%m-%d'))

        canvas.setStrokeColor(LIGHT_GRAY)
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)

        canvas.setFillColor(TEXT_GRAY)
        canvas.setFont(FONT_NAME, 7)
        canvas.drawString(2 * cm, 0.8 * cm, f'第 {self.page_count} 页')
        canvas.drawRightString(A4[0] - 2 * cm, 0.8 * cm,
                               '© 公交客流数据可视化分析系统')

        canvas.restoreState()


def _fig_to_bytes(fig, dpi=150):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none', pad_inches=0.3)
    plt.close(fig)
    buf.seek(0)
    return buf


def _create_heatmap_chart(heatmap_data, title='公交客流热力图'):
    fig, ax = plt.subplots(figsize=(10, max(4, len(heatmap_data) * 0.45)))

    cmap = LinearSegmentedColormap.from_list(
        'bus_flow', ['#f0f9e8', '#ccebc5', '#a8ddb5', '#4eb3d3', '#2b8cbe', '#08589e']
    )

    hour_labels = [f'{h:02d}:00' for h in heatmap_data.columns]
    im = ax.imshow(heatmap_data.values, cmap=cmap, aspect='auto')

    for i in range(len(heatmap_data.index)):
        for j in range(len(heatmap_data.columns)):
            val = heatmap_data.iloc[i, j]
            if val > 0:
                color = 'white' if val > heatmap_data.values.max() * 0.5 else '#2c3e50'
                ax.text(j, i, str(int(val)), ha='center', va='center',
                        fontsize=7, color=color)

    ax.set_xticks(range(len(hour_labels)))
    ax.set_xticklabels(hour_labels, rotation=45, ha='right', fontsize=8)
    ax.set_yticks(range(len(heatmap_data.index)))
    ax.set_yticklabels(heatmap_data.index, fontsize=9)
    ax.set_xlabel('时段', fontsize=11)
    ax.set_ylabel('公交线路', fontsize=11)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=12)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('客流人数', fontsize=10)

    fig.tight_layout()
    return _fig_to_bytes(fig)


def _create_hourly_trend_chart(hourly_data):
    fig, ax = plt.subplots(figsize=(10, 5))

    hours = hourly_data['时段'].values
    avg_flow = hourly_data['平均客流'].values
    hour_labels = [f'{h:02d}:00' for h in hours]

    ax.fill_between(range(len(hours)), avg_flow, alpha=0.15, color='#3498db')
    ax.plot(range(len(hours)), avg_flow, color='#3498db', linewidth=2.5,
            marker='o', markersize=6, markerfacecolor='#2980b9', label='平均客流')

    peak_hours = {7, 8, 9, 17, 18, 19}
    for i, h in enumerate(hours):
        if h in peak_hours:
            ax.plot(i, avg_flow[i], marker='*', markersize=14,
                    color='#e74c3c', zorder=5)

    ax.axvspan(
        next((i for i, h in enumerate(hours) if h == 7), 0) - 0.5,
        next((i for i, h in enumerate(hours) if h == 9), 0) + 0.5,
        alpha=0.08, color='#e74c3c', label='早高峰'
    )
    ax.axvspan(
        next((i for i, h in enumerate(hours) if h == 17), 0) - 0.5,
        next((i for i, h in enumerate(hours) if h == 19), 0) + 0.5,
        alpha=0.08, color='#f39c12', label='晚高峰'
    )

    ax.set_xticks(range(len(hour_labels)))
    ax.set_xticklabels(hour_labels, rotation=45, ha='right', fontsize=9)
    ax.set_xlabel('时段', fontsize=11)
    ax.set_ylabel('平均客流人数', fontsize=11)
    ax.set_title('24小时客流趋势图', fontsize=14, fontweight='bold', pad=12)
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    return _fig_to_bytes(fig)


def _create_load_rate_chart(route_analysis, top_n=15):
    display_data = route_analysis.head(top_n).copy()
    display_data = display_data.sort_values('平均满载率', ascending=True)

    color_map = {
        '空载': '#3498db', '低载': '#2ecc71', '正常': '#f1c40f',
        '高载': '#e67e22', '超载': '#e74c3c'
    }
    colors = [color_map.get(level, '#95a5a6') for level in display_data['满载率等级']]

    fig, ax = plt.subplots(figsize=(10, max(4, len(display_data) * 0.5)))

    y_pos = range(len(display_data))
    bars = ax.barh(y_pos, display_data['平均满载率'] * 100, color=colors, height=0.6)

    for bar, val in zip(bars, display_data['平均满载率'] * 100):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f'{val:.1f}%', va='center', fontsize=9, color='#2c3e50')

    ax.axvline(x=85, color='#e74c3c', linewidth=1.5, linestyle='--', label='超载警戒线 (85%)')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(display_data['线路名称'], fontsize=10)
    ax.set_xlabel('平均满载率 (%)', fontsize=11)
    ax.set_title('公交线路满载率排名', fontsize=14, fontweight='bold', pad=12)
    ax.legend(loc='lower right', fontsize=9)
    ax.set_xlim(0, max(100, display_data['平均满载率'].max() * 110))
    ax.grid(axis='x', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    return _fig_to_bytes(fig)


def _create_peak_comparison_chart(peak_comparison, selected_routes=None):
    comparison = peak_comparison['comparison'].copy()
    if selected_routes:
        comparison = comparison[comparison['线路名称'].isin(selected_routes)]

    comparison = comparison.sort_values('早高峰平均客流', ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(comparison) * 0.5)))

    y_pos = np.arange(len(comparison))
    bar_h = 0.25

    ax.barh(y_pos - bar_h, comparison['早高峰平均客流'], bar_h,
            color='#e74c3c', label='早高峰')
    ax.barh(y_pos, comparison['晚高峰平均客流'], bar_h,
            color='#f39c12', label='晚高峰')
    ax.barh(y_pos + bar_h, comparison['平峰平均客流'], bar_h,
            color='#3498db', label='平峰')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(comparison['线路名称'], fontsize=10)
    ax.set_xlabel('平均客流人数', fontsize=11)
    ax.set_title('高峰与平峰时段客流对比', fontsize=14, fontweight='bold', pad=12)
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(axis='x', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    return _fig_to_bytes(fig)


def _build_styles():
    styles = {}

    styles['cover_title'] = ParagraphStyle(
        'CoverTitle', fontName=FONT_BOLD, fontSize=28, leading=36,
        textColor=white, alignment=TA_CENTER, spaceAfter=10
    )
    styles['cover_subtitle'] = ParagraphStyle(
        'CoverSubtitle', fontName=FONT_NAME, fontSize=14, leading=20,
        textColor=HexColor('#b0c4de'), alignment=TA_CENTER, spaceAfter=8
    )
    styles['cover_date'] = ParagraphStyle(
        'CoverDate', fontName=FONT_NAME, fontSize=12, leading=16,
        textColor=HexColor('#8899aa'), alignment=TA_CENTER
    )
    styles['section_title'] = ParagraphStyle(
        'SectionTitle', fontName=FONT_BOLD, fontSize=16, leading=22,
        textColor=PRIMARY_COLOR, spaceAfter=10, spaceBefore=6,
    )
    styles['subsection_title'] = ParagraphStyle(
        'SubsectionTitle', fontName=FONT_BOLD, fontSize=13, leading=18,
        textColor=SECONDARY_COLOR, spaceAfter=6, spaceBefore=4
    )
    styles['body'] = ParagraphStyle(
        'Body', fontName=FONT_NAME, fontSize=10, leading=16,
        textColor=TEXT_DARK, alignment=TA_JUSTIFY, spaceAfter=4
    )
    styles['body_bold'] = ParagraphStyle(
        'BodyBold', fontName=FONT_BOLD, fontSize=10, leading=16,
        textColor=TEXT_DARK, spaceAfter=4
    )
    styles['suggestion_high'] = ParagraphStyle(
        'SuggestionHigh', fontName=FONT_NAME, fontSize=9, leading=14,
        textColor=HexColor('#c0392b'), leftIndent=12, spaceAfter=2
    )
    styles['suggestion_medium'] = ParagraphStyle(
        'SuggestionMedium', fontName=FONT_NAME, fontSize=9, leading=14,
        textColor=HexColor('#d35400'), leftIndent=12, spaceAfter=2
    )
    styles['suggestion_low'] = ParagraphStyle(
        'SuggestionLow', fontName=FONT_NAME, fontSize=9, leading=14,
        textColor=HexColor('#2980b9'), leftIndent=12, spaceAfter=2
    )
    styles['table_header'] = ParagraphStyle(
        'TableHeader', fontName=FONT_BOLD, fontSize=8, leading=11,
        textColor=white, alignment=TA_CENTER
    )
    styles['table_cell'] = ParagraphStyle(
        'TableCell', fontName=FONT_NAME, fontSize=8, leading=11,
        textColor=TEXT_DARK, alignment=TA_CENTER
    )
    styles['table_cell_left'] = ParagraphStyle(
        'TableCellLeft', fontName=FONT_NAME, fontSize=8, leading=11,
        textColor=TEXT_DARK, alignment=TA_LEFT
    )
    styles['footer_note'] = ParagraphStyle(
        'FooterNote', fontName=FONT_NAME, fontSize=8, leading=12,
        textColor=TEXT_GRAY, alignment=TA_LEFT, spaceAfter=2
    )

    return styles


def _build_cover_page(styles, df, unique_routes):
    elements = []

    d = Drawing(A4[0], A4[1])
    d.add(Rect(0, 0, A4[0], A4[1], fillColor=PRIMARY_COLOR, strokeColor=None))
    d.add(Rect(0, A4[1] * 0.35, A4[0], 3, fillColor=ACCENT_BLUE, strokeColor=None))
    d.add(Rect(0, A4[1] * 0.35 - 6, A4[0], 2, fillColor=HexColor('#1a2f5a'), strokeColor=None))
    d.add(Line(A4[0] * 0.15, A4[1] * 0.72, A4[0] * 0.85, A4[1] * 0.72,
               strokeColor=ACCENT_BLUE, strokeWidth=1))

    elements.append(d)
    elements.append(Spacer(1, -A4[1] + A4[1] * 0.78))

    cover_data = [
        [Paragraph('公交客流数据', styles['cover_title'])],
        [Paragraph('可视化分析报告', styles['cover_title'])],
        [Spacer(1, 20)],
        [Paragraph('基于 Python + Streamlit + Plotly 的智能公交调度决策支持平台',
                    styles['cover_subtitle'])],
        [Spacer(1, 40)],
        [Paragraph(f'报告生成时间：{datetime.now().strftime("%Y年%m月%d日")}',
                    styles['cover_date'])],
        [Spacer(1, 8)],
        [Paragraph(f'分析线路：{unique_routes} 条  |  总客流：{df["客流人数"].sum():,} 人次',
                    styles['cover_date'])],
    ]

    cover_table = Table(cover_data, colWidths=[A4[0] - 4 * cm])
    cover_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(cover_table)
    elements.append(PageBreak())

    return elements


def _section_divider():
    line = Drawing(A4[0] - 4 * cm, 2)
    line.add(Line(0, 1, A4[0] - 4 * cm, 1, strokeColor=ACCENT_BLUE, strokeWidth=2))
    return line


def _build_overview_section(styles, df, avg_load_rate, peak_load_rate, unique_routes):
    elements = []

    elements.append(Paragraph('一、整体概况', styles['section_title']))
    elements.append(Spacer(1, 4))
    elements.append(_section_divider())
    elements.append(Spacer(1, 10))

    total = df['客流人数'].sum()
    metrics = [
        ('总客流人次', f'{total:,}', ACCENT_BLUE),
        ('平均满载率', f'{avg_load_rate * 100:.1f}%', ACCENT_GREEN),
        ('高峰满载率', f'{peak_load_rate * 100:.1f}%', ACCENT_RED),
        ('分析线路数', f'{unique_routes}', ACCENT_ORANGE),
    ]

    col_width = (A4[0] - 4 * cm) / 4
    row1 = []
    row2 = []
    for label, value, color in metrics:
        row1.append(Paragraph(value, ParagraphStyle(
            f'mv_{label}', fontName=FONT_BOLD, fontSize=20, leading=26,
            textColor=color, alignment=TA_CENTER)))
        row2.append(Paragraph(label, ParagraphStyle(
            f'ml_{label}', fontName=FONT_NAME, fontSize=9, leading=12,
            textColor=TEXT_GRAY, alignment=TA_CENTER)))

    metric_table = Table([row1, row2], colWidths=[col_width] * 4)
    metric_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 1), (-1, 1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ('LINEAFTER', (0, 0), (2, -1), 0.5, LIGHT_GRAY),
    ]))
    elements.append(metric_table)
    elements.append(Spacer(1, 12))

    overview_items = [
        f'本报告共分析 <b>{unique_routes}</b> 条公交线路，覆盖 <b>{df["所属区域"].nunique()}</b> 个运营区域。',
        f'统计周期为 <b>{df["日期"].nunique()}</b> 天，累计服务乘客 <b>{total:,}</b> 人次。',
        f'系统平均满载率为 <b>{avg_load_rate * 100:.1f}%</b>，高峰时段满载率达 <b>{peak_load_rate * 100:.1f}%</b>。',
    ]
    for item in overview_items:
        elements.append(Paragraph(f'● {item}', styles['body']))

    elements.append(Spacer(1, 6))
    return elements


def _build_chart_section(styles, title, img_buffer, width_cm=16, height_cm=9):
    elements = []

    elements.append(Paragraph(title, styles['section_title']))
    elements.append(Spacer(1, 4))
    elements.append(_section_divider())
    elements.append(Spacer(1, 8))

    if img_buffer:
        img = Image(img_buffer, width=width_cm * cm, height=height_cm * cm)
        elements.append(img)
    else:
        elements.append(Paragraph('（图表生成失败，请参考在线版本）', styles['body']))

    elements.append(Spacer(1, 8))
    return elements


def _build_route_analysis_table(styles, route_analysis):
    elements = []

    elements.append(Paragraph('二、线路满载率分析', styles['section_title']))
    elements.append(Spacer(1, 4))
    elements.append(_section_divider())
    elements.append(Spacer(1, 8))

    elements.append(Paragraph('满载率 TOP 5 线路：', styles['subsection_title']))

    header = [
        Paragraph('线路名称', styles['table_header']),
        Paragraph('所属区域', styles['table_header']),
        Paragraph('平均满载率', styles['table_header']),
        Paragraph('最大满载率', styles['table_header']),
        Paragraph('等级', styles['table_header']),
        Paragraph('总客流', styles['table_header']),
    ]

    rows = [header]
    for _, row in route_analysis.head(5).iterrows():
        level = row['满载率等级']
        level_style = styles['table_cell']
        if level == '超载':
            level_style = ParagraphStyle('tc_red', parent=styles['table_cell'],
                                          textColor=ACCENT_RED, fontName=FONT_BOLD)
        elif level == '高载':
            level_style = ParagraphStyle('tc_orange', parent=styles['table_cell'],
                                          textColor=ACCENT_ORANGE, fontName=FONT_BOLD)

        rows.append([
            Paragraph(str(row['线路名称']), styles['table_cell_left']),
            Paragraph(str(row['所属区域']), styles['table_cell']),
            Paragraph(f'{row["平均满载率"] * 100:.1f}%', styles['table_cell']),
            Paragraph(f'{row["最大满载率"] * 100:.1f}%', styles['table_cell']),
            Paragraph(str(level), level_style),
            Paragraph(f'{row["总客流"]:,}', styles['table_cell']),
        ])

    col_widths = [2.2 * cm, 2.2 * cm, 2.5 * cm, 2.5 * cm, 1.8 * cm, 2.8 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, BG_LIGHT]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    return elements


def _build_peak_analysis_section(styles, peak_comparison):
    elements = []

    elements.append(Paragraph('三、高峰时段分析', styles['section_title']))
    elements.append(Spacer(1, 4))
    elements.append(_section_divider())
    elements.append(Spacer(1, 8))

    peak_data = peak_comparison['comparison']

    cw = (A4[0] - 4 * cm) / 3
    peak_metric_table = Table(
        [[
            Paragraph(f'{peak_data["早高峰平均客流"].mean():.0f}',
                      ParagraphStyle('pv1', fontName=FONT_BOLD, fontSize=18, leading=24,
                                      textColor=ACCENT_RED, alignment=TA_CENTER)),
            Paragraph(f'{peak_data["晚高峰平均客流"].mean():.0f}',
                      ParagraphStyle('pv2', fontName=FONT_BOLD, fontSize=18, leading=24,
                                      textColor=ACCENT_ORANGE, alignment=TA_CENTER)),
            Paragraph(f'{peak_data["平峰平均客流"].mean():.0f}',
                      ParagraphStyle('pv3', fontName=FONT_BOLD, fontSize=18, leading=24,
                                      textColor=ACCENT_BLUE, alignment=TA_CENTER)),
        ],
         [
             Paragraph('早高峰平均客流',
                       ParagraphStyle('pl1', fontName=FONT_NAME, fontSize=8, leading=11,
                                       textColor=TEXT_GRAY, alignment=TA_CENTER)),
             Paragraph('晚高峰平均客流',
                       ParagraphStyle('pl2', fontName=FONT_NAME, fontSize=8, leading=11,
                                       textColor=TEXT_GRAY, alignment=TA_CENTER)),
             Paragraph('平峰平均客流',
                       ParagraphStyle('pl3', fontName=FONT_NAME, fontSize=8, leading=11,
                                       textColor=TEXT_GRAY, alignment=TA_CENTER)),
         ]],
        colWidths=[cw] * 3
    )
    peak_metric_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ('LINEAFTER', (0, 0), (1, -1), 0.5, LIGHT_GRAY),
    ]))
    elements.append(peak_metric_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f'● 早高峰客流是平峰的 <b>{peak_data["早高峰/平峰倍数"].mean():.2f}</b> 倍',
        styles['body']))
    elements.append(Paragraph(
        f'● 晚高峰客流是平峰的 <b>{peak_data["晚高峰/平峰倍数"].mean():.2f}</b> 倍',
        styles['body']))

    elements.append(Spacer(1, 8))
    return elements


def _build_suggestions_section(styles, suggestions):
    elements = []

    elements.append(Paragraph('四、优化建议', styles['section_title']))
    elements.append(Spacer(1, 4))
    elements.append(_section_divider())
    elements.append(Spacer(1, 8))

    high_count = sum(1 for s in suggestions if s['优先级'] == '高')
    med_count = sum(1 for s in suggestions if s['优先级'] == '中')
    low_count = sum(1 for s in suggestions if s['优先级'] == '低')

    summary_table = Table(
        [[Paragraph(f'高优先级: {high_count}',
                     ParagraphStyle('sh', fontName=FONT_BOLD, fontSize=10,
                                     textColor=ACCENT_RED, alignment=TA_CENTER)),
          Paragraph(f'中优先级: {med_count}',
                     ParagraphStyle('sm', fontName=FONT_BOLD, fontSize=10,
                                     textColor=ACCENT_ORANGE, alignment=TA_CENTER)),
          Paragraph(f'低优先级: {low_count}',
                     ParagraphStyle('sl', fontName=FONT_BOLD, fontSize=10,
                                     textColor=ACCENT_BLUE, alignment=TA_CENTER))]],
        colWidths=[(A4[0] - 4 * cm) / 3] * 3
    )
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 10))

    for i, s in enumerate(suggestions[:8], 1):
        if s['优先级'] == '高':
            s_style = styles['suggestion_high']
            bg = HexColor('#fff5f5')
        elif s['优先级'] == '中':
            s_style = styles['suggestion_medium']
            bg = HexColor('#fffbf0')
        else:
            s_style = styles['suggestion_low']
            bg = HexColor('#f0f8ff')

        item_data = [
            [Paragraph(f'[{s["优先级"]}] {s["类型"]} - {s["线路"]}',
                        ParagraphStyle('sit', fontName=FONT_BOLD, fontSize=9,
                                        textColor=TEXT_DARK))],
            [Paragraph(f'建议：{s["建议"]}', s_style)],
            [Paragraph(f'问题：{s["问题"]}', ParagraphStyle('sip', parent=s_style,
                                                             textColor=TEXT_GRAY))],
            [Paragraph(f'数据：{s["详细数据"]}', ParagraphStyle('sid', parent=s_style,
                                                               textColor=TEXT_GRAY,
                                                               fontSize=8))],
        ]

        item_table = Table(item_data, colWidths=[A4[0] - 4.5 * cm])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (0, 0), 6),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, 0), 0.3, LIGHT_GRAY),
        ]))

        elements.append(KeepTogether([item_table, Spacer(1, 4)]))

    elements.append(Spacer(1, 8))
    return elements


def _build_standards_section(styles):
    elements = []

    elements.append(Paragraph('五、满载率分级标准', styles['section_title']))
    elements.append(Spacer(1, 4))
    elements.append(_section_divider())
    elements.append(Spacer(1, 8))

    standards = [
        ('空载', '< 30%', '减少运营班次，优化线路布局', ACCENT_BLUE),
        ('低载', '30% - 50%', '可适当减少班次，或调整发车频率', ACCENT_GREEN),
        ('正常', '50% - 70%', '运力配置合理，保持现状', HexColor('#f1c40f')),
        ('高载', '70% - 85%', '关注高峰时段，可适当增加班次', ACCENT_ORANGE),
        ('超载', '>= 85%', '紧急增加运力，考虑区间车方案', ACCENT_RED),
    ]

    header = [
        Paragraph('等级', styles['table_header']),
        Paragraph('满载率范围', styles['table_header']),
        Paragraph('建议措施', styles['table_header']),
    ]

    rows = [header]
    for level, range_val, measure, color in standards:
        rows.append([
            Paragraph(level, ParagraphStyle('tl', parent=styles['table_cell'],
                                             textColor=color, fontName=FONT_BOLD)),
            Paragraph(range_val, styles['table_cell']),
            Paragraph(measure, styles['table_cell_left']),
        ])

    table = Table(rows, colWidths=[2.5 * cm, 3 * cm, 10.5 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, BG_LIGHT]),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 20))
    divider = Drawing(A4[0] - 4 * cm, 2)
    divider.add(Line(0, 1, A4[0] - 4 * cm, 1, strokeColor=LIGHT_GRAY, strokeWidth=0.5))
    elements.append(divider)
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f'报告生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}',
        styles['footer_note']))
    elements.append(Paragraph(
        '本报告由「公交客流数据可视化分析系统」自动生成，数据仅供参考。',
        styles['footer_note']))

    return elements


def generate_pdf_report(df, route_analysis, suggestions, peak_comparison,
                        heatmap_data, hourly_data, selected_routes=None):
    buffer = BytesIO()

    doc = PDFReportTemplate(
        buffer,
        pagesize=A4,
        title='公交客流数据分析报告',
        author='公交客流数据可视化分析系统',
    )

    styles = _build_styles()
    elements = []

    avg_load_rate = df['满载率'].mean()
    peak_load_rate = df[df['是否高峰']]['满载率'].mean() if df['是否高峰'].any() else 0
    unique_routes = df['线路名称'].nunique()

    elements.extend(_build_cover_page(styles, df, unique_routes))

    doc.handle_nextPageTemplate('Content')

    elements.extend(_build_overview_section(styles, df, avg_load_rate, peak_load_rate, unique_routes))

    elements.append(PageBreak())
    heatmap_img = _create_heatmap_chart(heatmap_data)
    elements.extend(_build_chart_section(
        styles, '六、客流热力图', heatmap_img, width_cm=16, height_cm=10))

    elements.append(PageBreak())
    trend_img = _create_hourly_trend_chart(hourly_data)
    elements.extend(_build_chart_section(
        styles, '七、24小时客流趋势', trend_img, width_cm=16, height_cm=9))

    elements.append(PageBreak())
    load_rate_img = _create_load_rate_chart(route_analysis)
    elements.extend(_build_chart_section(
        styles, '八、线路满载率排名', load_rate_img, width_cm=16, height_cm=10))

    elements.append(PageBreak())
    peak_img = _create_peak_comparison_chart(peak_comparison, selected_routes)
    elements.extend(_build_chart_section(
        styles, '九、高峰与平峰客流对比', peak_img, width_cm=16, height_cm=10))

    elements.append(PageBreak())
    elements.extend(_build_route_analysis_table(styles, route_analysis))

    elements.extend(_build_peak_analysis_section(styles, peak_comparison))

    elements.append(PageBreak())
    elements.extend(_build_suggestions_section(styles, suggestions))

    elements.extend(_build_standards_section(styles))

    doc.build(elements)

    buffer.seek(0)
    return buffer.getvalue()
