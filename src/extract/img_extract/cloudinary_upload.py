import json
import os

import cloudinary
import cloudinary.uploader
import pandas as pd
from PIL import Image, ImageOps
from tqdm import tqdm

with open('src/extract/img_extract/cloudinary_config.json', 'r', encoding='utf-8') as f:
    secrets = json.load(f)
cloudinary.config(
    cloud_name=secrets['cloud_name'],
    api_key=secrets['api_key'],
    api_secret=secrets['api_secret']
)

# === CAMINHOS ===
input_folder = "/home/lucas-silva/auto_shopee/notebooks/imagens"
optimized_folder = "/home/lucas-silva/auto_shopee/notebooks/imagens_otimizadas"
os.makedirs(optimized_folder, exist_ok=True)

# === PARÂMETROS ===
QUALIDADE = 85
TAMANHO_PADRAO = (1000, 1000)  # Padrão marketplace

# === LISTA DE RESULTADOS ===
resultados = []

# === LISTAR ARQUIVOS ===
arquivos = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]

# === LOOP COM PROGRESSO ===
for file in tqdm(arquivos, desc="Processando imagens", unit="img"):
    caminho = os.path.join(input_folder, file)
    otimizado_path = os.path.join(optimized_folder, file)
    try:
        # --- Abrir imagem ---
        img = Image.open(caminho).convert("RGB")

        # --- Redimensionar mantendo proporção e adicionando borda branca ---
        img_otimizada = ImageOps.pad(img, TAMANHO_PADRAO, color=(255, 255, 255), method=Image.Resampling.LANCZOS)

        # --- Salvar otimizada ---
        img_otimizada.save(otimizado_path, optimize=True, quality=QUALIDADE)

        # --- Upload para Cloudinary ---
        upload_result = cloudinary.uploader.upload(
            otimizado_path,
            folder="imagens_otimizadas_marketplace",
            use_filename=True,
            unique_filename=False
        )

        # --- URL otimizada ---
        url_otimizada = upload_result["secure_url"].replace(
            "/upload/",
            "/upload/f_auto,q_auto/"
        )

        resultados.append({
            "arquivo": file,
            "url_cloudinary": url_otimizada
        })

        # === SALVAR CSV ===
        df = pd.DataFrame(resultados)
        df.to_csv("/home/lucas-silva/auto_shopee/planilhas/input/urls_cloudinary.csv", index=False)

    except Exception as e:
        print(e)
