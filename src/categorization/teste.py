import pandas as pd
from rapidfuzz import fuzz


class AgrupadorFuzzyPaiFilho:
    def __init__(
        self,
        df: pd.DataFrame,
        col_codigo="Codigo Produto",
        col_Descricao_Limpa="Descricao_Limpa",
        col_dominio="Dominio",
        threshold=80,
    ):
        self.df = df.copy()
        self.col_codigo = col_codigo
        self.col_Descricao_Limpa = col_Descricao_Limpa
        self.col_dominio = col_dominio
        self.threshold = threshold

        self.df["grupo_id"] = None
        self.df["codigo_pai"] = None
        self.df["tipo_relacionamento"] = None
        self.df["score_fuzzy"] = None

    def _normalizar(self, texto: str) -> str:
        texto = texto.lower()
        texto = "".join(c for c in texto if c.isalnum() or c.isspace())
        return texto.strip()

    def _criar_grupos(self):
        grupo_atual = 0

        for dominio, df_dom in self.df.groupby(self.col_dominio):
            indices = df_dom.index.tolist()
            textos = df_dom[self.col_Descricao_Limpa].apply(self._normalizar).to_dict()

            visitados = set()

            for i in indices:
                if i in visitados:
                    continue

                grupo_atual += 1
                self.df.at[i, "grupo_id"] = grupo_atual
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
                continue

            # PAI = descrição mais curta
            df_ordenado = df_grupo.copy()
            df_ordenado["len_desc"] = df_ordenado[self.col_Descricao_Limpa].str.len()

            pai_idx = (
                df_ordenado
                .sort_values(["len_desc", self.col_codigo])
                .index[0]
            )

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


df = pd.read_excel('/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados.xlsx')

agrupador = AgrupadorFuzzyPaiFilho(
    df,
    col_codigo="Codigo Produto",
    col_Descricao_Limpa="Descricao_Limpa",
    col_dominio="Dominio",
    threshold=80
)

df_resultado = agrupador.processar()


agrupador = AgrupadorFuzzyPaiFilho(
    df,
    col_codigo="Codigo Produto",
    col_Descricao_Limpa="Descricao_Limpa",
    col_dominio="Dominio",
    threshold=80
)

df_resultado = agrupador.processar()



df_resultado.to_excel('Teste.xlsx', index=False)
