#!/usr/bin/env python3
"""
AUTO SHOPEE IMAGE PIPELINE - Versão Final e Corrigida
=====================================================

Pipeline completo para:
1) Buscar imagens via Google API
2) Gerar arquivo de revisão (CSV + HTML com thumbnails)
3) Baixar somente as imagens aprovadas
4) Otimizar e enviar ao Cloudinary
5) Preencher URLs das imagens no Excel final

Totalmente reescrito e corrigido:
- NÃO usa choose_first_existing() com strings
- Caminhos absolutos funcionando 100%
- Pausa obrigatória para revisão (modo B)
- 3 imagens por produto
"""

import json
import os
import re
import time

import cloudinary
import cloudinary.uploader
import pandas as pd
import requests
from PIL import Image, ImageOps
from tqdm import tqdm

# ==========================================================
# CONFIGURAÇÕES FIXAS DO LUCAS (estas paths estão corretas)
# ==========================================================

PRIORITY_BASE = "extract/img_extract"

EXCEL_PATH = "/home/lucas-silva/auto_shopee/planilhas/outputs/final.xlsx"
API_KEYS = "/home/lucas-silva/auto_shopee/src/extract/img_extract/api_keys.json"
CLOUDINARY_KEYS = "/home/lucas-silva/auto_shopee/src/extract/img_extract/cloudinary_config.json"

SEARCH_ENGINE_ID = "532347d8c03cc4861"
IMAGES_PER_PRODUCT = 3
SLEEP_TIME = 1

REVIEW_CSV = "review_images.csv"
REVIEW_HTML = "review_images.html"

DOWNLOAD_FOLDER_DEFAULTS = ["notebooks/imagens", "imagens", "images"]
OPT_FOLDER_DEFAULTS = ["notebooks/imagens_otimizadas", "imagens_otimizadas", "images_opt"]

OUTPUT_URLS_CSV = "urls_cloudinary.csv"
MERGE_OUTPUT = "final_com_urls.xlsx"


# ==========================================================
# FUNÇÕES UTILITÁRIAS
# ==========================================================

def log(msg):
    print(msg)


def find_folder(defaults):
    """ Retorna a primeira pasta válida ou cria a primeira """
    for d in defaults:
        if os.path.isdir(d):
            return d
    os.makedirs(defaults[0], exist_ok=True)
    return defaults[0]


def carregar_chaves(filepath):
    """ Carrega API KEYS de um único arquivo """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Arquivo de chaves não encontrado: {filepath}")

    data = json.load(open(filepath, "r", encoding="utf-8"))
    keys = data.get("keys") or data.get("api_keys")
    if not isinstance(keys, list) or not keys:
        raise ValueError(f"Arquivo {filepath} não contém lista 'keys' válida.")

    log(f"✔ API Keys carregadas de: {filepath}")
    return keys


def configure_cloudinary(filepath):
    """ Configura Cloudinary de arquivo JSON único """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Arquivo cloudinary_config.json não encontrado: {filepath}")

    cfg = json.load(open(filepath, "r", encoding="utf-8"))

    cloudinary.config(
        cloud_name=cfg.get("cloud_name"),
        api_key=cfg.get("api_key"),
        api_secret=cfg.get("api_secret"),
        secure=True
    )

    log(f"✔ Cloudinary configurado via {filepath}")


def buscar_imagens_google(query, api_key, cx, num=3):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cx,
        "searchType": "image",
        "num": num
    }
    r = requests.get(url, params=params, timeout=10)

    if r.status_code == 403:
        raise Exception("403 / Quota da API esgotada")

    data = r.json() if r.content else {}
    if "error" in data:
        raise Exception(data["error"]["message"])

    return [it["link"] for it in data.get("items", [])[:num]]


