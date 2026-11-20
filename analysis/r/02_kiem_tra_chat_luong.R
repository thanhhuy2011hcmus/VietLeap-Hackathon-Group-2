# 02 - Kiểm tra chất lượng dữ liệu
source("analysis/r/common.R")

p <- read("bctc/panel_quarterly_bctc.csv")
cat("dòng trùng (ticker, period):", sum(duplicated(p[c("ticker", "period")])), "\n")

# độ phủ: số quý có kết quả kinh doanh (KQKD) và có cân đối kế toán (CĐKT)
cov <- p %>%
  group_by(ticker) %>%
  summarise(kqkd = sum(!is.na(net_revenue)), cdkt = sum(!is.na(total_assets)),
            tu = min(period), den = max(period))
print(as.data.frame(cov), row.names = FALSE)

# quý bị thiếu nằm giữa kỳ đầu và kỳ cuối
cat("\nquý thiếu ở giữa:\n")
for (t in sort(unique(p$ticker))) {
  i <- q_index(p$period[p$ticker == t])
  thieu <- setdiff(min(i):max(i), i)
  cat(" ", t, if (length(thieu)) paste(q_label(thieu), collapse = ", ") else "không", "\n")
}

# các đẳng thức kế toán (lệch dưới 0,1 tỷ coi là khớp)
bs <- filter(p, !is.na(total_assets))
cat("\ntổng TS = TS ngắn hạn + TS dài hạn:",
    sum(abs(bs$current_assets + bs$non_current_assets - bs$total_assets) <= 0.1), "/", nrow(bs), "\n")
cat("tổng NV = nợ phải trả + vốn chủ:",
    sum(abs(bs$total_liabilities + bs$owner_equity - bs$total_resources) <= 0.1), "/", nrow(bs), "\n")
cat("LN gộp = doanh thu - giá vốn:",
    sum(abs(p$net_revenue - p$cogs - p$gross_profit) <= 0.1), "/", nrow(p), "\n")

# quy mô vốn điều lệ để nhận diện đúng doanh nghiệp (SRC rất nhỏ so với nhóm BĐS)
cat("\n")
print(p %>% filter(period == LATEST_Q) %>% select(ticker, paid_in_capital, total_assets) %>%
        arrange(paid_in_capital) %>% as.data.frame(), row.names = FALSE)
