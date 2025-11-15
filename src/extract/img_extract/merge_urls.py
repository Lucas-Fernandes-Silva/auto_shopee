# merge_urls.py
import pandas as pd

CSV_PATH = "urls_cloudinary.csv"
EXCEL_PATH = "planilhas/outputs/final.xlsx"
OUTPUT_PATH = "final_com_urls.xlsx"

urls_df = pd.read_csv(CSV_PATH)
final_df = pd.read_excel(EXCEL_PATH)

def parse_file(x):
    import re
    s = str(x)
    m = re.match(r"^0*([0-9]+)[^\d]*_(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

urls_df[["codigo", "num"]] = urls_df["arquivo"].apply(lambda x: pd.Series(parse_file(x)))
urls_df = urls_df.dropna()

pivot = urls_df.pivot_table(index="codigo", columns="num", values="url")

# Apenas 3 colunas
pivot.columns = [f"Url_Imagem{int(c)}" for c in pivot.columns]

if "Codigo Produto" not in final_df.columns:
    final_df = final_df.reset_index().rename(columns={"index": "Codigo Produto"})

final_df["codigo"] = final_df["Codigo Produto"]

merged = final_df.merge(pivot, on="codigo", how="left")

# Não sobrescrever imagens existentes
for i in range(1, 3+1):
    col = f"Url_Imagem{i}"
    if col in merged.columns:
        merged[col] = merged[col].combine_first(final_df.get(col)) # pyright: ignore[reportArgumentType]

merged.drop(columns=["codigo"], inplace=True)
merged.to_excel(OUTPUT_PATH, index=False)

print("✔ Merge concluído! ->", OUTPUT_PATH)
