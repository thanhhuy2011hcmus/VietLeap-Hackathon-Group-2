# -*- coding: utf-8 -*-
"""
build_report.py — dựng reports/bao_cao_xu_ly_du_lieu.html.

Chạy mọi file trong analysis/python và analysis/r, nhúng mã nguồn + kết quả chạy thật vào báo cáo.
Chạy sau clean_raw_data.py:   python src/build_report.py   (hoặc python run_pipeline.py)
"""
import base64
import glob
import html
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "reports", "bao_cao_xu_ly_du_lieu.html")
CODE = os.path.join(ROOT, "analysis")
FIG = os.path.join(ROOT, "reports", "figures")
RSCRIPT = shutil.which("Rscript") or next(iter(sorted(glob.glob(r"C:/Program Files/R/R-*/bin/Rscript.exe"))), None)
SECTIONS = {"s0": "00_tu_dien_bien", "s1": "01_nap_du_lieu", "s2": "02_kiem_tra_chat_luong", "s3": "03_lam_sach",
            "s4": "04_tao_bien_moi", "s5": "05_thong_ke_mo_ta", "s6": "06_truc_quan_chat_luong",
            "s7": "07_truc_quan_phan_phoi"}
LANGS = {"py": ("python", "py", "Python"), "r": ("r", "R", "R")}     # khóa -> (thư mục, đuôi file, tên hiển thị)

sys.path.insert(0, os.path.join(CODE, "python"))
os.chdir(ROOT)
from common import BASE_Q, LATEST_Q, QUARTERS, STRESS_Q, close, load_raw, to_wide  # noqa: E402


# ═════════════════════════════ CHẠY CODE PHÂN TÍCH ═════════════════════════════
def run_file(lang, name):
    folder, ext, _ = LANGS[lang]
    path = os.path.join(CODE, folder, f"{name}.{ext}")
    fig_glob = os.path.join(FIG, folder, f"{name[:2]}_*.png")
    for f in glob.glob(fig_glob):
        os.remove(f)
    if lang == "py":
        cmd = [sys.executable, path]
    elif RSCRIPT:
        cmd = [RSCRIPT, path]
    else:
        return "(Máy dựng báo cáo không có R — chưa chạy được đoạn code này.)", []
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if r.returncode != 0:
        raise RuntimeError(f"{path} lỗi:\n{r.stderr.decode('utf-8', 'replace')}")
    out = re.sub(r"\r+\n?", "\n", r.stdout.decode("utf-8", "replace")).rstrip()
    return out, sorted(glob.glob(fig_glob))


def code_block(sid, num, with_common=False):
    tabs, panes = [], []
    for i, (lang, (folder, ext, label)) in enumerate(LANGS.items()):
        out, figs = run_file(lang, SECTIONS[sid])
        srcs = (["common"] if with_common else []) + [SECTIONS[sid]]
        src_html = "".join(
            f'<div class="fname">analysis/{folder}/{n}.{ext}</div>'
            f'<pre class="src">{html.escape(open(os.path.join(CODE, folder, f"{n}.{ext}"), encoding="utf-8").read().rstrip())}</pre>'
            for n in srcs)
        imgs = "".join(
            f'<img src="data:image/png;base64,{base64.b64encode(open(f, "rb").read()).decode()}" '
            f'alt="Hình {os.path.basename(f)[:-4].replace("_", ".")} do code {label} tạo ra" loading="lazy">'
            for f in figs)
        tabs.append(f'<button type="button" class="tab{" on" if i == 0 else ""}" data-lang="{lang}">{label}</button>')
        panes.append(f'<div class="pane" data-lang="{lang}"{"" if i == 0 else " hidden"}>{src_html}'
                     f'<div class="outhead">Kết quả chạy</div><pre class="out">{html.escape(out)}</pre>'
                     f'{f"<div class=imgs>{imgs}</div>" if imgs else ""}</div>')
    print(f"  đã chạy mục {sid[1]}: {SECTIONS[sid]} (Python + R)")
    return (f'<h3>{num}. Code và kết quả chạy</h3><div class="codebox"><div class="tabs">{"".join(tabs)}'
            f'<button type="button" class="copy">Sao chép code</button></div>{"".join(panes)}</div>')


# ═════════════════════════════ TIỆN ÍCH HTML ═════════════════════════════
def vn(x, d=0):
    if x is None or pd.isna(x):
        return "–"
    return f"{x:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def code(s):
    return f"<code>{html.escape(str(s))}</code>"


