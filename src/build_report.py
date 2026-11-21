# -*- coding: utf-8 -*-
"""
build_report.py — dựng reports/bao_cao_truc_quan_hoa.html.

Chạy mọi file trong analysis/python và analysis/r, nhúng mã nguồn (tô màu theo VS Code Light Modern),
kết quả chạy thật (nền vàng nhạt) và hình vào một file HTML.
Chạy sau khi đã làm sạch dữ liệu:  python src/build_report.py   (hoặc python run_pipeline.py)
"""
import base64
import glob
import html
import os
import re
import shutil
import subprocess
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
CODE = os.path.join(ROOT, "analysis")
FIG = os.path.join(ROOT, "reports", "figures")
OUT = os.path.join(ROOT, "reports", "bao_cao_truc_quan_hoa.html")
RSCRIPT = shutil.which("Rscript") or next(iter(sorted(glob.glob(r"C:/Program Files/R/R-*/bin/Rscript.exe"))), None)
SECTIONS = {"s0": "00_tu_dien_bien", "s1": "01_nap_du_lieu", "s2": "02_kiem_tra_chat_luong", "s3": "03_lam_sach",
            "s4": "04_tao_bien_moi", "s5": "05_thong_ke_mo_ta", "s6": "06_truc_quan_chat_luong",
            "s7": "07_truc_quan_phan_phoi"}
LANGS = {"py": ("python", "py", "Python"), "r": ("r", "R", "R")}

sys.path.insert(0, os.path.join(ROOT, "src"))
from clean_bctc_data import BALANCE_SHEET_MAP, FINANCIAL_RATIOS_MAP, INCOME_STATEMENT_MAP  # noqa: E402

# ═════════════════════ tô màu code theo VS Code Light Modern (nền trắng) ═════════════════════
PY_CONTROL = {"import", "from", "as", "for", "in", "if", "elif", "else", "return", "while", "break",
              "continue", "with", "try", "except", "finally", "raise", "pass", "yield", "assert", "del"}
PY_STORAGE = {"def", "class", "lambda", "and", "or", "not", "is", "True", "False", "None", "global"}
PY_TYPES = {"int", "str", "float", "list", "dict", "set", "tuple", "bool", "object", "range"}
R_CONTROL = {"if", "else", "for", "in", "while", "repeat", "return", "next", "break"}
R_STORAGE = {"function", "TRUE", "FALSE", "NULL", "NA", "Inf", "NaN", "NA_real_", "NA_character_"}
C = {"control": "#AF00DB", "storage": "#0000FF", "func": "#795E26", "type": "#267F99", "const": "#0070C1",
     "var": "#001080", "str": "#A31515", "num": "#098658", "com": "#008000"}
BRACKETS = ["#0431FA", "#319331", "#7B3814"]
TOKEN = {
    "py": re.compile(
        r'(?P<com>#[^\n]*)'
        r'|(?P<str>[rRfFbB]{0,2}(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'))'
        r'|(?P<num>\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b)|(?P<id>[A-Za-z_]\w*)|(?P<ws>\s+)|(?P<op>.)'),
    "r": re.compile(
        r'(?P<com>#[^\n]*)|(?P<str>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(?P<bt>`[^`]*`)'
        r'|(?P<num>\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?L?\b)|(?P<id>[A-Za-z.][A-Za-z0-9._]*)'
        r'|(?P<ws>\s+)|(?P<op>%[^%\n]*%|<-|.)'),
}


def imported_modules(src):
    names = set()
    for line in src.splitlines():
        s = line.split("#")[0].strip()
        if s.startswith("import "):
            for item in s[len("import "):].split(","):
                names.add(item.split(" as ")[-1].strip().split(".")[0])
    return names


def id_color(t, lang, prev, nxt, modules):
    if lang == "py":
        if t in PY_CONTROL:
            return C["control"]
        if t in PY_STORAGE:
            return C["storage"]
        if prev == "def":
            return C["func"]
        if nxt == "(" and (t[0].isupper() or t in PY_TYPES):
            return C["type"]
        if t in modules and prev != ".":
            return C["type"]
    else:
        if t in R_CONTROL:
            return C["control"]
        if t in R_STORAGE:
            return C["storage"]
    if nxt == "(":
        return C["func"]
    if prev not in (".", "$", "@") and re.fullmatch(r"[A-Z][A-Z0-9_]+", t):
        return C["const"]
    return C["var"]


