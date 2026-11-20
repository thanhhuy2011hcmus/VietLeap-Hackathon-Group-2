# 06 - Vẽ hình về chất lượng và độ phủ dữ liệu
source("analysis/r/common.R")

p <- read("bctc/panel_quarterly_bctc.csv")

# hình 6.1 - mã nào có số liệu ở quý nào
quarters <- q_label(seq(min(q_index(p$period)), max(q_index(p$period))))
grid <- expand_grid(ticker = unique(p$ticker), period = quarters) %>%
  left_join(select(p, ticker, period, net_revenue, total_assets), by = c("ticker", "period")) %>%
  mutate(state = case_when(!is.na(total_assets) ~ "có cả KQKD và CĐKT",
                           !is.na(net_revenue) ~ "chỉ có KQKD",
                           TRUE ~ "không có số liệu"))

g <- ggplot(grid, aes(factor(period, quarters), factor(ticker, rev(sort(unique(ticker)))))) +
  geom_tile(aes(fill = state), colour = "white") +
  scale_fill_manual(values = c("chỉ có KQKD" = "#9cc3f0", "có cả KQKD và CĐKT" = BLUE,
                               "không có số liệu" = "#e9ecef"), name = NULL) +
  labs(x = NULL, y = NULL) +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5), legend.position = "top",
        panel.grid = element_blank())
ggsave(file.path(FIG, "06_1.png"), g, width = 9, height = 3.8, dpi = 110, bg = "white")
cat("số mã có KQKD theo quý:\n")
print(table(factor(p$period[!is.na(p$net_revenue)], quarters)))

# hình 6.2 - số ô trống theo biến (tính trên các quý có loại báo cáo tương ứng)
is_cols <- c("net_revenue", "cogs", "financial_expense", "selling_expense", "associate_profit", "basic_eps_vnd")
bs <- filter(p, !is.na(total_assets))
miss <- c(colSums(is.na(p[is_cols])), colSums(is.na(select(bs, -all_of(is_cols)))))
miss <- sort(miss[miss > 0])

g <- ggplot(data.frame(bien = names(miss), n = as.numeric(miss)), aes(n, reorder(bien, n))) +
  geom_col(fill = ORANGE, width = 0.7) +
  labs(x = "số ô trống", y = NULL)
ggsave(file.path(FIG, "06_2.png"), g, width = 8, height = 3, dpi = 110, bg = "white")
cat("\n")
print(rev(miss))

# hình 6.3 - lãi suất theo quý và giai đoạn khủng hoảng 2022-2023
m <- read("macro/macro_quy.csv") %>% mutate(x = row_number())
i <- setNames(m$x, m$quarter)
long <- m %>%
  select(x, `tái cấp vốn NHNN` = sbv_refinancing_eoq_pct, `lãi suất Fed` = fed_upper_eoq_pct,
         `UST 10 năm` = ust10y_avg_pct) %>%
  pivot_longer(-x, names_to = "series", values_to = "rate")

g <- ggplot(long, aes(x, rate, colour = series)) +
  annotate("rect", xmin = i[[SHOCK[1]]] - .5, xmax = i[[SHOCK[2]]] + .5,
           ymin = -Inf, ymax = Inf, fill = "#fbe3d6") +
  geom_step(data = filter(long, series != "UST 10 năm"), direction = "mid", na.rm = TRUE) +
  geom_line(data = filter(long, series == "UST 10 năm"), na.rm = TRUE) +
  scale_colour_manual(values = c("lãi suất Fed" = ORANGE, "tái cấp vốn NHNN" = BLUE,
                                 "UST 10 năm" = GREEN), name = NULL) +
  scale_x_continuous(breaks = m$x[c(TRUE, FALSE)], labels = m$quarter[c(TRUE, FALSE)]) +
  labs(x = NULL, y = "%/năm", subtitle = "nền cam: 2022Q3-2023Q4") +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5), legend.position = "top")
ggsave(file.path(FIG, "06_3.png"), g, width = 9, height = 3.6, dpi = 110, bg = "white")
cat("\n")
print(as.data.frame(filter(m, quarter %in% c("2022Q2", "2022Q4", "2023Q4", "2026Q3")) %>% select(-x)),
      row.names = FALSE)
