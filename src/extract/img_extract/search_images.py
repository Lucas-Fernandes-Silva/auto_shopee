# search_images.py
import json
import time

import pandas as pd
import requests
from tqdm import tqdm

# CONFIG
EXCEL_PATH = "planilhas/outputs/final.xlsx"
API_KEYS_FILE = "notebooks/api_keys.json"
SEARCH_ENGINE_ID = "532347d8c03cc4861"
IMAGES_PER_PRODUCT = 3
SLEEP_TIME = 1
CSV_OUT = "review_images.csv"
HTML_OUT = "review_images.html"

def carregar_chaves():
    data = json.load(open(API_KEYS_FILE, "r"))
    keys = data.get("keys", [])
    if not keys:
        raise ValueError("Arquivo de chaves vazio.")
    return keys

def buscar_imagens(query, api_key, cx, num=3):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": query, "key": api_key, "cx": cx, "searchType": "image", "num": num}
    r = requests.get(url, params=params, timeout=10)
    data = r.json() if r.content else {}
    if r.status_code == 403 or "error" in data:
        msg = data.get("error", {}).get("message", "403/quota error")
        raise Exception(msg)
    r.raise_for_status()
    return data.get("items", [])

def gerar_html_preview(df):
    html = """
    <html>
    <head><meta charset="UTF-8">
    <style>
        body { font-family: Arial; }
        img { border:1px solid #ccc; margin:4px; }
        table { border-collapse: collapse; width:100%; }
        th, td { border:1px solid #ccc; padding:6px; }
        th { background:#eee; }
    </style>
    </head><body>
    <h2>Revisão de Imagens</h2>
    <p>Edite o arquivo <b>review_images.csv</b> e marque keep_1, keep_2, keep_3 como TRUE/FALSE.</p>
    <table>
        <tr>
            <th>Código</th>
            <th>Descrição</th>
            <th>Imagem 1</th>
            <th>Imagem 2</th>
            <th>Imagem 3</th>
        </tr>
    """

    for _, row in df.iterrows():
        html += f"""
        <tr>
            <td>{row["Codigo Produto"]}</td>
            <td>{row["Descrição"]}</td>
            <td><img src="{row['url_1']}" width="200"></td>
            <td><img src="{row['url_2']}" width="200"></td>
            <td><img src="{row['url_3']}" width="200"></td>
        </tr>
        """

    html += "</table></body></html>"

    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("📄 Thumbnails gerados em:", HTML_OUT)


if __name__ == "__main__":
    df = pd.read_excel(EXCEL_PATH)

    # Garantir coluna Codigo Produto
    if "Codigo Produto" not in df.columns:
        df = df.reset_index().rename(columns={"index": "Codigo Produto"})

    api_keys = carregar_chaves()
    key_idx = 0

    rows = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Buscando imagens"):
        codigo = int(row["Codigo Produto"])
        descricao = str(row["Descrição"])

        images = []

        attempts = 0
        while attempts < len(api_keys) and len(images) < IMAGES_PER_PRODUCT:
            key = api_keys[key_idx]
            try:
                items = buscar_imagens(descricao, key, SEARCH_ENGINE_ID, IMAGES_PER_PRODUCT)
                images = [it.get("link") for it in items][:IMAGES_PER_PRODUCT]
                break
            except Exception as e:
                if "quota" in str(e).lower() or "403" in str(e):
                    key_idx = (key_idx + 1) % len(api_keys)
                    attempts += 1
                    time.sleep(1)
                else:
                    print("Erro:", e)
                    break

        images += [None] * (IMAGES_PER_PRODUCT - len(images))
        r = {
            "Codigo Produto": codigo,
            "Descrição": descricao,
            "url_1": images[0],
            "url_2": images[1],
            "url_3": images[2],
            "keep_1": False,
            "keep_2": False,
            "keep_3": False,
        }
        rows.append(r)
        time.sleep(SLEEP_TIME)

    review_df = pd.DataFrame(rows)
    review_df.to_csv(CSV_OUT, index=False)
    print("📄 Arquivo de revisão salvo em:", CSV_OUT)

    gerar_html_preview(review_df)