def highlight(src, lang):
    toks = [(m.lastgroup, m.group()) for m in TOKEN[lang].finditer(src)]
    sig = [i for i, (k, _) in enumerate(toks) if k != "ws"]
    prev = {sig[j]: toks[sig[j - 1]][1] for j in range(1, len(sig))}
    nxt = {sig[j]: toks[sig[j + 1]][1] for j in range(len(sig) - 1)}
    modules = imported_modules(src) if lang == "py" else set()
    fixed = {"com": C["com"], "str": C["str"], "num": C["num"], "bt": C["var"]}
    out, depth = [], 0
    for i, (kind, t) in enumerate(toks):
        if kind in fixed:
            c = fixed[kind]
        elif kind == "id":
            c = id_color(t, lang, prev.get(i, ""), nxt.get(i, ""), modules)
        elif kind == "op" and t in "([{":
            c, depth = BRACKETS[depth % 3], depth + 1
        elif kind == "op" and t in ")]}":
            depth = max(depth - 1, 0)
            c = BRACKETS[depth % 3]
        else:
            out.append(html.escape(t))
            continue
        out.append(f'<span style="color:{c}">{html.escape(t)}</span>')
    return "".join(out)


# ═════════════════════ chạy code và dựng khối code ═════════════════════
def run_file(lang, name):
    folder, ext, _ = LANGS[lang]
    path = os.path.join(CODE, folder, f"{name}.{ext}")
    fig_glob = os.path.join(FIG, folder, f"{name[:2]}_*.png")
    for f in glob.glob(fig_glob):
        os.remove(f)
    if lang == "r" and not RSCRIPT:
        return "(Máy dựng báo cáo không có R — chưa chạy được đoạn code này.)", []
    cmd = [sys.executable, path] if lang == "py" else [RSCRIPT, path]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if r.returncode != 0:
        raise RuntimeError(f"{path} lỗi:\n{r.stderr.decode('utf-8', 'replace')}")
    out = re.sub(r"\r+\n?", "\n", r.stdout.decode("utf-8", "replace")).rstrip()
    return out, sorted(glob.glob(fig_glob))


def code_block(sid, num, with_common=False):
    tabs, panes = [], []
    for i, (lang, (folder, ext, label)) in enumerate(LANGS.items()):
        out, figs = run_file(lang, SECTIONS[sid])
        names = (["common"] if with_common else []) + [SECTIONS[sid]]
        src = "".join(
            f'<div class="fname">analysis/{folder}/{n}.{ext}</div><pre class="src">'
            f'{highlight(open(os.path.join(CODE, folder, f"{n}.{ext}"), encoding="utf-8").read().rstrip(), lang)}</pre>'
            for n in names)
        imgs = "".join(f'<img src="data:image/png;base64,{base64.b64encode(open(f, "rb").read()).decode()}" '
                       f'alt="Hình {os.path.basename(f)[:-4].replace("_", ".")} ({label})" loading="lazy">'
                       for f in figs)
        tabs.append(f'<button type="button" class="tab{" on" if i == 0 else ""}" data-lang="{lang}">{label}</button>')
        panes.append(f'<div class="pane" data-lang="{lang}"{"" if i == 0 else " hidden"}>{src}'
                     f'<div class="outhead">Kết quả chạy</div><pre class="out">{html.escape(out)}</pre>'
                     f'{f"<div class=imgs>{imgs}</div>" if imgs else ""}</div>')
    print(f"  đã chạy mục {sid[1]}: {SECTIONS[sid]} (Python + R)")
    return (f'<h3>{num}. Code và kết quả chạy</h3><div class="codebox"><div class="tabs">{"".join(tabs)}'
            f'<button type="button" class="copy">Sao chép code</button></div>{"".join(panes)}</div>')


