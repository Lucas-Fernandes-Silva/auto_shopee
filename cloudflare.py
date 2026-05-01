import os

import boto3
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
SECRET_KEY = os.getenv("R2_SECRET_KEY")
ENDPOINT = os.getenv("R2_ENDPOINT")
# CONFIG

PASTA_IMAGENS = "/home/lucas-silva/auto_shopee/src/extract/img_extract/imagens_otimizadas"

ACCESS_KEY = "SUA_ACCESS_KEY"
SECRET_KEY = "SEU_SECRET_KEY"
ENDPOINT = "https://SEU_ENDPOINT.r2.cloudflarestorage.com"
BUCKET = "produtos"

URL_BASE = "https://pub-6b1902641e5a40b2916ddf51bb1dfedf.r2.dev"

# CONEXÃO
s3 = boto3.client(
    "s3", endpoint_url=ENDPOINT, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY
)

# UPLOAD
arquivos = [
    f for f in os.listdir(PASTA_IMAGENS) if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp"))
]

for arquivo in tqdm(arquivos):
    caminho = os.path.join(PASTA_IMAGENS, arquivo)

    try:
        s3.upload_file(caminho, BUCKET, arquivo, ExtraArgs={"ACL": "public-read"})
    except Exception as e:
        print(f"Erro: {arquivo} -> {e}")

print("Upload finalizado!")

# GERAR URLS
urls = [URL_BASE + nome for nome in arquivos]

print("\nExemplo de URL:")
print(urls[0])
