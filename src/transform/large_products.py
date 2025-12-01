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
        self.df_custo_baixo = None   # << NOVO DF >>

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

        # --------------------------
        # 5 — Separação dos DataFrames
        # --------------------------
        self.df_pesados = self.df.loc[self.df.index.isin(pesados_dict.keys())].copy()
        restante = self.df.loc[~self.df.index.isin(pesados_dict.keys())].copy()

        # NOVOS FILTROS DE TAXA
        cond_custo_baixo = restante['Tipo de Taxa'].astype(str).str.contains("50%", case=False)
        cond_taxa_fixa = restante['Tipo de Taxa'].astype(str).str.contains("4.00", case=False)

        # 5.1 — DF custo baixo
        self.df_custo_baixo = restante.loc[cond_custo_baixo].copy()

        # 5.2 — DF restante (agora filtrado)
        self.df_restante = restante.loc[~cond_custo_baixo].copy()

        # ainda separar os que tem taxa fixa
        df_taxa_fixa = restante.loc[cond_taxa_fixa].copy()

        # junta os taxa fixa no df_restante
        self.df_restante = pd.concat([self.df_restante, df_taxa_fixa]).drop_duplicates()

        return self.df_pesados, self.df_restante, self.df_custo_baixo

    def save(self, pesados_path=None, restante_path=None, custo_baixo_path=None):
        """Salvar arquivos excel opcionalmente."""
        if pesados_path:
            self.df_pesados.to_excel(pesados_path, index=False) # type: ignore
        if restante_path:
            self.df_restante.to_excel(restante_path, index=False) # type: ignore
        if custo_baixo_path:
            self.df_custo_baixo.to_excel(custo_baixo_path, index=False) # type: ignore
