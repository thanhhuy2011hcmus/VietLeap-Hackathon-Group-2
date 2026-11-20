# -*- coding: utf-8 -*-
"""
clean_bctc_data.py — Làm sạch và hợp nhất toàn diện dữ liệu BCTC từ các file Excel/HTML
Dành cho: VietLeap Hackathon 2026 - Nhóm 2

Quy trình:
  1. Quét tự động tất cả các file *_BCTC_Tom_Tat*.xls (bao gồm cả các file tải theo đợt như (1), (2), (3)...).
  2. Bóc tách 3 bảng chuẩn từ cấu trúc HTML xuất bởi Vietstock/Cafef:
     - Bảng 1: Kết quả kinh doanh theo Quý (ghép nối lịch sử từ 2022 đến 2026).
     - Bảng 2: Cân đối kế toán theo Quý.
     - Bảng 3: Chỉ số tài chính theo Năm.
  3. Chuẩn hóa số liệu & khử trùng lặp (Deduplication):
     - Chuyển đổi định dạng số (loại bỏ dấu phẩy hàng nghìn, ngoặc âm, gạch ngang -> NaN).
     - Khử trùng lặp giữa các file tải trùng kỳ, giữ lại giá trị hợp lệ.
  4. Chuẩn hóa chu kỳ: 'Q4-2022' -> period='2022Q4', year=2022, quarter=4.
  5. Xuất các bảng dữ liệu sạch:
     - ket_qua_kinh_doanh_quy.csv (toàn bộ lịch sử các quý)
     - can_doi_ke_toan_quy.csv (các quý gần nhất)
     - panel_quarterly_bctc.csv (ghép CĐKT + KQKD theo ticker và period)
     - chi_so_tai_chinh_nam.csv (chỉ số tài chính theo năm)
  6. Kiểm tra tính toàn vẹn và logic kế toán & xuất báo cáo chất lượng.
"""

import os
import re
import glob
from html.parser import HTMLParser
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# 1. BẢNG MÃ HÓA BIẾN TÀI CHÍNH (METRIC MAPPING)
# ─────────────────────────────────────────────────────────────────────────────

INCOME_STATEMENT_MAP = {
    "Doanh thu thuần về bán hàng và cung cấp dịch vụ": "net_revenue",
    "Giá vốn hàng bán": "cogs",
    "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ": "gross_profit",
    "Doanh thu hoạt động tài chính": "financial_income",
    "Chi phí tài chính": "financial_expense",
    "Chi phí bán hàng": "selling_expense",
    "Chi phí quản lý doanh nghiệp": "admin_expense",
    "Lợi nhuận thuần từ hoạt động kinh doanh": "operating_profit",
    "Lợi nhuận khác": "other_profit",
    "Phần lợi nhuận/lỗ từ công ty liên kết liên doanh": "associate_profit",
    "Tổng lợi nhuận kế toán trước thuế": "profit_before_tax",
    "Lợi nhuận sau thuế thu nhập doanh nghiệp": "net_profit_after_tax",
    "Lợi nhuận sau thuế của cổ đông Công ty mẹ": "net_profit_parent_shareholders",
    "Lãi cơ bản trên cổ phiếu (VNÐ)": "basic_eps_vnd"
}

BALANCE_SHEET_MAP = {
    "Tài sản ngắn hạn": "current_assets",
    "Tiền và các khoản tương đương tiền": "cash_and_equivalents",
    "Các khoản đầu tư tài chính ngắn hạn": "short_term_investments",
    "Các khoản phải thu ngắn hạn": "short_term_receivables",
    "Hàng tồn kho": "inventory",
    "Tài sản ngắn hạn khác": "other_current_assets",
    "Tài sản dài hạn": "non_current_assets",
    "Tài sản cố định": "fixed_assets",
    "Bất động sản đầu tư": "investment_properties",
    "Các khoản đầu tư tài chính dài hạn": "long_term_investments",
    "Tổng cộng tài sản": "total_assets",
    "Nợ phải trả": "total_liabilities",
    "Nợ ngắn hạn": "short_term_liabilities",
    "Nợ dài hạn": "long_term_liabilities",
    "Vốn chủ sở hữu": "owner_equity",
    "Vốn đầu tư của chủ sở hữu": "paid_in_capital",
    "Thặng dư vốn cổ phần": "share_premium",
    "Lợi nhuận sau thuế chưa phân phối": "undistributed_earnings",
    "Lợi ích của cổ đông thiểu số": "minority_interests",
    "Tổng cộng nguồn vốn": "total_resources"
}

