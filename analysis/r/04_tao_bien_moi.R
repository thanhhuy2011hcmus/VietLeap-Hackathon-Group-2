# 04 - Tạo biến mới (chỉ những biến cần cho câu hỏi nghiên cứu)
source("analysis/r/common.R")

# làm lại các bước của mục 03
w <- to_wide(load_raw())
thieu <- is.na(w$interest_paid)
w$interest_paid[thieu] <- w$interest_expense[thieu]
money <- c("cash", "st_invest", "st_debt", "lt_debt", "adv_st", "adv_lt", "equity", FLOWS)
w <- w %>%
  mutate(interest_paid = -interest_paid,
         loan_repayments = -loan_repayments,
         across(all_of(money), ~ .x / 1e9))     # đổi sang tỷ đồng

# dựng đủ các quý 2021Q1-2026Q3 cho từng mã, kể cả quý không có số liệu,
# để khi cộng 4 quý không bị nhảy qua khoảng trống 2024-2025
pos <- function(x) ifelse(x > 0, x, NA)
d <- expand_grid(ticker = unique(w$ticker), period = QUARTERS) %>%
  left_join(w, by = c("ticker", "period")) %>%
  group_by(ticker) %>%
  mutate(liquid_assets = cash + st_invest,
         total_debt = st_debt + lt_debt,
         adv_customers = adv_st + adv_lt,
         across(all_of(FLOWS), sum4, .names = "{.col}_ttm"),   # cộng 4 quý gần nhất
         avg_debt = sum4(total_debt) / 4) %>%
  ungroup() %>%
  mutate(implied_rate_pct = interest_paid_ttm / pos(avg_debt) * 100,
         rollover_ratio = loan_proceeds_ttm / pos(loan_repayments_ttm),
         liquidity_gap_12m = liquid_assets + cfo_ttm - st_debt,
         liquidity_coverage = (liquid_assets + cfo_ttm) / st_debt,
         debt_to_equity = total_debt / equity)

cols <- c("liquid_assets", "st_debt", "cfo_ttm", "liquidity_gap_12m",
          "liquidity_coverage", "rollover_ratio", "implied_rate_pct", "debt_to_equity")
now <- d %>% filter(period == LATEST_Q) %>% arrange(liquidity_gap_12m)
now <- data.frame(round(now[cols], 2), row.names = now$ticker)
print(now[cols[1:4]])    # tỷ đồng
cat("\n")
print(now[cols[5:8]])    # lần, %

# đối chiếu với file sạch do src/clean_raw_data.py tạo ra
saved <- read_csv(file.path(PROC, "panel_quarterly.csv"), show_col_types = FALSE)
mine <- semi_join(d, saved, by = c("ticker", "period")) %>% arrange(ticker, period)
saved <- arrange(saved, ticker, period)
diff <- abs(as.matrix(mine[cols]) - as.matrix(saved[cols]))
cat("\nkhớp với panel_quarterly.csv:", all(diff < 1e-3, na.rm = TRUE), "\n")

# cú sốc 2022-2023: 4 quý khủng hoảng so với 4 quý trước đó
b <- filter(d, period == BASE_Q)
s <- filter(d, period == STRESS_Q)
shock <- data.frame(
  sales_shock_pct = (s$net_sales_ttm / b$net_sales_ttm - 1) * 100,
  adv_shock_pct = (s$adv_customers / b$adv_customers - 1) * 100,
  rate_shock_pp = s$implied_rate_pct - b$implied_rate_pct,
  rollover_stress = s$rollover_ratio,
  row.names = b$ticker)
cat("\n")
print(round(shock, 2))
cat("\ntrung vị ngành:\n")
print(round(sapply(shock, median, na.rm = TRUE), 2))
