import pandas as pd
import numpy as np
import re
import unicodedata
from logger import logger

# === 1. Carregar o arquivo ===
df = pd.read_excel("produtos.xlsx")


# === 2. Função para limpar e normalizar texto ===
def limpar_texto(txt):
    if not isinstance(txt, str):
        return ""
    # Remove acentos
    txt = unicodedata.normalize("NFD", txt)
    txt = txt.encode("ascii", "ignore").decode("utf-8")
    # Converte para maiúsculas
    txt = txt.upper()
    # Remove caracteres especiais
    txt = re.sub(r"[^A-Z0-9 ]", "", txt)
    # Remove espaços duplicados
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


# === 3. Lista de marcas fixas (forçadas a fazer parte da análise) ===
marcas_adicionais = [
    "SHIVA",
    "BRASCOLA",
    "FERTAK",
    "NATICON",
    "NOBRE",
    "ADELBRAS",
    "STA MARINA",
    "FIRMEZA",
    "OLIPLAS",
    "STAM",
    "R.C.A",
    "CORONA",
    "TOP FIO",
    "MAKITA",
    "REXON",
    "SOPRANO",
    "FAST LUB",
    "ACQUA",
    "KIAN",
    "SOUDAL",
    "DEPLAST",
    "TATU",
    "GRENDHA",
    "PANASONIC",
    "PAULICEIA",
    "MORIA",
    "ALLTAPE",
    "PLASTILIT",
    "TITANIUM",
    "FERRARI",
    "NEGREIRA",
    "RADIAL",
    "BLUMENAU",
    "J.F METAIS",
    "ART METAIS",
    "LONAX",
    "GHEL PLUS",
    "CHEMICOLOR",
    "SANY",
    "PROAQUA",
    "BICROM",
    "WAGO",
    "TECHNA",
    "METASUL",
    "GARAPEIRA",
    "ROCO",
    "PRO FOAM",
    "DURACELL",
    "POLIBEL",
    "AGELUX",
    "REMOX",
    "RORATO",
    "WAVES",
    "LEGRAND",
    "PAPAIZ",
    "AGELUZ",
    "IMPERIAL",
    "HYDRA",
    "KITUBO",
    "NETTE",
    "SANLIMP",
    "EMA METAIS",
    "M&M" "BEARS",
    "ADTEX",
    "GALO",
    "PEGAFORTE",
    "EMAVE",
    "ELGIN",
    "LUCONI",
    "VEGA",
    "MUNDIAL",
    "DELTA",
    "COBRECOM",
    "PLASTBIG",
    "FERE",
    "SATA",
    "ALUMBRA",
    "FIOLUX",
    "PACETTA",
    "ITAMBE",
    "PEXCEL",
    "EMAVA",
    "KADESH",
    "IBERE",
    "GOLD",
    "PERLEX",
    "IMA",
    "SAFETY",
    "PIAL",
    "PLASTIK",
    "OUROLUX",
    "LED BEE",
    "BELZER",
    "PROTEG",
    "NASTRO",
    "FJ FERR",
    "SAO RAFAEL",
    "STILLUS",
    "FLASH LIMP",
    "ZUMPLAST",
    "REDY",
    "PRIMETECH",
    "SECALUX",
    "PLASTIC",
    "SUPER BONDER",
    "ARTPLAS",
    "FABER CASTELL",
    "GUARANI",
    "DEWALT",
    "ALUREM",
    "PERFIX ",
    "STELL",
    "FERROX",
    "USAF",
    "INJET",
    "CMK",
    "BEARS",
    "MINASUL",
    "DEGOMASTER",
    "SIENA",
]
marcas_adicionais = [limpar_texto(m) for m in marcas_adicionais]


# === 4. Dicionário de sinônimos / variações ===
mapa_variacoes = {
    "TRAMONTINA": [
        "TRAMON",
        "TRAMONTINA",
        "TRAMONTINA ELE",
        "TRAMONTINA GARI",
        "TRAMONTINA MULT",
        "TRAM",
    ],
    "JOMARCA": ["JOMARCA", "JOMARC", "JOMARCA JMC", "JMC"],
    "NEW FIX": [
        "NEW FIX",
        "NEWFIX",
        "NEW-FIX",
        "NEW F",
        "PARAF CHIPBOARD CHATA PHS",
        "PARAF SEX.ROS.SOBERBA",
    ],
    "NOVA": ["NOVA TINTAS", "NOVA"],
    "DRYKO": ["DRYKO", "DRYKOPRIMER"],
    "SIKA": ["SIKATOP", "SIKA"],
    "BRASFORT": ["BRASF", "BRASFORT"],
    "ILUMI": ["ILUM", "ILUMI"],
    "DENVER": [
        "DENVER",
        "DENVERIMPER",
        "DENVERLAJE",
        "DENVERTEC",
        "DENVERCRILL",
        "DENVERFITA",
        "DENVERFIX",
    ],
    "THOMPSOM": ["THOMPSOM", "THOMP"],
    "PEGAFORTE": ["PEGAFORTE", "PEGA FORTE"],
    "CALHA FORTE": ["CALHA FORTE", "CALHA FORT"],
    "VEDACIT": ["VEDACIT", "BIANCO"],
    "LORENZETTI": ["LOREN", "LORENZETTI", "ORIG.L&C D", ".PMR D.", ".L&C "],
    "KADESH": ["BOT FLEX ELASTICO PRETA BI"],
}


# === 5. Montar lista final de marcas conhecidas ===
marcas_planilha = df["Marca"].dropna().unique().tolist()
marcas_planilha.remove("5+")
marcas_planilha = [
    limpar_texto(m) for m in marcas_planilha if isinstance(m, str) and m.strip()
]

# Combinar todas
marcas = list(set(marcas_planilha + marcas_adicionais))

# Adicionar também as variações do mapa
for marca_principal, variacoes in mapa_variacoes.items():
    marcas.append(marca_principal)
    marcas.extend([limpar_texto(v) for v in variacoes])

marcas = list(set(marcas))


# === 7. Função para detectar marca na descrição ===
def detectar_marca(descricao):
    desc_limpa = limpar_texto(descricao)

    # Verifica variações conhecidas primeiro
    for marca_padrao, variacoes in mapa_variacoes.items():
        for v in variacoes:
            if limpar_texto(v) in desc_limpa:
                return marca_padrao

    # Caso não encontre nas variações, busca direta na lista geral
    for marca in marcas:
        if marca and marca in desc_limpa:
            return marca

    return np.nan


df_filtrado = df.copy()

# === 8. Detectar e preencher marcas ausentes ===
df_filtrado["Marca Detectada"] = df_filtrado["Descrição"].apply(detectar_marca)

# Preenche apenas onde está vazio
df_filtrado["Marca"] = df_filtrado["Marca"].fillna(df_filtrado["Marca Detectada"])

df_filtrado["Marca"] = df_filtrado["Marca"].fillna("GENÉRICO")
# Atualiza no dataframe principal
df.update(df_filtrado)


# === 9. Salvar resultado ===
df.to_excel("produtos_com_marcas.xlsx", index=False)

# === 10. Relatório simples ===
logger.info("✅ Processamento concluído!")
logger.info(f"Total de produtos analisados: {len(df_filtrado)}")
logger.info(
    f"Marcas detectadas automaticamente: {df_filtrado['Marca Detectada'].notna().sum()}"
)

# Top 10 marcas mais detectadas
logger.info("\nTop marcas detectadas:")
logger.info(df_filtrado["Marca Detectada"].value_counts().head(10))
