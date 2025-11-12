
import pandas as pd

# === Caminhos dos arquivos ===
CSV_PATH = "/home/lucas-silva/github/auto_shopee/urls_cloudinary.csv"     # arquivo com os nomes e URLs
EXCEL_PATH = "/home/lucas-silva/github/auto_shopee/planilhas/outputs/final.xlsx"            # planilha principal
OUTPUT_PATH = "final_com_urls.xlsx"  # saída com URLs adicionadas

# === 1. Carregar os dados ===
urls_df = pd.read_csv(CSV_PATH, header=None, names=["arquivo", "url"])
final_df = pd.read_excel(EXCEL_PATH)

# === 2. Extrair número do índice (ex: 0000_1_FITA -> 0000) e número da imagem ===
# Garante que o índice seja numérico (remove zeros à esquerda)
urls_df["codigo"] = urls_df["arquivo"].str.extract(r"^(\d+)_")[0].astype(int)
urls_df["num_imagem"] = urls_df["arquivo"].str.extract(r"_(\d+)_")[0].astype(int)

# === 3. Pivotar as URLs em colunas Url_Imagem1, Url_Imagem2, ... ===
urls_pivot = urls_df.pivot_table(index="codigo", columns="num_imagem", values="url", aggfunc="first")
urls_pivot.columns = [f"Url_Imagem{i}" for i in urls_pivot.columns]

# === 4. Garantir que o índice da planilha principal é o mesmo formato (int) ===
# Caso o número esteja em outra coluna, ajuste o nome aqui:
final_df["codigo"] = final_df.index.astype(int)  # se o índice é o código
# ou, se há uma coluna "Código", use: final_df["codigo"] = final_df["Código"].astype(int)

# === 5. Fazer o merge, preservando todas as linhas do Excel ===
merged_df = final_df.merge(urls_pivot, on="codigo", how="left")

# === 6. Salvar o resultado ===
merged_df.to_excel(OUTPUT_PATH, index=False)

print("✅ URLs adicionadas com sucesso!")
print("Arquivo salvo em:", OUTPUT_PATH)
