# 01 - Nạp dữ liệu và đổi tên biến
source("analysis/r/common.R")

raw <- load_raw()
cat("số dòng, số cột:", dim(raw), "\n")
cat("số mã:", n_distinct(raw$ticker), "| số chỉ tiêu:", n_distinct(raw$field_path), "\n")
print(head(as.data.frame(raw[c("ticker", "year", "quarter", "value")]), 3))

# chỉ tiêu có trong file nhưng không dùng tới
for (path in sort(setdiff(unique(raw$field_path), FIELDS))) cat("bỏ:", path, "\n")

# chuyển sang bảng ngang, mỗi dòng là 1 mã trong 1 quý
w <- to_wide(raw)
cat("\nbảng ngang:", dim(w), "\n")

# xem thử VHM 4 quý gần nhất, đơn vị tỷ đồng (dấu giữ nguyên như FiinQuant)
vhm <- tail(filter(w, ticker == "VHM"), 4)
m <- t(as.matrix(vhm[names(FIELDS)])) / 1e9
colnames(m) <- vhm$period
print(round(m))

# các file còn lại trong data/raw
for (f in sort(Sys.glob(file.path(RAW, "*.csv")), method = "radix")) {
  if (!grepl("_bctc_min_raw", f)) cat(f, dim(read_csv(f, show_col_types = FALSE)), "\n")
}
