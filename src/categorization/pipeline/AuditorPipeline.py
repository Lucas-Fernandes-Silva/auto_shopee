import numpy as np
import pandas as pd


class AuditorPipeline:
    def __init__(
        self,
        col_descricao="Descricao_Limpa",
        col_base="Nome_Produto_Base",
        col_variacao="Nome_Variacao",
        col_grupo="grupo_id",
        col_codigo_pai="codigo_pai",
        col_tipo="tipo_relacionamento",
        col_score="score_fuzzy",
        col_marca="Marca",
        col_dominio="Dominio",
        dominios_auditaveis=None,
    ):
        self.col_descricao = col_descricao
        self.col_base = col_base
        self.col_variacao = col_variacao
        self.col_grupo = col_grupo
        self.col_codigo_pai = col_codigo_pai
        self.col_tipo = col_tipo
        self.col_score = col_score
        self.col_marca = col_marca
        self.col_dominio = col_dominio
        self.dominios_auditaveis = set(dominios_auditaveis or [])

    def auditar(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        colunas_texto = [
            self.col_descricao,
            self.col_base,
            self.col_variacao,
            self.col_tipo,
            self.col_marca,
            self.col_dominio,
        ]

        for col in colunas_texto:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        if self.col_score in df.columns:
            df[self.col_score] = pd.to_numeric(df[self.col_score], errors="coerce")

        if self.dominios_auditaveis:
            mask_auditavel = df[self.col_dominio].isin(self.dominios_auditaveis)
        else:
            mask_auditavel = pd.Series(True, index=df.index)

        df["dominio_auditavel"] = mask_auditavel

        df["flag_base_vazia"] = mask_auditavel & df[self.col_base].eq("")
        df["flag_variacao_vazia"] = mask_auditavel & df[self.col_variacao].eq("")

        df["flag_base_igual_descricao"] = (
            mask_auditavel
            & (df[self.col_base].str.upper() == df[self.col_descricao].str.upper())
        )

        df["flag_base_muito_curto"] = (
            mask_auditavel
            & (df[self.col_base].str.len().fillna(0) <= 5)
        )

        if self.col_score in df.columns:
            df["flag_score_baixo"] = (
                mask_auditavel
                & (df[self.col_score].fillna(100) < 85)
            )
        else:
            df["flag_score_baixo"] = False

        df["flag_pai_com_variacao"] = (
            mask_auditavel
            & (df[self.col_tipo].str.upper() == "PAI")
            & (df[self.col_variacao] != "")
        )

        if self.col_codigo_pai in df.columns:
            df["flag_filho_sem_codigo_pai"] = (
                mask_auditavel
                & (df[self.col_tipo].str.upper() == "FILHO")
                & (
                    df[self.col_codigo_pai].isna()
                    | df[self.col_codigo_pai].astype(str).str.strip().eq("")
                    | df[self.col_codigo_pai].astype(str).str.lower().eq("nan")
                )
            )
        else:
            df["flag_filho_sem_codigo_pai"] = False

        if self.col_grupo in df.columns:
            grupo_size = df.groupby(self.col_grupo)[self.col_grupo].transform("size")
            df["grupo_tamanho"] = grupo_size

            marcas_por_grupo = (
                df.groupby(self.col_grupo)[self.col_marca]
                .transform(lambda s: s.nunique(dropna=True))
            )
            df["flag_marcas_multiplas_grupo"] = (
                mask_auditavel & (marcas_por_grupo > 1)
            )

            df["variacao_norm"] = df[self.col_variacao].str.upper().fillna("")
            dup_variacao = (
                df.groupby([self.col_grupo, "variacao_norm"])["variacao_norm"]
                .transform("size")
            )
            df["flag_variacao_duplicada_no_grupo"] = (
                mask_auditavel
                & (df["variacao_norm"] != "")
                & (dup_variacao > 1)
            )

            pais_por_grupo = (
                df.assign(_is_pai=df[self.col_tipo].str.upper().eq("PAI"))
                .groupby(self.col_grupo)["_is_pai"]
                .transform("sum")
            )
            df["flag_multiplos_pais_no_grupo"] = (
                mask_auditavel & (pais_por_grupo > 1)
            )

            df["flag_grupo_unitario_com_filho"] = (
                mask_auditavel
                & (df["grupo_tamanho"] == 1)
                & (df[self.col_tipo].str.upper() == "FILHO")
            )
        else:
            df["grupo_tamanho"] = np.nan
            df["flag_marcas_multiplas_grupo"] = False
            df["flag_variacao_duplicada_no_grupo"] = False
            df["flag_multiplos_pais_no_grupo"] = False
            df["flag_grupo_unitario_com_filho"] = False

        flags_cols = [c for c in df.columns if c.startswith("flag_")]

        def montar_status(row):
            if not row["dominio_auditavel"]:
                return "DOMINIO_NAO_AUDITADO"

            ativos = [col for col in flags_cols if bool(row[col])]
            return "OK" if not ativos else " | ".join(ativos)

        df["status_auditoria"] = df.apply(montar_status, axis=1)

        df["tem_suspeita"] = (
            df["dominio_auditavel"]
            & (df["status_auditoria"] != "OK")
        )

        colunas_inicio = [
            c for c in [
                self.col_dominio,
                self.col_marca,
                self.col_descricao,
                self.col_base,
                self.col_variacao,
                self.col_grupo,
                self.col_codigo_pai,
                self.col_tipo,
                self.col_score,
                "grupo_tamanho",
                "dominio_auditavel",
                "status_auditoria",
                "tem_suspeita",
            ]
            if c in df.columns
        ]

        colunas_flags = [c for c in df.columns if c.startswith("flag_")]
        colunas_restantes = [
            c for c in df.columns
            if c not in colunas_inicio + colunas_flags
        ]

        df = df[colunas_inicio + colunas_flags + colunas_restantes]

        return df

    def resumo(self, df_auditado: pd.DataFrame) -> pd.DataFrame:
        df_base = df_auditado[df_auditado["dominio_auditavel"]].copy()
        flags_cols = [c for c in df_base.columns if c.startswith("flag_")]

        resumo = []
        for col in flags_cols:
            qtd = int(df_base[col].sum())
            resumo.append({"Regra": col, "Quantidade": qtd})

        resumo_df = pd.DataFrame(resumo).sort_values("Quantidade", ascending=False)
        return resumo_df


if __name__ == "__main__":
    INPUT_XLSX = "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Com_Nomes.xlsx"
    OUTPUT_XLSX = "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Auditados.xlsx"

    # coloque aqui apenas os domínios que já possuem extractors/nomes prontos
    DOMINIOS_AUDITAVEIS = {
        "HIDRAULICA",
        "ELETRICA",
        "PARAFUSOS",
        "TOMADAS",
    }

    df = pd.read_excel(INPUT_XLSX, dtype=str)

    auditor = AuditorPipeline(
        dominios_auditaveis=DOMINIOS_AUDITAVEIS
    )

    df_auditado = auditor.auditar(df)
    df_resumo = auditor.resumo(df_auditado)
    df_suspeitas = df_auditado[df_auditado["tem_suspeita"]].copy()

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Resultado_Final", index=False)
        df_auditado.to_excel(writer, sheet_name="Auditoria", index=False)
        df_resumo.to_excel(writer, sheet_name="Resumo_Auditoria", index=False)
        df_suspeitas.to_excel(writer, sheet_name="Suspeitas", index=False)

    print(f"Auditoria gerada com sucesso: {OUTPUT_XLSX}")
