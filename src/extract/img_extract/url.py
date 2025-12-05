import json
import os
import re
import time

import pandas as pd
import requests
from tqdm import tqdm


class Download:
    def __init__(
        self,
        df,
        progress="/home/lucas-silva/auto_shopee/src/extract/img_extract/json_files/progresso.json",
        keys_file="/home/lucas-silva/auto_shopee/src/extract/img_extract/json_files/api_keys.json",
        output_folder="/home/lucas-silva/auto_shopee/src/extract/img_extract/imagens",
    ):

        # Remove duplicados por Descrição
        self.df = df.drop_duplicates(subset=["Descrição"], keep="first").reset_index(drop=True)

        self.progress_file = progress
        self.keys_file_path = keys_file
        self.output_folder = output_folder

        # Colunas que serão verificadas antes de buscar imagens
        self.cols_imgs = [
            "Url_Imagem1.0",
            "Url_Imagem2.0",
            "Url_Imagem3.0",
            "Url Imagem"
        ]

        # Criar colunas se não existirem
        for col in self.cols_imgs:
            if col not in self.df.columns:
                self.df[col] = None

        os.makedirs(self.output_folder, exist_ok=True)

        # Carregamentos iniciais
        self.progress = self.carregar_progresso()
        self.keys = self.carregar_chaves()

        self.blacklist = [
        "fliphtml5.com"
        "kdfoundation.org"
        "percar.com.br"
        "yumpu.com"
        "fermat.com.br"
        "atacadistasigma.com.br"
        "pubhtml5.com"
        "casadolojista.com.br"
        "pt.aliexpress.com"
        "ysoc.net"
        "ccpvirtual.com.br"
        "gfixdistribuidora.com.br"
        "www.magiadistribuidora.com.br"
        "pt.scribd.com"
        "amazon.ae"
        "https://collections.carli.illinois.edu"
        "mackglobe.com"
        "sciencedirect.com"
        "ebay.com"
        "econominet.com.br"
        "barzel.com.br"
        "eletroleste.com.br"
        "comercialmaia.com.br"
    ]

    # =========================================================
    # MANIPULAÇÃO DE ARQUIVOS JSON
    # =========================================================
    def carregar_progresso(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r") as f:
                    data = json.load(f)
                    return {
                        "last_index": data.get("last_index", 0),
                        "current_key_index": data.get("current_key_index", 0),
                    }
            except Exception:
                pass

        return {"last_index": 0, "current_key_index": 0}

    def salvar_progresso(self, data):
        with open(self.progress_file, "w") as f:
            json.dump(data, f)

    def carregar_chaves(self):
        if not os.path.exists(self.keys_file_path):
            raise FileNotFoundError(f"Arquivo de chaves não encontrado: {self.keys_file_path}")

        with open(self.keys_file_path, "r") as f:
            data = json.load(f)
            if "keys" not in data or not isinstance(data["keys"], list):
                raise ValueError("O arquivo de chaves deve conter uma lista chamada 'keys'.")
            return data["keys"]

    # =========================================================
    # BLACKLIST
    # =========================================================
    def url_bloqueada(self, url):
        if not isinstance(url, str):
            return True

        url_lower = url.lower()
        return any(host in url_lower for host in self.blacklist)

    # =========================================================
    # GOOGLE SEARCH
    # =========================================================
    def buscar_imagens(self, query, api_key, cx, num=3):
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

    # =========================================================
    # DOWNLOAD DA IMAGEM
    # =========================================================
    def baixar_imagem(self, url, save_path):
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
        return False

    # =========================================================
    # EXECUÇÃO PRINCIPAL
    # =========================================================
    def run(self):

        current_key_index = self.progress["current_key_index"]
        last_index = self.progress["last_index"]

        print(
            f"🚀 Iniciando busca a partir do índice {last_index} "
            f"com chave {current_key_index + 1}/{len(self.keys)}"
        )

        for i in tqdm(range(last_index, len(self.df)), desc="Buscando imagens"):

            produto = str(self.df.loc[i, "Descrição"]).strip()
            query = produto

            # -------------------------------
            # 1) VERIFICA SE O PRODUTO JÁ POSSUI IMAGENS
            # -------------------------------
            tem_img_boa = any(
                pd.notna(self.df.loc[i, col]) and str(self.df.loc[i, col]).strip() != ""
                for col in ["Url_Imagem1.0", "Url_Imagem2.0", "Url_Imagem3.0"]
            )

            url_fornecedor = self.df.loc[i, "Url Imagem"]
            tem_url_fornecedor = pd.notna(url_fornecedor) and str(url_fornecedor).strip() != ""

            if tem_img_boa:
                print(f"⏩ Pulando '{produto}': já tem imagens preenchidas no DF.")
                self.progress = {"last_index": i + 1, "current_key_index": current_key_index}
                self.salvar_progresso(self.progress)
                continue

            if tem_url_fornecedor:
                print(f"⏩ Pulando '{produto}': possui URL do fornecedor (será tratada no upload).")
                self.progress = {"last_index": i + 1, "current_key_index": current_key_index}
                self.salvar_progresso(self.progress)
                continue

            # -------------------------------
            # 2) NÃO TEM IMAGEM → BUSCAR NO GOOGLE
            # -------------------------------
            tentativa = 0

            while True:
                if tentativa >= len(self.keys):
                    print("🚫 Todas as chaves atingiram o limite.")
                    self.salvar_progresso({"last_index": i, "current_key_index": current_key_index})
                    return self.df

                api_key = self.keys[current_key_index]

                try:
                    imagens = self.buscar_imagens(query, api_key, cx="532347d8c03cc4861", num=3)

                    if not imagens:
                        print(f"⚠ Nenhum resultado encontrado para: {produto}")
                        break

                    for j, img in enumerate(imagens):
                        link = img.get("link")
                        if not link:
                            continue

                        # ---------------------------
                        # BLACKLIST → ignorar links proibidos
                        # ---------------------------
                        if self.url_bloqueada(link):
                            print(f"⛔ Ignorando link bloqueado: {link}")
                            continue

                        nome_limpo = re.sub(r'[\\/*?:"<>|]', "_", produto[:40])
                        nome_arquivo = f"{j+1}_{nome_limpo.replace(' ', '_')}.jpg"
                        caminho = os.path.join(self.output_folder, nome_arquivo)

                        try:
                            self.baixar_imagem(link, caminho)
                        except Exception as e:
                            print(f"❌ Erro ao baixar imagem {j+1} de {produto}: {e}")

                    break  # terminou produto

                except Exception as e:
                    erro = str(e)

                    if "Quota" in erro or "403" in erro or "disabled" in erro:
                        print(f"⚠ Limite atingido para chave {current_key_index + 1}. Trocando...")
                        current_key_index = (current_key_index + 1) % len(self.keys)
                        tentativa += 1
                        continue

                    print(f"❌ Erro no produto '{produto}': {erro}")
                    break

            # Progresso
            self.progress = {
                "last_index": i + 1,
                "current_key_index": current_key_index,
            }
            self.salvar_progresso(self.progress)
            time.sleep(1)

        return self.df
