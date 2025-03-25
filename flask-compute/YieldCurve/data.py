import re
import numpy as np
import pandas as pd
import os
import sys
from db import SessionLocal, YieldData

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def parse_maturity(label):
    match = re.match(r"(\d+)\s*(-?)(Month|M|Year|Y)", label, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        unit = match.group(3).lower()
        if unit in ['month', 'm']:
            return num
        elif unit in ['year', 'y']:
            return num * 12
    num_match = re.search(r'\d+', label)
    return int(num_match.group()) if num_match else label

def get_yield_data(start_date, end_date):
    session = SessionLocal()
    try:
        records = session.query(YieldData).filter(
            YieldData.date >= start_date,
            YieldData.date <= end_date
        ).all()
        if not records:
            return np.array([]), np.array([]), np.array([])
        
        data = []
        for r in records:
            maturity = parse_maturity(r.label)
            data.append({
                "date": r.date,
                "maturity": maturity,
                "yield": float(r.close)
            })
        df = pd.DataFrame(data)
        
        pivot_yield = df.pivot(index='date', columns='maturity', values='yield')
        desired_maturities = [3, 60, 120, 360]
        available = [m for m in desired_maturities if m in pivot_yield.columns]
        pivot_yield = pivot_yield[available] if available else pd.DataFrame()
        
        if pivot_yield.empty:
            return np.array([]), np.array([]), np.array([])
        
        return (
            pivot_yield.columns.to_numpy(),
            pivot_yield.index.to_numpy(),
            pivot_yield.to_numpy()
        )
    finally:
        session.close()