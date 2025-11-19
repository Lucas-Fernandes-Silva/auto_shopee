import re

import pandas as pd
from rapidfuzz import fuzz, process
from unidecode import unidecode  # usamos para normalizar textos

# === Caminhos ===
CSV_PATH = "/home/lucas-silva/auto_shopee/urls_cloudinary.csv"
EXCEL_PATH = "/home/lucas-silva/auto_shopee/grandes.xlsx"
OUTPUT_PATH = "final_com_urls.xlsx"

# === 1. Carregar dados ===
urls_df = pd.read_csv(CSV_PATH, header=None, names=["arquivo", "url"])
final_df = pd.read_excel(EXCEL_PATH)

COL_DESC = "Descrição"

# === Normalização da descrição no Excel ===
def norm(s):
    if not isinstance(s, str):
        return ""
    s = s.upper()
    s = unidecode(s)
    s = "".join(c for c in s if c.isalnum() or c.isspace())
    return s.strip()

final_df[COL_DESC] = final_df[COL_DESC].astype(str).apply(norm)

# === 2. Extrair descrição dos arquivos ===
def extrair_info(arquivo):
    arquivo = str(arquivo)

    # Número da imagem
    num_img = re.search(r"_(\d+)_", arquivo)
    num_img = int(num_img.group(1)) if num_img else None

    # Remove prefixos como "123_1_"
    desc_raw = re.sub(r"^\d+_\d+_", "", arquivo)

    # Transforma underline em espaço e normaliza
    descricao = norm(desc_raw.replace("_", " "))

    return pd.Series([descricao, num_img])

urls_df[["descricao_extraida", "num_imagem"]] = urls_df["arquivo"].apply(extrair_info)
urls_df = urls_df.dropna(subset=["descricao_extraida"])

# === 3. Fuzzy Matching para vincular descrição ===
descs_final = final_df[COL_DESC].unique().tolist()
descs_norm = [norm(x) for x in descs_final]  # normalizada para comparação


def melhor_match(descricao, limiar=70):

    desc_norm = norm(descricao)

    # Match exato
    if desc_norm in descs_norm:
        idx = descs_norm.index(desc_norm)
        return descs_final[idx]  # retorna versão original

    # Fuzzy match
    match = process.extractOne(
        desc_norm,
        descs_norm,
        scorer=fuzz.ratio
    )

    print("DEBUG:", descricao, "→", match)

    if match is None:
        return None

    best_norm, score, idx = match

    if score < limiar:
        return None

    return descs_final[idx]  # versão original da planilha


urls_df["descricao_final"] = urls_df["descricao_extraida"].apply(melhor_match)

print(urls_df["descricao_final"].head())

# Remove imagens sem correspondência
urls_df = urls_df.dropna(subset=["descricao_final"])

# === 4. Pivotar em Url_ImagemX ===
urls_pivot = urls_df.pivot_table(
    index="descricao_final",
    columns="num_imagem",
    values="url",
    aggfunc="first"
)

urls_pivot.columns = [f"Url_Imagem{i}" for i in urls_pivot.columns]
urls_pivot = urls_pivot.reset_index()

# === 5. Merge final por descrição ===
merged_df = final_df.merge(
    urls_pivot,
    left_on=COL_DESC,
    right_on="descricao_final",
    how="left"
)

merged_df = merged_df.drop(columns=["descricao_final"])

# === 6. Salvar ===
merged_df.to_excel(OUTPUT_PATH, index=False)

print("✅ URLs adicionadas com fuzzy matching!")
print("📄 Arquivo salvo em:", OUTPUT_PATH)
