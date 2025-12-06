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

        # Remove duplicados por descrição
        self.df = df.drop_duplicates(subset=["Descrição"], keep="first").reset_index(drop=True)

        self.progress_file = progress
        self.keys_file_path = keys_file
        self.output_folder = output_folder

        # Colunas que indicam imagens já existentes
        self.cols_imgs = ["Url_Imagem1.0", "Url_Imagem2.0", "Url_Imagem3.0", "Url Imagem"]
        for col in self.cols_imgs:
            if col not in self.df.columns:
                self.df[col] = None

        os.makedirs(self.output_folder, exist_ok=True)

        # Carregar estado
        self.progress = self.carregar_progresso()
        self.keys = self.carregar_chaves()

        # Domínios proibidos (somente o domínio base!)
        self.blacklist = [
            "scribd.com",
            "fliphtml5.com",
            "yumpu.com",
            "pubhtml5.com",
            "aliexpress.com",
            "ebay.com",
            "amazon.ae",
            "mackglobe.com",
            "sciencedirect.com",
            "percar.com.br",
            "atacadistasigma.com.br",
            "casadolojista.com.br",
            "ccpvirtual.com.br",
            "gfixdistribuidora.com.br",
            "econominet.com.br",
            "barzel.com.br",
            "eletroleste.com.br",
            "comercialmaia.com.br",
        ]

    # ============================================================
    # PROGRESSO
    # ============================================================
    def carregar_progresso(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r") as f:
                    data = json.load(f)
                return {
                    "produtos_processados": data.get("produtos_processados", {}),
                    "current_key_index": data.get("current_key_index", 0),
                }
            except Exception:
                pass

        return {"produtos_processados": {}, "current_key_index": 0}

    def salvar_progresso(self):
        with open(self.progress_file, "w") as f:
            json.dump(self.progress, f, indent=2)

    # ============================================================
    # CHAVES
    # ============================================================
    def carregar_chaves(self):
        with open(self.keys_file_path, "r") as f:
            data = json.load(f)
        return data["keys"]

    # ============================================================
    # BLACKLIST POR DOMÍNIO
    # ============================================================
    def url_bloqueada(self, url):
        if not isinstance(url, str):
            return True

        try:
            url = url.strip().lower()

            # Remove protocolo e www
            url = url.replace("https://", "").replace("http://", "").replace("www.", "")

            # Extrair domínio base
            dominio = re.split(r"[/?#:]", url)[0].strip()

            # Remover porta caso exista
            dominio = dominio.split(":")[0]

        except Exception:
            return True

        # Bloqueia se o domínio terminar com algum domínio proibido
        return any(
            dominio == b or dominio.endswith(b)
            for b in self.blacklist
        )

    # ============================================================
    # BUSCAR IMAGENS
    # ============================================================
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

        # Erros da API
        if response.status_code == 403 or "error" in data:
            msg = data.get("error", {}).get("message", "")
            raise Exception(f"API Error: {msg}")

        response.raise_for_status()
        return data.get("items", [])

    # ============================================================
    # DOWNLOAD
    # ============================================================
    def baixar_imagem(self, url, save_path):
        try:
            resp = requests.get(url, stream=True, timeout=10)
            if resp.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(1024):
                        f.write(chunk)
                return True
            return False
        except Exception:
            return False

    # ============================================================
    # EXECUÇÃO PRINCIPAL
    # ============================================================
    def run(self):
        produtos_processados = self.progress["produtos_processados"]
        current_key_index = self.progress["current_key_index"]

        print(f"🚀 Iniciando busca com chave {current_key_index+1}/{len(self.keys)}")

        for i in tqdm(range(len(self.df)), desc="Buscando imagens"):

            produto = str(self.df.loc[i, "Descrição"]).strip()
            codigo_produto = str(self.df.loc[i, "Codigo Produto"]).strip()

            # (1) Já processado antes?
            if codigo_produto in produtos_processados:
                continue

            # (2) Já tem imagens válidas?
            tem_img_boa = any(
                pd.notna(self.df.loc[i, col]) and str(self.df.loc[i, col]).strip() != ""
                for col in ["Url_Imagem1.0", "Url_Imagem2.0", "Url_Imagem3.0"]
            )

            url_fornecedor = self.df.loc[i, "Url Imagem"]
            tem_fornecedor = pd.notna(url_fornecedor) and str(url_fornecedor).strip() != ""

            if tem_img_boa:
                produtos_processados[codigo_produto] = True
                self.salvar_progresso()
                continue

            if tem_fornecedor:
                produtos_processados[codigo_produto] = True
                self.salvar_progresso()
                continue

            # (3) Buscar imagens no Google
            tentativa = 0

            while True:
                api_key = self.keys[current_key_index]

                try:
                    imagens = self.buscar_imagens(
                        produto,
                        api_key,
                        cx="532347d8c03cc4861",
                        num=3,
                    )

                    if not imagens:
                        break

                    for j, img in enumerate(imagens):
                        link = img.get("link")

                        # Link inválido
                        if not link:
                            continue

                        # Blacklist por domínio
                        if self.url_bloqueada(link):
                            print(f"⛔ BLOQUEADO: {link}")
                            continue

                        # Nome do arquivo
                        nome_limpo = re.sub(r'[\\/*?:"<>|]', "_", produto[:40])
                        nome_arquivo = f"{j+1}_{nome_limpo.replace(' ', '_')}.jpg"
                        caminho = os.path.join(self.output_folder, nome_arquivo)

                        # Baixar imagem
                        self.baixar_imagem(link, caminho)

                    break

                except Exception as e:
                    err = str(e)

                    # Trocar chave se limite atingido
                    if "quota" in err.lower() or "403" in err:
                        current_key_index = (current_key_index + 1) % len(self.keys)
                        tentativa += 1

                        if tentativa >= len(self.keys):
                            self.salvar_progresso()
                            return self.df
                        continue

                    break

            # Marcar como processado
            produtos_processados[codigo_produto] = True
            self.progress["current_key_index"] = current_key_index
            self.salvar_progresso()

            time.sleep(1)

        return self.df


