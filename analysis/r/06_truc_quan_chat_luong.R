# 06 - Vẽ hình về chất lượng và độ phủ dữ liệu
source("analysis/r/common.R")

p <- read_csv(file.path(PROC, "panel_quarterly.csv"), show_col_types = FALSE)

# hình 6.1 - mã nào có số liệu ở quý nào
grid <- expand_grid(ticker = unique(p$ticker), period = QUARTERS) %>%
  left_join(select(p, ticker, period, cfo_ttm), by = c("ticker", "period")) %>%
  mutate(state = case_when(
    !paste(ticker, period) %in% paste(p$ticker, p$period) ~ "không có số liệu",
    is.na(cfo_ttm) ~ "có số liệu quý",
    TRUE ~ "tính được số 12 tháng"))

g <- ggplot(grid, aes(factor(period, QUARTERS), factor(ticker, rev(sort(unique(ticker)))))) +
  geom_tile(aes(fill = state), colour = "white") +
  scale_fill_manual(values = c("có số liệu quý" = "#9cc3f0", "không có số liệu" = "#e9ecef",
                               "tính được số 12 tháng" = BLUE), name = NULL) +
  labs(x = NULL, y = NULL) +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5), legend.position = "top",
        panel.grid = element_blank())
ggsave(file.path(FIG, "06_1.png"), g, width = 9, height = 3.8, dpi = 110, bg = "white")
n <- table(factor(p$period, QUARTERS))
cat("quý không có mã nào:", paste(names(n)[n == 0], collapse = ", "), "\n")
cat("các quý còn lại đều đủ", max(n), "mã\n")

# hình 6.2 - các lỗi đã gắn cờ
names <- c(interest_paid_sign = "lãi vay đã trả mang dấu dương",
           loan_proceeds_sign = "tiền vay mới mang dấu âm",
           net_sales_sign = "doanh thu thuần âm",
           loan_repayments_sign = "trả nợ gốc mang dấu dương",
           interest_paid_from_pl = "lãi vay đã trả lấy từ B02",
           cash_bs_ne_cf = "tiền B01 khác tiền cuối kỳ B03")
flags <- sort(table(names[unlist(strsplit(na.omit(p$dq_flags), ";"))]), decreasing = TRUE)

g <- ggplot(as.data.frame(flags), aes(Freq, reorder(Var1, Freq))) +
  geom_col(fill = BLUE, width = 0.7) +
  labs(x = "số quý bị gắn cờ", y = NULL)
ggsave(file.path(FIG, "06_2.png"), g, width = 8, height = 2.8, dpi = 110, bg = "white")
cat("\n")
print(setNames(as.data.frame(flags), c("lỗi", "số quý")), row.names = FALSE)

# hình 6.3 - lãi suất và 2 giai đoạn dùng để đo cú sốc
m <- read_csv(file.path(PROC, "macro_quarterly.csv"), show_col_types = FALSE) %>%
  mutate(x = row_number())
i <- setNames(m$x, m$period)
long <- m %>%
  select(x, `tái cấp vốn NHNN` = sbv_refinancing_eoq, `lãi suất Fed` = fed_upper_eoq,
         `UST 10 năm` = ust10y_avg) %>%
  pivot_longer(-x, names_to = "series", values_to = "rate")

g <- ggplot(long, aes(x, rate, colour = series)) +
  annotate("rect", xmin = i[["2021Q3"]] - .5, xmax = i[[BASE_Q]] + .5,
           ymin = -Inf, ymax = Inf, fill = "#dfe7f3") +
  annotate("rect", xmin = i[["2022Q3"]] - .5, xmax = i[[STRESS_Q]] + .5,
           ymin = -Inf, ymax = Inf, fill = "#fbe3d6") +
  geom_step(data = filter(long, series != "UST 10 năm"), direction = "mid", na.rm = TRUE) +
  geom_line(data = filter(long, series == "UST 10 năm"), na.rm = TRUE) +
  scale_colour_manual(values = c("lãi suất Fed" = ORANGE, "tái cấp vốn NHNN" = BLUE,
                                 "UST 10 năm" = GREEN), name = NULL) +
  scale_x_continuous(breaks = m$x, labels = m$period) +
  labs(x = NULL, y = "%/năm", subtitle = "nền xanh: trước khủng hoảng   nền cam: khủng hoảng") +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5), legend.position = "top")
ggsave(file.path(FIG, "06_3.png"), g, width = 9, height = 3.6, dpi = 110, bg = "white")
cat("\n")
print(as.data.frame(filter(m, period %in% c("2021Q4", BASE_Q, "2022Q4", STRESS_Q, "2026Q3"))
                    %>% select(-x)))