# ═════════════════════ tiện ích HTML ═════════════════════
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


# ═════════════════════ số liệu cho phần chữ ═════════════════════
panel = pd.read_csv(os.path.join(PROC, "bctc", "panel_quarterly_bctc.csv"))
feat = pd.read_csv(os.path.join(PROC, "features", "bien_moi_quy.csv"))
macro = pd.read_csv(os.path.join(PROC, "macro", "macro_quy.csv"))
RE = sorted(feat.loc[feat["is_real_estate"], "ticker"].unique())
LATEST = panel["period"].max()
now = feat[(feat["period"] == LATEST) & feat["ticker"].isin(RE)].set_index("ticker")
short = now[now["cash_coverage"] < 1].sort_values("cash_coverage")
gap_q = {t: [str(x) for x in pd.period_range(g["period"].min(), g["period"].max(), freq="Q")
             if str(x) not in set(g["period"])] for t, g in panel.groupby("ticker")}
gap_q = {t: v for t, v in gap_q.items() if v}
yoy = feat[feat["ticker"].isin(RE)].dropna(subset=["revenue_yoy_pct"])
y23 = yoy[yoy["period"] <= "2023Q4"]["revenue_yoy_pct"]
ylast = yoy[yoy["period"] >= "2025Q4"]["revenue_yoy_pct"]

# ═════════════════════ nội dung ═════════════════════
sections = []


def sec(sid, title, body):
    sections.append((sid, title, f'<section id="{sid}"><h2>{title}</h2>{body}</section>'))


NEW = "Biến mới"
sec("q", "Câu hỏi nghiên cứu", f"""
<blockquote>If higher interest rates and slower sales hit again in the next 12 months, as they did in 2022–2023, which
listed Vietnamese residential developers would not have enough cash to repay the debt falling due, how large is each gap,
how much shock can each one absorb, and what should each developer — and the banks that lend to them — do now?</blockquote>
<p>Nếu lãi suất tăng và bán hàng chậm lại trong 12 tháng tới giống giai đoạn 2022–2023, doanh nghiệp BĐS dân cư niêm yết
nào sẽ không đủ tiền trả các khoản nợ đến hạn, thiếu bao nhiêu, chịu được cú sốc đến đâu, và doanh nghiệp cũng như ngân hàng
cho vay nên làm gì ngay bây giờ?</p>
<p>Báo cáo này chuẩn bị và trực quan hóa dữ liệu cho câu hỏi trên. Chỉ những biến trả lời trực tiếp một ý của câu hỏi
mới được tạo thêm.</p>
{table(["Ý của câu hỏi", "Biến dùng", "File"], [
    ["Ai không đủ tiền trả nợ đến hạn", code("liquid_assets") + ", " + code("short_term_liabilities") + ", "
     + code("cash_coverage"), code("bien_moi_quy.csv") + ", " + code("panel_quarterly_bctc.csv")],
    ["Thiếu bao nhiêu", code("liquidity_gap") + " (tỷ đồng)", code("bien_moi_quy.csv")],
    ["Bán hàng chậm lại đến mức nào", code("revenue_yoy_pct") + ", " + code("revenue_ttm"), code("bien_moi_quy.csv")],
    ["Chịu được lãi suất tăng đến đâu", code("fin_cost_ratio_pct") + ", " + code("liab_to_equity"),
     code("bien_moi_quy.csv")],
    ["Tài sản ngắn hạn có dễ chuyển thành tiền không", code("inventory_share"), code("bien_moi_quy.csv")],
    ["Bối cảnh lãi suất 2022–2023 và hiện tại", code("sbv_refinancing_eoq_pct") + ", " + code("fed_upper_eoq_pct")
     + ", " + code("ust10y_avg_pct"), code("macro_quy.csv")],
])}
<p><b>Nguồn dữ liệu.</b> Báo cáo tài chính tóm tắt theo quý từ Vietstock của {len(RE)} doanh nghiệp bất động sản
({", ".join(RE)}) và SRC; lãi suất Fed, lợi suất trái phiếu kho bạc Mỹ 10 năm và CPI từ FRED; lạm phát Việt Nam từ IMF;
quyết định lãi suất điều hành của NHNN.</p>
<p><b>Giới hạn cần biết trước.</b> Bộ tóm tắt Vietstock không có báo cáo lưu chuyển tiền tệ và không tách riêng nợ vay,
nên “nợ đến hạn trong 12 tháng” được đo gián tiếp bằng <i>nợ ngắn hạn</i> (gồm cả phải trả người bán và tiền khách hàng
trả trước, phần sau không phải trả bằng tiền mặt). Các con số thiếu hụt ở đây vì vậy là chỉ báo thận trọng, chưa phải
số nợ vay thực phải trả. Mã SRC là Cao su Sao Vàng, không phải doanh nghiệp BĐS, nên chỉ xuất hiện ở phần kiểm tra
dữ liệu.</p>""")

