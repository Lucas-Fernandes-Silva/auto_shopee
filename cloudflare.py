import json
import mimetypes
import os
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
import pandas as pd
from dotenv import load_dotenv
from PIL import Image
from tqdm import tqdm
from rapidfuzz import process, fuzz
# =========================
# CONFIGURAÇÕES
# =========================

CAMINHO_PLANILHA = "/home/lucas-silva/auto_shopee/planilhas/outputs/download.xlsx"
PASTA_IMAGENS = "/home/lucas-silva/auto_shopee/src/extract/img_extract/imagens_otimizadas"

COLUNA_DESCRICAO = "Descrição"

COLUNAS_IMAGENS = ["Url_Imagem1.0", "Url_Imagem2.0", "Url_Imagem3.0"]

EXTENSOES_VALIDAS = (".jpg", ".jpeg", ".png", ".webp")

MAX_WORKERS = 8
MAX_TENTATIVAS = 3

REDIMENSIONAR = True
TAMANHO_MAXIMO = (2000, 2000)
QUALIDADE_JPG = 85

PASTA_OTIMIZADAS = "imagens_otimizadas"
CHECKPOINT_FILE = "checkpoint_upload_r2.json"


CAMINHO_ENV = "/home/lucas-silva/auto_shopee/dados/.env.py"

# =========================
# CHECKPOINT
# =========================

lock_checkpoint = threading.Lock()


def carregar_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"uploads": {}}


def salvar_checkpoint(checkpoint):
    with lock_checkpoint:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)


# =========================
# NORMALIZAÇÃO
# =========================


def normalizar(texto):
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^A-Z0-9]+", "_", texto)
    texto = re.sub(r"_+", "_", texto)
    return texto.strip("_")


def extrair_info_imagem(nome_arquivo):
    nome_sem_extensao = os.path.splitext(nome_arquivo)[0]
    match = re.match(r"^([1-3])_(.+)$", nome_sem_extensao)

    if not match:
        return None, None

    ordem = int(match.group(1))
    chave = normalizar(match.group(2))

    return ordem, chave


# =========================
# IMAGEM
# =========================

def buscar_chave_imagem(chave_produto, imagens_por_chave, limite=92):
    # 1. tenta bater exatamente
    if chave_produto in imagens_por_chave:
        return chave_produto, 100

    # 2. tenta por prefixo
    for chave_img in imagens_por_chave.keys():
        if chave_produto.startswith(chave_img) or chave_img.startswith(chave_produto):
            return chave_img, 98

    # 3. tenta similaridade
    resultado = process.extractOne(
        chave_produto,
        imagens_por_chave.keys(),
        scorer=fuzz.ratio
    )

    if resultado:
        chave_encontrada, score, _ = resultado

        if score >= limite:
            return chave_encontrada, score

    return None, 0


def otimizar_imagem(caminho_original, nome_arquivo):
    if not REDIMENSIONAR:
        return caminho_original, nome_arquivo

    os.makedirs(PASTA_OTIMIZADAS, exist_ok=True)

    nome_sem_ext = os.path.splitext(nome_arquivo)[0]
    novo_nome = f"{nome_sem_ext}.jpg"
    novo_caminho = os.path.join(PASTA_OTIMIZADAS, novo_nome)

    if os.path.exists(novo_caminho):
        return novo_caminho, novo_nome

    try:
        img = Image.open(caminho_original).convert("RGB")
        img.thumbnail(TAMANHO_MAXIMO)
        img.save(novo_caminho, "JPEG", quality=QUALIDADE_JPG, optimize=True)
        return novo_caminho, novo_nome

    except Exception as e:
        print(f"Erro ao otimizar imagem {nome_arquivo}: {e}")
        return None, None


def listar_imagens():
    imagens = {}
    imagens_invalidas = []

    for arquivo in os.listdir(PASTA_IMAGENS):
        if not arquivo.lower().endswith(EXTENSOES_VALIDAS):
            continue

        ordem, chave = extrair_info_imagem(arquivo)

        if ordem is None:
            imagens_invalidas.append(arquivo)
            continue

        caminho_original = os.path.join(PASTA_IMAGENS, arquivo)
        caminho_final, arquivo_final = otimizar_imagem(caminho_original, arquivo)

        if not caminho_final:
            imagens_invalidas.append(arquivo)
            continue

        imagens.setdefault(chave, []).append(
            {
                "ordem": ordem,
                "arquivo_original": arquivo,
                "arquivo": arquivo_final,
                "caminho": caminho_final,
                "chave": chave,
            }
        )

    for chave in imagens:
        imagens[chave] = sorted(imagens[chave], key=lambda x: x["ordem"])[:3]

    return imagens, imagens_invalidas


# =========================
# R2
# =========================


def conectar_r2():

    load_dotenv(dotenv_path=CAMINHO_ENV)
    access_key = os.getenv("R2_ACCESS_KEY", "")
    secret_key = os.getenv("R2_SECRET_KEY", "")
    endpoint = os.getenv("R2_ENDPOINT", "")
    bucket = os.getenv("R2_BUCKET", "")
    public_url = os.getenv("R2_PUBLIC_URL", "")

    if not all([access_key, secret_key, endpoint, bucket, public_url]):
        raise RuntimeError("Confira se o arquivo .env está preenchido corretamente.")

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )

    return s3, bucket, public_url.rstrip("/")