FINANCIAL_RATIOS_MAP = {
    "Thu nhập trên mỗi cổ phần của 4 quý gần nhất (EPS)": "eps_ttm",
    "Giá trị sổ sách của cổ phiếu (BVPS)": "bvps",
    "Chỉ số giá thị trường trên thu nhập (P/E)": "pe_ratio",
    "Chỉ số giá thị trường trên giá trị sổ sách (P/B)": "pb_ratio",
    "Tỷ suất lợi nhuận gộp biên": "gross_margin_pct",
    "Tỷ suất sinh lợi trên doanh thu thuần": "net_margin_pct",
    "Tỷ suất lợi nhuận trên vốn chủ sở hữu bình quân (ROEA)": "roea_pct",
    "Tỷ suất sinh lợi trên tổng tài sản bình quân (ROAA)": "roaa_pct",
    "Tỷ số thanh toán hiện hành (ngắn hạn)": "current_ratio",
    "Khả năng thanh toán lãi vay": "interest_coverage",
    "Tỷ số Nợ trên Tổng tài sản": "debt_to_assets",
    "Tỷ số Nợ vay trên Vốn chủ sở hữu": "debt_to_equity"
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. BỘ PHÂN TÍCH HTML (PARSER)
# ─────────────────────────────────────────────────────────────────────────────
class VietstockHtmlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._current_table = []
        self._current_row = []
        self._current_cell = []
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._current_table = []
        elif tag == "tr":
            self._current_row = []
        elif tag in ("td", "th"):
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag):
        if tag == "table":
            if self._current_table:
                self.tables.append(self._current_table)
        elif tag == "tr":
            if self._current_row:
                self._current_table.append(self._current_row)
        elif tag in ("td", "th"):
            self._in_cell = False
            text = "".join(self._current_cell).strip().replace("\xa0", " ")
            self._current_row.append(text)

    def handle_data(self, data):
        if self._in_cell:
            self._current_cell.append(data)


# ─────────────────────────────────────────────────────────────────────────────
# 3. HÀM CHUẨN HÓA DỮ LIỆU SỐ VÀ CHU KỲ
# ─────────────────────────────────────────────────────────────────────────────
def clean_numeric_value(val):
    if val is None or pd.isna(val):
        return np.nan
    val_str = str(val).strip().replace(",", "")
    if val_str in ("", "-", "—", "N/A", "nan", "None", "."):
        return np.nan
    if val_str.startswith("(") and val_str.endswith(")"):
        val_str = "-" + val_str[1:-1].strip()
    val_str = val_str.replace("−", "-")
    try:
        return float(val_str)
    except ValueError:
        return np.nan


def parse_quarter_period(period_str):
    period_str = str(period_str).strip()
    m = re.match(r"Q(\d)[-_](\d{4})", period_str, re.IGNORECASE)
    if m:
        q = int(m.group(1))
        y = int(m.group(2))
        return f"{y}Q{q}", y, q
    m2 = re.match(r"(\d{4})[-_]?Q(\d)", period_str, re.IGNORECASE)
    if m2:
        y = int(m2.group(1))
        q = int(m2.group(2))
        return f"{y}Q{q}", y, q
    return period_str, np.nan, np.nan


