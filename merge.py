import pandas as pd

# === Caminhos dos arquivos ===
CSV_PATH = "/home/lucas-silva/auto_shopee/urls_cloudinary.csv"
EXCEL_PATH = "/home/lucas-silva/auto_shopee/planilhas/outputs/final.xlsx"
OUTPUT_PATH = "final_com_urls.xlsx"

# === 1. Carregar os dados ===
urls_df = pd.read_csv(CSV_PATH, header=None, names=["arquivo", "url"])
final_df = pd.read_excel(EXCEL_PATH)

# === 2. Extrair o código numérico e número da imagem, de forma segura ===
# Exemplo: "0000_1_FITA_DUREX_TRANSP_12X50"
urls_df["codigo"] = urls_df["arquivo"].astype(str).str.extract(r"^(\d+)_")[0]

# Converte para número, ignorando erros
urls_df["codigo"] = pd.to_numeric(urls_df["codigo"], errors="coerce")

# Extrai o número da imagem (ex: 1, 2, 3)
urls_df["num_imagem"] = urls_df["arquivo"].astype(str).str.extract(r"_(\d+)_")[0]
urls_df["num_imagem"] = pd.to_numeric(urls_df["num_imagem"], errors="coerce").fillna(0).astype(int)

# === 3. Pivotar as URLs em colunas Url_Imagem1, Url_Imagem2, etc ===
urls_pivot = urls_df.pivot_table(
    index="codigo", columns="num_imagem", values="url", aggfunc="first"
)
urls_pivot.columns = [f"Url_Imagem{i}" for i in urls_pivot.columns]

# === 4. Garantir que o índice da planilha principal é numérico ===
final_df = final_df.reset_index(drop=True).copy()
final_df["codigo"] = final_df.index.astype(int)  # usa o índice como código (ex: 2245, 2246...)

# === 5. Fazer o merge preservando todas as linhas ===
merged_df = final_df.merge(urls_pivot, on="codigo", how="left")

# === 6. Salvar o resultado ===
merged_df.to_excel(OUTPUT_PATH, index=False)

print("✅ URLs adicionadas com sucesso!")
print("📄 Arquivo salvo em:", OUTPUT_PATH)