# ---------- 0 ----------
def rows_from_map(m, kind="Liên tục", unit="tỷ đồng", used=()):
    return [[code(v), html.escape(k), kind, "đồng/cp" if v == "basic_eps_vnd" else unit, "có" if v in used else ""]
            for k, v in m.items()]


USED = {"net_revenue", "financial_expense", "cogs", "gross_profit", "cash_and_equivalents", "short_term_investments",
        "inventory", "current_assets", "short_term_liabilities", "total_liabilities", "owner_equity", "total_assets",
        "non_current_assets", "total_resources", "paid_in_capital", "gross_margin_pct", "net_margin_pct",
        "debt_to_assets", "roea_pct"}
dict_head = ["Tên trong CSV", "Tên gốc (Vietstock)", "Loại", "Đơn vị", "Dùng trong báo cáo"]
key_rows = [[code("ticker"), "Mã cổ phiếu", "Phân loại", "–", "có"],
            [code("period, year, quarter"), "Kỳ báo cáo, ví dụ 2026Q3", "Thời gian", "–", "có"]]
ratio_rows = [[code(v), html.escape(k), "Liên tục", "%" if v.endswith("pct") or v == "debt_to_assets" else
               ("nghìn đồng/cp" if v in ("eps_ttm", "bvps") else "lần"), "có" if v in USED else ""]
              for k, v in FINANCIAL_RATIOS_MAP.items()
              if v in pd.read_csv(os.path.join(PROC, "bctc", "chi_so_tai_chinh_nam.csv"), nrows=1).columns]
