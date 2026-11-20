# -*- coding: utf-8 -*-
"""
clean_macro_data.py — làm sạch dữ liệu vĩ mô (FRED, IMF, NHNN).

Đọc:  data/raw/fred/*.csv, data/raw/sbv/*.csv
Ghi:  data/processed/macro/
        macro_thang.csv              CPI Mỹ, lãi suất Fed, lợi suất UST 10 năm theo tháng
        macro_quy.csv                tổng hợp theo quý (+ lãi suất tái cấp vốn NHNN cuối quý)
        cpi_viet_nam_nam.csv         lạm phát VN theo năm (IMF), có cột phân biệt thực tế / ước tính / dự báo
        lai_suat_nhnn_su_kien.csv    các quyết định lãi suất điều hành NHNN đã tách số
        bao_cao_chat_luong_vi_mo.txt

Chạy:  python src/clean_macro_data.py
"""
import os
import re
import unicodedata

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRED = os.path.join(ROOT, "data", "raw", "fred")
SBV = os.path.join(ROOT, "data", "raw", "sbv")
OUT = os.path.join(ROOT, "data", "processed", "macro")
LAST_ACTUAL_YEAR = 2025          # IMF: năm 2026 là ước tính, sau 2026 là dự báo

log = []


def note(msg):
    print(msg)
    log.append(msg)


# ───────────────────────────── FRED ─────────────────────────────
def read_fred(fname, col):
    """Chuỗi tháng trên lưới liên tục; ô '.' hoặc trống -> NaN."""
    d = pd.read_csv(os.path.join(FRED, fname))
    d["observation_date"] = pd.to_datetime(d["observation_date"])
    s = pd.to_numeric(d[col], errors="coerce")
    s.index = d["observation_date"].dt.to_period("M")
    s = s[~s.index.duplicated(keep="last")]
    s = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"))
    note(f"  {fname}: {len(d)} dòng, {s.index.min()} – {s.index.max()}, ô trống: "
         f"{', '.join(str(i) for i in s.index[s.isna()]) or 'không'}")
    return s


def clean_fred():
    note("FRED")
    cpi = read_fred("fred_CPIAUCSL_2019-2026.csv", "CPIAUCSL")
    fed = read_fred("fred_DFEDTARU_thang_cuoiky_2019-2026.csv", "DFEDTARU")
    ust = read_fred("fred_DGS10_thang_trungbinh_2019-2026.csv", "DGS10")

    # CPI: tháng trống nằm giữa chuỗi -> nội suy tuyến tính (gắn cờ); không ngoại suy phần đuôi
    imputed = cpi.isna()
    cpi = cpi.interpolate(limit_area="inside")
    imputed &= cpi.notna()
    note(f"  CPI Mỹ: nội suy {int(imputed.sum())} tháng ({', '.join(str(i) for i in imputed.index[imputed])})")
    yoy = cpi.pct_change(12, fill_method=None) * 100      # 12 tháng đầu trống vì file bắt đầu 2019-01

    # lợi suất 10 năm: bỏ các tháng trống ở cuối (chưa công bố)
    tail = ust.index[ust.isna() & (ust.index > ust.last_valid_index())]
    ust = ust.loc[:ust.last_valid_index()]
    note(f"  UST 10 năm: bỏ {len(tail)} tháng chưa công bố ở cuối ({', '.join(map(str, tail))})")

    m = pd.DataFrame({"us_cpi_index": cpi, "us_cpi_imputed": imputed, "us_cpi_yoy_pct": yoy.round(4),
                      "fed_upper_pct": fed, "ust10y_pct": ust})
    m.index.name = "month"
    return m


# ───────────────────────────── IMF ─────────────────────────────
def clean_imf():
    d = pd.read_csv(os.path.join(FRED, "fred_VNMPCPIPCPPPT_IMF_nam.csv"))
    d["year"] = pd.to_datetime(d["observation_date"]).dt.year
    d = d.rename(columns={"VNMPCPIPCPPPT": "vn_cpi_yoy_pct"})[["year", "vn_cpi_yoy_pct"]]
    d["data_type"] = np.select([d["year"] <= LAST_ACTUAL_YEAR, d["year"] == LAST_ACTUAL_YEAR + 1],
                               ["thuc_te", "uoc_tinh"], default="du_bao")
    note(f"IMF: {len(d)} năm; thực tế {d['year'].min()}–{LAST_ACTUAL_YEAR}, ước tính {LAST_ACTUAL_YEAR + 1}, "
         f"dự báo {LAST_ACTUAL_YEAR + 2}–{d['year'].max()} (giữ trong file, phân biệt bằng cột data_type)")
    return d