def upload_com_retry(s3, bucket, imagem, checkpoint, public_url):
    object_key = imagem["arquivo"]

    if object_key in checkpoint["uploads"]:
        return {
            "ok": True,
            "arquivo": object_key,
            "url": checkpoint["uploads"][object_key],
            "status": "checkpoint",
        }

    content_type, _ = mimetypes.guess_type(imagem["caminho"])

    extra_args = {"ContentType": content_type or "image/jpeg"}

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            s3.upload_file(
                Filename=imagem["caminho"], Bucket=bucket, Key=object_key, ExtraArgs=extra_args
            )

            url = f"{public_url}/{object_key}"

            with lock_checkpoint:
                checkpoint["uploads"][object_key] = url

            salvar_checkpoint(checkpoint)

            return {"ok": True, "arquivo": object_key, "url": url, "status": "enviado"}

        except Exception as e:
            if tentativa == MAX_TENTATIVAS:
                return {"ok": False, "arquivo": object_key, "url": "", "status": f"erro: {e}"}

            time.sleep(2 * tentativa)


# =========================
# PRINCIPAL
# =========================


def main():
    print("Lendo planilha...")
    df = pd.read_excel(CAMINHO_PLANILHA)

    if COLUNA_DESCRICAO not in df.columns:
        raise ValueError(f"Coluna não encontrada: {COLUNA_DESCRICAO}")

    for col in COLUNAS_IMAGENS:
        if col not in df.columns:
            df[col] = ""

    print("Lendo e preparando imagens...")
    imagens_por_chave, imagens_invalidas = listar_imagens()

    print("Conectando ao Cloudflare R2...")
    s3, bucket, public_url = conectar_r2()

    checkpoint = carregar_checkpoint()

    tarefas_upload = {}
    produtos_sem_imagem = []
    imagens_usadas = set()

    print("Montando lista de uploads...")

    for idx, row in df.iterrows():
        descricao = row[COLUNA_DESCRICAO]

        if pd.isna(descricao) or str(descricao).strip() == "":
            continue

        chave_produto = normalizar(descricao)
        chave_encontrada, score = buscar_chave_imagem(chave_produto, imagens_por_chave)

        if chave_encontrada:
            imagens_produto = imagens_por_chave.get(chave_encontrada, [])
        else:
            imagens_produto = []

        if not imagens_produto:
            produtos_sem_imagem.append(
                {"linha_excel": list(df.index).index(idx) + 2, "descricao": descricao, "chave_procurada": chave_produto,  "melhor_chave_encontrada": chave_encontrada, "score": score}
            )
            continue


        for imagem in imagens_produto:
            imagens_usadas.add(imagem["arquivo"])
            tarefas_upload[imagem["arquivo"]] = imagem

    print(f"Total de imagens para considerar: {len(tarefas_upload)}")
    print(f"Já no checkpoint: {len(checkpoint['uploads'])}")

    resultados_upload = {}

    print("Fazendo upload paralelo...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(upload_com_retry, s3, bucket, imagem, checkpoint, public_url): nome
            for nome, imagem in tarefas_upload.items()
        }

        for future in tqdm(as_completed(futures), total=len(futures)):
            nome = futures[future]
            resultado = future.result()
            resultados_upload[nome] = resultado

    print("Preenchendo URLs na planilha...")

    for idx, row in df.iterrows():
        descricao = row[COLUNA_DESCRICAO]

        if pd.isna(descricao) or str(descricao).strip() == "":
            continue

        chave_produto = normalizar(descricao)
        imagens_produto = imagens_por_chave.get(chave_produto, [])

        for pos, col in enumerate(COLUNAS_IMAGENS):
            if pos < len(imagens_produto):
                nome_arquivo = imagens_produto[pos]["arquivo"]
                resultado = resultados_upload.get(nome_arquivo)

                if resultado and resultado["ok"]:
                    df.at[idx, col] = resultado["url"]
                else:
                    df.at[idx, col] = ""
            else:
                df.at[idx, col] = ""

    imagens_sem_produto = []

    for chave, lista in imagens_por_chave.items():
        for imagem in lista:
            if imagem["arquivo"] not in imagens_usadas:
                imagens_sem_produto.append({"arquivo": imagem["arquivo"], "chave": chave})

    erros_upload = [r for r in resultados_upload.values() if not r["ok"]]

    df.to_excel("produtos_com_urls_imagens.xlsx", index=False)

    pd.DataFrame(produtos_sem_imagem).to_excel("relatorio_produtos_sem_imagem.xlsx", index=False)

    pd.DataFrame(imagens_sem_produto).to_excel("relatorio_imagens_sem_produto.xlsx", index=False)

    pd.DataFrame(imagens_invalidas, columns=["arquivo"]).to_excel(
        "relatorio_imagens_invalidas.xlsx", index=False
    )

    pd.DataFrame(erros_upload).to_excel("relatorio_erros_upload.xlsx", index=False)

    print("Finalizado!")
    print("Gerado: produtos_com_urls_imagens.xlsx")
    print("Gerado: relatorio_produtos_sem_imagem.xlsx")
    print("Gerado: relatorio_imagens_sem_produto.xlsx")
    print("Gerado: relatorio_imagens_invalidas.xlsx")
    print("Gerado: relatorio_erros_upload.xlsx")


if __name__ == "__main__":
    main()
