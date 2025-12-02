import re

import pandas as pd

from dados import dados


class HeavyClassifier:

    def __init__(self, df):
        self.df = df
        self.column = 'Descrição'
        self.heavy_keywords = dados.heavy_keywords
        self.exclude_keywords = dados.exclude_keywords


        self.df_pesados = None
        self.df_restante = None
        self.df_custo_baixo = None

    def classify(self):
        pesados_dict = {}

        for idx, desc in self.df[self.column].items():
            d = str(desc).upper()

            # 1 — Exclusões diretas
            if any(ex in d for ex in self.exclude_keywords):
                continue

            # 2 — Massa corrida ou massa acrílica leve
            if ("MASSA CORRIDA" in d or "MASSA ACR" in d) and any(
                x in d for x in ["1KG", "900G", "500G", "3.6KG"]
            ):
                continue

            # 3 — Tintas pesadas somente 15/18/20L
            if "TINTA" in d and not any(x in d for x in ["15", "18L", "20L"]):
                continue

            # 4 — Checagem principal (regex)
            if any(re.search(k, d) for k in self.heavy_keywords):
                pesados_dict[idx] = desc

        # ----------------------------------------------------------------------
        # 5 — Separação dos DataFrames
        # ----------------------------------------------------------------------
        self.df_pesados = self.df.loc[self.df.index.isin(pesados_dict.keys())].copy()
        restante = self.df.loc[~self.df.index.isin(pesados_dict.keys())].copy()

        # -------- NOME REAL DA COLUNA (AJUSTE AQUI SE NECESSÁRIO) --------------
        col = "Tipo Taxa"     # mude para "Tipo de Taxa" se for esse o nome real
        # ------------------------------------------------------------------------

        # Custo baixo → qualquer taxa que tenha %
        cond_custo_baixo = restante[col] \
            .astype(str) \
            .str.contains(r'\d+\s*%\s*', regex=True, na=False)

        # Taxa fixa → qualquer valor com 4.00
        cond_taxa_fixa = restante[col].astype(str).str.contains(r"4\.00", regex=True, na=False)

        # --- DF custo baixo ---
        self.df_custo_baixo = restante.loc[cond_custo_baixo].copy()

        # --- DF restante (tudo que não é custo baixo e não é taxa fixa) ---
        self.df_restante = restante.loc[~cond_custo_baixo & ~cond_taxa_fixa].copy()

        # --- Une taxa fixa ao restante ---
        df_taxa_fixa = restante.loc[cond_taxa_fixa].copy()
        self.df_restante = pd.concat([self.df_restante, df_taxa_fixa], ignore_index=True).drop_duplicates()

        return self.df_pesados, self.df_restante, self.df_custo_baixo


