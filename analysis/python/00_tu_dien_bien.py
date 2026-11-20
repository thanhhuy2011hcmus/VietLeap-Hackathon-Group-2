# 00 - Từ điển biến: các file sạch gồm những cột nào
import glob
import textwrap

import pandas as pd

for f in sorted(glob.glob("data/processed/*.csv")):
    df = pd.read_csv(f)
    print(f, df.shape)
    print(textwrap.indent(textwrap.fill(", ".join(df.columns), 90), "  "))
    print()
