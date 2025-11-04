import pandas as pd


class PrecoVenda:
    """
    Calcula o preço de venda ideal considerando comissões, taxas e margem de lucro.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        coluna_custo: str = 'Valor_unitário',
        comissao: float = 0.18,
        taxa_transacao: float = 0.02,
        taxa_fixa: float = 4.0,
        margem_lucro: float = 0.10
    ):
        """
        :param df: DataFrame contendo os preços de custo.
        :param coluna_custo: Nome da coluna que contém o preço de custo.
        :param comissao: Percentual de comissão da plataforma (ex: 0.18 = 18%).
        :param taxa_transacao: Percentual de taxa de transação (ex: 0.02 = 2%).
        :param taxa_fixa: Taxa fixa aplicada em pedidos acima de R$8,00.
        :param margem_lucro: Margem de lucro desejada (ex: 0.10 = 10%).
        """
        self.df = df.copy()
        self.coluna_custo = coluna_custo
        self.comissao_percentual = comissao
        self.taxa_transacao_percentual = taxa_transacao
        self.taxa_fixa_padrao = taxa_fixa
        self.margem_lucro_desejada = margem_lucro

        # Garante que a coluna de custo seja numérica
        if self.coluna_custo not in self.df.columns:
            raise KeyError(f"A coluna '{self.coluna_custo}' não existe no DataFrame.")

        self.df[self.coluna_custo] = pd.to_numeric(self.df[self.coluna_custo], errors='coerce')

    def _calcular_preco_venda(self, preco_custo) -> pd.Series:
        """
        Calcula o preço de venda, taxas e lucro para um item individual.
        """
        # Ignora valores inválidos
        if pd.isna(preco_custo) or preco_custo <= 0:
            return pd.Series({'Preço Final': None, 'Taxas': None, 'Lucro': None})

        # Taxa fixa variável
        taxa_aplicada = preco_custo / 2 if preco_custo <= 8 else self.taxa_fixa_padrao

        # Percentual total sobre o preço de venda
        total_percentuais = (
            self.comissao_percentual
            + self.taxa_transacao_percentual
            + self.margem_lucro_desejada
        )

        # Cálculo principal
        preco_venda = (preco_custo + taxa_aplicada) / (1 - total_percentuais)
        comissao = preco_venda * self.comissao_percentual
        taxa_transacao = preco_venda * self.taxa_transacao_percentual
        total_taxas = comissao + taxa_transacao + taxa_aplicada
        lucro = preco_venda - preco_custo - total_taxas

        return pd.Series({
            'Preço Final': round(preco_venda, 2),
            'Taxas': round(total_taxas, 2),
            'Lucro': round(lucro, 2),
        })

    def aplicar(self) -> pd.DataFrame:
        """
        Aplica o cálculo de preço de venda a todo o DataFrame.
        """
        resultados = self.df[self.coluna_custo].apply(self._calcular_preco_venda)
        self.df = pd.concat([self.df, resultados], axis=1)
        return self.df