# ───────────────────────────── NHNN ─────────────────────────────
RATE_CODES = [("tái cấp vốn", "refinancing", "dieu_hanh"), ("tái chiết khấu", "rediscount", "dieu_hanh"),
              ("qua đêm", "overnight", "dieu_hanh"),
              (r"tiền gửi.*(không kỳ hạn|dưới 1 tháng)", "deposit_cap_under_1m", "tran_tien_gui"),
              (r"tiền gửi.*1 tháng đến dưới 6 tháng", "deposit_cap_1m_6m", "tran_tien_gui"),
              (r"cho vay.*ưu tiên", "priority_lending_cap", "tran_cho_vay")]
# Thông tin bổ sung cho các ô trống, theo nhóm quyết định
EFFECTIVE_BY_DECISION = {"313/QĐ-NHNN": "2023-03-15", "314/QĐ-NHNN": "2023-03-15"}       # ký 14/03, hiệu lực hôm sau
DECISIONS_BY_EFFECTIVE = {"2023-04-03": ("2023-03-31", {"dieu_hanh": "574/QĐ-NHNN", "tran_tien_gui": "575/QĐ-NHNN",
                                                         "tran_cho_vay": "576/QĐ-NHNN"})}


def text(x):
    return "" if pd.isna(x) else re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(x))).strip()


def rates_from_sentence(s):
    """'từ 5,0%/năm lên 6,0%/năm' -> (5.0, 6.0); 'giữ nguyên ở mức 6%' -> (6, 6); 'xuống còn 5,5%' -> (NaN, 5.5)"""
    t = text(s).lower()
    nums = [float(x.replace(",", ".")) for x in re.findall(r"(\d+(?:[.,]\d+)?)\s*%", t)]
    if "giữ nguyên" in t and nums:
        return nums[0], nums[0]
    if len(nums) >= 2 and re.search(r"\btừ\b", t):
        return nums[0], nums[1]
    return (np.nan, nums[0]) if len(nums) == 1 else (np.nan, np.nan)


def clean_sbv():
    d = pd.read_csv(os.path.join(SBV, "sbv_lai_suat_dieu_hanh_trich_nguon.csv"), dtype=str)
    blank = int(d[["ngay_hieu_luc", "so_quyet_dinh", "ngay_quyet_dinh"]].isna().sum().sum())
    hit = d["loai_lai_suat"].map(lambda s: next(((c, f) for p, c, f in RATE_CODES if re.search(p, text(s).lower())),
                                                (None, None)))
    d["rate_code"], d["group"] = hit.str[0], hit.str[1]
    r = d["trich_nguyen_van"].map(rates_from_sentence)
    d["rate_before"], d["rate_after"] = r.str[0].astype(float), r.str[1].astype(float)
    d["effective_date"] = pd.to_datetime(d["ngay_hieu_luc"], format="%d/%m/%Y", errors="coerce")
    d["decision_date"] = pd.to_datetime(d["ngay_quyet_dinh"], format="%d/%m/%Y", errors="coerce")
    d["decision_no"] = d["so_quyet_dinh"].map(text).replace("", np.nan)
    # cùng bài nguồn + cùng nhóm lãi suất -> cùng số quyết định; cùng bài nguồn -> cùng ngày ký
    d["decision_no"] = d.groupby(["nguon_url", "group"])["decision_no"].transform(lambda s: s.ffill().bfill())
    d["decision_date"] = d.groupby("nguon_url")["decision_date"].transform(lambda s: s.ffill().bfill())
    for dec, eff in EFFECTIVE_BY_DECISION.items():
        d.loc[d["decision_no"].eq(dec) & d["effective_date"].isna(), "effective_date"] = pd.Timestamp(eff)
    for eff, (ddate, decs) in DECISIONS_BY_EFFECTIVE.items():
        m = d["effective_date"].eq(pd.Timestamp(eff))
        d.loc[m & d["decision_date"].isna(), "decision_date"] = pd.Timestamp(ddate)
        for g, dec in decs.items():
            d.loc[m & d["decision_no"].isna() & d["group"].eq(g), "decision_no"] = dec
    # "giảm xuống còn X%": mức trước = mức hiện hành của đợt trước cùng loại
    d = d.sort_values(["rate_code", "effective_date"])
    prev = d.groupby("rate_code")["rate_after"].shift()
    d["rate_before"] = d["rate_before"].fillna(prev)
    gaps = d[prev.notna() & (d["rate_before"] != prev)]
    note(f"NHNN: {len(d)} quyết định; ô trống ngày/số QĐ {blank} -> "
         f"{int(d[['effective_date', 'decision_date', 'decision_no']].isna().sum().sum())}")
    note("  Chuỗi đứt gãy (mức trước ≠ mức sau đợt trước, nguồn thiếu đợt điều chỉnh): "
         + "; ".join(f"{r.rate_code} {r.effective_date:%Y-%m-%d}" for r in gaps.itertuples()))
    out = d.sort_values(["effective_date", "rate_code"])[
        ["effective_date", "decision_date", "decision_no", "rate_code", "rate_before", "rate_after", "nguon_url"]]
    return out


