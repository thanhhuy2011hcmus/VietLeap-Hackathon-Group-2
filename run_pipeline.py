"""
run_pipeline.py — chạy toàn bộ quy trình dữ liệu của dự án.

    python run_pipeline.py              # làm sạch dữ liệu + dựng báo cáo
    python run_pipeline.py --clean      # chỉ làm sạch (data/raw -> data/processed)
    python run_pipeline.py --report     # chỉ dựng báo cáo (cần data/processed có sẵn)
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
STEPS = {
    "clean": ("Làm sạch dữ liệu", os.path.join("src", "clean_raw_data.py")),
    "report": ("Dựng báo cáo HTML", os.path.join("src", "build_report.py")),
}


def run(key):
    title, script = STEPS[key]
    print(f"\n>>> {title}: {script}")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    code = subprocess.call([sys.executable, script], cwd=ROOT, env=env)
    if code != 0:
        sys.exit(f"Bước '{title}' lỗi (mã {code}).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clean", action="store_true", help="chỉ chạy bước làm sạch")
    ap.add_argument("--report", action="store_true", help="chỉ chạy bước dựng báo cáo")
    a = ap.parse_args()
    steps = [k for k in STEPS if getattr(a, k)] or list(STEPS)
    for k in steps:
        run(k)
    print("\nHoàn tất. Báo cáo: reports/bao_cao_xu_ly_du_lieu.html")


if __name__ == "__main__":
    main()
