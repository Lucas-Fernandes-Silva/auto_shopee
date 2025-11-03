import json
import os
import re  # 👈 adicionado
import time

import pandas as pd
import requests
from tqdm import tqdm

# === CONFIGURAÇÕES ===
EXCEL_PATH = "planilhas/outputs/final.xlsx"
OUTPUT_FOLDER = "notebooks/imagens"
PROGRESS_FILE = "notebooks/progresso.json"
API_KEYS_FILE = "notebooks/api_keys.json"
SEARCH_ENGINE_ID = "532347d8c03cc4861"

IMAGES_PER_PRODUCT = 3
SLEEP_TIME = 1  # segundos entre buscas


# === FUNÇÕES AUXILIARES ===
def carregar_progresso():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                data = json.load(f)
                return {
                    "last_index": data.get("last_index", 0),
                    "current_key_index": data.get("current_key_index", 0),
                }
        except Exception:
            pass
    return {"last_index": 0, "current_key_index": 0}


def salvar_progresso(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)


def carregar_chaves():
    if not os.path.exists(API_KEYS_FILE):
        raise FileNotFoundError(f"Arquivo de chaves não encontrado: {API_KEYS_FILE}")
    with open(API_KEYS_FILE, "r") as f:
        data = json.load(f)
        if "keys" not in data or not isinstance(data["keys"], list):
            raise ValueError("O arquivo de chaves deve conter uma lista chamada 'keys'.")
        return data["keys"]


def buscar_imagens(query, api_key, cx, num=3):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cx,
        "searchType": "image",
        "num": num,
    }
    response = requests.get(url, params=params, timeout=10)
    data = response.json() if response.content else {}

    if response.status_code == 403 or "error" in data:
        error_msg = data.get("error", {}).get("message", "")
        raise Exception(f"API Error: {error_msg or '403 Forbidden'}")

    response.raise_for_status()
    return data.get("items", [])


def baixar_imagem(url, save_path):
    response = requests.get(url, stream=True, timeout=10)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return True
    return False


# === EXECUÇÃO PRINCIPAL ===
if __name__ == "__main__":
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Arquivo Excel não encontrado: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH)
    if "Descrição" not in df.columns:
        raise ValueError("A planilha deve conter a coluna 'Descrição'.")

    df = df.drop_duplicates(subset=["Descrição"], keep="first").reset_index(drop=True)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    progresso = carregar_progresso()
    api_keys = carregar_chaves()

    current_key_index = progresso["current_key_index"]
    last_index = progresso["last_index"]

    print(f"🚀 Iniciando busca a partir do índice {last_index} com chave {current_key_index + 1}/{len(api_keys)}")

    for i in tqdm(range(last_index, len(df)), desc="Buscando imagens"):
        produto = str(df.loc[i, "Descrição"]).strip()
        if not produto:
            continue

        query = produto
        tentativa = 0

        while True:
            if tentativa > len(api_keys):
                print("🚫 Todas as chaves atingiram o limite diário.")
                salvar_progresso({"last_index": i, "current_key_index": current_key_index})
                exit(0)

            api_key = api_keys[current_key_index]
            try:
                imagens = buscar_imagens(query, api_key, SEARCH_ENGINE_ID, IMAGES_PER_PRODUCT)
                if not imagens:
                    print(f"⚠️ Nenhum resultado para: {produto}")
                    break

                for j, img in enumerate(imagens):
                    link = img.get("link")
                    if not link:
                        continue

                    # 🔧 Corrigido: limpa caracteres inválidos
                    nome_limpo = re.sub(r'[\\/*?:"<>|]', "_", produto[:40])
                    nome_arquivo = f"{i:04d}_{j+1}_{nome_limpo.replace(' ', '_')}.jpg"
                    caminho = os.path.join(OUTPUT_FOLDER, nome_arquivo)

                    try:
                        baixar_imagem(link, caminho)
                    except Exception as e:
                        print(f"❌ Falha ao baixar imagem {j+1} de {produto}: {e}")
                        continue
                break

            except Exception as e:
                erro = str(e)
                if "Quota" in erro or "403" in erro or "disabled" in erro:
                    print(f"⚠️ Limite atingido para chave {current_key_index+1}/{len(api_keys)}.")
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    tentativa += 1
                    continue
                else:
                    print(f"❌ Erro em '{produto}': {erro}")
                    break

        progresso = {"last_index": i + 1, "current_key_index": current_key_index}
        salvar_progresso(progresso)
        time.sleep(SLEEP_TIME)

    print("✅ Processamento concluído com sucesso!")
