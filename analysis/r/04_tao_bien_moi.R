# 04 - Tạo biến mới (chỉ những biến cần cho câu hỏi nghiên cứu)
source("analysis/r/common.R")

sum4 <- function(x) {                       # tổng 4 quý liên tiếp, NA nếu thiếu quý nào
  out <- rep(NA_real_, length(x))
  for (i in seq_along(x)[-(1:3)]) out[i] <- sum(x[(i - 3):i])
  out
}

p <- read("bctc/panel_quarterly_bctc.csv") %>% mutate(qi = q_index(period))
f <- p %>%
  group_by(ticker) %>%
  # lưới quý liên tục, để cộng 4 quý / so cùng kỳ không nhảy qua quý bị thiếu
  complete(qi = full_seq(qi, 1)) %>%
  arrange(qi, .by_group = TRUE) %>%
  mutate(period = q_label(qi),
         # nguồn trả nợ sẵn có; đầu tư ngắn hạn ghi "-" coi là 0 trong phép cộng
         liquid_assets = cash_and_equivalents + coalesce(short_term_investments, 0),
         liquidity_gap = liquid_assets - short_term_liabilities,
         cash_coverage = liquid_assets / short_term_liabilities,
         inventory_share = inventory / current_assets,
         liab_to_equity = total_liabilities / owner_equity,
         # cú sốc bán hàng và gánh nặng chi phí tài chính
         revenue_ttm = sum4(net_revenue),
         lag = lag(net_revenue, 4),
         revenue_yoy_pct = (net_revenue - lag) / ifelse(lag > 0, lag, NA) * 100,
         fin_cost_ratio_pct = sum4(financial_expense) / revenue_ttm * 100) %>%
  ungroup() %>%
  filter(!is.na(net_revenue) | !is.na(total_assets))

now <- f %>% filter(period == LATEST_Q, ticker %in% RE)
print(now %>% arrange(liquidity_gap) %>% select(ticker, liquid_assets, liquidity_gap, revenue_ttm) %>%
        mutate(across(where(is.numeric), ~ round(.x, 2))) %>% as.data.frame(), row.names = FALSE)
cat("\n")
print(now %>% arrange(cash_coverage) %>%
        select(ticker, cash_coverage, inventory_share, liab_to_equity, revenue_yoy_pct, fin_cost_ratio_pct) %>%
        mutate(across(where(is.numeric), ~ round(.x, 2))) %>% as.data.frame(), row.names = FALSE)

# đối chiếu với file do src/build_features.py tạo ra
saved <- read("features/bien_moi_quy.csv")
cols <- c("liquid_assets", "liquidity_gap", "cash_coverage", "inventory_share", "liab_to_equity",
          "revenue_ttm", "revenue_yoy_pct", "fin_cost_ratio_pct")
m <- inner_join(saved, f, by = c("ticker", "period"), suffix = c("_s", ""))
d <- abs(as.matrix(m[cols]) - as.matrix(m[paste0(cols, "_s")]))
cat("\nkhớp với bien_moi_quy.csv:", nrow(m) == nrow(saved) && all(d < 1e-3, na.rm = TRUE), "\n")
cat("số quan sát có revenue_ttm:", sum(!is.na(f$revenue_ttm)),
    "| có revenue_yoy_pct:", sum(!is.na(f$revenue_yoy_pct)), "\n")
