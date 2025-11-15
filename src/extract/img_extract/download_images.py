# download_images.py
import os
import time

import pandas as pd
import requests
from tqdm import tqdm

CSV_REVIEW = "review_images.csv"
OUT_FOLDER = "notebooks/imagens"
os.makedirs(OUT_FOLDER, exist_ok=True)

def baixar(url, path):
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            with open(path, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return True
    except:  # noqa: E722
        pass
    return False

df = pd.read_csv(CSV_REVIEW)

for _, row in tqdm(df.iterrows(), total=len(df), desc="Baixando imagens"):
    codigo = int(row["Codigo Produto"])
    for i in range(1, 3+1):
        if not row.get(f"keep_{i}", False):
            continue
        url = row.get(f"url_{i}")
        if not isinstance(url, str):
            continue
        fname = f"{codigo}_{i}.jpg"
        path = os.path.join(OUT_FOLDER, fname)
        if os.path.exists(path):
            continue
        baixar(url, path)
        time.sleep(0.3)

print("✔ Download concluído!")
