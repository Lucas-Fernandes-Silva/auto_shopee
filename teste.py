import os
import boto3
from dotenv import load_dotenv





load_dotenv("/home/lucas-silva/auto_shopee/dados/.env.py")  # ajuste se seu .env estiver em outra pasta

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
    region_name="auto"
)

bucket = os.getenv("R2_BUCKET")

s3.put_object(
    Bucket=bucket,
    Key="teste.txt",
    Body=b"teste"
)

print("Upload teste enviado com sucesso")
