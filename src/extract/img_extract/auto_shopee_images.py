# #!/usr/bin/env python3
# """
# auto_shopee_images.py — versão final multithread

# Pipeline completo:
# 1. Busca imagens no Google (pula produtos com Url_Imagem já preenchido)
# 2. Gera review_images.csv + review_images.html com thumbnails
# 3. Baixa imagens aprovadas (keep_X) com MULTITHREAD
# 4. Otimiza + envia Cloudinary com MULTITHREAD
# 5. Merge final no Excel com preservação de URLs existentes
# """

# import json
# import os
# import re
# import time
# from concurrent.futures import ThreadPoolExecutor, as_completed

# import cloudinary
# import cloudinary.uploader
# import pandas as pd
# import requests
# from PIL import Image, ImageOps
# from tqdm import tqdm

# # ==========================
# # CONFIGURAÇÕES
# # ==========================

# EXCEL_PATH = "/home/lucas-silva/github/auto_shopee/planilhas/outputs/final.xlsx"
# API_KEYS = "/home/lucas-silva/github/auto_shopee/src/extract/img_extract/api_keys.json"
# CLOUDINARY_KEYS = "/home/lucas-silva/github/auto_shopee/src/extract/img_extract/cloudinary_config.json"

# SEARCH_ENGINE_ID = "532347d8c03cc4861"

# IMAGES_PER_PRODUCT = 3
# SLEEP_TIME = 1

# REVIEW_CSV = "review_images.csv"
# REVIEW_HTML = "review_images.html"
# OUTPUT_URLS_CSV = "urls_cloudinary.csv"
# MERGE_OUTPUT = "final_com_urls.xlsx"

# DOWNLOAD_FOLDER_DEFAULTS = ["imagens", "images", "img_extract/imagens"]
# OPT_FOLDER_DEFAULTS = ["imagens_otimizadas", "images_opt", "img_extract/imagens_otimizadas"]


# # ==========================
# # FUNÇÕES UTILITÁRIAS
# # ==========================

# def log(msg):
#     print(msg)


# def find_folder(folders):
#     for p in folders:
#         if os.path.isdir(p):
#             return p
#     os.makedirs(folders[0], exist_ok=True)
#     return folders[0]


# def carregar_chaves(path):
#     with open(path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     keys = data.get("keys") or data.get("api_keys")
#     if not keys:
#         raise ValueError("api_keys.json precisa conter {\"keys\": [..]}")
#     return keys


# def configure_cloudinary(path):
#     with open(path, "r", encoding="utf-8") as f:
#         cfg = json.load(f)
#     cloudinary.config(
#         cloud_name=cfg["cloud_name"],
#         api_key=cfg["api_key"],
#         api_secret=cfg["api_secret"],
#         secure=True
#     )
#     log("✔ Cloudinary configurado")


# def buscar_imagens_google(query, api_key, cx, num=IMAGES_PER_PRODUCT):
#     url = "https://www.googleapis.com/customsearch/v1"
#     params = {
#         "q": query,
#         "key": api_key,
#         "cx": cx,
#         "searchType": "image",
#         "num": num
#     }
#     r = requests.get(url, params=params, timeout=10)
#     if r.status_code == 403:
#         raise Exception("403 / Rate limit / Quota")
#     data = r.json() if r.content else {}
#     items = data.get("items", []) or []
#     return [i.get("link") for i in items[:num]]


# # ==========================
# # PREVIEW HTML
# # ==========================

# def gerar_html_preview(df):
#     headers = "".join(f"<th>Imagem {i}</th>" for i in range(1, IMAGES_PER_PRODUCT + 1))

#     html = f"""
#     <!doctype html>
#     <html><head><meta charset="utf-8">
#     <style>
#         body {{ font-family: Arial }}
#         table {{ border-collapse: collapse; width: 100% }}
#         th, td {{ border: 1px solid #ccc; padding: 6px }}
#         img {{ max-width: 200px; max-height: 150px; border: 1px solid #999 }}
#         .url {{ font-size: 11px; color: #555; word-break: break-all }}
#     </style>
#     </head>
#     <body>
#     <h2>Revisão de Imagens</h2>
#     <p>Edite <b>{REVIEW_CSV}</b> marcando keep_X = True para as imagens aprovadas.</p>
#     <table>
#         <tr><th>Código</th><th>Descrição</th>{headers}</tr>
#     """

#     for _, r in df.iterrows():
#         html += f"<tr><td>{r['Codigo Produto']}</td><td>{r['Descrição']}</td>"
#         for i in range(1, IMAGES_PER_PRODUCT + 1):
#             url = r.get(f"url_{i}")
#             if url and isinstance(url, str):
#                 html += f"<td><img src='{url}' /><div class='url'>{url}</div></td>"
#             else:
#                 html += "<td><i>sem imagem</i></td>"
#         html += "</tr>"

