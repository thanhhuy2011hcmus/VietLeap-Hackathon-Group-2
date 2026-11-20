# 03 - Làm sạch: ô trống, ô "-" và ngoại lai
source("analysis/r/common.R")

p <- read("bctc/panel_quarterly_bctc.csv")

# ô "-" trong file Vietstock (không phát sinh / không có số) đã được để trống, không thay bằng 0.
# đếm riêng từng bảng để không lẫn với phần CĐKT vốn không có trong nguồn
for (name in c("KQKD", "CĐKT")) {
  d <- read(if (name == "KQKD") "bctc/ket_qua_kinh_doanh_quy.csv" else "bctc/can_doi_ke_toan_quy.csv")
  na <- colSums(is.na(d))
  cat("ô trống trong ", name, " (", nrow(d), " quý):\n", sep = "")
  print(na[na > 0])
}

# vĩ mô: tháng CPI Mỹ bị thiếu đã được nội suy và gắn cờ
m <- read("macro/macro_thang.csv")
cat("\nCPI Mỹ nội suy:", paste(m$month[m$us_cpi_imputed], m$us_cpi_index[m$us_cpi_imputed]), "\n")

# ngoại lai theo quy tắc 1,5 IQR - chỉ đánh dấu, không xóa
ngoai_lai <- function(x, ten) {
  ok <- !is.na(x); x <- x[ok]; ten <- ten[ok]
  q <- quantile(x, c(0.25, 0.75), names = FALSE)
  o <- x < q[1] - 1.5 * (q[2] - q[1]) | x > q[2] + 1.5 * (q[2] - q[1])
  list(x = x[o], ten = ten[o])
}

# doanh thu quý của từng doanh nghiệp: quý nào cao/thấp bất thường so với chính DN đó
cat("\nquý có doanh thu ngoại lai (tỷ đồng):\n")
for (t in RE) {
  g <- filter(p, ticker == t)
  o <- ngoai_lai(g$net_revenue, g$period)
  cat("  ", t, ": ", if (length(o$x)) paste(o$ten, format(round(o$x), big.mark = ","), collapse = ", ")
      else "không có", "\n", sep = "")
}

# chỉ số năm 2025 giữa các doanh nghiệp
r <- read("bctc/chi_so_tai_chinh_nam.csv") %>% filter(year == 2025, ticker %in% RE)
cat("\nngoại lai giữa các DN, năm 2025:\n")
for (col in c("gross_margin_pct", "net_margin_pct", "debt_to_assets", "roea_pct")) {
  o <- ngoai_lai(r[[col]], r$ticker)
  cat("  ", col, ": ", if (length(o$x)) paste(o$ten, sprintf("%.2f", o$x), collapse = ", ") else "không có",
      "\n", sep = "")
}
