import pandas as pd
from rapidfuzz import fuzz
from tqdm import tqdm
import logging

# === CONFIGURAÇÕES ===
ARQUIVO = "variantes.xlsx"
LIMIAR_SIMILARIDADE = 70
LOG_FILE = "conflitos.log"

# === CONFIGURAÇÃO DO LOGGER ===
logging.basicConfig(
    filename=LOG_FILE,
    filemode="w",  # sobrescreve a cada execução
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger()

logger.info("🔍 Iniciando análise de conflitos...")

# === LEITURA ===
df = pd.read_excel(ARQUIVO)

# Confere colunas essenciais
for col in ["Descrição", "SKU Principal", "SKU Variação"]:
    if col not in df.columns:
        raise ValueError(f"A planilha precisa ter a coluna '{col}'")

# Limpeza básica
df["Descrição"] = df["Descrição"].astype(str).str.strip().str.upper()
df["SKU Principal"] = df["SKU Principal"].astype(str).str.strip()

# === 1️⃣ CONFLITO TIPO 1: mesmo SKU Principal, descrições diferentes ===
logger.info("\n=== [1] Conflitos: Mesmo SKU Principal, descrições diferentes ===")
conflitos_1 = []
for sku, grupo in df.groupby("SKU Principal"):
    descricoes = grupo["Descrição"].unique().tolist()
    if len(descricoes) > 1:
        for i in range(len(descricoes)):
            for j in range(i + 1, len(descricoes)):
                sim = fuzz.token_sort_ratio(descricoes[i], descricoes[j])
                if sim < 100 and sim >= LIMIAR_SIMILARIDADE:
                    conflitos_1.append((sku, descricoes[i], descricoes[j], sim))

if conflitos_1:
    for c in conflitos_1:
        logger.warning(
            f"SKU Principal: {c[0]}\n - {c[1]}\n - {c[2]}\n Similaridade: {c[3]:.1f}%\n"
        )
else:
    logger.info("✅ Nenhum conflito encontrado neste tipo.\n")

# === 2️⃣ CONFLITO TIPO 2: mesma descrição, SKUs principais diferentes ===
logger.info("\n=== [2] Conflitos: Mesma descrição, SKUs principais diferentes ===")
conflitos_2 = []
for desc, grupo in tqdm(df.groupby("Descrição"), total=len(df["Descrição"].unique()), desc="Verificando descrições"):
    skus = grupo["SKU Principal"].unique().tolist()
    if len(skus) > 1:
        conflitos_2.append((desc, skus))

if conflitos_2:
    for c in conflitos_2:
        logger.warning(f"Descrição: {c[0]}\n SKUs Principais: {', '.join(c[1])}\n")
else:
    logger.info("✅ Nenhum conflito encontrado neste tipo.\n")

# === CONTAGEM FINAL ===
logger.info(
    f"\n✅ Análise concluída.\nResumo:\n - Conflitos tipo 1: {len(conflitos_1)}\n - Conflitos tipo 2: {len(conflitos_2)}\n"
)

print("✅ Análise concluída. Veja o arquivo 'conflitos.log' para os detalhes.")