new_rows = [
    [code("is_real_estate"), "–", NEW, "đúng/sai", "Loại SRC khỏi phân tích BĐS"],
    [code("liquid_assets"), "cash_and_equivalents + short_term_investments", NEW, "tỷ đồng", "Nguồn trả nợ sẵn có"],
    [code("liquidity_gap"), "liquid_assets − short_term_liabilities", NEW, "tỷ đồng", "Thiếu bao nhiêu"],
    [code("cash_coverage"), "liquid_assets / short_term_liabilities", NEW, "lần", "Ai không đủ tiền"],
    [code("inventory_share"), "inventory / current_assets", NEW, "tỷ lệ", "Chất lượng tài sản ngắn hạn"],
    [code("liab_to_equity"), "total_liabilities / owner_equity", NEW, "lần", "Đòn bẩy, góc nhìn ngân hàng"],
    [code("revenue_ttm"), "tổng net_revenue 4 quý liên tiếp", NEW, "tỷ đồng", "Quy mô bán hàng 12 tháng"],
    [code("revenue_yoy_pct"), "net_revenue so với cùng quý năm trước", NEW, "%", "Cú sốc bán hàng"],
    [code("fin_cost_ratio_pct"), "financial_expense 4 quý / revenue_ttm", NEW, "%", "Sức chịu lãi suất"],
    [code("st_invest_filled_0"), "–", NEW, "đúng/sai", "Đánh dấu đầu tư ngắn hạn “-” tính là 0"],
]
macro_rows = [
    [code("month / quarter"), "observation_date", "Thời gian", "–", "có"],
    [code("us_cpi_index, us_cpi_yoy_pct"), "CPIAUCSL", "Liên tục", "chỉ số, %", ""],
    [code("fed_upper_pct / fed_upper_eoq_pct"), "DFEDTARU", "Liên tục", "%/năm", "có"],
    [code("ust10y_pct / ust10y_avg_pct"), "DGS10", "Liên tục", "%/năm", "có"],
    [code("sbv_refinancing_eoq_pct"), "loai_lai_suat = tái cấp vốn", "Liên tục", "%/năm", "có"],
    [code("vn_cpi_yoy_pct, data_type"), "VNMPCPIPCPPPT", "Liên tục / Phân loại", "%", ""],
]
sec("s0", "0. Từ điển biến",
    "<p>Biến lấy từ file gốc giữ tên tiếng Anh ngắn do <code>src/clean_bctc_data.py</code> đặt; cột “Tên gốc” là tên "
    "chỉ tiêu trong file Vietstock. Cột “Loại” ghi <b>Biến mới</b> cho biến do nhóm tạo ra ở mục 4.</p>"
    "<h3>0.1. Kết quả kinh doanh theo quý — <code>ket_qua_kinh_doanh_quy.csv</code></h3>"
    + table(dict_head, key_rows + rows_from_map(INCOME_STATEMENT_MAP, used=USED), "dict")
    + "<h3>0.2. Cân đối kế toán theo quý — <code>can_doi_ke_toan_quy.csv</code></h3>"
    + table(dict_head, rows_from_map(BALANCE_SHEET_MAP, used=USED), "dict")
    + "<h3>0.3. Chỉ số tài chính theo năm — <code>chi_so_tai_chinh_nam.csv</code></h3>"
    + table(dict_head, ratio_rows, "dict")
    + "<h3>0.4. Vĩ mô — <code>macro_thang.csv</code>, <code>macro_quy.csv</code>, <code>cpi_viet_nam_nam.csv</code></h3>"
    + table(["Tên trong CSV", "Tên gốc (FRED / IMF / NHNN)", "Loại", "Đơn vị", "Dùng trong báo cáo"], macro_rows, "dict")
    + "<h3>0.5. Biến mới — <code>bien_moi_quy.csv</code></h3>"
    + table(["Tên trong CSV", "Công thức", "Loại", "Đơn vị", "Dùng cho"], new_rows, "dict")
    + code_block("s0", "0.6"))

# ---------- 1 ----------
sec("s1", "1. Nạp dữ liệu và đồng bộ tên biến",
    "<p>Mỗi mã có 4 file tải từ Vietstock (mỗi file chứa 4 quý kết quả kinh doanh). <code>src/clean_bctc_data.py</code> "
    "đọc cả 4, đổi tên chỉ tiêu tiếng Việt sang tên biến tiếng Anh, gộp và khử trùng lặp. Dữ liệu vĩ mô do "
    "<code>src/clean_macro_data.py</code> làm sạch. Hai nhóm dùng chung khóa thời gian dạng <code>2026Q3</code> nên ghép "
    "trực tiếp được.</p>"
    + table(["Nhóm", "Thư mục gốc", "File sạch"], [
        ["Báo cáo tài chính", code("data/raw/vietstock/<MÃ>/"), code("data/processed/bctc/")],
        ["FRED, IMF", code("data/raw/fred/"), code("data/processed/macro/")],
        ["NHNN", code("data/raw/sbv/"), code("data/processed/macro/lai_suat_nhnn_su_kien.csv")],
        ["Biến mới", "–", code("data/processed/features/bien_moi_quy.csv")]])
    + code_block("s1", "1.1", with_common=True))

