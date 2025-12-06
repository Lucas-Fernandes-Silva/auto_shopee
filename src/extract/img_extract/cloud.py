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
from rapidfuzz import fuzz, process
from tqdm import tqdm


# =============================================================
# NORMALIZADOR BÁSICO (caso você queira usar seu Normalizer original, posso adaptar)
# =============================================================
def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# =============================================================
# CLASSE PRINCIPAL (UPLOAD + MERGE)
# =============================================================
class UploaderAndMerge:
    def __init__(
        self,
        df_produtos,
        cloudinary_config_path,
        pasta_imagens_local,
        output_path="final_com_urls.xlsx",
        size=(1000, 1000),
        quality=85,
        upload_folder="imagens_otimizadas_marketplace",
        cache_csv="cache_urls.csv",
    ):
        self.df = df_produtos.copy()
        self.pasta = pasta_imagens_local
        self.output_path = output_path
        self.size = size
        self.quality = quality
        self.upload_folder = upload_folder
        self.cache_csv = cache_csv

        # =====================
        # Carregar Cloudinary
        # =====================
        with open(cloudinary_config_path, "r") as f:
            cfg = json.load(f)

        cloudinary.config(
            cloud_name=cfg["cloud_name"],
            api_key=cfg["api_key"],
            api_secret=cfg["api_secret"],
            secure=True,
        )

        # =====================
        # Carregar Cache
        # =====================
        if os.path.exists(cache_csv):
            dfc = pd.read_csv(cache_csv)
            self.cache = dict(zip(dfc["chave"], dfc["url_cloudinary"]))
        else:
            self.cache = {}

        # Garantir colunas
        self.cols_imgs = ["Url_Imagem1.0", "Url_Imagem2.0", "Url_Imagem3.0", "Url Imagem"]
        for col in self.cols_imgs:
            if col not in self.df.columns:
                self.df[col] = None

    # =============================================================
    # AUXILIARES
    # =============================================================
    def salvar_cache(self):
        dfc = pd.DataFrame(
            [{"chave": k, "url_cloudinary": v} for k, v in self.cache.items()]
        )
        dfc.to_csv(self.cache_csv, index=False)

    def sanitize(self, text):
        if not isinstance(text, str):
            return "sem_descricao"
        text = text.lower()
        text = re.sub(r"[^a-z0-9_-]+", "_", text)
        text = re.sub(r"_+", "_", text).strip("_")
        return text[:120]

    # =============================================================
    # PROCESSAMENTO DE ARQUIVOS LOCAIS
    # =============================================================
    def processar_local(self, file_path):

        nome = os.path.basename(file_path)
        public_id = f"{self.upload_folder}/{os.path.splitext(nome)[0]}".lower()  # noqa: F841
        chave = f"local_{nome}"

        # Cache
        if chave in self.cache:
            return {"descricao": nome, "url": self.cache[chave]}

        # Processar imagem local
        try:
            img = Image.open(file_path).convert("RGB")
            img_ot = ImageOps.pad(img, self.size, color=(255, 255, 255))

            temp_path = f"/tmp/{nome}"
            img_ot.save(temp_path, quality=self.quality, optimize=True)

            upload = cloudinary.uploader.upload(
                temp_path,
                folder=self.upload_folder,
                public_id=os.path.splitext(nome)[0],
                use_filename=False,
                unique_filename=False,
            )

            url = upload["secure_url"].replace("/upload/", "/upload/f_auto,q_auto/")
            self.cache[chave] = url
            return {"descricao": nome, "url": url}

        except Exception as e:
            print(f"❌ Erro local: {file_path} → {e}")
            return None

    # =============================================================
    # PROCESSAR URL (Fornecedor)
    # =============================================================
    def processar_url(self, url, descricao):
        if not isinstance(url, str) or url.strip() == "":
            return None

        clean_name = self.sanitize(descricao)
        public_id = f"{self.upload_folder}/{clean_name}"
        chave = f"url_{public_id}"

        # Cache
        if chave in self.cache:
            return {"descricao": descricao, "url": self.cache[chave]}

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()

            img = Image.open(BytesIO(resp.content)).convert("RGB")

            temp_path = f"/tmp/{clean_name}.jpg"
            img_ot = ImageOps.pad(img, self.size, color=(255, 255, 255))
            img_ot.save(temp_path, quality=self.quality, optimize=True)

            upload = cloudinary.uploader.upload(
                temp_path,
                folder=self.upload_folder,
                public_id=clean_name,
                use_filename=False,
                unique_filename=False,
            )

            url_cloud = upload["secure_url"].replace("/upload/", "/upload/f_auto,q_auto/")
            self.cache[chave] = url_cloud
            return {"descricao": descricao, "url": url_cloud}

        except Exception as e:
            print(f"❌ Erro processando URL: {url} → {e}")
            return None

    # =============================================================
    # PROCESSAR TUDO
    # =============================================================
    def processar_todas(self, max_workers=10):
        resultados = []
        jobs = []

        arquivos = [
            os.path.join(self.pasta, f)
            for f in os.listdir(self.pasta)
            if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp"))
        ]

        # ======== ThreadPool ========
        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            # arquivos locais
            for f in arquivos:
                jobs.append(executor.submit(self.processar_local, f))

            # URLs de fornecedor
            for _, row in self.df.iterrows():
                url = row["Url Imagem"]
                descricao = row["Descrição"]
                if isinstance(url, str) and url.strip() != "":
                    jobs.append(executor.submit(self.processar_url, url, descricao))

            for future in tqdm(as_completed(jobs), total=len(jobs), desc="Upload Cloudinary"):
                res = future.result()
                if res:
                    resultados.append(res)

        self.salvar_cache()

        df_urls = pd.DataFrame(resultados)
        df_urls.columns = ["descricao_extraida", "url_cloud"]
        return df_urls

    # =============================================================
    # MERGE FINAL (fuzzy)
    # =============================================================
    def merge_final(self, df_urls):
        df_urls = df_urls.dropna()

        # Normalizar descrições
        df_urls["descricao_norm"] = df_urls["descricao_extraida"].apply(normalize_text)
        self.df["desc_norm"] = self.df["Descrição"].apply(normalize_text)

        desc_base = self.df["desc_norm"].tolist()
        desc_urls = df_urls["descricao_norm"].tolist()

        # Fuzzy match
        matches = []
        for i, desc in enumerate(desc_urls):
            match = process.extractOne(desc, desc_base, scorer=fuzz.ratio)
            if match and match[1] >= 70:
                idx = match[2]
                matches.append((df_urls.iloc[i], idx))

        # Preencher DataFrame final
        for row, idx_prod in matches:
            url_cloud = row["url_cloud"]

            # Substituir a URL do fornecedor pela do cloudinary
            self.df.at[idx_prod, "Url Imagem"] = url_cloud

            # Preencher nas colunas de imagem (1ª vaga disponível)
            for col in ["Url_Imagem1.0", "Url_Imagem2.0", "Url_Imagem3.0"]:
                if pd.isna(self.df.at[idx_prod, col]) or str(self.df.at[idx_prod, col]).strip() == "":
                    self.df.at[idx_prod, col] = url_cloud
                    break

        # Salvar saída final
        self.df.drop(columns=["desc_norm"], inplace=True)
        self.df.to_excel(self.output_path, index=False)
        print(f"🔥 Arquivo final gerado: {self.output_path}")

        return self.df


# =============================================================
# EXECUÇÃO
# =============================================================
if __name__ == "__main__":

    df_prod = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/download.xlsx")

    processor = UploaderAndMerge(
        df_produtos=df_prod,
        cloudinary_config_path="/home/lucas-silva/auto_shopee/src/extract/img_extract/json_files/cloudinary_config.json",
        pasta_imagens_local="/home/lucas-silva/auto_shopee/src/extract/img_extract/imagens",
        output_path="/home/lucas-silva/auto_shopee/planilhas/outputs/final_urls_cloudinary.xlsx"
    )

    df_urls = processor.processar_todas()
    processor.merge_final(df_urls)
