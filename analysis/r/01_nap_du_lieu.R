# 01 - Nạp dữ liệu và đồng bộ tên biến
source("analysis/r/common.R")

# file gốc: mỗi mã 4 đợt tải Vietstock, cộng dữ liệu vĩ mô
for (t in sort(list.files(file.path(RAW, "vietstock")))) {
  cat(t, length(Sys.glob(file.path(RAW, "vietstock", t, "*.xls"))), "file .xls\n")
}
for (f in sort(c(Sys.glob(file.path(RAW, "fred", "*.csv")), Sys.glob(file.path(RAW, "sbv", "*.csv"))))) {
  cat(basename(f), dim(read_csv(f, show_col_types = FALSE)), "\n")
}

# dữ liệu sạch: tên chỉ tiêu tiếng Việt đã đổi sang tên biến tiếng Anh ngắn
panel <- read("bctc/panel_quarterly_bctc.csv")
macro <- read("macro/macro_quy.csv")
cat("\npanel BCTC:", dim(panel), "| vĩ mô theo quý:", dim(macro), "\n")

# đồng bộ khóa thời gian: cả hai bảng dùng kỳ dạng 2026Q3 -> ghép trực tiếp
df <- left_join(panel, macro, by = c("period" = "quarter"))
print(as.data.frame(tail(filter(df, ticker == "NVL") %>%
  select(ticker, period, net_revenue, fed_upper_eoq_pct, sbv_refinancing_eoq_pct), 5)), row.names = FALSE)
cat("\nquý BCTC không ghép được với vĩ mô:", setdiff(panel$period, macro$quarter), "\n")
