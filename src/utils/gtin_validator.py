import pandas as pd


class GTINValidator:
    def __init__(self, df, fornecedores_web_scraping):
        self.df = df
        self.fornecedores_web_scraping = fornecedores_web_scraping

    def is_valid_gtin(self, codigo):
        return str(codigo).isdigit() and len(str(codigo)) in [8, 12, 13, 14]

    def filter_priority(self):
        df = self.df.copy()
        df["GTIN_Válido"] = df["Código de Barras"].astype(str).apply(self.is_valid_gtin)

        def escolher_prioritario(grupo):
            fornecedores = grupo["Fornecedor"].tolist()
            preferidos = [
                f for f in fornecedores if f in self.fornecedores_web_scraping
            ]
            return (
                grupo[grupo["Fornecedor"].isin(preferidos)].head(1)
                if preferidos
                else grupo.head(1)
            )

        df_validos = df[df["GTIN_Válido"]]
        df_filtrado = df_validos.groupby("Código de Barras", group_keys=False).apply(
            escolher_prioritario
        )
        df_final = pd.concat([df_filtrado, df[~df["GTIN_Válido"]]], ignore_index=True)
        return df_final.reset_index(drop=True)
