import os
import sys

import numpy as np
from rapidfuzz import fuzz
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.utils.normalizer import Normalizer  # ou usar sua função normalizar direto


class VariationGrouper:
    def __init__(self, df, limiar=90):
        self.df = df
        self.limiar = limiar

    def aplicar(self):
        df = self.df.copy()

        # --- Define categorias que exigem concatenação ---
        categorias_com_chave = {"CONEXÕES ESGOTO", "CONEXÕES ÁGUA"}

        # --- Normaliza e cria chave condicionalmente ---
        df["Chave"] = np.where(
            df["Categoria"].isin(categorias_com_chave),
            df["Categoria"].map(Normalizer.normalize)
            + " "
            + df["Descrição"].map(Normalizer.normalize),
            df["Descrição"].map(Normalizer.normalize),
        )

        # --- Inicializa colunas auxiliares ---
        df["ID_Variacao"], df["Tipo"], df["SKU_Pai"] = None, None, None

        # --- Agrupa por similaridade ---
        grupo_id, usados = 1, set()
        for i, linha in tqdm(df.iterrows(), total=len(df), desc="Agrupando variações"):
            if i in usados:
                continue

            chave_ref = linha["Chave"]
            similares = df.index[
                df["Chave"].map(lambda x: fuzz.token_sort_ratio(chave_ref, x) >= self.limiar)
            ].tolist()

            sku_pai = linha.get("Sku", linha.get("Código", i))
            df.loc[i, ["Tipo", "SKU_Pai", "ID_Variacao"]] = ["PAI", sku_pai, grupo_id]

            for idx in similares:
                if idx not in usados:
                    df.loc[idx, ["Tipo", "SKU_Pai", "ID_Variacao"]] = [
                        "FILHO" if idx != i else "PAI",
                        sku_pai,
                        grupo_id,
                    ]
                    usados.add(idx)

            grupo_id += 1

        return df.sort_values(["ID_Variacao", "Tipo"]).reset_index(drop=True)
