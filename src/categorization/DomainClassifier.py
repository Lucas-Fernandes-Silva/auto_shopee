import re

import pandas as pd


class DomainClassifier:
    def __init__(self, df_dominios: pd.DataFrame):
        self.df_dominios = df_dominios

    def classificar(self, descricao):
        if pd.isna(descricao):
            return None

        texto = descricao.upper()

        matches = []

        for _, row in self.df_dominios.iterrows():
            termo = row["termo"]
            dominio = row["dominio"]

            if re.search(rf"\b{re.escape(termo)}\b", texto):
                matches.append(dominio)

        if not matches:
            return None

        # domínio mais frequente ganha
        return max(set(matches), key=matches.count)
