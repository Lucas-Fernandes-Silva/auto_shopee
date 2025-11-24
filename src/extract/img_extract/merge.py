import re

import pandas as pd
from rapidfuzz import fuzz, process

from src.utils.normalizer import Normalizer


class Merge:
    def __init__(self, df, project_path="/home/lucas-silva/auto_shopee/", debug=False):
        self.df = df
        self.project_path = project_path
        self.url_cloud = f"{self.project_path}/urls_cloudinary.csv"
        self.output_path = f"{self.project_path}planilhas/outputs/final_com_urls.xlsx"
        self.debug = debug

        # Normaliza descrição da planilha principal
        self.df["Descrição"] = (
            self.df["Descrição"]
            .astype(str)
            .apply(Normalizer.normalize)
        )

        # Carrega URLs do Cloudinary
        self.urls_df = pd.read_csv(self.url_cloud, header=None, names=["arquivo", "url"])

    # ============================================================
    # 1. Extrair informações do nome do arquivo
    # ============================================================
    @staticmethod
    def extrair_info(arquivo):
        arquivo = str(arquivo)

        # Número da imagem
        num_img = re.search(r"_(\d+)_", arquivo)
        num_img = int(num_img.group(1)) if num_img else None

        # Remove prefixos como "123_1_"
        desc_raw = re.sub(r"^\d+_\d+_", "", arquivo)

        # Trata underline e normaliza
        descricao = Normalizer.normalize(desc_raw.replace("_", " "))

        return pd.Series([descricao, num_img])

    # ============================================================
    # 2. Fuzzy Matching
    # ============================================================
    def melhor_match(self, descricao, limiar=70):
        desc_norm = Normalizer.normalize(descricao)

        # Listas pré-processadas
        descs_final = self.descs_final
        descs_norm = self.descs_norm

        # Se bate exatamente, usa direto
        if desc_norm in descs_norm:
            idx = descs_norm.index(desc_norm)
            return descs_final[idx]

        # Caso contrário, fuzzy match
        match = process.extractOne(
            desc_norm,
            descs_norm,
            scorer=fuzz.ratio
        )

        if self.debug:
            print("DEBUG:", descricao, "→", match)

        if match is None:
            return None

        best_norm, score, idx = match

        if score < limiar:
            return None

        return descs_final[idx]

    # ============================================================
    # 3. Pipeline completo
    # ============================================================
    def run(self):
        # Extrai infos
        self.urls_df[["descricao_extraida", "num_imagem"]] = \
            self.urls_df["arquivo"].apply(self.extrair_info)

        self.urls_df = self.urls_df.dropna(subset=["descricao_extraida"])

        # Prepara listas de comparação
        self.descs_final = self.df['Descrição'].unique().tolist()
        self.descs_norm = [Normalizer.normalize(x) for x in self.descs_final]

        # Aplica fuzzy match
        self.urls_df["descricao_final"] = self.urls_df["descricao_extraida"].apply(
            self.melhor_match
        )

        self.urls_df = self.urls_df.dropna(subset=["descricao_final"])

        # Pivot com URLs
        urls_pivot = self.urls_df.pivot_table(
            index="descricao_final",
            columns="num_imagem",
            values="url",
            aggfunc="first"
        )

        # Renomeia colunas (Url_Imagem1, Url_Imagem2, ...)
        urls_pivot.columns = [f"Url_Imagem{i}" for i in urls_pivot.columns]
        urls_pivot = urls_pivot.reset_index()

        # Merge final
        merged_df = self.df.merge(
            urls_pivot,
            left_on="Descrição",
            right_on="descricao_final",
            how="left"
        ).drop(columns=["descricao_final"])

        # Salva
        merged_df.to_excel(self.output_path, index=False)

        print("✅ URLs adicionadas com sucesso!")
        print(f"📄 Arquivo salvo em: {self.output_path}")

        return merged_df
