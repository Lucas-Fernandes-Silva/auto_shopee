import json
import os
import re
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

        self._load_cloudinary(cloudinary_config_path)
        self.cache = self._load_cache()

    # -------------------------------------------------------------------------
    # CONFIG CLOUDINARY
    # -------------------------------------------------------------------------
    def _load_cloudinary(self, path):
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        cloudinary.config(
            cloud_name=cfg["cloud_name"],
            api_key=cfg["api_key"],
            api_secret=cfg["api_secret"],
            secure=True
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
    # SANITIZAR TEXTO PARA PUBLIC ID
    # -------------------------------------------------------------------------
    def _sanitize(self, text):
        if not isinstance(text, str):
            return "sem_descricao"

        text = text.lower()
        text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text)
        text = re.sub(r"_+", "_", text).strip("_")
        return text[:120]

    # -------------------------------------------------------------------------
    # VERIFICAR SE A IMAGEM EXISTE NO CLOUDINARY (SEM USAR ADMIN API)
    # -------------------------------------------------------------------------
    def _existe_no_cloudinary(self, public_id):

        cloud_name = cloudinary.config().cloud_name
        url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{public_id}.jpg"

        try:
            resp = requests.head(url, timeout=10)

            # 200 → existe
            return resp.status_code == 200

        except Exception:
            return False

    # -------------------------------------------------------------------------
    # PROCESSAR ARQUIVO LOCAL
    # -------------------------------------------------------------------------
    def _processar_local(self, file_path):

        if not os.path.isfile(file_path):
            print(f"⚠ Caminho inválido (não é arquivo): {file_path}")
            return None

        nome = os.path.basename(file_path)
        public_id = f"{self.upload_folder}/{os.path.splitext(nome)[0]}".lower()
        chave = f"local_{nome}"

        # cache local
        if chave in self.cache:
            return {"nome": nome, "url_cloudinary": self.cache[chave]}

        # já existe no cloudinary
        if self._existe_no_cloudinary(public_id):
            url = cloudinary.CloudinaryImage(public_id).build_url(
                transformation=["f_auto", "q_auto"]
            )
            self.cache[chave] = url
            return {"nome": nome, "url_cloudinary": url}

        # processar imagem
        try:
            img = Image.open(file_path).convert("RGB")

            img_otimizada = ImageOps.pad(
                img,
                self.size,
                color=(255, 255, 255),
                method=Image.Resampling.LANCZOS,
            )

            temp_path = os.path.join(self.temp_folder, nome)
            img_otimizada.save(temp_path, quality=self.quality, optimize=True)

            upload = cloudinary.uploader.upload(
                temp_path,
                folder=self.upload_folder,
                public_id=os.path.splitext(nome)[0].lower(),
                use_filename=False,
                unique_filename=False,
            )

            url = upload["secure_url"].replace("/upload/", "/upload/f_auto,q_auto/")
            self.cache[chave] = url
            return {"nome": nome, "url_cloudinary": url}

        except Exception as e:
            print(f"❌ Erro ao processar local {file_path}: {e}")
            return None

    # -------------------------------------------------------------------------
    # PROCESSAR URL
    # -------------------------------------------------------------------------
    def _processar_url(self, url, descricao):

        if not isinstance(url, str) or url.strip() == "":
            print(f"⚠ URL inválida ignorada: {url}")
            return None

        nome = descricao if isinstance(descricao, str) else "sem_descricao"
        clean_name = self._sanitize(nome)

        public_id = f"{self.upload_folder}/{clean_name}"
        chave = f"url_{public_id}"

        # cache
        if chave in self.cache:
            return {"nome": nome, "url_cloudinary": self.cache[chave]}

        # já existe
        if self._existe_no_cloudinary(public_id):
            url_cloud = cloudinary.CloudinaryImage(public_id).build_url(
                transformation=["f_auto", "q_auto"]
            )
            self.cache[chave] = url_cloud
            return {"nome": nome, "url_cloudnary": url_cloud}

        # baixar + subir
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()

            img = Image.open(BytesIO(resp.content)).convert("RGB")

            temp_path = os.path.join(self.temp_folder, clean_name + ".jpg")
            img_otimizada = ImageOps.pad(
                img,
                self.size,
                color=(255, 255, 255),
                method=Image.Resampling.LANCZOS,
            )
            img_otimizada.save(temp_path, quality=self.quality, optimize=True)

            upload = cloudinary.uploader.upload(
                temp_path,
                folder=self.upload_folder,
                public_id=clean_name,
                use_filename=False,
                unique_filename=False,
            )

            url_cloud = upload["secure_url"].replace("/upload/", "/upload/f_auto,q_auto/")
            self.cache[chave] = url_cloud
            return {"nome": nome, "url_cloudinary": url_cloud}

        except Exception as e:
            print(f"❌ Erro ao processar URL {url}: {e}")
            return None

    # -------------------------------------------------------------------------
    # PROCESSAR TUDO
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

            # locais
            if arquivos_locais:
                for f in arquivos_locais:
                    jobs.append(executor.submit(self._processar_local, f))

            # urls
            if df_urls is not None:
                for _, row in df_urls.iterrows():
                    jobs.append(
                        executor.submit(
                            self._processar_url,
                            row[coluna_url],
                            row[coluna_desc] if coluna_desc else None,
                        )
                    )

            for future in tqdm(as_completed(jobs), total=len(jobs), desc="Processando"):
                res = future.result()
                if res:
                    resultados.append(res)

        self._save_cache()

        df_final = pd.DataFrame(resultados)[["nome", "url_cloudinary"]]
        df_final.to_csv(output_csv, index=False)

        print(f"\n📁 CSV final salvo em: {output_csv}")
        return df_final



config_path = (
    "/home/lucas-silva/auto_shopee/src/extract/img_extract/json_files/cloudinary_config.json"
)
upload = UniversalImageUploader(config_path)

pasta = "/home/lucas-silva/auto_shopee/src/extract/img_extract/imagens"

arquivos = [
    os.path.join(pasta, f)
    for f in os.listdir(pasta)
    if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp"))
]

df = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/download.xlsx")

upload.processar(
    arquivos_locais=arquivos,
    df_urls=df,
    coluna_url=["Url Imagem"],
    coluna_desc=["Descrição"],
)
