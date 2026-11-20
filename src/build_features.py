# -*- coding: utf-8 -*-
"""
build_features.py — tạo các biến mới phục vụ câu hỏi nghiên cứu (chỉ những biến được dùng).

Đọc:  data/processed/bctc/panel_quarterly_bctc.csv
Ghi:  data/processed/features/bien_moi_quy.csv

  liquid_assets       = cash_and_equivalents + short_term_investments        (tỷ đồng)
  liquidity_gap       = liquid_assets − short_term_liabilities                (tỷ đồng)
  cash_coverage       = liquid_assets / short_term_liabilities                (lần)
  inventory_share     = inventory / current_assets                            (tỷ lệ)
  liab_to_equity      = total_liabilities / owner_equity                      (lần)
  revenue_ttm         = tổng doanh thu thuần 4 quý liên tiếp                   (tỷ đồng)
  revenue_yoy_pct     = doanh thu quý so với cùng quý năm trước                (%)
  fin_cost_ratio_pct  = chi phí tài chính 4 quý / revenue_ttm                  (%)

short_term_investments ghi "-" (không phát sinh) được tính là 0 trong liquid_assets và gắn cờ.
Phép cộng 4 quý chỉ dùng 4 quý liên tiếp có số liệu; quý bị thiếu (vd. 2024Q2) làm trống các cửa sổ chứa nó.
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "processed", "bctc", "panel_quarterly_bctc.csv")
OUT = os.path.join(ROOT, "data", "processed", "features")
NON_REAL_ESTATE = {"SRC"}      # SRC = Cao su Sao Vàng, không phải doanh nghiệp bất động sản


def build(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for t, g in panel.groupby("ticker"):
        q = pd.PeriodIndex(g["period"], freq="Q")
        g = g.set_index(q).reindex(pd.period_range(q.min(), q.max(), freq="Q"))   # lưới quý liên tục
        f = pd.DataFrame(index=g.index)
        f["ticker"] = t
        f["has_report"] = g["ticker"].notna()
        f["st_invest_filled_0"] = g["short_term_investments"].isna() & g["cash_and_equivalents"].notna()
        f["liquid_assets"] = g["cash_and_equivalents"] + g["short_term_investments"].fillna(0)
        f["liquidity_gap"] = f["liquid_assets"] - g["short_term_liabilities"]
        f["cash_coverage"] = f["liquid_assets"] / g["short_term_liabilities"].where(g["short_term_liabilities"] > 0)
        f["inventory_share"] = g["inventory"] / g["current_assets"].where(g["current_assets"] > 0)
        f["liab_to_equity"] = g["total_liabilities"] / g["owner_equity"].where(g["owner_equity"] > 0)
        rev = g["net_revenue"]
        f["revenue_ttm"] = rev.rolling(4, min_periods=4).sum()
        lag = rev.shift(4)
        f["revenue_yoy_pct"] = (rev - lag) / lag.where(lag > 0) * 100
        fin_ttm = g["financial_expense"].rolling(4, min_periods=4).sum()
        f["fin_cost_ratio_pct"] = fin_ttm / f["revenue_ttm"].where(f["revenue_ttm"] > 0) * 100
        rows.append(f[f["has_report"]].drop(columns="has_report"))
    out = pd.concat(rows).rename_axis("period").reset_index()
    out["period"] = out["period"].astype(str)
    out.insert(1, "is_real_estate", ~out["ticker"].isin(NON_REAL_ESTATE))
    num = out.select_dtypes("number").columns
    out[num] = out[num].round(4)
    return out[["ticker", "period", "is_real_estate", "liquid_assets", "liquidity_gap", "cash_coverage",
                "inventory_share", "liab_to_equity", "revenue_ttm", "revenue_yoy_pct", "fin_cost_ratio_pct",
                "st_invest_filled_0"]]


def main():
    os.makedirs(OUT, exist_ok=True)
    f = build(pd.read_csv(SRC))
    path = os.path.join(OUT, "bien_moi_quy.csv")
    f.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"Đã ghi {path}: {len(f)} dòng × {f.shape[1]} cột")
    print(f"  revenue_ttm có giá trị: {f['revenue_ttm'].notna().sum()} quan sát; "
          f"revenue_yoy_pct: {f['revenue_yoy_pct'].notna().sum()}; liquid_assets: {f['liquid_assets'].notna().sum()}")


if __name__ == "__main__":
    main()
