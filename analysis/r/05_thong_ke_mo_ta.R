# 05 - Thống kê mô tả
source("analysis/r/common.R")

p <- read_csv(file.path(PROC, "panel_quarterly.csv"), show_col_types = FALSE)
shock <- read_csv(file.path(PROC, "stress_calibration.csv"), show_col_types = FALSE)
cols <- c("liquidity_gap_12m", "liquidity_coverage", "rollover_ratio",
          "implied_rate_pct", "debt_to_equity")

# độ lệch tính giống pandas để hai bản cho cùng kết quả
skew <- function(x) {
  x <- na.omit(x); n <- length(x); m <- mean(x)
  mean((x - m)^3) / mean((x - m)^2)^1.5 * sqrt(n * (n - 1)) / (n - 2)
}
mo_ta <- function(df) {
  t(sapply(df[cols], function(x) c(
    count = sum(!is.na(x)), mean = mean(x, na.rm = TRUE), std = sd(x, na.rm = TRUE),
    quantile(x, c(0, .25, .5, .75, 1), na.rm = TRUE), skew = skew(x)))) %>% round(2)
}

now <- filter(p, period == LATEST_Q)
cat("quý", LATEST_Q, "-", nrow(now), "doanh nghiệp\n")
print(mo_ta(now))

ttm <- filter(p, !is.na(cfo_ttm))
cat("\ntất cả các quý có số 12 tháng -", nrow(ttm), "quan sát\n")
print(mo_ta(ttm))

# ai không đủ tiền trả nợ vay ngắn hạn nếu không vay thêm được
thieu <- now %>% filter(liquidity_gap_12m < 0) %>% arrange(liquidity_gap_12m)
cat("\nthiếu tiền tại", LATEST_Q, "\n")
print(thieu %>% select(ticker, liquidity_gap_12m, liquidity_coverage, rollover_ratio) %>%
        mutate(across(where(is.numeric), ~ round(.x, 2))) %>% as.data.frame(), row.names = FALSE)

# chỉ số này có nhận ra những DN đã chậm trả trái phiếu năm 2022-2023 không?
v <- filter(shock, ticker != "MEDIAN")
cat("\nthiếu hụt tại", BASE_Q, "so với danh sách chậm trả HNX:\n")
print(addmargins(table(`gap < 0` = v$liquidity_gap_base < 0,
                       `có tên HNX` = v$bond_default_flag)))