def table(head, rows, cls=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'


def dict_table(rows):
    return table(["Tên trong CSV", "Tên gốc", "Ý nghĩa", "Dùng để", "Loại", "Đơn vị"],
                 [[code(a), code(b) if b != "–" else "–", c, d, e, u] for a, b, c, d, e, u in rows], cls="dict")


def lst(items):
    return ", ".join(items) if len(items) else "không có"


# ═════════════════════════════ SỐ LIỆU CHO PHẦN CHỮ ═════════════════════════════
p = pd.read_csv(os.path.join(PROC, "panel_quarterly.csv"))
cal = pd.read_csv(os.path.join(PROC, "stress_calibration.csv"))
lab = pd.read_csv(os.path.join(PROC, "hnx_default_labels.csv"))
macro = pd.read_csv(os.path.join(PROC, "macro_quarterly.csv"))
raw = load_raw()
w = to_wide(raw)

tickers = sorted(p["ticker"].unique())
have = set(p["period"])
missing_q = [q for q in QUARTERS if q not in have]
ttm_q = sorted(p.loc[p["cfo_ttm"].notna(), "period"].unique())
L = p[p["period"] == LATEST_Q].set_index("ticker")
short = L[L["liquidity_gap_12m"] < 0].sort_values("liquidity_gap_12m")
med = cal[cal["ticker"] == "MEDIAN"].iloc[0]
c13 = cal[cal["ticker"] != "MEDIAN"]
flags = p["dq_flags"].dropna().str.split(";").explode().value_counts()
n_ident = int(close(w["total_assets"], w["liabilities"] + w["equity"]).sum())
cash_bad = w.loc[~close(w["cf_cash_end"], w["cash"]), ["ticker", "period"]].agg(" ".join, axis=1).tolist()
gap_b = c13["liquidity_gap_base"] < 0
dflt = c13["bond_default_flag"] == 1
hit, miss_def = int((gap_b & dflt).sum()), int((~gap_b & dflt).sum())
false_al = c13.loc[gap_b & ~dflt, "ticker"].tolist()

# ═════════════════════════════ NỘI DUNG ═════════════════════════════
sections = []


def sec(sid, title, body):
    sections.append((sid, title, f'<section id="{sid}"><h2>{title}</h2>{body}</section>'))


sec("q", "Câu hỏi nghiên cứu", f"""
<blockquote>If higher interest rates and slower sales hit again in the next 12 months, as they did in 2022–2023, which
listed Vietnamese residential developers would not have enough cash to repay the debt falling due, how large is each gap,
how much shock can each one absorb, and what should each developer — and the banks that lend to them — do now?</blockquote>
<p>Nếu lãi suất tăng và bán hàng chậm lại trong 12 tháng tới giống giai đoạn 2022–2023, doanh nghiệp BĐS dân cư niêm yết
nào sẽ không đủ tiền trả nợ đến hạn, thiếu bao nhiêu, chịu được cú sốc đến mức nào, và doanh nghiệp cũng như ngân hàng
cho vay nên làm gì ngay bây giờ?</p>
<p>Bộ dữ liệu chỉ giữ những biến trả lời trực tiếp các ý trên. Biến nào không dùng thì không tạo.</p>
{table(["Ý của câu hỏi", "Biến dùng", "File"], [
    ["Ai không đủ tiền trả nợ đến hạn trong 12 tháng",
     code("liquid_assets") + ", " + code("st_debt") + ", " + code("cfo_ttm") + ", " + code("liquidity_coverage"), code("panel_quarterly.csv")],
    ["Thiếu bao nhiêu", code("liquidity_gap_12m") + " (tỷ VND)", code("panel_quarterly.csv")],
    ["Chịu được cú sốc đến đâu (cú sốc lấy theo 2022–2023)",
     code("sales_shock_pct") + ", " + code("adv_shock_pct") + ", " + code("rate_shock_pp") + ", " + code("rollover_stress")
     + "; mức hiện tại " + code("net_sales_ttm") + ", " + code("adv_customers") + ", " + code("interest_paid_ttm") + ", "
     + code("implied_rate_pct") + ", " + code("rollover_ratio"),
     code("stress_calibration.csv") + ", " + code("panel_quarterly.csv")],
    ["DN và ngân hàng nên làm gì", code("debt_to_equity") + ", " + code("total_debt") + ", " + code("rollover_ratio")
     + ", cơ cấu " + code("st_debt") + "/" + code("lt_debt"), code("panel_quarterly.csv")],
    ["Kiểm chứng: chỉ báo có nhận ra DN đã chậm trả năm 2022–2023 không",
     code("liquidity_gap_base") + ", " + code("bond_default_flag"), code("stress_calibration.csv") + ", " + code("hnx_default_labels.csv")],
    ["Xác định thời điểm cú sốc", code("sbv_refinancing_eoq") + ", " + code("fed_upper_eoq") + ", " + code("ust10y_avg"),
     code("macro_quarterly.csv")],
])}
<p><b>Nguồn dữ liệu.</b> Báo cáo tài chính hợp nhất theo quý của {len(tickers)} doanh nghiệp từ FiinQuant
({", ".join(tickers)}); lãi suất Fed và lợi suất trái phiếu kho bạc Mỹ 10 năm từ FRED; quyết định lãi suất điều hành
của NHNN; danh sách tổ chức chậm trả gốc, lãi trái phiếu do HNX công bố cho giai đoạn 16/9/2022 – 31/1/2023.</p>""")

# ---------- 0 ----------
NEW = "Biến mới"
d_panel = [
    ("ticker", "ticker", "Mã cổ phiếu", "Khóa", "Phân loại", "–"),
    ("period, year, quarter", "year, quarter", "Kỳ báo cáo, ví dụ 2026Q3", "Khóa", "Thời gian", "–"),
    ("cash", "BS · total_cash_and_cash_equivalents", "Tiền và tương đương tiền", "Nguồn trả nợ", "Liên tục", "tỷ VND"),
    ("st_invest", "BS · total_short_term_investments", "Đầu tư tài chính ngắn hạn (đã trừ dự phòng)", "Nguồn trả nợ", "Liên tục", "tỷ VND"),
    ("st_debt", "BS · short_term_borrowings", "Vay ngắn hạn, gồm nợ dài hạn đến hạn trả trong 12 tháng", "Nợ đến hạn", "Liên tục", "tỷ VND"),
    ("lt_debt", "BS · long_term_borrowings", "Vay dài hạn", "Tổng nợ, lãi suất", "Liên tục", "tỷ VND"),
    ("equity", "BS · owner_s_equity", "Vốn chủ sở hữu", "Đòn bẩy (góc nhìn ngân hàng)", "Liên tục", "tỷ VND"),
    ("net_sales", "IS · net_sales", "Doanh thu thuần trong quý", "Cú sốc bán hàng", "Liên tục", "tỷ VND"),
    ("cfo", "CF · net_cash_inflows_outflows_from_operating_activities", "Lưu chuyển tiền thuần từ HĐKD (đã trừ lãi vay đã trả)", "Nguồn trả nợ", "Liên tục", "tỷ VND"),
    ("interest_paid", "CF · interest_paid", "Tiền lãi vay đã trả (dương = chi ra)", "Lãi suất thực trả", "Liên tục", "tỷ VND"),
    ("loan_proceeds", "CF · proceeds_from_loans", "Tiền vay mới nhận được", "Khả năng đảo nợ", "Liên tục", "tỷ VND"),
    ("loan_repayments", "CF · repayment_of_loans", "Tiền trả nợ gốc vay (dương = chi ra)", "Khả năng đảo nợ", "Liên tục", "tỷ VND"),
    ("liquid_assets", "–", "cash + st_invest", "Nguồn trả nợ sẵn có", NEW, "tỷ VND"),
    ("total_debt", "–", "st_debt + lt_debt", "Lãi suất thực trả, đòn bẩy", NEW, "tỷ VND"),
    ("adv_customers", "–", "Người mua trả tiền trước ngắn hạn + dài hạn", "Cú sốc bán hàng", NEW, "tỷ VND"),
    ("*_ttm", "–", "Tổng 4 quý liên tiếp của net_sales, cfo, interest_paid, loan_proceeds, loan_repayments", "Quy về 12 tháng", NEW, "tỷ VND"),
    ("implied_rate_pct", "–", "interest_paid_ttm / nợ vay bình quân 4 quý", "Cú sốc lãi suất", NEW, "%/năm"),
    ("rollover_ratio", "–", "loan_proceeds_ttm / loan_repayments_ttm", "Khả năng đảo nợ", NEW, "lần"),
    ("liquidity_gap_12m", "–", "liquid_assets + cfo_ttm − st_debt", "Ai thiếu, thiếu bao nhiêu", NEW, "tỷ VND"),
    ("liquidity_coverage", "–", "(liquid_assets + cfo_ttm) / st_debt", "Xếp hạng mức an toàn", NEW, "lần"),
    ("debt_to_equity", "–", "total_debt / equity", "Khuyến nghị cho ngân hàng", NEW, "lần"),
    ("dq_flags", "–", "Cờ chất lượng của dòng (mục 3)", "Truy vết xử lý", NEW, "–"),
]
d_cal = [
    ("ticker", "–", "Mã cổ phiếu; dòng MEDIAN là trung vị ngành", "Khóa", "Phân loại", "–"),
    ("sales_ttm_base / _stress", "–", f"Doanh thu TTM tại {BASE_Q} và {STRESS_Q}", "Cú sốc bán hàng", NEW, "tỷ VND"),
    ("sales_shock_pct", "–", "Thay đổi doanh thu TTM giữa hai giai đoạn", "Cú sốc bán hàng", NEW, "%"),
    ("adv_base / _stress, adv_shock_pct", "–", "Tiền khách trả trước và mức thay đổi", "Cú sốc bán hàng", NEW, "tỷ VND, %"),
    ("cfo_ttm_base / _stress, cfo_shock", "–", "CFO TTM và mức thay đổi", "Cú sốc dòng tiền", NEW, "tỷ VND"),
    ("rate_base_pct / _stress_pct, rate_shock_pp", "–", "Lãi suất thực trả và mức tăng", "Cú sốc lãi suất", NEW, "%, điểm %"),
    ("rollover_base / _stress", "–", "Tỷ lệ vay mới / trả nợ gốc trong từng giai đoạn", "Cú sốc đảo nợ", NEW, "lần"),
    ("liquidity_gap_base", "–", f"liquidity_gap_12m tại {BASE_Q}, trước khủng hoảng", "Kiểm chứng với nhãn HNX", NEW, "tỷ VND"),
    ("bond_default_flag", "–", "Lấy từ hnx_default_labels.csv", "Kiểm chứng", NEW, "0/1"),
]
d_other = [
    ("period", "observation_date", "Quý", "Khóa", "Thời gian", "–"),
    ("sbv_refinancing_eoq", "loai_lai_suat = tái cấp vốn", "Lãi suất tái cấp vốn NHNN cuối quý", "Mốc thời gian cú sốc", NEW, "%/năm"),
    ("sbv_uncertain", "–", "Quý có mức lãi suất chưa chắc chắn do nguồn thiếu đợt điều chỉnh", "Cảnh báo khi đọc", NEW, "đúng/sai"),
    ("fed_upper_eoq", "DFEDTARU", "Trần lãi suất mục tiêu Fed cuối quý", "Mốc thời gian cú sốc", NEW, "%/năm"),
    ("ust10y_avg", "DGS10", "Lợi suất trái phiếu kho bạc Mỹ 10 năm, trung bình quý", "Mốc thời gian cú sốc", NEW, "%/năm"),
    ("effective_date, decision_date, decision_no", "ngay_hieu_luc, ngay_quyet_dinh, so_quyet_dinh", "Ngày hiệu lực, ngày ký, số quyết định NHNN", "Dựng chuỗi lãi suất", "Thời gian / Phân loại", "–"),
    ("rate_code", "loai_lai_suat", "Mã loại lãi suất", "Lọc lãi suất tái cấp vốn", "Phân loại", "–"),
    ("rate_before, rate_after", "trich_nguyen_van", "Mức lãi suất trước và sau điều chỉnh, tách từ câu chữ", "Dựng chuỗi lãi suất", NEW, "%/năm"),
    ("bond_default_flag", "–", "1 nếu DN (hoặc công ty con) có tên trong danh sách chậm trả HNX", "Kiểm chứng", NEW, "0/1"),
    ("n_entities, n_via_subsidiary, entities", "ten_to_chuc_phat_hanh_nguyen_van", "Số pháp nhân, số pháp nhân là công ty con, tên", "Kiểm chứng", NEW, "–"),
]
sec("s0", "0. Từ điển biến",
    "<p>Cột <b>Dùng để</b> cho biết mỗi biến phục vụ ý nào của câu hỏi. Tên gốc của BCTC rút gọn tiền tố: "
    "<code>BS</code> = <code>balance_sheet[0].</code>, <code>IS</code> = <code>income_statement[0].</code>, "
    "<code>CF</code> = <code>cash_flow[0].</code>. Mọi số tiền tính bằng tỷ VND.</p>"
    "<h3>0.1. <code>panel_quarterly.csv</code> — mã × quý</h3>" + dict_table(d_panel)
    + "<h3>0.2. <code>stress_calibration.csv</code> — cú sốc 2022–2023 của từng DN</h3>" + dict_table(d_cal)
    + "<h3>0.3. <code>macro_quarterly.csv</code>, <code>sbv_policy_events.csv</code>, <code>hnx_default_labels.csv</code></h3>"
    + dict_table(d_other)
    + code_block("s0", "0.4"))

# ---------- 1 ----------
files = [
    ["FiinQuant", code("<MÃ>_bctc_min_raw.csv") + f" × {len(tickers)}", f"{len(raw):,}".replace(",", "."), "Dùng: 17/19 chỉ tiêu"],
    ["FRED", code("fred_DFEDTARU_thang_cuoiky_2019-2026.csv"), "93", "Dùng: lãi suất Fed"],
    ["FRED", code("fred_DGS10_thang_trungbinh_2019-2026.csv"), "94", "Dùng: lợi suất UST 10 năm"],
    ["NHNN", code("sbv_lai_suat_dieu_hanh_trich_nguon.csv"), "16", "Dùng: lãi suất tái cấp vốn"],
    ["HNX", code("hnx_54_to_chuc_cham_tra_trich_nguon.csv"), "30", "Dùng: nhãn chậm trả để kiểm chứng"],
    ["FiinQuant", code("bctc_full_VHM_2026Q3.csv"), "207", "Không dùng: 19 chỉ tiêu trùng khớp 100% với file mới"],
    ["FRED", code("fred_CPIAUCSL_2019-2026.csv"), "94", "Không dùng: lạm phát Mỹ không vào phép tính nào"],
    ["FRED / IMF", code("fred_VNMPCPIPCPPPT_IMF_nam.csv"), "13", "Không dùng: lạm phát Việt Nam không vào phép tính nào"],
]
sec("s1", "1. Nạp dữ liệu và đồng bộ tên biến",
    "<p>Mọi file BCTC có dạng dài: mỗi dòng là một chỉ tiêu (<code>field_path</code>) của một mã trong một quý. "
    "Script đọc tất cả file <code>data/raw/*_bctc_min_raw.csv</code>, nên muốn thêm mã chỉ cần thả file mới vào thư mục. "
    "Từ điển <code>FIELDS</code> trong <code>common.py</code> / <code>common.R</code> đổi 17 đường dẫn FiinQuant sang tên ngắn "
    "rồi pivot thành bảng ngang mã × quý. Hai chỉ tiêu còn lại (đầu tư nắm giữ đến đáo hạn, lợi nhuận sau thuế) không phục "
    "vụ câu hỏi nên bị bỏ. Năm chỉ tiêu (tổng tài sản, nợ phải trả, chi phí lãi vay, tiền đầu kỳ và cuối kỳ trên B03) chỉ "
    "dùng để kiểm tra chéo và điền thiếu, không xuất ra file sạch.</p>"
    + table(["Nguồn", "File trong data/raw", "Số dòng", "Trạng thái"], files)
    + code_block("s1", "1.1", with_common=True))

# ---------- 2 ----------
nf = lambda k: int(flags.get(k, 0))  # noqa: E731
checks = [
    ["Trùng khóa (mã, năm, quý, chỉ tiêu)", "0 dòng", "Đạt"],
    ["Ô trống", "1 ô: lãi vay đã trả của DIG 2021Q3", "Xử lý ở mục 3"],
    ["Độ phủ thời gian", f"{len(have)}/{len(QUARTERS)} quý; thiếu {missing_q[0]} – {missing_q[-1]}",
     f"TTM chỉ tính được cho {ttm_q[0]} – {ttm_q[-2]} và {ttm_q[-1]}"],
    ["Tổng tài sản = Nợ phải trả + VCSH", f"{n_ident}/{len(w)}", "Đạt"],
    ["Tiền cuối kỳ B03 = tiền B01", f"{len(w) - len(cash_bad)}/{len(w)}; lệch: {lst(cash_bad)}", "Dùng số B01, gắn cờ"],
    ["Số riêng quý hay lũy kế", "142/143 cặp quý liền kề là số riêng quý, 0 cặp lũy kế", "Không cần tách lũy kế"],
    ["Lãi vay đã trả mang dấu dương", f"{nf('interest_paid_sign')} quý", "Gắn cờ, giữ dấu (mục 3)"],
    ["Trả nợ gốc dương / vay mới âm", f"{nf('loan_repayments_sign')} / {nf('loan_proceeds_sign')} quý", "Gắn cờ, giữ dấu"],
    ["Doanh thu thuần âm", f"{nf('net_sales_sign')} quý (LDG, NRC)", "Gắn cờ, giữ dấu"],
    ["File VHM cũ so với file mới", "19 chỉ tiêu trùng, lệch 0", "Bỏ file cũ"],
    ["Chuỗi lãi suất NHNN liên tục", "4 chỗ mức trước đợt sau ≠ mức sau đợt trước", "Gắn cờ " + code("sbv_uncertain")],
]
sec("s2", "2. Kiểm tra chất lượng dữ liệu",
    table(["Phép kiểm tra", "Kết quả", "Xử lý"], checks)
    + "<p>Kiểm tra “riêng quý hay lũy kế” quan trọng nhất: nếu số quý là lũy kế từ đầu năm mà cộng 4 quý lại thì CFO, "
      "doanh thu, lãi vay 12 tháng sẽ bị thổi phồng nhiều lần. Tiền đầu kỳ trên B03 của quý sau luôn bằng tiền cuối kỳ của "
      "quý trước, nên đây là số riêng từng quý.</p>"
    + code_block("s2", "2.1"))

# ---------- 3 ----------
sec("s3", "3. Làm sạch: xử lý thiếu, dấu và ngoại lai",
    "<h3>3.1. Thiếu và mâu thuẫn</h3>"
    + table(["Vấn đề", "Cách xử lý", "Lý do"], [
        ["Lãi vay đã trả DIG 2021Q3 trống", "Lấy chi phí lãi vay B02 cùng quý (−1,62 tỷ), cờ " + code("interest_paid_from_pl"),
         "Ô này nằm trong TTM nền của DIG; để trống sẽ mất cả cú sốc lãi suất của DIG"],
        ["Quý 2024Q1 – 2025Q3 không có số liệu", "Không nội suy. Dựng lưới quý đầy đủ để phép cộng 4 quý không nhảy qua khoảng trống",
         "Nội suy dòng tiền của DN BĐS 7 quý liền là bịa số"],
        ["Tiền B01 ≠ tiền cuối kỳ B03 (VHM 2025Q4)", "Dùng số B01, cờ " + code("cash_bs_ne_cf"),
         "B01 là số dư thực tế dùng để trả nợ"],
        ["Dòng tiền ra mang dấu âm theo quy ước FiinQuant", "Đổi dấu " + code("interest_paid") + ", " + code("loan_repayments")
         + " để số dương = chi ra", "Dễ đọc, dễ cộng"],
        ["Quý mang dấu ngược (lãi vay dương, trả nợ dương, vay mới âm, doanh thu âm)",
         "<b>Giữ dấu</b>, không lấy " + code("abs()") + "; gắn cờ " + code("*_sign"),
         "Đây là phần hiệu chỉnh khi nhà cung cấp tách số lũy kế; " + code("abs()") + " làm lãi vay 2023 của HQC tăng từ 4,6 lên 18,6 tỷ"],
        ["Đơn vị VND", "Chia 1e9 sang tỷ VND", "Số dễ đọc, sai số làm tròn không đáng kể"],
    ])
    + "<h3>3.2. Ngoại lai</h3>"
    "<p>Dùng quy tắc 1,5 × IQR, chỉ gắn cờ và giải thích, không xóa. Với 13 doanh nghiệp, xóa một DN là mất câu trả lời "
    "cho chính DN đó. Các tỷ số cực đoan đều do mẫu số quá nhỏ:</p><ul>"
    "<li><b>HQC:</b> nợ vay chỉ khoảng 13 tỷ nhưng trả 50–70 tỷ tiền lãi mỗi năm (lãi cho khoản phải trả khác), nên "
    "lãi suất thực trả lên tới 544%. Cú sốc lãi suất và đảo nợ của HQC không có ý nghĩa kinh tế.</li>"
    "<li><b>DIG:</b> hệ số bao phủ 14,4 lần vì nợ vay ngắn hạn rất nhỏ so với tiền và đầu tư ngắn hạn.</li>"
    "<li><b>Cú sốc doanh thu:</b> PDR, NRC giảm hơn 93%; VHM, HPX, KDH lại tăng do bàn giao dự án lớn đúng giai đoạn này.</li></ul>"
    "<p>Vì vậy cú sốc chung của ngành lấy <b>trung vị</b> (không bị ngoại lai kéo lệch) thay vì trung bình. "
    "Cú sốc riêng của từng DN vẫn giữ nguyên để so sánh.</p>"
    + code_block("s3", "3.3"))

# ---------- 4 ----------
sec("s4", "4. Tạo biến mới",
    "<p>Biến nào cũng phải trả lời được một ý của câu hỏi; mục đích của từng biến ghi ở cột “Dùng để” trong từ điển.</p>"
    "<h3>4.1. Biến cho từng quý</h3>"
    + table(["Biến", "Công thức", "Trả lời ý nào"], [
        [code("liquid_assets"), "cash + st_invest", "Tiền có thể dùng ngay để trả nợ"],
        [code("total_debt"), "st_debt + lt_debt", "Nền để tính lãi suất thực trả và đòn bẩy"],
        [code("*_ttm"), "Tổng 4 quý liên tiếp của net_sales, cfo, interest_paid, loan_proceeds, loan_repayments; trống nếu thiếu quý",
         "Quy mọi dòng tiền về 12 tháng, cùng kỳ hạn với nợ đến hạn"],
        [code("cfo_ttm"), "Tổng CFO 4 quý gần nhất (đã trừ lãi vay đã trả)", "Tiền tạo ra trong 12 tháng nếu kinh doanh như năm qua"],
        [code("liquidity_gap_12m"), "liquid_assets + cfo_ttm − st_debt",
         "<b>Thiếu bao nhiêu</b> nếu không vay được đồng nào mới; âm là thiếu"],
        [code("liquidity_coverage"), "(liquid_assets + cfo_ttm) / st_debt", "Xếp hạng an toàn; dưới 1 là không đủ"],
        [code("rollover_ratio"), "loan_proceeds_ttm / loan_repayments_ttm",
         "Ngân hàng đang cho đảo nợ đến đâu; dưới 1 là đang phải trả ròng"],
        [code("implied_rate_pct"), "interest_paid_ttm / nợ vay bình quân 4 quý × 100", "Mức lãi suất thực trả, nền để cộng cú sốc lãi suất"],
        [code("adv_customers"), "Người mua trả trước ngắn hạn + dài hạn", "Chỉ báo bán hàng, nguồn tiền không lãi"],
        [code("debt_to_equity"), "total_debt / equity", "Mức đòn bẩy để ngân hàng đặt điều kiện cho vay"],
    ])
    + f"<h3>4.2. Cú sốc 2022–2023 của từng DN</h3>"
    f"<p>So tổng 4 quý khủng hoảng (2022Q3–{STRESS_Q}, sau đợt tăng lãi suất 10/2022 và thị trường trái phiếu đóng băng) "
    f"với 4 quý trước đó (2021Q3–{BASE_Q}). Lấy trung vị của 13 DN: doanh thu giảm {vn(-med['sales_shock_pct'], 1)}%, "
    f"tiền khách trả trước giảm {vn(-med['adv_shock_pct'], 1)}%, lãi suất thực trả tăng {vn(med['rate_shock_pp'], 2)} điểm %, "
    f"còn cứ 1 đồng nợ trả đi thì chỉ vay lại được {vn(med['rollover_stress'], 2)} đồng. Bốn con số này sẽ là kịch bản "
    "“2022–2023 lặp lại” ở bước mô hình.</p>"
    + code_block("s4", "4.3"))

# ---------- 5 ----------
neg_rows = [[code(t), vn(r["liquidity_gap_12m"]), vn(r["liquidity_coverage"], 2), vn(r["rollover_ratio"], 2),
             vn(r["debt_to_equity"], 2), "có" if lab.set_index("ticker").loc[t, "bond_default_flag"] == 1 else "không"]
            for t, r in short.iterrows()]
sec("s5", "5. Thống kê mô tả",
    f"<h3>5.1. Ai đang thiếu tiền ở {LATEST_Q}</h3>"
    f"<p>Giả sử 12 tháng tới dòng tiền kinh doanh giống 12 tháng vừa qua và ngân hàng không cho vay thêm. Khi đó "
    f"{len(short)}/{len(L)} DN không đủ tiền trả hết nợ vay ngắn hạn, dù chưa tính tới cú sốc nào:</p>"
    + table(["Mã", "Thiếu hụt (tỷ VND)", "Bao phủ (lần)", "Vay mới / trả nợ", "Nợ / VCSH", "Có tên HNX 2022–2023"], neg_rows)
    + f"<h3>5.2. Kiểm chứng với 2022–2023</h3>"
    f"<p>Nếu tính cùng chỉ số tại {BASE_Q}, trước khủng hoảng, thì {hit}/{int(dflt.sum())} DN về sau có tên trong danh sách "
    f"chậm trả của HNX đã thiếu hụt từ trước. Trường hợp sót là {lst(c13.loc[~gap_b & dflt, 'ticker'].tolist())} "
    f"(vẫn đủ tiền tại {BASE_Q}, nhưng CFO 12 tháng giảm "
    f"{vn(-c13.set_index('ticker').loc['NVL', 'cfo_shock'])} tỷ trong khủng hoảng: rủi ro đến từ cú sốc dòng tiền chứ không có sẵn). "
    f"{len(false_al)} DN thiếu hụt nhưng không có tên ({lst(false_al)}). Danh sách HNX đã trích mới có 30/54 tổ chức nên "
    "không có tên chưa chắc là không chậm trả.</p>"
    "<p>Thiếu hụt và hệ số bao phủ lệch phải mạnh (độ lệch khoảng 2,5–3,6 ở lát cắt hiện tại, 6,7–8,3 khi gộp mọi quý): "
    "VHM quá lớn và vài DN có nợ vay rất nhỏ kéo trung bình đi xa trung vị. Khi trình bày nên dùng trung vị và giá trị "
    "riêng từng DN, không dùng trung bình.</p>"
    + code_block("s5", "5.3"))

# ---------- 6 ----------
sec("s6", "6. Trực quan hóa (1): chất lượng và độ phủ dữ liệu",
    "<ul><li><b>Hình 6.1</b> — độ phủ mã × quý. Khoảng trống 2024Q1–2025Q3 làm TTM chỉ tính được ở hai đoạn; "
    f"lát cắt hiện tại duy nhất là {LATEST_Q}.</li>"
    "<li><b>Hình 6.2</b> — số quý bị gắn cờ theo loại. Phần lớn là dấu ngược do hiệu chỉnh số liệu, giá trị nhỏ.</li>"
    "<li><b>Hình 6.3</b> — lãi suất và hai cửa sổ dùng để đo cú sốc. Chuỗi NHNN chỉ bắt đầu từ 10/2022 vì nguồn chỉ trích "
    "các quyết định từ đó.</li></ul>"
    + code_block("s6", "6.1"))

# ---------- 7 ----------
sec("s7", "7. Trực quan hóa (2): phân phối và ngoại lai",
    f"<ul><li><b>Hình 7.1</b> — hệ số bao phủ nợ vay ngắn hạn tại {LATEST_Q}; cột cam là DN thiếu hụt, nhãn ghi số tỷ VND "
    "thiếu hoặc dư.</li>"
    "<li><b>Hình 7.2</b> — cú sốc 2022–2023 giữa các DN, ghi tên DN ngoại lai. Biên độ rất rộng nên kịch bản chung dùng trung vị.</li>"
    "<li><b>Hình 7.3</b> — lãi suất thực trả trên mọi quan sát có TTM. Phần lớn nằm 6–10%; các điểm vượt biên gần như "
    "toàn là HQC.</li></ul>"
    + code_block("s7", "7.1"))

# ═════════════════════════════ GHÉP HTML ═════════════════════════════
CSS = """
:root{--bg:#fff;--ink:#1f2328;--ink2:#59636e;--muted:#6e7781;--line:#d8dee4;--th:#f6f8fa;--code:#eff1f3;--link:#0969da}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--ink:#e6edf3;--ink2:#9198a1;
--muted:#8b949e;--line:#30363d;--th:#161b22;--code:#21262d;--link:#4493f8}}
:root[data-theme="dark"]{--bg:#0d1117;--ink:#e6edf3;--ink2:#9198a1;--muted:#8b949e;--line:#30363d;--th:#161b22;
--code:#21262d;--link:#4493f8}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 "Segoe UI",-apple-system,"Helvetica Neue",Arial,sans-serif}
.wrap{display:flex;align-items:flex-start;gap:40px;padding:32px 24px 80px;max-width:1320px}
nav{position:sticky;top:24px;flex:0 0 250px;font-size:14.5px}
nav .t{font-weight:600;margin:0 0 8px}
nav ol{list-style:none;margin:0;padding:0;border-left:1px solid var(--line)}
nav a{display:block;padding:5px 0 5px 14px;color:var(--ink2);text-decoration:none;margin-left:-1px;border-left:2px solid transparent}
nav a:hover{color:var(--ink)}nav a.on{color:var(--ink);border-left-color:var(--ink);font-weight:600}
main{flex:1 1 auto;min-width:0;max-width:1000px}
h1{font-size:30px;line-height:1.25;margin:0 0 6px}.sub{color:var(--muted);margin:0 0 28px;font-size:15px}
h2{font-size:26px;margin:52px 0 20px;padding-bottom:10px;border-bottom:1px solid var(--line)}
h3{font-size:18px;margin:30px 0 12px}p,ul{margin:0 0 14px}ul{padding-left:22px}li{margin:4px 0}a{color:var(--link)}
blockquote{margin:0 0 14px;padding:4px 0 4px 16px;border-left:3px solid var(--line);color:var(--ink2);font-style:italic}
code{font-family:Consolas,"SFMono-Regular",Menlo,monospace;font-size:.86em;background:var(--code);padding:2px 6px;border-radius:5px}
pre{margin:0;padding:12px 16px;overflow:auto;font:13.5px/1.5 Consolas,Menlo,monospace}
.tw{overflow-x:auto;margin:0 0 18px}
table{border-collapse:collapse;width:100%;font-size:15px}
th,td{border:1px solid var(--line);padding:10px 13px;text-align:left;vertical-align:middle}
th{background:var(--th);font-weight:600}
td:first-child code{white-space:nowrap}
table.dict td:nth-child(2) code{word-break:break-all}
.codebox{border:1px solid var(--line);border-radius:6px;margin:0 0 26px;overflow:hidden}
.tabs{display:flex;border-bottom:1px solid var(--line);background:var(--th)}
.tab,.copy{font:inherit;font-size:14px;border:0;background:none;color:var(--ink2);cursor:pointer;padding:8px 18px}
.tab{border-bottom:2px solid transparent;margin-bottom:-1px}.tab:hover,.copy:hover{color:var(--ink)}
.tab.on{color:var(--ink);font-weight:600;border-bottom-color:var(--ink);background:var(--bg)}
.copy{margin-left:auto;font-size:13px}
.fname{font:12.5px Consolas,Menlo,monospace;color:var(--muted);padding:8px 16px 0;border-top:1px solid var(--line)}
.pane .fname:first-child{border-top:0}
.pane pre{white-space:pre}
.outhead{font-size:13px;font-weight:600;color:var(--ink2);padding:7px 16px;background:var(--th);
border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.pane pre.out{background:var(--code)}
.imgs{padding:12px 16px;display:grid;gap:12px;border-top:1px solid var(--line)}
.imgs img{max-width:100%;height:auto;border:1px solid var(--line);background:#fff}
@media (max-width:900px){.wrap{display:block;padding:20px 16px 60px}nav{position:static;margin-bottom:24px}
h1{font-size:24px}h2{font-size:22px}}
"""
JS = """
const links=[...document.querySelectorAll('nav a')];
const io=new IntersectionObserver(es=>{es.forEach(en=>{if(en.isIntersecting){links.forEach(a=>a.classList.toggle('on',
 a.getAttribute('href')==='#'+en.target.id))}})},{rootMargin:'0px 0px -70% 0px'});
document.querySelectorAll('main section').forEach(s=>io.observe(s));
function setLang(l){document.querySelectorAll('.codebox').forEach(b=>{
 b.querySelectorAll('.tab').forEach(t=>t.classList.toggle('on',t.dataset.lang===l));
 b.querySelectorAll('.pane').forEach(p=>p.hidden=p.dataset.lang!==l)});
 try{localStorage.setItem('codeLang',l)}catch(e){}}
document.addEventListener('click',ev=>{const t=ev.target.closest('.tab');if(t){setLang(t.dataset.lang);return}
 const c=ev.target.closest('.copy');if(c){const src=[...c.closest('.codebox').querySelectorAll('.pane:not([hidden]) .src')]
 .map(e=>e.textContent).join('\\n\\n');const done=()=>{c.textContent='Đã sao chép';setTimeout(()=>c.textContent='Sao chép code',1500)};
 if(navigator.clipboard){navigator.clipboard.writeText(src).then(done,()=>{})}}});
try{const l=localStorage.getItem('codeLang');if(l)setLang(l)}catch(e){}
"""
toc = "".join(f'<li><a href="#{sid}">{t}</a></li>' for sid, t, _ in sections)
doc = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Xử lý dữ liệu – Nhóm 2</title><style>{CSS}</style></head>
<body><div class="wrap">
<nav aria-label="Mục lục"><p class="t">Mục lục</p><ol>{toc}</ol></nav>
<main>
<h1>Xử lý dữ liệu: rủi ro thanh khoản của doanh nghiệp BĐS dân cư niêm yết</h1>
<p class="sub">VietLeap Hackathon 2026 · Nhóm 2 · {len(tickers)} doanh nghiệp · dữ liệu đến {LATEST_Q} · cập nhật {pd.Timestamp.now():%d/%m/%Y}</p>
{"".join(s for _, _, s in sections)}
</main></div>
<script>{JS}</script>
</body></html>"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(doc)
print(f"Đã ghi {OUT} ({len(doc) / 1024:.0f} KB)")