def gerar_html_preview(df, html_path=REVIEW_HTML):
    html = """
    <html><head><meta charset="utf-8"/>
    <style>
        body { font-family: Arial; }
        img { max-width: 240px; border:1px solid #ccc; margin:4px; }
        table { border-collapse: collapse; width:100%; }
        th,td { border:1px solid #ccc; padding:6px; }
        th { background:#f0f0f0; }
    </style>
    </head><body>
    <h2>Revisão de Imagens</h2>
    <p>Edite o arquivo <b>review_images.csv</b> e marque keep_1..keep_3 = True.</p>
    <table>
    <tr><th>Código</th><th>Descrição</th><th>Imagem 1</th><th>Imagem 2</th><th>Imagem 3</th></tr>
    """

    for _, r in df.iterrows():
        html += f"<tr><td>{r['Codigo Produto']}</td><td>{r['Descrição']}</td>"

        for i in range(1, 4):
            url = r.get(f"url_{i}")
            if url and isinstance(url, str) and url.strip():
                html += f"<td><img src='{url}'><br>{url}</td>"
            else:
                html += "<td><i>sem imagem</i></td>"

        html += "</tr>"

    html += "</table></body></html>"

    open(html_path, "w", encoding="utf-8").write(html)
    log(f"✔ HTML gerado: {html_path}")


# ==========================================================
# ETAPA 1 – Buscar imagens e gerar arquivos de revisão
# ==========================================================

def step_search_and_generate_review():
    if not os.path.isfile(EXCEL_PATH):
        raise FileNotFoundError(f"Excel não encontrado: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH)

    if "Codigo Produto" not in df.columns:
        df = df.reset_index().rename(columns={"index": "Codigo Produto"})

    api_keys = carregar_chaves(API_KEYS)

    rows = []
    key_idx = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Buscando imagens"):
        codigo = int(row["Codigo Produto"])
        descricao = str(row["Descrição"])

        imagens = []

        # Tentativa com troca inteligente de chaves
        while len(imagens) < IMAGES_PER_PRODUCT:
            api_key = api_keys[key_idx]
            try:
                imagens = buscar_imagens_google(descricao, api_key, SEARCH_ENGINE_ID, IMAGES_PER_PRODUCT)
                break
            except Exception as e:
                msg = str(e).lower()
                if "quota" in msg or "403" in msg:
                    key_idx = (key_idx + 1) % len(api_keys)
                else:
                    break

        imagens += [None] * (IMAGES_PER_PRODUCT - len(imagens))

        row_out = {"Codigo Produto": codigo, "Descrição": descricao}
        for i, img in enumerate(imagens, start=1):
            row_out[f"url_{i}"] = img
            row_out[f"keep_{i}"] = False

        rows.append(row_out)
        time.sleep(SLEEP_TIME)

    review_df = pd.DataFrame(rows)
    review_df.to_csv(REVIEW_CSV, index=False)
    gerar_html_preview(review_df)

    log("\n📝 Edite review_images.csv e marque TRUE nas imagens aprovadas.")
    log("Depois pressione ENTER no menu para continuar.")

    return REVIEW_CSV


# ==========================================================
# ETAPA 2 – Download apenas das imagens aprovadas
# ==========================================================

def step_download_images():
    download_folder = find_folder(DOWNLOAD_FOLDER_DEFAULTS)
    os.makedirs(download_folder, exist_ok=True)

    if not os.path.isfile(REVIEW_CSV):
        raise FileNotFoundError("review_images.csv não encontrado.")

    df = pd.read_csv(REVIEW_CSV).fillna("")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Baixando imagens"):
        codigo = int(row["Codigo Produto"])

        for i in range(1, 4):
            if str(row[f"keep_{i}"]).lower() not in ("true", "1"):
                continue

            url = row[f"url_{i}"]
            if not url:
                continue

            fname = f"{codigo}_{i}.jpg"
            dest = os.path.join(download_folder, fname)

            if os.path.exists(dest):
                continue

            try:
                r = requests.get(url, stream=True, timeout=12)
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                else:
                    log(f"Falha {r.status_code} ao baixar: {url}")

            except Exception as e:
                log(f"Erro ao baixar {url}: {e}")

    log("✔ Download concluído.")


# ==========================================================
# ETAPA 3 – Otimização + Upload Cloudinary
# ==========================================================

def step_upload_cloudinary():
    configure_cloudinary(CLOUDINARY_KEYS)

    download_folder = find_folder(DOWNLOAD_FOLDER_DEFAULTS)
    opt_folder = find_folder(OPT_FOLDER_DEFAULTS)
    os.makedirs(opt_folder, exist_ok=True)

    arquivos = [f for f in os.listdir(download_folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))]

    resultados = []

    for file in tqdm(arquivos, desc="Upload Cloudinary"):
        path_src = os.path.join(download_folder, file)
        path_opt = os.path.join(opt_folder, file)

        try:
            # otimização
            img = Image.open(path_src).convert("RGB")
            img_opt = ImageOps.pad(img, (1000, 1000), color=(255, 255, 255))
            img_opt.save(path_opt, optimize=True, quality=85)

            res = cloudinary.uploader.upload(
                path_opt,
                folder="imagens_otimizadas_marketplace",
                use_filename=True,
                unique_filename=False,
            )

            url = res["secure_url"].replace("/upload/", "/upload/f_auto,q_auto/")
            resultados.append({"arquivo": file, "url": url})

            pd.DataFrame(resultados).to_csv(OUTPUT_URLS_CSV, index=False)

        except Exception as e:
            log(f"Erro upload {file}: {e}")

    log("✔ Upload concluído. Arquivo:", OUTPUT_URLS_CSV) # type: ignore


