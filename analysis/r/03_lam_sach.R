# 03 - Làm sạch: ô trống, dấu, ngoại lai
source("analysis/r/common.R")

w <- to_wide(load_raw())

# DIG 2021Q3 thiếu lãi vay đã trả -> tạm lấy chi phí lãi vay cùng quý trên B02
thieu <- is.na(w$interest_paid)
print(as.data.frame(w[thieu, c("ticker", "period", "interest_paid", "interest_expense")]))
w$interest_paid[thieu] <- w$interest_expense[thieu]

# tiền chi ra đang mang dấu âm -> đổi dấu cho dễ đọc.
# không dùng abs(): quý mang dấu ngược là số điều chỉnh, cộng 4 quý thì phải trừ đi.
# so thử lãi vay đã trả cả năm 2023 theo 2 cách (tỷ đồng):
cmp <- w %>%
  filter(year == 2023) %>%
  group_by(ticker) %>%
  summarise(doi_dau = -sum(interest_paid) / 1e9,
            abs = sum(abs(interest_paid)) / 1e9) %>%
  filter(abs - doi_dau > 0.01)
cat("\n")
print(as.data.frame(mutate(cmp, across(where(is.numeric), ~ round(.x, 2)))))

# ngoại lai theo quy tắc 1,5 IQR - chỉ đánh dấu, không xóa
ngoai_lai <- function(x, ten) {
  ok <- !is.na(x)
  x <- x[ok]; ten <- ten[ok]
  q <- quantile(x, c(0.25, 0.75), names = FALSE)
  iqr <- q[2] - q[1]
  o <- x < q[1] - 1.5 * iqr | x > q[2] + 1.5 * iqr
  if (any(o)) paste(ten[o], sprintf("%.2f", x[o]), collapse = ", ") else "không có"
}

p <- read_csv(file.path(PROC, "panel_quarterly.csv"), show_col_types = FALSE)
now <- filter(p, period == LATEST_Q)
cat("\nngoại lai tại", LATEST_Q, "\n")
for (col in c("liquidity_coverage", "implied_rate_pct", "rollover_ratio", "debt_to_equity")) {
  cat("  ", col, ": ", ngoai_lai(now[[col]], now$ticker), "\n", sep = "")
}

shock <- read_csv(file.path(PROC, "stress_calibration.csv"), show_col_types = FALSE) %>%
  filter(ticker != "MEDIAN")
cat("\nngoại lai trong cú sốc 2022-2023\n")
for (col in c("sales_shock_pct", "adv_shock_pct", "rate_shock_pp", "rollover_stress")) {
  cat("  ", col, ": ", ngoai_lai(shock[[col]], shock$ticker), "\n", sep = "")
}