# ─────────────────────────────────────────────────────────────────────────────
# 4. TRÍCH XUẤT VÀ CHUYỂN ĐỔI BẢNG
# ─────────────────────────────────────────────────────────────────────────────
def parse_single_file(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    parser = VietstockHtmlParser()
    parser.feed(content)
    return parser.tables


def extract_quarterly_table(table_data, ticker, metric_map, category_name):
    if not table_data or len(table_data) < 2:
        return pd.DataFrame()

    header = table_data[0]
    period_cols = header[1:]
    
    records = []
    for row in table_data[1:]:
        if not row:
            continue
        raw_metric = row[0].strip()
        metric_code = metric_map.get(raw_metric, re.sub(r"[^\w]", "_", raw_metric.lower()))
        
        for idx, col_period in enumerate(period_cols):
            val_raw = row[idx + 1] if idx + 1 < len(row) else None
            cleaned_val = clean_numeric_value(val_raw)
            period_norm, year, quarter = parse_quarter_period(col_period)
            
            records.append({
                "ticker": ticker,
                "period": period_norm,
                "year": year,
                "quarter": quarter,
                "category": category_name,
                "metric_vn": raw_metric,
                "metric_code": metric_code,
                "value": cleaned_val
            })
            
    return pd.DataFrame(records)


def extract_yearly_ratios(table_data, ticker, metric_map):
    if not table_data or len(table_data) < 2:
        return pd.DataFrame()

    header = table_data[0]
    year_cols = header[1:]
    
    records = []
    for row in table_data[1:]:
        if not row:
            continue
        raw_metric = row[0].strip()
        metric_code = metric_map.get(raw_metric, re.sub(r"[^\w]", "_", raw_metric.lower()))
        
        for idx, col_year in enumerate(year_cols):
            val_raw = row[idx + 1] if idx + 1 < len(row) else None
            cleaned_val = clean_numeric_value(val_raw)
            try:
                y = int(str(col_year).strip())
            except ValueError:
                y = col_year
            
            records.append({
                "ticker": ticker,
                "year": y,
                "metric_vn": raw_metric,
                "metric_code": metric_code,
                "value": cleaned_val
            })
            
    return pd.DataFrame(records)


# ─────────────────────────────────────────────────────────────────────────────
# 5. KIỂM TRA CHẤT LƯỢNG VÀ TÍNH LOGIC KẾ TOÁN
# ─────────────────────────────────────────────────────────────────────────────
def run_accounting_validation(df_panel):
    val_results = []
    
    # 1. Tổng tài sản = TS ngắn hạn + TS dài hạn
    if {"current_assets", "non_current_assets", "total_assets"}.issubset(df_panel.columns):
        sub = df_panel.dropna(subset=["current_assets", "non_current_assets", "total_assets"])
        diff_assets = (sub["current_assets"] + sub["non_current_assets"]) - sub["total_assets"]
        mismatch_assets = sub[diff_assets.abs() > 0.1]
        val_results.append({
            "check": "Tổng tài sản = TS ngắn hạn + TS dài hạn",
            "passed": len(mismatch_assets) == 0,
            "failed_count": len(mismatch_assets),
            "details": mismatch_assets[["ticker", "period", "current_assets", "non_current_assets", "total_assets"]].to_dict("records")
        })

    # 2. Tổng nguồn vốn = Nợ phải trả + Vốn chủ sở hữu
    if {"total_liabilities", "owner_equity", "total_resources"}.issubset(df_panel.columns):
        sub = df_panel.dropna(subset=["total_liabilities", "owner_equity", "total_resources"])
        diff_liab = (sub["total_liabilities"] + sub["owner_equity"]) - sub["total_resources"]
        mismatch_liab = sub[diff_liab.abs() > 0.1]
        val_results.append({
            "check": "Tổng nguồn vốn = Nợ phải trả + Vốn chủ sở hữu",
            "passed": len(mismatch_liab) == 0,
            "failed_count": len(mismatch_liab),
            "details": mismatch_liab[["ticker", "period", "total_liabilities", "owner_equity", "total_resources"]].to_dict("records")
        })

    # 3. Lợi nhuận gộp = Doanh thu thuần - Giá vốn
    if {"net_revenue", "cogs", "gross_profit"}.issubset(df_panel.columns):
        sub = df_panel.dropna(subset=["net_revenue", "cogs", "gross_profit"])
        diff_gp = (sub["net_revenue"] - sub["cogs"]) - sub["gross_profit"]
        mismatch_gp = sub[diff_gp.abs() > 0.1]
        val_results.append({
            "check": "Lợi nhuận gộp = Doanh thu thuần - Giá vốn",
            "passed": len(mismatch_gp) == 0,
            "failed_count": len(mismatch_gp),
            "details": mismatch_gp[["ticker", "period", "net_revenue", "cogs", "gross_profit"]].to_dict("records")
        })

    return val_results


# ─────────────────────────────────────────────────────────────────────────────
# 6. QUY TRÌNH CHÍNH (MAIN PIPELINE)
# ─────────────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "vietstock")
OUT_DIR = os.path.join(ROOT, "data", "processed", "bctc")


def main(input_dir=RAW_DIR, output_dir=OUT_DIR):
    print("=" * 80)
    print(" BẮT ĐẦU QUY TRÌNH LÀM SẠCH VÀ CHUẨN HÓA DỮ LIỆU BCTC")
    print("=" * 80)

    os.makedirs(output_dir, exist_ok=True)
    
    # Quét tất cả các file *_BCTC_Tom_Tat*.xls kể cả các file có đuôi (1), (2),...
    file_pattern = os.path.join(input_dir, "**", "*_BCTC_Tom_Tat*.xls")      # mỗi mã một thư mục con
    files = sorted(glob.glob(file_pattern, recursive=True))
    
    if not files:
        print(f"[!] Không tìm thấy file nào khớp mẫu: {file_pattern}")
        return

    print(f"[*] Tìm thấy {len(files)} file BCTC tóm tắt:")

    list_is = []
    list_bs = []
    list_ratios = []

    for file_path in files:
        fname = os.path.basename(file_path)
        ticker = fname.split("_")[0].upper()
        tables = parse_single_file(file_path)
        
        if len(tables) < 3:
            print(f"    - [Bỏ qua] {fname}: chỉ có {len(tables)} bảng!")
            continue

        # Bảng 1: Kết quả kinh doanh
        df_is_single = extract_quarterly_table(tables[0], ticker, INCOME_STATEMENT_MAP, "ket_qua_kinh_doanh")
        list_is.append(df_is_single)

        # Bảng 2: Cân đối kế toán
        df_bs_single = extract_quarterly_table(tables[1], ticker, BALANCE_SHEET_MAP, "can_doi_ke_toan")
        list_bs.append(df_bs_single)

        # Bảng 3: Chỉ số tài chính
        df_rat_single = extract_yearly_ratios(tables[2], ticker, FINANCIAL_RATIOS_MAP)
        list_ratios.append(df_rat_single)

        # ghi nhận file nguồn và thời điểm tải để xử lý trùng lặp
        for d in (df_is_single, df_bs_single, df_rat_single):
            d["source_file"] = fname
            d["file_mtime"] = os.path.getmtime(file_path)

    df_is_all = pd.concat(list_is, ignore_index=True)
    df_bs_all = pd.concat(list_bs, ignore_index=True)
    df_ratios_all = pd.concat(list_ratios, ignore_index=True)

    print(f"[*] Đã đọc thô: KQKD={len(df_is_all)}, CĐKT={len(df_bs_all)}, Ratios={len(df_ratios_all)} bản ghi.")

    # KHỬ TRÙNG LẶP: cùng (ticker, kỳ, chỉ tiêu) xuất hiện ở nhiều đợt tải.
    # Ưu tiên ô có giá trị; nếu nhiều file ghi giá trị khác nhau (điều chỉnh hồi tố) thì lấy file tải sau cùng
    # và đếm lại để đưa vào báo cáo.
    conflicts = {}

    def deduplicate_long(df, keys, name):
        valued = df.dropna(subset=["value"])
        n = valued.groupby(keys)["value"].nunique()
        conflicts[name] = int((n > 1).sum())
        df = df.assign(_has=df["value"].notna()).sort_values(keys + ["_has", "file_mtime"])
        return df.drop_duplicates(subset=keys, keep="last").drop(columns=["_has", "source_file", "file_mtime"])

    df_is_all = deduplicate_long(df_is_all, ["ticker", "period", "metric_code"], "KQKD")
    df_bs_all = deduplicate_long(df_bs_all, ["ticker", "period", "metric_code"], "CĐKT")
    df_ratios_all = deduplicate_long(df_ratios_all, ["ticker", "year", "metric_code"], "Chỉ số")

    print(f"[*] Sau khi khử trùng lặp: KQKD={len(df_is_all)}, CĐKT={len(df_bs_all)}, Ratios={len(df_ratios_all)}")

    # PIVOT SANG DẠNG PANEL RỘNG (Wide Format)
    df_is_wide = df_is_all.pivot_table(
        index=["ticker", "period", "year", "quarter"],
        columns="metric_code",
        values="value"
    ).reset_index()
    df_is_wide.columns.name = None

    df_bs_wide = df_bs_all.pivot_table(
        index=["ticker", "period", "year", "quarter"],
        columns="metric_code",
        values="value"
    ).reset_index()
    df_bs_wide.columns.name = None

    # Đẳng thức kế toán: Tổng cộng tài sản = Tổng cộng nguồn vốn. Nếu nguồn để trống ("-") một trong hai ô
    # thì điền từ ô còn lại; không đoán thêm bất kỳ ô nào khác.
    filled_identity = 0
    if {"total_assets", "total_resources"}.issubset(df_bs_wide.columns):
        for a, b in [("total_assets", "total_resources"), ("total_resources", "total_assets")]:
            m = df_bs_wide[a].isna() & df_bs_wide[b].notna()
            df_bs_wide.loc[m, a] = df_bs_wide.loc[m, b]
            filled_identity += int(m.sum())

    # Ghép bảng tổng hợp Panel theo Quý (KQKD + CĐKT)
    df_panel_quarterly = pd.merge(
        df_is_wide,
        df_bs_wide,
        on=["ticker", "period", "year", "quarter"],
        how="outer"
    )

    # Bảng Chỉ số tài chính theo Năm
    df_ratios_wide = df_ratios_all.pivot_table(
        index=["ticker", "year"],
        columns="metric_code",
        values="value"
    ).reset_index()
    df_ratios_wide.columns.name = None

    # Sắp xếp thời gian
    df_panel_quarterly = df_panel_quarterly.sort_values(by=["ticker", "period"]).reset_index(drop=True)
    df_is_wide = df_is_wide.sort_values(by=["ticker", "period"]).reset_index(drop=True)
    df_bs_wide = df_bs_wide.sort_values(by=["ticker", "period"]).reset_index(drop=True)
    df_ratios_wide = df_ratios_wide.sort_values(by=["ticker", "year"]).reset_index(drop=True)

    # Lưu kết quả CSV (utf-8-sig mở tốt trong Excel tiếng Việt)
    p_is = os.path.join(output_dir, "ket_qua_kinh_doanh_quy.csv")
    p_bs = os.path.join(output_dir, "can_doi_ke_toan_quy.csv")
    p_panel = os.path.join(output_dir, "panel_quarterly_bctc.csv")
    p_ratios = os.path.join(output_dir, "chi_so_tai_chinh_nam.csv")

    df_is_wide.to_csv(p_is, index=False, encoding="utf-8-sig")
    df_bs_wide.to_csv(p_bs, index=False, encoding="utf-8-sig")
    df_panel_quarterly.to_csv(p_panel, index=False, encoding="utf-8-sig")
    df_ratios_wide.to_csv(p_ratios, index=False, encoding="utf-8-sig")

    print("\n[+] ĐÃ LƯU THÀNH CÔNG CÁC TỆP DỮ LIỆU SẠCH:")
    print(f"    1. {p_panel} (Bảng tổng hợp: {len(df_panel_quarterly)} dòng quý)")
    print(f"    2. {p_is} (Kết quả kinh doanh theo Quý: {len(df_is_wide)} dòng)")
    print(f"    3. {p_bs} (Cân đối kế toán theo Quý: {len(df_bs_wide)} dòng)")
    print(f"    4. {p_ratios} (Chỉ số tài chính theo Năm: {len(df_ratios_wide)} dòng)")

    # KIỂM TRA CHẤT LƯỢNG VÀ VIẾT BÁO CÁO
    validations = run_accounting_validation(df_panel_quarterly)
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append(f" BÁO CÁO KIỂM TRA CHẤT LƯỢNG DỮ LIỆU BCTC (DATA QUALITY REPORT)")
    report_lines.append(f" Thời điểm thực hiện: {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}")
    report_lines.append("=" * 80)
    report_lines.append(f"\n1. TỔNG QUAN:")
    report_lines.append(f"   - Số doanh nghiệp: {df_panel_quarterly['ticker'].nunique()} ({', '.join(sorted(df_panel_quarterly['ticker'].unique()))})")
    report_lines.append(f"   - Tổng số quý quan sát: {len(df_panel_quarterly)}")
    report_lines.append(f"   - Dải thời gian KQKD: từ {df_panel_quarterly['period'].min()} đến {df_panel_quarterly['period'].max()}")
    report_lines.append(f"   - Số file đọc: {len(files)}")
    report_lines.append("   - Đơn vị: KQKD và CĐKT tính bằng tỷ đồng; EPS/BVPS trong bảng chỉ số tính bằng nghìn đồng/cp;"
                        " cột *_pct là %")
    report_lines.append(f"   - Ô điền theo đẳng thức Tổng tài sản = Tổng nguồn vốn: {filled_identity}")
    report_lines.append("   - Ô \"-\" trong file gốc (không phát sinh hoặc không có số liệu) để trống, không thay bằng 0")
    report_lines.append("   - Ô bị nhiều đợt tải ghi giá trị khác nhau: "
                        + ", ".join(f"{k} {v}" for k, v in conflicts.items()) + " (nếu có, lấy file tải sau cùng)")

    report_lines.append(f"\n2. KẾT QUẢ KIỂM TRA LOGIC CÂN ĐỐI KẾ TOÁN:")
    for v in validations:
        status = "ĐẠT (PASSED)" if v["passed"] else f"CẢNH BÁO ({v['failed_count']} dòng lệch)"
        report_lines.append(f"   [+] {v['check']}: {status}")

    report_lines.append(f"\n3. TỶ LỆ DỮ LIỆU ĐẦY ĐỦ TRÊN BẢNG QUÝ:")
    report_lines.append(f"   - Số quý có KQKD: {df_panel_quarterly['net_revenue'].notna().sum()}/{len(df_panel_quarterly)}")
    report_lines.append(f"   - Số quý có CĐKT: {df_panel_quarterly['total_assets'].notna().sum()}/{len(df_panel_quarterly)}")

    report_lines.append("\n4. ĐỘ PHỦ THEO MÃ (kỳ đầu – kỳ cuối, số quý, quý bị thiếu ở giữa):")
    for t, g in df_panel_quarterly.groupby("ticker"):
        for name, col in [("KQKD", "net_revenue"), ("CĐKT", "total_assets")]:
            q = pd.PeriodIndex(g.loc[g[col].notna(), "period"], freq="Q").sort_values()
            if len(q) == 0:
                report_lines.append(f"   - {t} {name}: không có số liệu"); continue
            gap = [str(x) for x in pd.period_range(q.min(), q.max(), freq="Q") if x not in set(q)]
            report_lines.append(f"   - {t} {name}: {q.min()} – {q.max()}, {len(q)} quý"
                                + (f", thiếu {', '.join(gap)}" if gap else ", liên tục"))
    report_lines.append("   CĐKT chỉ có 4 quý gần nhất vì file tóm tắt Vietstock chỉ chứa 4 quý cân đối kế toán.")
    report_lines.append("   Quý KQKD bị thiếu là do chính file Vietstock nhảy cóc kỳ (vd. Q1-2024 rồi Q3-2024);"
                        " cần tải riêng kỳ đó để bổ sung.")

    report_text = "\n".join(report_lines)
    report_path = os.path.join(output_dir, "bao_cao_chat_luong_du_lieu.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print("\n" + report_text)
    print(f"\n[+] Báo cáo chất lượng đã lưu vào: {report_path}")
    print("=" * 80)
    print(" HOÀN TẤT XỬ LÝ DỮ LIỆU!")
    print("=" * 80)


if __name__ == "__main__":
    main()
