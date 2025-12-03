import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

import cloudinary
import cloudinary.uploader
import pandas as pd
import requests
from PIL import Image, ImageOps
from tqdm import tqdm


class URLToCloudinary:
    def __init__(
        self,
        quality=85,
        size=(1000, 1000),
        cloudinary_config_path="/home/lucas-silva/auto_shopee/src/extract/img_extract/json_files/cloudinary_config.json",
    ):
        self.quality = quality
        self.size = size
        self.cloudinary_config_path = cloudinary_config_path

        # mantém a mesma estrutura do seu projeto
        self.temp_folder = "/home/lucas-silva/auto_shopee/src/extract/img_extract/temp"
        os.makedirs(self.temp_folder, exist_ok=True)

        self._load_cloudinary()

    def _load_cloudinary(self):
        with open(self.cloudinary_config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        cloudinary.config(
            cloud_name=cfg["cloud_name"],
            api_key=cfg["api_key"],
            api_secret=cfg["api_secret"],
        )

    def processar_dataframe(self, df, coluna_urls, coluna_saida="Url Cloudinary", max_workers=8):
        # Garante que a coluna de saída exista
        if coluna_saida not in df.columns:
            df[coluna_saida] = None

        # URLs já processadas
        urls_processadas = {
            row[coluna_urls]: row[coluna_saida]
            for _, row in df.dropna(subset=[coluna_saida]).iterrows()
        }

        # Lista de URLs a processar
        urls_para_processar = [
            url for url in df[coluna_urls].tolist() if url not in urls_processadas
        ]

        print(f"\n🔍 Total de URLs: {len(df)}")
        print(f"✔ Já processadas: {len(urls_processadas)}")
        print(f"➡ Faltam processar: {len(urls_para_processar)}\n")

        resultados = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._converter_url, url): url for url in urls_para_processar
            }

            for fut in tqdm(
                as_completed(futures), total=len(futures), desc="Convertendo URLs", unit="url"
            ):
                url_original = futures[fut]
                try:
                    resultados[url_original] = fut.result()
                except Exception as e:
                    print(f"❌ Erro inesperado com {url_original}: {e}")
                    resultados[url_original] = None

        # Unindo tudo no DataFrame
        df[coluna_saida] = df[coluna_urls].map(
            lambda u: urls_processadas.get(u) or resultados.get(u)
        )

        return df

    def _converter_url(self, url):
        try:
            # baixar imagem
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()

            img = Image.open(BytesIO(resp.content)).convert("RGB")

            # redimensionar / pad branco
            img_otimizada = ImageOps.pad(
                img,
                self.size,
                color=(255, 255, 255),
                method=Image.Resampling.LANCZOS,
            )

            temp_path = os.path.join(self.temp_folder, "img_temp.jpg")
            img_otimizada.save(temp_path, optimize=True, quality=self.quality)

            # fazer upload
            upload = cloudinary.uploader.upload(
                temp_path,
                folder="imagens_otimizadas_marketplace",
                use_filename=True,
                unique_filename=False,
            )

            # gerar URL otimizada automática
            return upload["secure_url"].replace("/upload/", "/upload/f_auto,q_auto/")

        except Exception as e:
            print(f"❌ Falha ao converter {url}: {e}")
            return None


df = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/download.xlsx")

conv = URLToCloudinary()

df = conv.processar_dataframe(
    df, coluna_urls="Url Imagem", coluna_saida="Url Cloudinary", max_workers=10
)

df.to_excel("/home/lucas-silva/auto_shopee/planilhas/input/produtos_convertido.xlsx", index=False)

print("✔ Processo finalizado!")
