# 02 - Kiểm tra chất lượng dữ liệu
source("analysis/r/common.R")

raw <- load_raw()
key <- c("ticker", "year", "quarter", "field_path")
cat("dòng trùng:", sum(duplicated(raw[key])), "\n")
cat("ô trống:", sum(is.na(raw$value)), "\n")
print(as.data.frame(filter(raw, is.na(value))[c("ticker", "year", "quarter")]))

w <- to_wide(raw)
cat("\nquý không có số liệu:", setdiff(QUARTERS, w$period), "\n")

# tổng tài sản phải bằng nợ phải trả + vốn chủ
ok <- close(w$total_assets, w$liabilities + w$equity)
cat("\ncân đối kế toán khớp:", sum(ok), "/", nrow(w), "\n")

# tiền cuối kỳ trên B03 phải bằng tiền trên B01
cat("tiền B03 khác B01 (tỷ đồng):\n")
print(w %>% filter(!close(cf_cash_end, cash)) %>%
        transmute(ticker, period, B01 = cash / 1e9, B03 = cf_cash_end / 1e9) %>% as.data.frame())

# số theo quý là riêng từng quý hay lũy kế từ đầu năm?
# riêng quý  -> tiền đầu kỳ quý này = tiền cuối kỳ quý trước
# lũy kế     -> tiền đầu kỳ quý nào cũng = tiền đầu năm
s <- w %>%
  group_by(ticker, year) %>%
  mutate(lien_ke = lag(quarter) == quarter - 1,
         rieng_quy = close(cf_cash_begin, lag(cf_cash_end)),
         luy_ke = close(cf_cash_begin, first(cf_cash_begin)) & !rieng_quy) %>%
  ungroup() %>%
  filter(lien_ke)
cat("\ncặp quý liền kề:", nrow(s), "\n")
cat("  khớp kiểu riêng quý:", sum(s$rieng_quy), "\n")
cat("  khớp kiểu lũy kế:", sum(s$luy_ke), "\n")

# dấu bất thường (theo quy ước FiinQuant, tiền chi ra mang dấu âm)
cat("\nlãi vay đã trả > 0:", sum(w$interest_paid > 0, na.rm = TRUE), "quý\n")
cat("trả nợ gốc > 0:", sum(w$loan_repayments > 0), "quý\n")
cat("vay mới < 0:", sum(w$loan_proceeds < 0), "quý\n")
cat("doanh thu < 0:", sum(w$net_sales < 0), "quý\n")

# file VHM cũ có trùng với file mới không?
old <- read_csv(file.path(RAW, "bctc_full_VHM_2026Q3.csv"), show_col_types = FALSE)
m <- inner_join(old, raw, by = key, suffix = c("_cu", "_moi"))
cat("\nfile VHM cũ: trùng", nrow(m), "chỉ tiêu, lệch",
    sum(abs(m$value_cu - m$value_moi) > 1e-5 * abs(m$value_moi)), "\n")

# chuỗi lãi suất NHNN: mức trước đợt sau phải bằng mức sau đợt trước
gap <- read_csv(file.path(PROC, "sbv_policy_events.csv"), show_col_types = FALSE) %>%
  arrange(rate_code, effective_date) %>%
  group_by(rate_code) %>%
  mutate(sau_dot_truoc = lag(rate_after)) %>%
  ungroup() %>%
  filter(!is.na(sau_dot_truoc), rate_before != sau_dot_truoc)
cat("\nchỗ đứt gãy trong chuỗi NHNN:\n")
print(as.data.frame(gap[c("rate_code", "effective_date", "sau_dot_truoc", "rate_before")]))
