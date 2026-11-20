# 00 - Từ điển biến: các file sạch gồm những cột nào
library(readr)

for (f in sort(Sys.glob("data/processed/*/*.csv"), method = "radix")) {
  df <- read_csv(f, show_col_types = FALSE)
  cat(f, dim(df), "\n")
  cat(strwrap(paste(names(df), collapse = ", "), 90, prefix = "  "), sep = "\n")
  cat("\n")
}
