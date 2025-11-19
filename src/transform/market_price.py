import pandas as pd


class PrecoVenda:
    def __init__(
        self,
        df: pd.DataFrame,
        coluna_custo: str = 'Valor_unitário',
        comissao: float = 0.18,
        taxa_transacao: float = 0.02,
        taxa_fixa: float = 4.0,
        margem_lucro: float = 0.10  # margem sobre o custo
    ):
        self.df = df.copy()
        self.coluna_custo = coluna_custo
        self.comissao = comissao
        self.taxa_transacao = taxa_transacao
        self.taxa_fixa_padrao = taxa_fixa
        self.margem = margem_lucro

        if self.coluna_custo not in self.df.columns:
            raise KeyError(f"A coluna '{self.coluna_custo}' não existe no DataFrame.")
        self.df[self.coluna_custo] = pd.to_numeric(self.df[self.coluna_custo], errors='coerce')

    def _calcular_preco_venda(self, custo):
        if pd.isna(custo) or custo <= 0:
            return pd.Series({'Preço Final': None, 'Taxas': None, 'Lucro': None, 'Tipo Taxa': None})

        com = self.comissao
        tx = self.taxa_transacao
        m = self.margem

        if custo <= 2.18:
            f = 0.5  # 50% do preço
            denom = 1 - f - com - tx
            if denom <= 0:
                raise ValueError("Denominador inválido (soma de percentuais >= 1). Verifique taxas/margem.")
            preco_venda = custo * (1 + m) / denom
            taxa_fixa_val = preco_venda * f
            tipo = "50% do preço"
        else:
            denom = 1 - com - tx
            if denom <= 0:
                raise ValueError("Denominador inválido (soma de percentuais >= 1). Verifique taxas/margem.")
            taxa_fixa_val = self.taxa_fixa_padrao
            preco_venda = (custo * (1 + m) + taxa_fixa_val) / denom
            tipo = f"R$ {self.taxa_fixa_padrao:.2f} fixo"

        comissao_val = preco_venda * com
        taxa_trans_val = preco_venda * tx
        total_taxas = comissao_val + taxa_trans_val + taxa_fixa_val
        lucro = custo * m  # margem sobre o custo

        return pd.Series({
            'Preço Final': round(preco_venda, 2),
            'Taxas': round(total_taxas, 2),
            'Lucro': round(lucro, 2),
            'Tipo Taxa': tipo
        })

    def aplicar(self) -> pd.DataFrame:
        resultados = self.df[self.coluna_custo].apply(self._calcular_preco_venda)
        self.df = pd.concat([self.df, resultados], axis=1)
        return self.df


df = pd.read_excel("/home/lucas-silva/auto_shopee/final_com_urls.xlsx")
preco = PrecoVenda(df)
df = preco.aplicar()

df.to_excel('taxas_corrigidas.xlsx', index=False)