# ---------- 2 ----------
sec("s2", "2. Kiểm tra chất lượng dữ liệu",
    table(["Phép kiểm tra", "Kết quả", "Ghi chú"], [
        ["Trùng (mã, kỳ)", "0", "Đạt"],
        ["Tổng tài sản = TS ngắn hạn + TS dài hạn", "40/40 quý", "Đạt"],
        ["Tổng nguồn vốn = nợ phải trả + vốn chủ", "40/40 quý", "Đạt"],
        ["Lợi nhuận gộp = doanh thu − giá vốn", "160/160 quý", "Đạt"],
        ["Kết quả kinh doanh", "16 quý mỗi mã", "Quý thiếu ở giữa: " + "; ".join(f"{t} {', '.join(v)}"
                                                                              for t, v in gap_q.items())],
        ["Cân đối kế toán", "4 quý mỗi mã (2025Q4–2026Q3)", "Giới hạn của file tóm tắt"],
        ["Nhận diện doanh nghiệp", "SRC có vốn điều lệ 365 tỷ, tổng tài sản 5.917 tỷ", "Cao su Sao Vàng, loại khỏi phân tích BĐS"],
    ])
    + "<p>Quý bị thiếu là do chính file Vietstock nhảy cóc kỳ (Q1-2024 rồi Q3-2024), không phải do bước làm sạch. "
      "Các phép tính 4 quý và so cùng kỳ chạm vào những quý này sẽ để trống thay vì nối qua khoảng trống.</p>"
    + code_block("s2", "2.1"))

# ---------- 3 ----------
sec("s3", "3. Làm sạch: xử lý thiếu, dấu và ngoại lai",
    table(["Vấn đề", "Cách xử lý", "Lý do"], [
        ["Ô “-” trong file Vietstock", "Để trống, không thay bằng 0", "“-” có thể là không phát sinh hoặc không có số"],
        ["Đầu tư ngắn hạn “-” khi tính nguồn trả nợ", "Tính là 0, gắn cờ " + code("st_invest_filled_0"),
         "Không có khoản đầu tư thì không có tiền từ khoản đó"],
        ["Tổng tài sản SRC 2026Q1 trống", "Lấy tổng nguồn vốn cùng quý", "Đẳng thức kế toán"],
        ["Nhiều đợt tải trùng kỳ", "Giữ ô có giá trị, nếu khác nhau lấy file tải sau cùng", "Hiện không có ô xung đột"],
        ["CPI Mỹ thiếu 10/2025", "Nội suy tuyến tính, gắn cờ " + code("us_cpi_imputed"), "Tránh mất số so cùng kỳ 10/2026"],
        ["UST 10 năm 10/2026 trống", "Bỏ tháng", "Chưa công bố"],
    ])
    + "<p><b>Ngoại lai</b> được dò bằng quy tắc 1,5 × IQR và chỉ đánh dấu, không xóa. Doanh thu bất động sản ghi nhận "
      "theo đợt bàn giao nên một quý có thể cao gấp nhiều lần quý khác (VHM 2025Q4, NLG 2024Q4…). Đó là đặc thù ngành, "
      "không phải lỗi số liệu, nên giữ nguyên và dùng trung vị khi tóm tắt.</p>"
    + code_block("s3", "3.1"))

# ---------- 4 ----------
sec("s4", "4. Tạo biến mới",
    "<p>Mỗi biến mới gắn với một ý của câu hỏi nghiên cứu (xem bảng 0.5). Phép cộng 4 quý và so cùng kỳ dùng lưới quý "
    "liên tục, nên quý bị thiếu làm trống các cửa sổ chứa nó chứ không bị nối qua.</p>"
    + table(["Biến", "Đọc thế nào"], [
        [code("cash_coverage"), "Dưới 1: tiền và đầu tư ngắn hạn không đủ trả hết nợ ngắn hạn nếu không bán được hàng, "
                                "không vay thêm."],
        [code("liquidity_gap"), "Âm: số tỷ đồng còn thiếu theo cách đo trên."],
        [code("inventory_share"), "Cao: tài sản ngắn hạn chủ yếu là hàng tồn kho (dự án), khó chuyển thành tiền nhanh."],
        [code("revenue_yoy_pct"), "Âm: doanh thu quý thấp hơn cùng quý năm trước."],
        [code("fin_cost_ratio_pct"), "Cao: chi phí tài chính chiếm phần lớn doanh thu, nhạy với lãi suất."],
    ])
    + code_block("s4", "4.1"))

