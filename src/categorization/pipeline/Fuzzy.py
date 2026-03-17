import pandas as pd
from rapidfuzz import fuzz


class AgrupadorFuzzyPaiFilho:
    def __init__(
        self,
        df: pd.DataFrame,
        col_codigo="Codigo Produto",
        col_base="Nome_Produto_Base",
        col_variacao="Nome_Variacao",
        col_chave="Chave_Agrupamento",
        threshold=90,
    ):
        self.df = df.copy()
        self.col_codigo = col_codigo
        self.col_base = col_base
        self.col_variacao = col_variacao
        self.col_chave = col_chave
        self.threshold = threshold

        self.df["grupo_id"] = None
        self.df["codigo_pai"] = None
        self.df["tipo_relacionamento"] = None
        self.df["score_fuzzy"] = None

    def _normalizar(self, texto) -> str:
        if isinstance(texto, pd.Series):
            if texto.empty:
                return ""
            texto = texto.iloc[0]

        if texto is None or pd.isna(texto):
            return ""

        texto = str(texto).lower()
        texto = "".join(c for c in texto if c.isalnum() or c.isspace())
        return " ".join(texto.split()).strip()

    def _criar_grupos(self):
        grupo_atual = 0

        for chave, df_sub in self.df.groupby(self.col_chave, dropna=False):
            indices = df_sub.index.tolist()

            textos = {}
            for idx in indices:
                valor = df_sub.loc[idx, self.col_base]
                if isinstance(valor, pd.Series):
                    valor = valor.iloc[0]
                textos[idx] = self._normalizar(valor)

            visitados = set()

            for i in indices:
                if i in visitados:
                    continue

                grupo_atual += 1
                self.df.at[i, "grupo_id"] = grupo_atual
                self.df.at[i, "score_fuzzy"] = 100
                visitados.add(i)

                texto_i = textos.get(i, "")
                if not texto_i:
                    continue

                for j in indices:
                    if j in visitados:
                        continue

                    texto_j = textos.get(j, "")
                    if not texto_j:
                        continue

                    score = fuzz.token_set_ratio(texto_i, texto_j)

                    if score >= self.threshold:
                        self.df.at[j, "grupo_id"] = grupo_atual
                        self.df.at[j, "score_fuzzy"] = score
                        visitados.add(j)

    def _definir_pai_filho(self):
        for grupo, df_grupo in self.df.groupby("grupo_id", dropna=False):
            if pd.isna(grupo):
                continue

            if len(df_grupo) == 1:
                idx = df_grupo.index[0]
                self.df.at[idx, "tipo_relacionamento"] = "PAI"
                self.df.at[idx, "codigo_pai"] = None
                self.df.at[idx, "score_fuzzy"] = 100
                continue

            df_ordenado = df_grupo.copy()
            df_ordenado["len_base"] = df_ordenado[self.col_base].fillna("").astype(str).str.len()
            df_ordenado["len_variacao"] = df_ordenado[self.col_variacao].fillna("").astype(str).str.len()

            pai_idx = df_ordenado.sort_values(
                ["len_base", "len_variacao", self.col_codigo]
            ).index[0]

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
