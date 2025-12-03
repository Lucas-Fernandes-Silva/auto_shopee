import hashlib
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


class UniversalImageUploader:
    def __init__(
        self,
        cloudinary_config_path,
        cache_csv=None,
        size=(1000, 1000),
        quality=85,
        upload_folder="imagens_otimizadas_marketplace",
    ):
        self.size = size
        self.quality = quality
        self.cache_csv = cache_csv
        self.upload_folder = upload_folder

        self.temp_folder = "/tmp/upload_temp"
        os.makedirs(self.temp_folder, exist_ok=True)

        # Carregar Cloudinary
        self._load_cloudinary(cloudinary_config_path)

        # Carregar cache
        self.cache = self._load_cache()

    # -------------------------------------------------------------------------
    # CONFIGURAÇÃO CLOUDINARY
    # -------------------------------------------------------------------------
    def _load_cloudinary(self, path):
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        cloudinary.config(
            cloud_name=cfg["cloud_name"],
            api_key=cfg["api_key"],
            api_secret=cfg["api_secret"],
        )

    # -------------------------------------------------------------------------
    # CACHE
    # -------------------------------------------------------------------------
    def _load_cache(self):
        if self.cache_csv and os.path.exists(self.cache_csv):
            df = pd.read_csv(self.cache_csv)
            return dict(zip(df["chave"], df["url_cloudinary"]))
        return {}

    def _save_cache(self):
        if self.cache_csv:
            df = pd.DataFrame(
                [{"chave": k, "url_cloudinary": v} for k, v in self.cache.items()]
            )
            df.to_csv(self.cache_csv, index=False)

    # -------------------------------------------------------------------------
    # UTIL: hash único
    # -------------------------------------------------------------------------
    def _hash(self, value: str):
        return hashlib.md5(value.encode()).hexdigest()

    # -------------------------------------------------------------------------
    # PROCESSAR ARQUIVO LOCAL
    # -------------------------------------------------------------------------
    def _processar_local(self, file_path):
        nome = os.path.basename(file_path)
        chave = f"local_{nome}"

        # Cache
        if chave in self.cache:
            return {"nome": nome, "url_cloudinary": self.cache[chave]}

        try:
            img = Image.open(file_path).convert("RGB")

            img_otimizada = ImageOps.pad(
                img, self.size,
                color=(255, 255, 255),
                method=Image.Resampling.LANCZOS,
            )

            hashed_name = self._hash(nome) + ".jpg"
            temp_path = os.path.join(self.temp_folder, hashed_name)
            img_otimizada.save(temp_path, quality=self.quality, optimize=True)

            upload = cloudinary.uploader.upload(
                temp_path,
                folder=self.upload_folder,
                use_filename=True,
                unique_filename=False,
            )

            url = upload["secure_url"].replace("/upload/", "/upload/f_auto,q_auto/")
            self.cache[chave] = url

            return {"nome": nome, "url_cloudinary": url}

        except Exception as e:
            print(f"❌ Erro ao processar arquivo local {file_path}: {e}")
            return None

    # -------------------------------------------------------------------------
    # PROCESSAR URL
    # -------------------------------------------------------------------------
    def _processar_url(self, url, descricao):
        nome = descricao if isinstance(descricao, str) else "sem_descricao"
        chave = f"url_{self._hash(url)}"

        # Cache
        if chave in self.cache:
            return {"nome": nome, "url_cloudinary": self.cache[chave]}

        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content)).convert("RGB")

            hashed = self._hash(url) + ".jpg"
            temp_path = os.path.join(self.temp_folder, hashed)

            img_otimizada = ImageOps.pad(
                img, self.size,
                color=(255, 255, 255),
                method=Image.Resampling.LANCZOS,
            )

            img_otimizada.save(temp_path, quality=self.quality, optimize=True)

            upload = cloudinary.uploader.upload(
                temp_path,
                folder=self.upload_folder,
                use_filename=True,
                unique_filename=False,
            )

            url_cloud = upload["secure_url"].replace("/upload/", "/upload/f_auto,q_auto/")
            self.cache[chave] = url_cloud

            return {"nome": nome, "url_cloudinary": url_cloud}

        except Exception as e:
            print(f"❌ Erro ao processar URL {url}: {e}")
            return None

    # -------------------------------------------------------------------------
    # PROCESSAR TUDO + SALVAR CSV FINAL COM 2 COLUNAS
    # -------------------------------------------------------------------------
    def processar(
        self,
        arquivos_locais=None,
        df_urls=None,
        coluna_url=None,
        coluna_desc=None,
        output_csv="resultado.csv",
        max_workers=10,
    ):
        resultados = []
        jobs = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            # Arquivos locais
            if arquivos_locais:
                for f in arquivos_locais:
                    jobs.append(executor.submit(self._processar_local, f))

            # URLs do dataframe
            if df_urls is not None:
                for _, row in df_urls.iterrows():
                    url = row[coluna_url]
                    desc = row[coluna_desc] if coluna_desc else None

                    jobs.append(
                        executor.submit(self._processar_url, url, desc)
                    )

            # coletar resultados
            for future in tqdm(as_completed(jobs), total=len(jobs), desc="Processando"):
                res = future.result()
                if res:
                    resultados.append(res)

        # salvar cache
        self._save_cache()

        # CSV final com apenas 2 colunas
        df_final = pd.DataFrame(resultados)[["nome", "url_cloudinary"]]
        df_final.to_csv(output_csv, index=False)

        print(f"📁 CSV final salvo em: {output_csv}")
        return df_final


# -------------------------------------------------------------------------
# EXEMPLO DE USO
# -------------------------------------------------------------------------

uploader = UniversalImageUploader(
    cloudinary_config_path="/home/lucas-silva/auto_shopee/src/extract/img_extract/json_files/cloudinary_config.json",
    cache_csv="/home/lucas-silva/auto_shopee/cache/cache_uploads.csv"
)

arquivos = [
    "/home/lucas-silva/auto_shopee/src/extract/img_extract/imagens/produto1.jpg",
    "/home/lucas-silva/auto_shopee/src/extract/img_extract/imagens/produto2.png",
]

df_urls = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/download.xlsx")

df_final = uploader.processar(
    arquivos_locais=arquivos,
    df_urls=df_urls,
    coluna_url="Url Imagem",
    coluna_desc="Descrição",
    output_csv="/home/lucas-silva/auto_shopee/planilhas/input/final.csv",
    max_workers=10
)
