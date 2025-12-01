import json
import os

import cloudinary
import cloudinary.uploader
import pandas as pd
from PIL import Image, ImageOps
from tqdm import tqdm


class ImageOptimizerUploader:
    def __init__(
        self,
        cloudinary_config_path="/home/lucas-silva/auto_shopee/src/extract/img_extract/json_files/cloudinary_config.json",
        qualidade=85,
        tamanho_padrao=(1000, 1000),
    ):
        self.cloudinary_config_path = cloudinary_config_path
        self.qualidade = qualidade
        self.tamanho_padrao = tamanho_padrao

        self.project_dir = '/home/lucas-silva/auto_shopee'
        self.input_folder = f"{self.project_dir}/src/extract/img_extract/imagens"
        self.optimized_folder = f"{self.project_dir}/src/extract/img_extract/imagens_otimizadas"
        os.makedirs(self.optimized_folder, exist_ok=True)

        self._load_cloudinary_config()
        self.resultados = []



    def _load_cloudinary_config(self):
        with open(self.cloudinary_config_path, "r", encoding="utf-8") as f:
            secrets = json.load(f)

        cloudinary.config(
            cloud_name=secrets["cloud_name"],
            api_key=secrets["api_key"],
            api_secret=secrets["api_secret"],
        )

    def processar_imagens(self, output_csv_path=None):
        arquivos = [
            f
            for f in os.listdir(self.input_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]

        for file in tqdm(arquivos, desc="Processando imagens", unit="img"):
            self._processar_imagem(file)

            if output_csv_path:
                df = pd.DataFrame(self.resultados)
                df.to_csv(output_csv_path, index=False)


    def _processar_imagem(self, file):
        try:
            caminho = os.path.join(self.input_folder, file)
            otimizado_path = os.path.join(self.optimized_folder, file)

            # --- Abrir ---
            img = Image.open(caminho).convert("RGB")

            # --- Redimensionar ---
            img_otimizada = ImageOps.pad(
                img, self.tamanho_padrao, color=(255, 255, 255), method=Image.Resampling.LANCZOS
            )

            # --- Salvar temporário ---
            img_otimizada.save(otimizado_path, optimize=True, quality=self.qualidade)

            # --- Upload ---
            upload_result = cloudinary.uploader.upload(
                otimizado_path,
                folder="imagens_otimizadas_marketplace",
                use_filename=True,
                unique_filename=False,
            )

            url_otimizada = upload_result["secure_url"].replace(
                "/upload/", "/upload/f_auto,q_auto/"
            )

            self.resultados.append({"arquivo": file, "url_cloudinary": url_otimizada})

        except Exception as e:
            print(f"❌ Erro ao processar {file}: {e}")


processor = ImageOptimizerUploader()

processor.processar_imagens(
    output_csv_path="/home/lucas-silva/auto_shopee/planilhas/input/urls_cloudinary.csv"
)



