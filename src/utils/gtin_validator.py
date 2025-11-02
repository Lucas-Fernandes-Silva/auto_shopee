import pandas as pd


class GTINValidator:
    def __init__(self, df, fornecedores_web_scraping):
        self.df = df
        self.fornecedores_web_scraping = set(fornecedores_web_scraping)

    def is_valid_gtin(self, codigo):
        return str(codigo).isdigit() and len(str(codigo)) in [8, 12, 13, 14]

    def filter_priority(self):
        df = self.df.copy()
        df["GTIN_Válido"] = df["Código de Barras"].astype(str).apply(self.is_valid_gtin)

        # Marca os fornecedores que estão na lista de scraping
        df["Fornecedor_Preferido"] = df["Fornecedor"].isin(self.fornecedores_web_scraping)

        # Separa válidos e inválidos
        df_validos = df[df["GTIN_Válido"]].copy()
        df_invalidos = df[~df["GTIN_Válido"]].copy()

        # Ordena de modo que fornecedores preferidos venham primeiro
        df_validos = df_validos.sort_values(
            by=["Código de Barras", "Fornecedor_Preferido"], ascending=[True, False]
        )

        # Mantém apenas o primeiro fornecedor por GTIN (preferido se existir)
        df_filtrado = df_validos.drop_duplicates(subset=["Código de Barras"], keep="first")

        # Junta de volta os inválidos
        df_final = pd.concat([df_filtrado, df_invalidos], ignore_index=True)

        # Limpa colunas auxiliares
        df_final = df_final.drop(columns=["Fornecedor_Preferido"])

        return df_final.reset_index(drop=True)