#     html += "</table></body></html>"

#     with open(REVIEW_HTML, "w", encoding="utf-8") as f:
#         f.write(html)

#     log(f"✔ Preview HTML gerado: {REVIEW_HTML}")


# # ==========================
# # 1 — BUSCAR IMAGENS
# # ==========================

# def step_search_and_generate_review():
#     df = pd.read_excel(EXCEL_PATH)

#     if "Codigo Produto" not in df.columns:
#         df = df.reset_index().rename(columns={"index": "Codigo Produto"})

#     image_columns = [c for c in df.columns if c.startswith("Url_Imagem")]

#     keys = carregar_chaves(API_KEYS)
#     key_idx = 0

#     out_rows = []

#     for _, row in tqdm(df.iterrows(), total=len(df), desc="Buscando imagens"):
#         codigo = int(row["Codigo Produto"])
#         descricao = str(row.get("Descrição", "")).strip()

#         # se já tem qualquer imagem → NÃO busca
#         if any(str(row.get(c, "")).strip() for c in image_columns):
#             r = {"Codigo Produto": codigo, "Descrição": descricao}
#             for i in range(1, IMAGES_PER_PRODUCT + 1):
#                 r[f"url_{i}"] = None
#                 r[f"keep_{i}"] = False
#             out_rows.append(r)
#             continue

#         # busca imagens
#         imgs = []
#         tentativas = 0
#         while tentativas < len(keys):
#             try:
#                 api_key = keys[key_idx]
#                 imgs = buscar_imagens_google(descricao, api_key, SEARCH_ENGINE_ID)
#                 break
#             except Exception:
#                 key_idx = (key_idx + 1) % len(keys)
#                 tentativas += 1

#         imgs += [None] * (IMAGES_PER_PRODUCT - len(imgs))

#         r = {"Codigo Produto": codigo, "Descrição": descricao}
#         for i in range(1, IMAGES_PER_PRODUCT + 1):
#             r[f"url_{i}"] = imgs[i - 1]
#             r[f"keep_{i}"] = False
#         out_rows.append(r)

#         time.sleep(SLEEP_TIME)

#     review_df = pd.DataFrame(out_rows)
#     review_df.to_csv(REVIEW_CSV, index=False)
#     gerar_html_preview(review_df)

#     log("📝 Revise o CSV e o HTML, marque keep_X = True e volte ao terminal.")


# # ==========================
# # 2 — DOWNLOAD MULTITHREAD
# # ==========================

# def download_single(url, fpath):
#     try:
#         r = requests.get(url, stream=True, timeout=15)
#         if r.status_code == 200:
#             with open(fpath, "wb") as f:
#                 for chunk in r.iter_content(1024):
#                     f.write(chunk)
#             return True
#         return False
#     except:
#         return False


# def step_download_images(max_workers=10):
#     df = pd.read_csv(REVIEW_CSV).fillna("")

#     folder = find_folder(DOWNLOAD_FOLDER_DEFAULTS)
#     os.makedirs(folder, exist_ok=True)

#     tasks = []

#     for _, r in df.iterrows():
#         try:
#             codigo = int(r["Codigo Produto"])
#         except:
#             continue

#         for i in range(1, IMAGES_PER_PRODUCT + 1):
#             if str(r.get(f"keep_{i}", "")).lower() not in ("true", "1", "t", "yes", "y"):
#                 continue

#             url = r.get(f"url_{i}", "")
#             if not url:
#                 continue

#             fname = f"{codigo}_{i}.jpg"
#             fpath = os.path.join(folder, fname)

#             if os.path.exists(fpath):
#                 continue

#             tasks.append((url, fpath))

#     log(f"🚀 Baixando {len(tasks)} imagens com {max_workers} threads...")

#     with ThreadPoolExecutor(max_workers=max_workers) as pool:
#         futures = [
#             pool.submit(download_single, url, fpath)
#             for url, fpath in tasks
#         ]

#         for _ in tqdm(as_completed(futures), total=len(futures), desc="Downloads"):
#             pass

#     log("✔ Downloads completos.")


# # ==========================
# # 3 — UPLOAD MULTITHREAD
# # ==========================

# def upload_single(file, upload_folder, opt_folder):
#     try:
#         src = os.path.join(upload_folder, file)
#         opt_path = os.path.join(opt_folder, file)

#         img = Image.open(src).convert("RGB")
#         img_opt = ImageOps.pad(
#             img, (1000, 1000),
#             color=(255, 255, 255),
#             method=Image.Resampling.LANCZOS
#         )
#         img_opt.save(opt_path, optimize=True, quality=85)