# ---------- 5 ----------
sec("s5", "5. Thống kê mô tả",
    f"<p>Tại {LATEST}, {len(short)}/{len(now)} doanh nghiệp BĐS có tiền và đầu tư ngắn hạn ít hơn nợ ngắn hạn "
    f"({', '.join(short.index)}); chỉ {', '.join(now.index[now['cash_coverage'] >= 1]) or 'không DN nào'} đủ. "
    f"Doanh thu quý so cùng kỳ: trung vị {vn(y23.median(), 1)}% trong năm 2023 và {vn(ylast.median(), 1)}% trong "
    "bốn quý gần nhất, tức bán hàng hiện tại cũng đang chững lại.</p>"
    "<p>Thiếu hụt tuyệt đối phụ thuộc quy mô (VHM lớn hơn các DN khác nhiều lần), nên khi so sánh nên dùng "
    "<code>cash_coverage</code> hoặc trung vị thay vì trung bình.</p>"
    + code_block("s5", "5.1"))

# ---------- 6 ----------
sec("s6", "6. Trực quan hóa (1): chất lượng và độ phủ dữ liệu",
    "<ul><li><b>Hình 6.1</b> — mã nào có số liệu ở quý nào. Cân đối kế toán chỉ có 4 quý cuối; DXG, KDH, NLG, NVL, SRC thiếu 2024Q2 và NVL thiếu thêm 2025Q2.</li>"
    "<li><b>Hình 6.2</b> — số ô trống theo biến. Nhiều nhất là lợi nhuận từ công ty liên kết và bất động sản đầu tư "
    "(khoản không phải DN nào cũng có) và EPS cơ bản (Vietstock không ghi cho nhiều quý).</li>"
    "<li><b>Hình 6.3</b> — lãi suất Fed, lợi suất UST 10 năm và lãi suất tái cấp vốn NHNN theo quý; nền cam là "
    "giai đoạn 2022Q3–2023Q4. Chuỗi NHNN chỉ bắt đầu từ 10/2022 vì nguồn chỉ trích các quyết định từ đó.</li></ul>"
    + code_block("s6", "6.1"))

# ---------- 7 ----------
sec("s7", "7. Trực quan hóa (2): phân phối và ngoại lai",
    "<ul><li><b>Hình 7.1</b> — tiền và đầu tư ngắn hạn so với nợ ngắn hạn, quý mới nhất; cột cam là DN không đủ.</li>"
    "<li><b>Hình 7.2</b> — doanh thu quý so cùng kỳ của từng DN. Biên độ rất rộng do doanh thu ghi nhận theo đợt bàn "
    "giao; vài quý tăng hàng nghìn phần trăm vì quý năm trước gần như bằng 0.</li>"
    "<li><b>Hình 7.3</b> — phân phối doanh thu so cùng kỳ năm 2023 so với các quý sau.</li>"
    "<li><b>Hình 7.4</b> — đòn bẩy và khả năng trả nợ ngắn hạn; bóng càng lớn thì thiếu hụt càng lớn.</li></ul>"
    + code_block("s7", "7.1"))