# ==========================================================
# ETAPA 4 – Merge final das URLs no Excel
# ==========================================================

def step_merge_urls():
    if not os.path.isfile(EXCEL_PATH):
        raise FileNotFoundError(f"Excel não encontrado: {EXCEL_PATH}")

    if not os.path.isfile(OUTPUT_URLS_CSV):
        raise FileNotFoundError(OUTPUT_URLS_CSV)

    urls_df = pd.read_csv(OUTPUT_URLS_CSV)
    final_df = pd.read_excel(EXCEL_PATH)

    def parse_nome(file):
        m = re.match(r"(\d+)_(\d+)", file)
        if m:
            return int(m.group(1)), int(m.group(2))
        return None, None

    urls_df[["codigo", "num"]] = urls_df["arquivo"].apply(lambda x: pd.Series(parse_nome(x)))
    urls_df = urls_df.dropna()

    pivot = urls_df.pivot_table(index="codigo", columns="num", values="url", aggfunc="first")
    pivot = pivot[[1, 2, 3]]  # somente 3 imagens
    pivot.columns = ["Url_Imagem1", "Url_Imagem2", "Url_Imagem3"]

    final_df["codigo"] = final_df["Codigo Produto"]
    merged = final_df.merge(pivot, on="codigo", how="left")

    # Não sobrescrever existentes
    for col in ["Url_Imagem1", "Url_Imagem2", "Url_Imagem3"]:
        if col in final_df.columns:
            merged[col] = final_df[col].combine_first(merged[col])

    merged.drop(columns=["codigo"], inplace=True)
    merged.to_excel(MERGE_OUTPUT, index=False)

    log("✔ Merge final concluído:", MERGE_OUTPUT) # type: ignore


# ==========================================================
# MENU PRINCIPAL
# ==========================================================

def menu():
    while True:
        print("""
================ MENU AUTO SHOPEE =================
1 - Buscar imagens -> gerar CSV + HTML (revisão)
2 - Gerar HTML somente (se CSV já existe)
3 - Baixar imagens aprovadas
4 - Upload Cloudinary + otimização
5 - Merge final das URLs no Excel
6 - Executar TUDO (1 -> pausa -> 3 -> 4 -> 5)
0 - Sair
===================================================
""")
        c = input("Escolha: ").strip()

        if c == "1":
            step_search_and_generate_review()

        elif c == "2":
            if os.path.isfile(REVIEW_CSV):
                gerar_html_preview(pd.read_csv(REVIEW_CSV).fillna(""))
                log("HTML regenerado.")
            else:
                log("review_images.csv não existe. Use opção 1.")

        elif c == "3":
            step_download_images()

        elif c == "4":
            step_upload_cloudinary()

        elif c == "5":
            step_merge_urls()

        elif c == "6":
            step_search_and_generate_review()
            input("\n⏸  Revise o CSV e pressione ENTER para continuar...\n")
            step_download_images()
            step_upload_cloudinary()
            step_merge_urls()

        elif c == "0":
            print("Saindo...")
            break

        else:
            print("Opção inválida.")


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    menu()
