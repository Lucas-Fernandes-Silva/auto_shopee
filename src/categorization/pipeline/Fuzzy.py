import pandas as pd
from rapidfuzz import fuzz


class AgrupadorFuzzyPaiFilho:
    def __init__(
        self,
        df: pd.DataFrame,
        col_codigo="Codigo Produto",
        col_base="Nome_Produto_Base",
        col_variacao="Nome_Variacao",
        col_dominio="Dominio",
        coluna_marca="Marca",
        threshold=90,
    ):
        self.df = df.copy()
        self.col_codigo = col_codigo
        self.col_base = col_base
        self.col_variacao = col_variacao
        self.col_dominio = col_dominio
        self.coluna_marca = coluna_marca
        self.threshold = threshold

        self.df["grupo_id"] = None
        self.df["codigo_pai"] = None
        self.df["tipo_relacionamento"] = None
        self.df["score_fuzzy"] = None

    def _normalizar(self, texto: str) -> str:
        texto = str(texto).lower()
        texto = "".join(c for c in texto if c.isalnum() or c.isspace())
        return " ".join(texto.split()).strip()

    def _criar_grupos(self):
        grupo_atual = 0

        for (dominio, marca), df_sub in self.df.groupby([self.col_dominio, self.coluna_marca]):
            indices = df_sub.index.tolist()
            textos = df_sub[self.col_base].fillna("").apply(self._normalizar).to_dict()

            visitados = set()

            for i in indices:
                if i in visitados:
                    continue

                grupo_atual += 1
                self.df.at[i, "grupo_id"] = grupo_atual
                self.df.at[i, "score_fuzzy"] = 100
                visitados.add(i)

                for j in indices:
                    if j in visitados:
                        continue

                    score = fuzz.token_set_ratio(textos[i], textos[j])

                    if score >= self.threshold:
                        self.df.at[j, "grupo_id"] = grupo_atual
                        self.df.at[j, "score_fuzzy"] = score
                        visitados.add(j)

    def _definir_pai_filho(self):
        for grupo, df_grupo in self.df.groupby("grupo_id"):
            if len(df_grupo) == 1:
                idx = df_grupo.index[0]
                self.df.at[idx, "tipo_relacionamento"] = "PAI"
                self.df.at[idx, "codigo_pai"] = None
                self.df.at[idx, "score_fuzzy"] = 100
                continue

            df_ordenado = df_grupo.copy()
            df_ordenado["len_base"] = df_ordenado[self.col_base].fillna("").str.len()
            df_ordenado["tem_variacao"] = df_ordenado[self.col_variacao].fillna("").str.len()

            # prioridade:
            # 1. menor nome base
            # 2. menor nome variação
            # 3. menor código
            pai_idx = df_ordenado.sort_values(["len_base", "tem_variacao", self.col_codigo]).index[
                0
            ]

            codigo_pai = self.df.at[pai_idx, self.col_codigo]

            for idx in df_grupo.index:
                if idx == pai_idx:
                    self.df.at[idx, "tipo_relacionamento"] = "PAI"
                    self.df.at[idx, "codigo_pai"] = None
                    self.df.at[idx, "score_fuzzy"] = 100
                else:
                    self.df.at[idx, "tipo_relacionamento"] = "FILHO"
                    self.df.at[idx, "codigo_pai"] = codigo_pai

    def processar(self) -> pd.DataFrame:
        self._criar_grupos()
        self._definir_pai_filho()
        return self.df
