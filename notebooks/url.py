import json
import os
import time

import pandas as pd
import requests
from projeto import cx
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from tqdm import tqdm

# Caminho seguro do client_secrets.json
CAMINHO_PADRAO = '../../../../home/lucas-silva/.credentials/auto_shope/client_secrets.json'
CLIENT_SECRETS = os.getenv("GOOGLE_CLIENT_SECRETS", CAMINHO_PADRAO)

if not os.path.exists(CLIENT_SECRETS):
    raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {CLIENT_SECRETS}")


gauth = GoogleAuth()
gauth.LoadClientConfigFile(CLIENT_SECRETS)

# Usa token salvo (credentials.json)
gauth.LoadCredentialsFile("credentials.json")

if gauth.credentials is None:
    # Primeira autenticação
    gauth.CommandLineAuth()
elif gauth.access_token_expired:
    # Token expirado → renova
    gauth.Refresh()
else:
    # Token ainda válido
    gauth.Authorize()

# Salva token atualizado
gauth.SaveCredentialsFile("credentials.json")

drive = GoogleDrive(gauth)


# === CONFIGURAÇÕES ===
API_KEY = 'projeto'
CX = cx
IMAGES_PER_QUERY = 3
MAX_REQUESTS_PER_DAY = 100
SAVE_DIR = "imagens"
EXCEL_PATH =  "/home/lucas-silva/auto_shopee/planilhas/outputs/final.xlsx"
OUTPUT_EXCEL = "/home/lucas-silva/auto_shopee/planilhas/outputs/final_com_imagens.xlsx"
PROGRESS_FILE = "progresso.json"

# === PREPARO ===
os.makedirs(SAVE_DIR, exist_ok=True)

# === CARREGAR DATA ===
df = pd.read_excel(EXCEL_PATH)

# Criar colunas de imagem, se não existirem
for i in range(1, IMAGES_PER_QUERY + 1):
    url_col = f"URL Imagem {i}"
    drive_col = f"URL Drive Imagem {i}"
    if url_col not in df.columns:
        df[url_col] = None
    if drive_col not in df.columns:
        df[drive_col] = None

# === CONTROLAR PROGRESSO ===
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        progresso = json.load(f)
else:
    progresso = {"ultimo_indice": -1}


# === LOOP PRINCIPAL ===
unicos = df["Base"].dropna().unique()
inicio = progresso["ultimo_indice"] + 1
fim = min(inicio + MAX_REQUESTS_PER_DAY, len(unicos))

print(f"🔍 Executando de {inicio} até {fim} (limite diário atingido em {fim})")

for i, termo in enumerate(tqdm(unicos[inicio:fim], desc="Buscando imagens")):
    try:
        params = {
            "q": termo,
            "cx": CX,
            "key": API_KEY,
            "searchType": "image",
            "num": IMAGES_PER_QUERY,
        }

        res = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        data = res.json()

        if "items" not in data:
            print(f"⚠️ Nenhum resultado para: {termo}")
            continue

        image_links = [item["link"] for item in data["items"][:IMAGES_PER_QUERY]]

        # Atualizar DataFrame para todas as linhas com essa Base
        mask = df["Base"] == termo

        for j, link in enumerate(image_links):
            df.loc[mask, f"URL Imagem {j+1}"] = link

            ext = os.path.splitext(link)[1].split("?")[0] or ".jpg"
            local_path = os.path.join(SAVE_DIR, f"{termo}_{j+1}{ext}")

            try:
                # Baixar imagem
                r = requests.get(link, timeout=10)
                if r.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(r.content)

                    # Upload pro Drive
                    drive_file = drive.CreateFile({'title': os.path.basename(local_path)})
                    drive_file.SetContentFile(local_path)
                    drive_file.Upload()

                    # Tornar o arquivo público
                    drive_file.InsertPermission({
                        'type': 'anyone',
                        'value': 'anyone',
                        'role': 'reader'
                    })

                    # Salvar link público no DataFrame
                    df.loc[mask, f"URL Drive Imagem {j+1}"] = f"https://drive.google.com/uc?id={drive_file['id']}"

            except Exception as e:
                print(f"❌ Erro ao baixar/enviar imagem {j+1} de {termo}: {e}")

        time.sleep(1)  # evitar bloqueio da API

    except Exception as e:
        print(f"❌ Erro geral ao buscar {termo}: {e}")

    # Salvar progresso e Excel a cada iteração
    progresso["ultimo_indice"] = inicio + i
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progresso, f)

    df.to_excel(OUTPUT_EXCEL, index=False)

print("✅ Finalizado! Continue amanhã para retomar o restante.")
