# 05 - Thống kê mô tả
source("analysis/r/common.R")

f <- read("features/bien_moi_quy.csv") %>% filter(ticker %in% RE)
cols <- c("liquidity_gap", "cash_coverage", "inventory_share", "liab_to_equity", "fin_cost_ratio_pct")

skew <- function(x) {                     # độ lệch tính giống pandas
  x <- na.omit(x); n <- length(x); m <- mean(x)
  mean((x - m)^3) / mean((x - m)^2)^1.5 * sqrt(n * (n - 1)) / (n - 2)
}
now <- filter(f, period == LATEST_Q)
t <- t(sapply(now[cols], function(x) c(count = sum(!is.na(x)), mean = mean(x, na.rm = TRUE),
                                       std = sd(x, na.rm = TRUE),
                                       quantile(x, c(0, .25, .5, .75, 1), na.rm = TRUE), skew = skew(x))))
cat("quý", LATEST_Q, "-", nrow(now), "doanh nghiệp BĐS\n")
print(round(t, 2))

# cú sốc doanh thu: so cùng kỳ trong năm 2023 với các giai đoạn sau
g <- f %>%
  mutate(giai_doan = case_when(period <= "2023Q4" ~ "1. 2023 (khủng hoảng)",
                               period <= "2025Q3" ~ "2. 2024-2025Q3",
                               TRUE ~ "3. 2025Q4-2026Q3")) %>%
  group_by(giai_doan) %>%
  summarise(n = sum(!is.na(revenue_yoy_pct)), trung_vi = median(revenue_yoy_pct, na.rm = TRUE),
            ty_le_giam = mean(revenue_yoy_pct < 0, na.rm = TRUE))
cat("\ndoanh thu quý so cùng kỳ (%):\n")
print(as.data.frame(mutate(g, across(where(is.numeric), ~ round(.x, 2)))), row.names = FALSE)

# xếp hạng theo khoảng thiếu hụt thanh khoản tại quý mới nhất
cat("\nxếp hạng thiếu hụt tại", LATEST_Q, "(tỷ đồng):\n")
print(now %>% arrange(liquidity_gap) %>% select(ticker, liquidity_gap, cash_coverage, liab_to_equity) %>%
        mutate(across(where(is.numeric), ~ round(.x, 2))) %>% as.data.frame(), row.names = FALSE)