#         res = cloudinary.uploader.upload(
#             opt_path,
#             folder="imagens_otimizadas_marketplace",
#             use_filename=True,
#             unique_filename=False
#         )

#         url = res.get("secure_url", "")
#         if url:
#             url = url.replace("/upload/", "/upload/f_auto,q_auto/")
#             return file, url
#         return file, None

#     except Exception:
#         return file, None


# def step_upload_cloudinary(max_workers=8):
#     configure_cloudinary(CLOUDINARY_KEYS)

#     upload_folder = find_folder(DOWNLOAD_FOLDER_DEFAULTS)
#     opt_folder = find_folder(OPT_FOLDER_DEFAULTS)
#     os.makedirs(opt_folder, exist_ok=True)

#     files = [
#         f for f in os.listdir(upload_folder)
#         if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
#     ]

#     resultados = []

#     log(f"🚀 Upload Cloudinary multithread ({max_workers} threads)")

#     with ThreadPoolExecutor(max_workers=max_workers) as pool:
#         futures = [
#             pool.submit(upload_single, f, upload_folder, opt_folder)
#             for f in files
#         ]

#         for future in tqdm(as_completed(futures), total=len(futures), desc="Uploads"):
#             file, url = future.result()
#             if url:
#                 resultados.append({"arquivo": file, "url": url})

#     pd.DataFrame(resultados).to_csv(OUTPUT_URLS_CSV, index=False)
#     log(f"✔ Upload completo. CSV salvo: {OUTPUT_URLS_CSV}")


# # ==========================
# # 4 — MERGE FINAL
# # ==========================

# def step_merge_urls():
#     df = pd.read_excel(EXCEL_PATH)
#     urls = pd.read_csv(OUTPUT_URLS_CSV)

#     def parse_file(name):
#         m = re.match(r"0*([0-9]+).*_(\d+)", str(name))
#         if m:
#             return int(m.group(1)), int(m.group(2))
#         return None, None

#     urls[["codigo", "num"]] = urls["arquivo"].apply(
#         lambda x: pd.Series(parse_file(x))
#     )

#     urls = urls.dropna()
#     urls["codigo"] = urls["codigo"].astype(int)
#     urls["num"] = urls["num"].astype(int)

#     pivot = urls.pivot_table(index="codigo", columns="num", values="url", aggfunc="first")

#     cols_keep = [c for c in pivot.columns if 1 <= c <= IMAGES_PER_PRODUCT] # type: ignore
#     pivot = pivot[cols_keep]

#     pivot.columns = [f"Url_Imagem{c}" for c in pivot.columns]

#     if "Codigo Produto" not in df.columns:
#         df = df.reset_index().rename(columns={"index": "Codigo Produto"})

#     df["codigo"] = df["Codigo Produto"].astype(int)

#     merged = df.merge(pivot, on="codigo", how="left", suffixes=("", "_new"))

#     for i in range(1, IMAGES_PER_PRODUCT + 1):
#         col = f"Url_Imagem{i}"
#         new = col + "_new"
#         if new in merged.columns:
#             merged[col] = merged[col].combine_first(merged[new])
#             merged.drop(columns=[new], inplace=True)

#     merged.drop(columns=["codigo"], inplace=True, errors="ignore")

#     merged.to_excel(MERGE_OUTPUT, index=False)
#     log(f"✔ Merge concluído: {MERGE_OUTPUT}")


# # ==========================
# # MENU
# # ==========================

# def menu():
#     print("""
# ================ MENU AUTO SHOPEE ================
# 1 - Buscar imagens (gera CSV + HTML)
# 2 - Regerar preview HTML
# 3 - Baixar imagens aprovadas (MULTITHREAD)
# 4 - Upload Cloudinary (MULTITHREAD)
# 5 - Merge final no Excel
# 6 - Executar tudo (1 → PAUSA → 3 → 4 → 5)
# 0 - Sair
# ==================================================
# """)

#     while True:
#         op = input("Escolha: ").strip()

#         if op == "1":
#             step_search_and_generate_review()

#         elif op == "2":
#             df = pd.read_csv(REVIEW_CSV)
#             gerar_html_preview(df)

#         elif op == "3":
#             step_download_images()

#         elif op == "4":
#             step_upload_cloudinary()

#         elif op == "5":
#             step_merge_urls()

#         elif op == "6":
#             step_search_and_generate_review()
#             input("\n⏸ Agora revise o CSV e HTML. Pressione ENTER quando terminar.\n")
#             step_download_images()
#             step_upload_cloudinary()
#             step_merge_urls()

#         elif op == "0":
#             return

#         else:
#             print("Opção inválida.")


# if __name__ == "__main__":
#     menu()
