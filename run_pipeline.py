"""Chạy toàn bộ: làm sạch -> tạo biến -> dựng báo cáo.   python run_pipeline.py"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
STEPS = ["src/clean_bctc_data.py", "src/clean_macro_data.py", "src/build_features.py", "src/build_report.py"]

for step in STEPS:
    print(f"\n>>> {step}")
    code = subprocess.call([sys.executable, step], cwd=ROOT, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if code:
        sys.exit(f"Lỗi ở {step} (mã {code})")
print("\nXong. Dữ liệu sạch ở data/processed/, báo cáo ở reports/bao_cao_truc_quan_hoa.html")
