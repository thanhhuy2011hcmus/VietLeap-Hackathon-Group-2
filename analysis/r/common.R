# Những thứ dùng chung cho các file 00-07. Chạy từ thư mục gốc của dự án.
suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(readr)
  library(ggplot2)
})
options(width = 100, scipen = 20, dplyr.summarise.inform = FALSE)

RAW <- "data/raw"
PROC <- "data/processed"
FIG <- "reports/figures/r"

# 9 doanh nghiệp bất động sản; SRC là Cao su Sao Vàng nên chỉ dùng ở phần kiểm tra dữ liệu
RE <- c("DIG", "DXG", "HPX", "KDH", "NLG", "NVL", "PDR", "QCG", "VHM")
LATEST_Q <- "2026Q3"
SHOCK <- c("2022Q3", "2023Q4")        # giai đoạn lãi suất tăng, bán hàng chậm

BLUE <- "#2a78d6"; ORANGE <- "#eb6834"; GREEN <- "#1baf7a"; GREY <- "#9ca3af"

read <- function(name) read_csv(file.path(PROC, name), show_col_types = FALSE)

# chuyển "2026Q3" thành số thứ tự quý để so sánh, dựng lưới quý liên tục
q_index <- function(p) as.integer(substr(p, 1, 4)) * 4 + as.integer(substr(p, 6, 6)) - 1
q_label <- function(i) paste0(i %/% 4, "Q", i %% 4 + 1)

theme_set(theme_minimal(base_size = 10) + theme(panel.grid.minor = element_blank()))
dir.create(FIG, showWarnings = FALSE, recursive = TRUE)
