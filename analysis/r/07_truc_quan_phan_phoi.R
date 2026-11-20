# 07 - Vẽ hình về phân phối và ngoại lai
source("analysis/r/common.R")

f <- read("features/bien_moi_quy.csv") %>% filter(ticker %in% RE)
now <- f %>% filter(period == LATEST_Q) %>% arrange(cash_coverage)

# hình 7.1 - tiền + đầu tư ngắn hạn so với nợ ngắn hạn; dưới 1 là không đủ
g <- ggplot(now, aes(cash_coverage, factor(ticker, ticker))) +
  geom_col(aes(fill = cash_coverage < 1), width = 0.7, show.legend = FALSE) +
  geom_vline(xintercept = 1, linetype = "dashed") +
  geom_text(aes(label = sprintf("%.2fx  (%s tỷ)", cash_coverage,
                                format(round(liquidity_gap), big.mark = ",", trim = TRUE))),
            hjust = -0.05, size = 2.8) +
  scale_fill_manual(values = c(`FALSE` = BLUE, `TRUE` = ORANGE)) +
  xlim(0, 1.6) +
  labs(x = "(tiền + đầu tư ngắn hạn) / nợ ngắn hạn (lần)", y = NULL)
ggsave(file.path(FIG, "07_1.png"), g, width = 8, height = 4, dpi = 110, bg = "white")
print(now %>% select(ticker, cash_coverage, liquidity_gap) %>%
        mutate(across(where(is.numeric), ~ round(.x, 2))) %>% as.data.frame(), row.names = FALSE)

# hình 7.2 - doanh thu quý so cùng kỳ theo từng doanh nghiệp (cắt ở ±300% cho dễ nhìn)
d <- filter(f, !is.na(revenue_yoy_pct))
order <- d %>% group_by(ticker) %>% summarise(m = median(revenue_yoy_pct)) %>% arrange(m) %>% pull(ticker)
g <- ggplot(d, aes(pmin(pmax(revenue_yoy_pct, -100), 300), factor(ticker, order))) +
  geom_boxplot(fill = "#cfe0f6", colour = BLUE, outlier.colour = ORANGE, width = 0.6) +
  geom_vline(xintercept = 0, colour = GREY) +
  labs(x = "doanh thu quý so cùng kỳ năm trước (%), cắt ở -100 và 300", y = NULL)
ggsave(file.path(FIG, "07_2.png"), g, width = 8, height = 4.2, dpi = 110, bg = "white")
hi <- quantile(d$revenue_yoy_pct, .75) + 1.5 * IQR(d$revenue_yoy_pct)
big <- d %>% filter(revenue_yoy_pct > hi) %>% arrange(desc(revenue_yoy_pct))
cat(sprintf("\nngưỡng ngoại lai trên %.1f%%, %d quan sát vượt:\n", hi, nrow(big)))
print(big %>% select(ticker, period, revenue_yoy_pct) %>%
        mutate(revenue_yoy_pct = round(revenue_yoy_pct, 2)) %>% as.data.frame(), row.names = FALSE)

# hình 7.3 - phân phối doanh thu so cùng kỳ: năm 2023 so với các quý sau
d <- d %>% mutate(nhom = ifelse(period <= "2023Q4", "năm 2023", "2024 trở đi"))
g <- ggplot(d, aes(pmin(pmax(revenue_yoy_pct, -100), 300), fill = nhom)) +
  geom_histogram(binwidth = 20, boundary = -100, position = "identity", alpha = 0.8, colour = "white") +
  geom_vline(xintercept = 0) +
  scale_fill_manual(values = c("2024 trở đi" = GREY, "năm 2023" = ORANGE), name = NULL) +
  labs(x = "doanh thu quý so cùng kỳ (%)", y = "số quan sát") +
  theme(legend.position = "top")
ggsave(file.path(FIG, "07_3.png"), g, width = 8, height = 3, dpi = 110, bg = "white")
cat("\ntrung vị năm 2023:", round(median(d$revenue_yoy_pct[d$nhom == "năm 2023"]), 2),
    "| trung vị từ 2024:", round(median(d$revenue_yoy_pct[d$nhom != "năm 2023"]), 2), "\n")

# hình 7.4 - đòn bẩy và khả năng trả nợ ngắn hạn (kích thước = khoảng thiếu hụt)
g <- ggplot(now, aes(liab_to_equity, cash_coverage)) +
  geom_point(aes(size = abs(pmin(liquidity_gap, 0))), colour = ORANGE, alpha = 0.6, show.legend = FALSE) +
  geom_text(aes(label = ticker), hjust = -0.3, vjust = -0.3, size = 2.8) +
  geom_hline(yintercept = 1, linetype = "dashed", colour = GREY) +
  scale_size(range = c(2, 16), trans = "sqrt") +
  scale_x_continuous(expand = expansion(mult = c(0.05, 0.12))) +
  labs(x = "nợ phải trả / vốn chủ sở hữu (lần)", y = "(tiền + ĐTNH) / nợ ngắn hạn (lần)")
ggsave(file.path(FIG, "07_4.png"), g, width = 8, height = 4, dpi = 110, bg = "white")
cat("\ntương quan giữa đòn bẩy và khả năng trả nợ ngắn hạn:",
    round(cor(now$liab_to_equity, now$cash_coverage), 2), "\n")
