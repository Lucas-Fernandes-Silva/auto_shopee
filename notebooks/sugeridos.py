# Script Python — Sugerir descrições menores que 30 caracteres usando OpenAI API
import os
import time

import pandas as pd
from openai import OpenAI

# =========================================================
# CONFIGURAÇÕES
# =========================================================

ARQUIVO_ENTRADA = "/home/lucas-silva/auto_shopee/notebooks/produtos_com_validacao.csv"
ARQUIVO_SAIDA = "produtos_descricoes_ajustadas.csv"

# Modelo OpenAI
MODELO = "gpt-4.1-mini"

# Quantidade de linhas por salvamento automático
SALVAR_A_CADA = 20

# =========================================================
# OPENAI
# =========================================================

# Defina sua chave:
# Linux/Mac:
# export OPENAI_API_KEY="sua_chave"
#
# Windows PowerShell:
# setx OPENAI_API_KEY "sua_chave"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY não encontrada nas variáveis de ambiente."
    )

# =========================================================
# FUNÇÃO PARA GERAR NOME REDUZIDO
# =========================================================


def gerar_nome_curto(descricao_original):
    """
    Gera uma descrição com até 30 caracteres
    sem perder o sentido principal do produto.
    """

    prompt = f"""
Você é especialista em títulos de produtos para marketplace.

Regras:
- Retorne APENAS o novo nome.
- Máximo de 30 caracteres.
- Não use aspas.
- Não invente informações.
- Preserve o sentido principal do produto.
- Abrevie de forma inteligente.
- Sem cortar informações
- (Exemplo)

- O nome precisa continuar claro.

Produto:
{descricao_original}
"""

    try:
        response = client.chat.completions.create(
            model=MODELO,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "Você cria nomes curtos para produtos.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        nome = response.choices[0].message.content.strip()

        # Segurança extra
        nome = nome.replace('"', "")
        nome = nome.replace("'", "")

        if len(nome) > 30:
            nome = nome[:30].strip()

        return nome

    except Exception as erro:
        print(f"Erro ao gerar nome: {erro}")
        return "ERRO_OPENAI"


# =========================================================
# CARREGAR PLANILHA
# =========================================================

print("Carregando arquivo...")

df = pd.read_csv(ARQUIVO_ENTRADA)

# =========================================================
# FILTRO
# =========================================================

# Produtos pai:
# Código Pai vazio
# Descrição maior que 30 caracteres

mask_produto_pai = df["Código Pai"].isna()
mask_maior_30 = (
    df["Descrição"].fillna("").astype(str).str.len() > 30
)

mask = mask_produto_pai & mask_maior_30

produtos_filtrados = df[mask].copy()

print(f"Produtos encontrados: {len(produtos_filtrados)}")

# =========================================================
# CRIAR COLUNA
# =========================================================

NOME_COLUNA = "Descricao_Sugerida_OpenAI"

if NOME_COLUNA not in df.columns:
    df[NOME_COLUNA] = ""

# =========================================================
# PROCESSAMENTO
# =========================================================

for i, indice in enumerate(produtos_filtrados.index, start=1):
    descricao = str(df.at[indice, "Descrição"])

    print("=" * 80)
    print(f"[{i}/{len(produtos_filtrados)}]")
    print(f"Descrição original: {descricao}")
    print(f"Tamanho atual: {len(descricao)}")

    nome_sugerido = gerar_nome_curto(descricao)

    print(f"Sugestão: {nome_sugerido}")
    print(f"Tamanho sugestão: {len(nome_sugerido)}")

    df.at[indice, NOME_COLUNA] = nome_sugerido

    # Salvamento automático
    if i % SALVAR_A_CADA == 0:
        df.to_csv(ARQUIVO_SAIDA, index=False)
        print(f"Salvo parcial: {ARQUIVO_SAIDA}")

    # Pequena pausa para evitar excesso de requisições
    time.sleep(0.5)

# =========================================================
# SALVAR FINAL
# =========================================================

print("Salvando resultado final...")

df.to_csv(ARQUIVO_SAIDA, index=False)

print("=" * 80)
print("PROCESSO FINALIZADO")
print(f"Arquivo salvo: {ARQUIVO_SAIDA}")
