import os
import re
import sys

import pandas as pd
from rapidfuzz import fuzz, process

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.transform.large_products import HeavyClassifier
from src.utils.normalizer import Normalizer


class Merge:
    def __init__(self, df, project_path="/home/lucas-silva/auto_shopee/", debug=False):
        self.df = df
        self.project_path = project_path
        self.url_cloud = f"{self.project_path}/urls_cloudinary.csv"
        self.output_path = f"{self.project_path}planilhas/outputs/final_com_urls.xlsx" #Salvar em DF
        self.debug = debug

        # Normalização da descrição da base principal
        self.df["Descrição"] = (
            self.df["Descrição"]
            .astype(str)
            .apply(Normalizer.normalize)
        )

        # Carrega URLs já enviadas ao Cloudinary
        self.urls_df = pd.read_csv(self.url_cloud, header=None, names=["arquivo", "url"])

        # Colunas criadas no url.py
        self.cols_imgs = ["Url_Imagem1.0", "Url_Imagem2.0", "Url_Imagem3.0", "Url Imagem"]

        # Garante que existem no dataframe
        for col in self.cols_imgs:
            if col not in self.df.columns:
                self.df[col] = None

    # ============================================================
    # Extrair informações do nome do arquivo
    # ============================================================
    @staticmethod
    def extrair_info(arquivo):
        arquivo = str(arquivo)

        # Numero da imagem: "_1_", "_2_", ...
        num_img = re.search(r"_(\d+)_", arquivo)
        num_img = int(num_img.group(1)) if num_img else None

        # Remove prefixos como "123_1_"
        desc_raw = re.sub(r"^\d+_\d+_", "", arquivo)

        # Normaliza a parte limpa
        descricao = Normalizer.normalize(desc_raw.replace("_", " "))

        return pd.Series([descricao, num_img])

    # ============================================================
    # Fuzzy Match Para Encontrar Produto na Base
    # ============================================================
    def melhor_match(self, descricao, limiar=70):
        desc_norm = Normalizer.normalize(descricao)

        if desc_norm in self.descs_norm:
            idx = self.descs_norm.index(desc_norm)
            return self.descs_final[idx]

        # Caso não seja match exato, usa fuzzy
        match = process.extractOne(desc_norm, self.descs_norm, scorer=fuzz.ratio)

        if self.debug:
            print("DEBUG:", descricao, "→", match)

        if not match:
            return None

        _, score, idx = match
        if score < limiar:
            return None

        return self.descs_final[idx]

    # ============================================================
    # EXECUÇÃO COMPLETA
    # ============================================================
    def run(self):
        # Extrai dados do nome do arquivo
        self.urls_df[["descricao_extraida", "num_imagem"]] = \
            self.urls_df["arquivo"].apply(self.extrair_info)

        self.urls_df = self.urls_df.dropna(subset=["descricao_extraida"])

        # Listas para comparação
        self.descs_final = self.df["Descrição"].unique().tolist()
        self.descs_norm = [Normalizer.normalize(x) for x in self.descs_final]

        # Fuzzy match
        self.urls_df["descricao_final"] = \
            self.urls_df["descricao_extraida"].apply(self.melhor_match)

        # Remove imagens sem match
        self.urls_df = self.urls_df.dropna(subset=["descricao_final"])

        # ============================================================
        # Preencher colunas originais criadas no url.py
        # ============================================================

        # Mapeia número da imagem para a coluna exata
        map_colunas = {
            1: "Url_Imagem1.0",
            2: "Url_Imagem2.0",
            3: "Url_Imagem3.0",
            None: "Url Imagem"
        }

        # Dicionário: {descricao_final: {coluna: url}}
        urls_dict = {}

        for _, row in self.urls_df.iterrows():
            desc = row["descricao_final"]
            num = row["num_imagem"]
            url = row["url"]

            coluna = map_colunas.get(num)

            if desc not in urls_dict:
                urls_dict[desc] = {}

            urls_dict[desc][coluna] = url

        # Preenche no df principal
        for idx, row in self.df.iterrows():
            desc = row["Descrição"]

            if desc in urls_dict:
                for coluna, valor in urls_dict[desc].items():
                    self.df.at[idx, coluna] = valor

        # Salvar arquivo final
        self.df.to_excel(self.output_path, index=False)

        print("🔥 URLs preenchidas nas colunas originais do url.py!")
        print(f"📄 Arquivo salvo em: {self.output_path}")

        return self.df


df = pd.read_excel('/home/lucas-silva/auto_shopee/planilhas/outputs/baixados.xlsx')
merge = Merge(df)
juntos = merge.run()


classifier = HeavyClassifier(df)
df_pesados, df_restante = classifier.classify()

print()

classifier.save(restante_path="produtos_padrao.xlsx")
classifier.save(pesados_path="grandes.xlsx")
