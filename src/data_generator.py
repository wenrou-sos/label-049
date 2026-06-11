import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

def generate_bus_data():
    np.random.seed(42)
    
    routes = [
        ('1路', '市中心区', 80),
        ('2路', '市中心区', 60),
        ('3路', '东城区', 70),
        ('4路', '西城区', 65),
        ('5路', '南城区', 75),
        ('6路', '北城区', 55),
        ('7路', '市中心区', 90),
        ('8路', '东城区', 50),
        ('9路', '西城区', 85),
        ('10路', '南城区', 60),
        ('11路', '北城区', 70),
        ('12路', '市中心区', 95),
        ('13路', '东城区', 55),
        ('14路', '西城区', 65),
        ('15路', '南城区', 80),
    ]
    
    hours = list(range(6, 23))
    days = 7
    
    data = []
    
    for route_name, district, capacity in routes:
        for day in range(days):
            for hour in hours:
                base_passengers = np.random.normal(30, 10)
                
                if 7 <= hour <= 9:
                    base_passengers *= 2.5 + np.random.uniform(0, 0.5)
                elif 17 <= hour <= 19:
                    base_passengers *= 2.2 + np.random.uniform(0, 0.4)
                elif 11 <= hour <= 13:
                    base_passengers *= 1.3 + np.random.uniform(0, 0.2)
                elif hour < 7 or hour > 20:
                    base_passengers *= 0.5 + np.random.uniform(0, 0.2)
                
                if route_name in ['1路', '7路', '9路', '12路']:
                    base_passengers *= 1.3
                
                if district == '市中心区':
                    base_passengers *= 1.2
                
                passengers = max(5, int(base_passengers + np.random.normal(0, 8)))
                passengers = min(passengers, capacity + 20)
                
                load_rate = min(passengers / capacity, 1.5)
                
                date = (datetime(2024, 1, 1) + timedelta(days=day)).strftime('%Y-%m-%d')
                weekday = (datetime(2024, 1, 1) + timedelta(days=day)).strftime('%A')
                
                is_peak = (7 <= hour <= 9) or (17 <= hour <= 19)
                peak_type = '早高峰' if 7 <= hour <= 9 else ('晚高峰' if 17 <= hour <= 19 else '平峰')
                
                data.append({
                    '线路名称': route_name,
                    '所属区域': district,
                    '车辆容量': capacity,
                    '日期': date,
                    '星期': weekday,
                    '时段': hour,
                    '时段类型': peak_type,
                    '是否高峰': is_peak,
                    '客流人数': passengers,
                    '满载率': round(load_rate, 3),
                    '运营班次': np.random.randint(4, 12) if is_peak else np.random.randint(2, 6),
                })
    
    df = pd.DataFrame(data)
    
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/bus_passenger_data.csv', index=False, encoding='utf-8-sig')
    df.to_excel('data/bus_passenger_data.xlsx', index=False)
    
    return df

if __name__ == '__main__':
    df = generate_bus_data()
    print(f'数据生成完成，共 {len(df)} 条记录')
    print(f'包含 {df["线路名称"].nunique()} 条线路')
    print(f'时间范围: {df["日期"].min()} 至 {df["日期"].max()}')
    print(df.head())
