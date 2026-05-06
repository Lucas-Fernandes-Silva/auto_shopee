import json
import os
import time

import pandas as pd
from openai import OpenAI

# =========================
# CONFIGURAÇÕES
# =========================

ARQUIVO_ENTRADA = "/home/lucas-silva/auto_shopee/planilhas/outputs/PRODUTOS.xlsx"
ABA = "Sheet1"
ARQUIVO_SAIDA = "produtos_com_descricoes.xlsx"
CHECKPOINT_JSON = "checkpoint_descricoes.json"

COLUNA_GRUPO = "grupo_id"
COLUNA_DESCRICAO_FINAL = "descricao_ia"

TAMANHO_LOTE = 10
MODELO = "gpt-4.1-mini"

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("Defina a variável OPENAI_API_KEY antes de rodar o script.")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =========================
# CHECKPOINT
# =========================


def carregar_checkpoint():
    if os.path.exists(CHECKPOINT_JSON):
        with open(CHECKPOINT_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_checkpoint(dados):
    with open(CHECKPOINT_JSON, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


# =========================
# PREPARAR GRUPOS
# =========================


def montar_grupos(df):
    grupos = []

    for grupo_id, grupo in df.groupby(COLUNA_GRUPO, dropna=False):
        if pd.isna(grupo_id):
            continue

        itens = []

        for _, row in grupo.iterrows():
            itens.append(
                {
                    "codigo_produto": str(row.get("Codigo Produto", "")),
                    "descricao_original": str(row.get("Descrição", "")),
                    "descricao_limpa": str(row.get("descricao_limpa", "")),
                    "nome_base": str(row.get("nome_base", "")),
                    "variacao": str(row.get("variacao", "")),
                    "marca": str(row.get("Marca", "")),
                    "categoria": str(row.get("Categoria", "")),
                    "peso_kg": str(row.get("Peso", "")),
                    "largura_cm": str(row.get("Largura", "")),
                    "altura_cm": str(row.get("Altura", "")),
                    "comprimento_cm": str(row.get("Comprimento", "")),
                }
            )

        nome_base = ""
        if "nome_base" in grupo.columns and grupo["nome_base"].notna().any():
            nome_base = str(grupo["nome_base"].dropna().iloc[0])

        grupos.append({"grupo_id": str(grupo_id), "nome_base": nome_base, "itens": itens})

    return grupos


# =========================
# OPENAI
# =========================


def criar_prompt(lote):
    return f"""
Você é especialista em cadastro de produtos para marketplace.

Crie uma descrição comercial para cada grupo de produto abaixo.

Regras:
- Retorne APENAS JSON válido.
- Não invente informações técnicas que não estejam nos dados.
- A descrição deve servir para todos os itens do mesmo grupo.
- Se houver variações, mencione que o produto possui variações disponíveis.
- Não cite código do produto.
- Não cite preço.
- Use português do Brasil.
- Texto claro, profissional e vendedor.
- Evite promessas exageradas.
- Estrutura da descrição:
  1. Parágrafo curto de apresentação
  2. Lista de características
  3. Sugestão de uso
  4. Observação sobre variações, quando existir

Formato obrigatório:
[
  {{
    "grupo_id": "G00000",
    "descricao": "texto da descrição"
  }}
]

Grupos:
{json.dumps(lote, ensure_ascii=False, indent=2)}
"""


def gerar_descricoes_lote(lote):
    prompt = criar_prompt(lote)

    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[
            {
                "role": "system",
                "content": "Você gera descrições de produtos para marketplace em JSON válido.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    conteudo = (resposta.choices[0].message.content or "").strip()

    try:
        return json.loads(conteudo)
    except json.JSONDecodeError:
        print("Erro ao converter resposta em JSON.")
        print(conteudo)
        raise


# =========================
# PROCESSAMENTO
# =========================


def processar():
    df = pd.read_excel(ARQUIVO_ENTRADA, sheet_name=ABA)

    if COLUNA_DESCRICAO_FINAL not in df.columns:
        df[COLUNA_DESCRICAO_FINAL] = ""

    checkpoint = carregar_checkpoint()
    grupos = montar_grupos(df)

    grupos_pendentes = [g for g in grupos if g["grupo_id"] not in checkpoint]

    total_grupos = len(grupos_pendentes)
    total_lotes = (total_grupos + TAMANHO_LOTE - 1) // TAMANHO_LOTE

    print(f"Total de grupos na planilha: {len(grupos)}")
    print(f"Grupos já processados: {len(checkpoint)}")
    print(f"Grupos pendentes: {total_grupos}")
    print(f"Tamanho do lote: {TAMANHO_LOTE}")
    print(f"Total de lotes pendentes: {total_lotes}")

    for i in range(0, total_grupos, TAMANHO_LOTE):
        lote_numero = (i // TAMANHO_LOTE) + 1
        lote = grupos_pendentes[i : i + TAMANHO_LOTE]

        processados_antes = i
        faltando_antes = total_grupos - processados_antes
        porcentagem_antes = (processados_antes / total_grupos) * 100 if total_grupos else 100

        print("\n" + "=" * 60)
        print(f"LOTE {lote_numero}/{total_lotes}")
        print(f"Grupos neste lote: {len(lote)}")
        print(f"Processados antes deste lote: {processados_antes}/{total_grupos}")
        print(f"Faltando antes deste lote: {faltando_antes}")
        print(f"Progresso: {porcentagem_antes:.1f}%")
        print("=" * 60)

        print("Enviando para API...")

        descricoes = gerar_descricoes_lote(lote)

        print(f"API respondeu com {len(descricoes)} descrições.")

        for item in descricoes:
            grupo_id = str(item["grupo_id"])
            descricao = item["descricao"]
            checkpoint[grupo_id] = descricao

        salvar_checkpoint(checkpoint)

        df[COLUNA_DESCRICAO_FINAL] = (
            df[COLUNA_GRUPO].astype(str).map(checkpoint).fillna(df[COLUNA_DESCRICAO_FINAL])
        )

        df.to_excel(ARQUIVO_SAIDA, index=False)

        processados_depois = min(i + len(lote), total_grupos)
        faltando_depois = total_grupos - processados_depois
        porcentagem_depois = (processados_depois / total_grupos) * 100 if total_grupos else 100

        print(f"Arquivo salvo: {ARQUIVO_SAIDA}")
        print(f"Processados agora: {processados_depois}/{total_grupos}")
        print(f"Faltando agora: {faltando_depois}")
        print(f"Progresso atual: {porcentagem_depois:.1f}%")

        time.sleep(1)

    print("\nFinalizado com sucesso!")


if __name__ == "__main__":
    processar()
