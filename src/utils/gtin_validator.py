import random

import pandas as pd


class GTINValidator:
    def __init__(self, df, fornecedores_web_scraping):
        self.df = df
        self.fornecedores_web_scraping = set(fornecedores_web_scraping)

    def is_valid_gtin(self, codigo):
        codigo = str(codigo)
        return codigo.isdigit() and len(codigo) in [8, 12, 13, 14]

    def filter_priority(self):
        df = self.df.copy()
        df["GTIN_Válido"] = df["Código de Barras"].astype(str).apply(self.is_valid_gtin)

        # Marca os fornecedores preferidos
        df["Fornecedor_Preferido"] = df["Fornecedor"].isin(self.fornecedores_web_scraping)

        # Separa válidos e inválidos
        df_validos = df[df["GTIN_Válido"]].copy()
        df_invalidos = df[~df["GTIN_Válido"]].copy()

        # Ordena preferindo fornecedores preferidos
        df_validos = df_validos.sort_values(
            by=["Código de Barras", "Fornecedor_Preferido"], ascending=[True, False]
        )

        # Mantém apenas o primeiro fornecedor por GTIN
        df_filtrado = df_validos.drop_duplicates(subset=["Código de Barras"], keep="first")

        # Junta inválidos novamente
        df_final = pd.concat([df_filtrado, df_invalidos], ignore_index=True)

        # Remove colunas auxiliares
        df_final = df_final.drop(columns=["Fornecedor_Preferido"])

        return df_final.reset_index(drop=True)

    # --- Novo método com seed interno ---
    def gerar_gtins_aleatorios(self, df_filtrado, seed=42):
        # Garante resultados repetíveis
        random.seed(seed)

        df = df_filtrado.copy()

        # Coleta GTINs válidos existentes
        gtins_existentes = set(
            df.loc[df["Código de Barras"].astype(str).apply(self.is_valid_gtin), "Código de Barras"]
        )

        def gerar_gtin_aleatorio_unico():
            while True:
                numeros = [random.randint(0, 9) for _ in range(12)]
                soma = sum(num * (3 if i % 2 else 1) for i, num in enumerate(numeros))
                digito = (10 - (soma % 10)) % 10
                numeros.append(digito)
                gtin = ''.join(map(str, numeros))
                if gtin not in gtins_existentes:
                    gtins_existentes.add(gtin)
                    return gtin

        # Máscara para GTINs inválidos ou vazios
        mask_invalido = ~df["Código de Barras"].astype(str).apply(self.is_valid_gtin)

        # Substitui apenas os inválidos
        df.loc[mask_invalido, "Código de Barras"] = [
            gerar_gtin_aleatorio_unico() for _ in range(mask_invalido.sum())
        ]

        # Atualiza a flag de validade
        df["GTIN_Válido"] = df["Código de Barras"].astype(str).apply(self.is_valid_gtin)

        return df.reset_index(drop=True)