def refinancing_eoq(ev, quarters):
    """Lãi suất tái cấp vốn cuối quý (giữ mức của quyết định gần nhất); trước quyết định đầu tiên để trống."""
    r = ev[ev["rate_code"] == "refinancing"].set_index("effective_date")["rate_after"].sort_index()
    out = []
    for q in quarters:
        end = q.end_time
        past = r[r.index <= end]
        out.append(past.iloc[-1] if len(past) else np.nan)
    return pd.Series(out, index=quarters)


# ───────────────────────────── main ─────────────────────────────
def main():
    os.makedirs(OUT, exist_ok=True)
    m = clean_fred()
    vn = clean_imf()
    ev = clean_sbv()

    g = m.groupby(m.index.asfreq("Q"))
    q = pd.DataFrame({"us_cpi_yoy_avg_pct": g["us_cpi_yoy_pct"].mean().round(4),
                      "fed_upper_eoq_pct": g["fed_upper_pct"].last(),
                      "ust10y_avg_pct": g["ust10y_pct"].mean().round(4),
                      "n_months": g["us_cpi_index"].count()})
    q["sbv_refinancing_eoq_pct"] = refinancing_eoq(ev, q.index)
    incomplete = q.index[q["n_months"] < 3]
    q = q.drop(index=incomplete).drop(columns="n_months")
    note(f"Quý: {q.index.min()} – {q.index.max()}; bỏ quý chưa đủ 3 tháng: {', '.join(map(str, incomplete)) or 'không'}")

    m.index = m.index.astype(str)
    q.index = q.index.astype(str)
    q.index.name = "quarter"
    m.to_csv(os.path.join(OUT, "macro_thang.csv"), encoding="utf-8-sig")
    q.to_csv(os.path.join(OUT, "macro_quy.csv"), encoding="utf-8-sig")
    vn.to_csv(os.path.join(OUT, "cpi_viet_nam_nam.csv"), index=False, encoding="utf-8-sig")
    ev.assign(effective_date=ev["effective_date"].dt.strftime("%Y-%m-%d"),
              decision_date=ev["decision_date"].dt.strftime("%Y-%m-%d")).to_csv(
        os.path.join(OUT, "lai_suat_nhnn_su_kien.csv"), index=False, encoding="utf-8-sig")
    head = ["=" * 80, " BÁO CÁO CHẤT LƯỢNG DỮ LIỆU VĨ MÔ", f" Thời điểm: {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}",
            "=" * 80, "Đơn vị: lãi suất và lạm phát tính bằng %; CPI Mỹ là chỉ số (1982–84 = 100).",
            "Lãi suất Fed/NHNN là lãi suất chính sách, không phải lãi suất vay của doanh nghiệp.", ""]
    with open(os.path.join(OUT, "bao_cao_chat_luong_vi_mo.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(head + log) + "\n")
    print(f"Đã ghi 5 file vào {OUT}")


if __name__ == "__main__":
    main()