# ═════════════════════ ghép HTML ═════════════════════
CSS = """
:root{--bg:#fff;--ink:#1f2328;--ink2:#59636e;--muted:#6e7781;--line:#d8dee4;--th:#f6f8fa;--code:#eff1f3;--link:#0969da;
--out-bg:#fffbe6;--out-head:#fff1bf;--out-line:#f0dfa0;--out-ink:#3d3300;--out-label:#7a5d00}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 "Segoe UI",-apple-system,"Helvetica Neue",Arial,sans-serif}
.top{max-width:1320px;padding:32px 24px 8px}.top h1{margin:0 0 6px}.top .sub{margin:0}
.wrap{display:flex;align-items:flex-start;gap:40px;padding:8px 24px 80px;max-width:1320px}
nav{position:sticky;top:24px;flex:0 0 250px;font-size:14.5px}
nav .t{font-weight:600;margin:0 0 8px}
nav ol{list-style:none;margin:0;padding:0;border-left:1px solid var(--line)}
nav a{display:block;padding:5px 0 5px 14px;color:var(--ink2);text-decoration:none;margin-left:-1px;border-left:2px solid transparent}
nav a:hover{color:var(--ink)}nav a.on{color:var(--ink);border-left-color:var(--ink);font-weight:600}
main{flex:1 1 auto;min-width:0;max-width:1000px}
main>section:first-child h2{margin-top:24px}
h1{font-size:30px;line-height:1.25;margin:0 0 6px}.sub{color:var(--muted);margin:0 0 28px;font-size:15px}
h2{font-size:26px;margin:52px 0 20px;padding-bottom:10px;border-bottom:1px solid var(--line)}
h3{font-size:18px;margin:30px 0 12px}p,ul{margin:0 0 14px}ul{padding-left:22px}li{margin:4px 0}a{color:var(--link)}
blockquote{margin:0 0 14px;padding:4px 0 4px 16px;border-left:3px solid var(--line);color:var(--ink2);font-style:italic}
code{font-family:Consolas,"SFMono-Regular",Menlo,monospace;font-size:.86em;background:var(--code);padding:2px 6px;border-radius:5px}
pre{margin:0;padding:12px 16px;overflow:auto;font:13.5px/1.55 Consolas,"Cascadia Code",Menlo,monospace;white-space:pre}
.tw{overflow-x:auto;margin:0 0 18px}
table{border-collapse:collapse;width:100%;font-size:15px}
th,td{border:1px solid var(--line);padding:10px 13px;text-align:left;vertical-align:middle}
th{background:var(--th);font-weight:600}
td:first-child code{white-space:nowrap}
.codebox{border:1px solid var(--line);border-radius:6px;margin:0 0 26px;overflow:hidden}
.tabs{display:flex;border-bottom:1px solid var(--line);background:var(--th)}
.tab,.copy{font:inherit;font-size:14px;border:0;background:none;color:var(--ink2);cursor:pointer;padding:8px 18px}
.tab{border-bottom:2px solid transparent;margin-bottom:-1px}.tab:hover,.copy:hover{color:var(--ink)}
.tab.on{color:var(--ink);font-weight:600;border-bottom-color:var(--ink);background:var(--bg)}
.copy{margin-left:auto;font-size:13px}
/* khung code: màu VS Code Light Modern, nền trắng */
.fname{font:12.5px Consolas,Menlo,monospace;color:#616161;background:#f8f8f8;padding:7px 16px;border-top:1px solid var(--line)}
.pane .fname:first-child{border-top:0}
.pane pre.src{background:#ffffff;color:#3b3b3b}
/* khung kết quả: nền vàng nhạt */
.outhead{font-size:13px;font-weight:600;color:var(--out-label);padding:7px 16px;background:var(--out-head);
border-top:1px solid var(--out-line);border-bottom:1px solid var(--out-line)}
.pane pre.out{background:var(--out-bg);color:var(--out-ink)}
.imgs{padding:12px 16px;display:grid;gap:12px;background:var(--out-bg);border-top:1px solid var(--out-line)}
.imgs img{max-width:100%;height:auto;border:1px solid var(--out-line);background:#fff}
@media (max-width:900px){.top{padding:20px 16px 0}.wrap{display:block;padding:12px 16px 60px}nav{position:static;margin-bottom:24px}
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
<title>Trực quan hóa dữ liệu – Nhóm 2</title><style>{CSS}</style></head>
<body>
<header class="top">
<h1>Trực quan hóa dữ liệu: rủi ro thanh khoản của doanh nghiệp BĐS dân cư niêm yết</h1>
<p class="sub">VietLeap Hackathon 2026 · Nhóm 2 · dữ liệu đến {LATEST} · cập nhật {pd.Timestamp.now():%d/%m/%Y}</p>
</header>
<div class="wrap">
<nav aria-label="Mục lục"><p class="t">Mục lục</p><ol>{toc}</ol></nav>
<main>
{"".join(s for _, _, s in sections)}
</main></div>
<script>{JS}</script>
</body></html>"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(doc)
print(f"Đã ghi {OUT} ({len(doc) / 1024:.0f} KB)")
