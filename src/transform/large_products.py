import re

from dados import dados


class HeavyClassifier:

    def __init__(self, df):
        self.df = df
        self.column = 'Descrição'
        self.heavy_keywords = dados.heavy_keywords
        self.exclude_keywords = dados.exclude_keywords

        self.df_pesados = None
        self.df_restante = None

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

        # Criação dos DataFrames
        self.df_pesados = self.df.loc[self.df.index.isin(pesados_dict.keys())].copy()
        self.df_restante = self.df.loc[~self.df.index.isin(pesados_dict.keys())].copy()

        return self.df_pesados, self.df_restante

    def save(self, pesados_path=None, restante_path=None):
        """Salvar arquivos excel opcionalmente."""
        if pesados_path:
            self.df_pesados.to_excel(pesados_path, index=False) # type: ignore
        if restante_path:
            self.df_restante.to_excel(restante_path, index=False) # type: ignore
