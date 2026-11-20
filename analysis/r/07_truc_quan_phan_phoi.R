# 07 - Vẽ hình về phân phối và ngoại lai
source("analysis/r/common.R")

p <- read_csv(file.path(PROC, "panel_quarterly.csv"), show_col_types = FALSE)
shock <- read_csv(file.path(PROC, "stress_calibration.csv"), show_col_types = FALSE) %>%
  filter(ticker != "MEDIAN")

# hình 7.1 - hệ số bao phủ nợ vay ngắn hạn tại quý mới nhất
# (tiền + đầu tư ngắn hạn + CFO 12 tháng) / nợ vay ngắn hạn; dưới 1 là không đủ
now <- p %>%
  filter(period == LATEST_Q) %>%
  arrange(liquidity_coverage) %>%
  mutate(ticker = factor(ticker, ticker),
         cov = pmin(liquidity_coverage, 6),      # DIG 14x, cắt bớt cho dễ nhìn
         label = sprintf("%.2fx  (%s tỷ)", liquidity_coverage,
                         format(round(liquidity_gap_12m), big.mark = ",")))

g <- ggplot(now, aes(cov, ticker)) +
  geom_col(aes(fill = cov < 1), width = 0.7, show.legend = FALSE) +
  geom_vline(xintercept = 1, linetype = "dashed") +
  geom_text(aes(x = pmax(cov, 0) + 0.1, label = label), hjust = 0, size = 2.8) +
  scale_fill_manual(values = c(`FALSE` = BLUE, `TRUE` = ORANGE)) +
  xlim(-1.6, 8.2) +
  labs(x = "hệ số bao phủ (lần), cột cắt ở 6", y = NULL)
ggsave(file.path(FIG, "07_1.png"), g, width = 8, height = 4.2, dpi = 110, bg = "white")
print(now %>% transmute(ticker = as.character(ticker), liquidity_coverage = round(liquidity_coverage, 2),
                        liquidity_gap_12m = round(liquidity_gap_12m, 2)) %>% as.data.frame(), row.names = FALSE)

# hình 7.2 - cú sốc 2022-2023 của từng DN, ghi tên DN ngoại lai
labels <- c(sales_shock_pct = "doanh thu (%)", adv_shock_pct = "khách trả trước (%)",
            rate_shock_pp = "lãi suất thực trả (điểm %)", rollover_stress = "vay mới / trả nợ")
long <- shock %>%
  select(ticker, all_of(names(labels))) %>%
  pivot_longer(-ticker, names_to = "var", values_to = "x") %>%
  filter(!is.na(x)) %>%
  group_by(var) %>%
  mutate(out = x < quantile(x, .25) - 1.5 * IQR(x) | x > quantile(x, .75) + 1.5 * IQR(x)) %>%
  arrange(x, .by_group = TRUE) %>%
  mutate(vj = ifelse(cumsum(out) %% 2 == 1, -1.1, 2.1)) %>%   # so le nhãn cho khỏi đè nhau
  ungroup() %>%
  mutate(label = factor(labels[var], labels))

g <- ggplot(long, aes(x, "")) +
  geom_boxplot(fill = "#cfe0f6", colour = BLUE, outlier.colour = ORANGE, width = 0.6) +
  geom_text(data = filter(long, out), aes(label = ticker, vjust = vj), size = 2.8) +
  facet_wrap(~label, ncol = 1, scales = "free") +
  labs(x = NULL, y = NULL)
ggsave(file.path(FIG, "07_2.png"), g, width = 8, height = 5.2, dpi = 110, bg = "white")
cat("\n")
for (v in names(labels)) {
  d <- filter(long, var == v)
  ds <- if (any(d$out)) paste(d$ticker[d$out], sprintf("%.2f", d$x[d$out]), collapse = ", ") else "không có"
  cat(sprintf("%s: trung vị %.2f; ngoại lai %s\n", v, median(d$x), ds))
}

# hình 7.3 - lãi suất thực trả trên mọi quan sát có số 12 tháng
r <- filter(p, !is.na(implied_rate_pct))
hi <- quantile(r$implied_rate_pct, .75) + 1.5 * IQR(r$implied_rate_pct)

g <- ggplot(r, aes(pmin(implied_rate_pct, 30))) +
  geom_histogram(binwidth = 1, boundary = 0, fill = BLUE, colour = "white") +
  geom_vline(xintercept = median(r$implied_rate_pct), linetype = "dashed") +
  geom_vline(xintercept = hi, colour = ORANGE) +
  labs(x = "lãi vay đã trả 12 tháng / nợ vay bình quân (%), cắt ở 30", y = "số quan sát")
ggsave(file.path(FIG, "07_3.png"), g, width = 8, height = 3, dpi = 110, bg = "white")
cat(sprintf("\ntrung vị %.2f%%, ngưỡng ngoại lai %.2f%%\n", median(r$implied_rate_pct), hi))
out <- r %>% filter(implied_rate_pct > hi) %>% arrange(desc(implied_rate_pct))
print(out %>% select(ticker, period, implied_rate_pct, interest_paid_ttm, total_debt) %>%
        mutate(across(where(is.numeric), ~ round(.x, 2))) %>% as.data.frame(), row.names = FALSE)
