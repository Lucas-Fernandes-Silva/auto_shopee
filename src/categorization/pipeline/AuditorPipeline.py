import pandas as pd
import numpy as np


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
        col_produto_unico="produto_unico",
        col_chave="Chave_Agrupamento",
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
        self.col_produto_unico = col_produto_unico
        self.col_chave = col_chave
        self.dominios_auditaveis = set(dominios_auditaveis or [])

    def auditar(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # =========================
        # Normalizações básicas
        # =========================
        colunas_texto = [
            self.col_descricao,
            self.col_base,
            self.col_variacao,
            self.col_tipo,
            self.col_marca,
            self.col_dominio,
            self.col_chave,
        ]

        for col in colunas_texto:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        if self.col_score in df.columns:
            df[self.col_score] = pd.to_numeric(df[self.col_score], errors="coerce")

        if self.col_produto_unico in df.columns:
            df[self.col_produto_unico] = (
                df[self.col_produto_unico]
                .fillna(False)
                .astype(str)
                .str.upper()
                .isin(["TRUE", "1", "SIM"])
            )
        else:
            df[self.col_produto_unico] = False

        # =========================
        # Máscara de domínios auditáveis
        # =========================
        if self.dominios_auditaveis:
            mask_auditavel = df[self.col_dominio].isin(self.dominios_auditaveis)
        else:
            mask_auditavel = pd.Series(True, index=df.index)

        df["dominio_auditavel"] = mask_auditavel

        # =========================
        # Flags básicas
        # =========================
        df["flag_chave_agrupamento_vazia"] = (
            mask_auditavel
            & df[self.col_chave].eq("")
        )

        df["flag_base_vazia"] = (
            mask_auditavel
            & df[self.col_base].eq("")
        )

        # produto único pode ter variação vazia
        df["flag_variacao_vazia"] = (
            mask_auditavel
            & (~df[self.col_produto_unico])
            & df[self.col_variacao].eq("")
        )

        # base igual descrição só é suspeita quando não é produto único
        df["flag_base_igual_descricao"] = (
            mask_auditavel
            & (~df[self.col_produto_unico])
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

        # pai com variação é suspeito apenas se não for produto único
        df["flag_pai_com_variacao"] = (
            mask_auditavel
            & (~df[self.col_produto_unico])
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

        # =========================
        # Flags por grupo
        # =========================
        if self.col_grupo in df.columns:
            grupo_size = df.groupby(self.col_grupo)[self.col_grupo].transform("size")
            df["grupo_tamanho"] = grupo_size

            chaves_por_grupo = (
                df.groupby(self.col_grupo)[self.col_chave]
                .transform(lambda s: s.fillna("").nunique())
            )
            df["flag_grupo_com_chaves_diferentes"] = (
                mask_auditavel
                & (chaves_por_grupo > 1)
            )

            pais_por_grupo = (
                df.assign(_is_pai=df[self.col_tipo].str.upper().eq("PAI"))
                .groupby(self.col_grupo)["_is_pai"]
                .transform("sum")
            )
            df["flag_multiplos_pais_no_grupo"] = (
                mask_auditavel
                & (pais_por_grupo > 1)
            )

            df["flag_grupo_unitario_com_filho"] = (
                mask_auditavel
                & (df["grupo_tamanho"] == 1)
                & (df[self.col_tipo].str.upper() == "FILHO")
            )

            df["variacao_norm"] = df[self.col_variacao].str.upper().fillna("")
            dup_variacao = (
                df.groupby([self.col_grupo, "variacao_norm"])["variacao_norm"]
                .transform("size")
            )
            df["flag_variacao_duplicada_no_grupo"] = (
                mask_auditavel
                & (~df[self.col_produto_unico])
                & (df["variacao_norm"] != "")
                & (dup_variacao > 1)
            )
        else:
            df["grupo_tamanho"] = np.nan
            df["flag_grupo_com_chaves_diferentes"] = False
            df["flag_multiplos_pais_no_grupo"] = False
            df["flag_grupo_unitario_com_filho"] = False
            df["flag_variacao_duplicada_no_grupo"] = False

        # =========================
        # Flags específicas de PARAFUSOS
        # =========================
        if "Tipo_Parafuso" in df.columns and self.col_grupo in df.columns:
            tipos_parafuso_por_grupo = (
                df.groupby(self.col_grupo)["Tipo_Parafuso"]
                .transform(lambda s: s.fillna("").replace("", pd.NA).dropna().nunique())
            )
            df["flag_tipos_parafuso_diferentes"] = (
                mask_auditavel
                & df[self.col_dominio].eq("PARAFUSOS")
                & (tipos_parafuso_por_grupo > 1)
            )
        else:
            df["flag_tipos_parafuso_diferentes"] = False

        if "Tipo_Cabeca" in df.columns and self.col_grupo in df.columns:
            tipos_cabeca_por_grupo = (
                df.groupby(self.col_grupo)["Tipo_Cabeca"]
                .transform(lambda s: s.fillna("").replace("", pd.NA).dropna().nunique())
            )
            df["flag_tipos_cabeca_diferentes"] = (
                mask_auditavel
                & df[self.col_dominio].eq("PARAFUSOS")
                & (tipos_cabeca_por_grupo > 1)
            )
        else:
            df["flag_tipos_cabeca_diferentes"] = False

        # =========================
        # Status consolidado
        # =========================
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

        # =========================
        # Reordenar colunas
        # =========================
        colunas_inicio = [
            c for c in [
                self.col_dominio,
                self.col_marca,
                self.col_chave,
                self.col_descricao,
                self.col_base,
                self.col_variacao,
                self.col_produto_unico,
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
            resumo.append({
                "Regra": col,
                "Quantidade": int(df_base[col].sum())
            })

        if not resumo:
            return pd.DataFrame(columns=["Regra", "Quantidade"])

        return pd.DataFrame(resumo).sort_values("Quantidade", ascending=False)


if __name__ == "__main__":
    INPUT_XLSX = "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Com_Nomes.xlsx"
    OUTPUT_XLSX = "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Auditados.xlsx"

    DOMINIOS_AUDITAVEIS = {
        "HIDRAULICA",
        "ELETRICA",
        "PARAFUSOS",
        "TOMADAS",
    }

    df = pd.read_excel(INPUT_XLSX, dtype=str)

    auditor = AuditorPipeline(
        dominios_auditaveis=DOMINIOS_AUDITAVEIS,
        col_chave="Chave_Agrupamento",
        col_produto_unico="produto_unico",
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
