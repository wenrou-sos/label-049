import sys
sys.path.insert(0, '.')

from src.data_processor import load_data, get_route_analysis, get_peak_comparison, generate_optimization_suggestions, get_heatmap_data, get_hourly_trend

df = load_data()
print(f'Loaded {len(df)} rows')

route_analysis = get_route_analysis(df)
peak_comparison = get_peak_comparison(df)
suggestions = generate_optimization_suggestions(df)
heatmap_data = get_heatmap_data(df)
hourly_data = get_hourly_trend(df)

from src.visualizations import create_passenger_heatmap, create_hourly_trend as crt, create_load_rate_ranking, create_peak_comparison_chart

heatmap_fig = create_passenger_heatmap(heatmap_data)
trend_fig = crt(hourly_data)
load_rate_fig = create_load_rate_ranking(route_analysis, top_n=len(route_analysis))
peak_fig = create_peak_comparison_chart(peak_comparison['comparison'])

print('Charts created, generating PDF...')

from src.pdf_report import generate_pdf_report
pdf_bytes = generate_pdf_report(
    df, route_analysis, suggestions, peak_comparison,
    heatmap_fig, trend_fig, load_rate_fig, peak_fig
)
print(f'PDF size: {len(pdf_bytes)} bytes')

with open('test_report.pdf', 'wb') as f:
    f.write(pdf_bytes)
print('Done!')
