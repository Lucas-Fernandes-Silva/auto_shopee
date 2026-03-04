import pandas as pd


class VariationPipeline:
    """
    Pipeline de extração de variações por domínio.

    - Não sobrescreve campos já preenchidos (a menos que a prioridade seja maior).
    - Suporta prioridade por extractor (método priority() ou atributo PRIORITY).
    - Respeita aplica(descricao) quando existir.
    - Pode gerar colunas de debug com origem dos campos.
    """

    def __init__(self, dominio_extractors: dict, debug: bool = False):
        self.dominio_extractors = dominio_extractors or {}
        self.debug = debug

    def _get_priority(self, extractor) -> int:
        # extractor.priority() > extractor.PRIORITY > 0
        try:
            if hasattr(extractor, "priority") and callable(getattr(extractor, "priority")):
                return int(extractor.priority())
        except Exception:
            pass

        try:
            if hasattr(extractor, "PRIORITY"):
                return int(getattr(extractor, "PRIORITY"))
        except Exception:
            pass

        return 0

    def extrair(self, descricao: str, dominio: str):
        if not isinstance(descricao, str) or not descricao.strip():
            if self.debug:
                return {}, {}
            return {}

        extractors = self.dominio_extractors.get(dominio, [])
        valores = {}
        origem = {}  # campo -> {"source": str, "priority": int}

        for extractor in extractors:
            try:
                # aplica() opcional
                if hasattr(extractor, "aplica") and callable(getattr(extractor, "aplica")):
                    if not extractor.aplica(descricao):
                        continue

                resultado = extractor.extrair(descricao)
                if not isinstance(resultado, dict) or not resultado:
                    continue

                p = self._get_priority(extractor)
                nome_ex = extractor.__class__.__name__

                for campo, valor in resultado.items():
                    if valor is None:
                        continue
                    valor_str = str(valor).strip()
                    if valor_str == "":
                        continue

                    if campo not in valores:
                        valores[campo] = valor_str
                        if self.debug:
                            origem[campo] = {"source": nome_ex, "priority": p}
                        continue

                    # campo já existe: só troca se prioridade for maior
                    if self.debug:
                        p_atual = origem.get(campo, {}).get("priority", 0)
                    else:
                        p_atual = 0

                    # Se não tem debug, ainda assim dá pra comparar prioridade se existir:
                    # nesse caso, assume que o atual tem prioridade 0.
                    if p > p_atual:
                        valores[campo] = valor_str
                        if self.debug:
                            origem[campo] = {"source": nome_ex, "priority": p}

            except Exception:
                continue

        if self.debug:
            return valores, origem
        return valores

    def processar_linha(self, row):
        descricao = row.get("Descricao_Limpa")
        dominio = row.get("Dominio")

        if self.debug:
            valores, origem = self.extrair(descricao, dominio)
            s = pd.Series(valores, dtype='object')

            # adiciona colunas de debug: Origem__Campo
            for campo, info in origem.items():
                s.at[f"Origem__{campo}"] = f"{info.get('source')}|p={info.get('priority')}"
            return s

        valores = self.extrair(descricao, dominio)
        return pd.Series(valores)

    def aplicar(self, df: pd.DataFrame):
        variacoes = df.apply(self.processar_linha, axis=1)
        return pd.concat([df, variacoes], axis=1)


df_dominios = pd.read_excel('')

variation_pipeline = VariationPipeline(dominio_extractors={}, debug=True)
df_final = variation_pipeline.aplicar(df_dominios)
