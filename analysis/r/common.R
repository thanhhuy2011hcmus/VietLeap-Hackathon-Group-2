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

QUARTERS <- paste0(rep(2021:2026, each = 4), "Q", 1:4)
QUARTERS <- QUARTERS[1:which(QUARTERS == "2026Q3")]
BASE_Q <- "2022Q2"     # 4 quý trước khủng hoảng: 2021Q3-2022Q2
STRESS_Q <- "2023Q2"   # 4 quý khủng hoảng: 2022Q3-2023Q2
LATEST_Q <- "2026Q3"

BLUE <- "#2a78d6"; ORANGE <- "#eb6834"; GREEN <- "#1baf7a"

# tên ngắn -> đường dẫn chỉ tiêu trong file FiinQuant
BS <- "balance_sheet[0]."
IS <- "income_statement[0]."
CF <- "cash_flow[0]."
FIELDS <- c(
  cash = paste0(BS, "cash_and_cash_equivalents.total_cash_and_cash_equivalents"),
  st_invest = paste0(BS, "short_term_investments.total_short_term_investments"),
  st_debt = paste0(BS, "current_liabilities.short_term_borrowings"),
  lt_debt = paste0(BS, "long_term_liabilities.long_term_borrowings"),
  adv_st = paste0(BS, "current_liabilities.advances_from_customers"),
  adv_lt = paste0(BS, "long_term_liabilities.long_term_advances_from_customers"),
  equity = paste0(BS, "owner_s_equity"),
  net_sales = paste0(IS, "net_sales"),
  cfo = paste0(CF, "net_cash_inflows_outflows_from_operating_activities"),
  interest_paid = paste0(CF, "operating_profit_loss_before_changes_in_working_capital",
                         ".interest_paid"),
  loan_proceeds = paste0(CF, "net_cash_inflows_outflows_from_financing_activities",
                         ".proceeds_from_loans"),
  loan_repayments = paste0(CF, "net_cash_inflows_outflows_from_financing_activities",
                           ".repayment_of_loans"),
  # 5 chỉ tiêu dưới chỉ để kiểm tra chéo, không đưa vào file sạch
  total_assets = paste0(BS, "total_assets"),
  liabilities = paste0(BS, "liabilities"),
  interest_expense = paste0(IS, "financial_expenses.in_which_interest_expenses"),
  cf_cash_begin = paste0(CF, "cash_and_cash_equivalents_at_the_beginning_o_period"),
  cf_cash_end = paste0(CF, "cash_and_cash_equivalents_at_the_end_of_period")
)
FLOWS <- c("net_sales", "cfo", "interest_paid", "loan_proceeds", "loan_repayments")

load_raw <- function() {
  files <- sort(Sys.glob(file.path(RAW, "*_bctc_min_raw.csv")))
  bind_rows(lapply(files, read_csv, show_col_types = FALSE))
}

# bảng dài (mỗi dòng 1 chỉ tiêu) -> bảng ngang (mỗi dòng 1 mã x 1 quý)
to_wide <- function(raw) {
  raw %>%
    filter(field_path %in% FIELDS) %>%
    mutate(var = names(FIELDS)[match(field_path, FIELDS)]) %>%
    select(ticker, year, quarter, var, value) %>%
    pivot_wider(names_from = var, values_from = value) %>%
    select(ticker, year, quarter, all_of(names(FIELDS))) %>%
    mutate(period = paste0(year, "Q", quarter)) %>%
    arrange(ticker, year, quarter)
}

# coi 2 số tiền (VND) là bằng nhau nếu lệch dưới 1 triệu đồng hoặc 0,01%
close <- function(a, b) {
  tol <- pmax(1e6, 1e-4 * pmax(abs(a), abs(b)))
  !is.na(a) & !is.na(b) & abs(a - b) <= tol
}

# tổng 4 quý liên tiếp, NA nếu thiếu quý nào
sum4 <- function(x) {
  out <- rep(NA_real_, length(x))
  for (i in seq_along(x)[-(1:3)]) out[i] <- sum(x[(i - 3):i])
  out
}

theme_set(theme_minimal(base_size = 10) + theme(panel.grid.minor = element_blank()))
dir.create(FIG, showWarnings = FALSE, recursive = TRUE)
