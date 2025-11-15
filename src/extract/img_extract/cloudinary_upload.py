# upload_cloudinary.py
import os

import cloudinary
import cloudinary.uploader
import pandas as pd
from PIL import Image, ImageOps
from tqdm import tqdm

# cloudinary config - mantenha as suas credenciais
cloudinary.config(
    cloud_name="dbpq32fiq",
    api_key="728699121312431",
    api_secret="pzmdaYjFR0lDCwJhpFAXNJ0OV9Y"
)

INPUT_FOLDER = "notebooks/imagens"
OPT_FOLDER = "notebooks/imagens_otimizadas"
os.makedirs(OPT_FOLDER, exist_ok=True)

QUALIDADE = 85
TAMANHO_PADRAO = (1000, 1000)

resultados = []
csv_out = "urls_cloudinary.csv"

arquivos = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
for file in tqdm(arquivos, desc="Processando imagens"):
    caminho = os.path.join(INPUT_FOLDER, file)
    otimizado_path = os.path.join(OPT_FOLDER, file)
    try:
        # otimizar
        img = Image.open(caminho).convert("RGB")
        img_otimizada = ImageOps.pad(img, TAMANHO_PADRAO, color=(255,255,255), method=Image.Resampling.LANCZOS)
        img_otimizada.save(otimizado_path, optimize=True, quality=QUALIDADE)

        # upload
        upload_result = cloudinary.uploader.upload(
            otimizado_path,
            folder="imagens_otimizadas_marketplace",
            use_filename=True,
            unique_filename=False
        )
        url_otimizada = upload_result.get("secure_url")
        if url_otimizada:
            # apply auto transformations in URL (optional)
            url_otimizada = url_otimizada.replace("/upload/", "/upload/f_auto,q_auto/")
            resultados.append({"arquivo": file, "url": url_otimizada})
            # save progressively
            pd.DataFrame(resultados).to_csv(csv_out, index=False)
    except Exception as e:
        print("Erro upload:", e)

print("✅ Upload concluído. CSV:", csv_out)
