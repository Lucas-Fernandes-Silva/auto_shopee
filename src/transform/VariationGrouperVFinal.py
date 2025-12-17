class VariationGrouperVFinal:
    def __init__(
        self,
        sku_col="Codigo Produto",
        categoria_alvo="TOMADAS INTERRUPTORES PINOS",
    ):
        self.sku_col = sku_col
        self.categoria_alvo = categoria_alvo.upper()

    # =========================
    # Validação de escopo
    # =========================
    def _categoria_valida(self, categoria):
        return categoria and categoria.upper().strip() == self.categoria_alvo

    # =========================
    # Chave pai
    # =========================
    def _chave_pai(self, row):
        grupo = row["Grupo_Eletrico"]
        marca = row["Marca"]

        if grupo in {"CONJUNTO", "MODULO", "PLACA"}:
            partes = [
                marca,
                grupo,
                row.get("linha"),
                row.get("formato"),
                row.get("cor"),
            ]

        elif grupo == "PROLONGADOR":
            partes = [
                marca,
                grupo,
                row.get("formato"),
                row.get("amperagem"),
            ]

        elif grupo == "PLUG_MACHO":
            partes = [
                marca,
                grupo,
                row.get("polos"),
            ]

        else:
            partes = [marca, grupo, row.get(self.sku_col)]

        partes = [str(p) for p in partes if p not in (None, "", "nan")]
        return "|".join(partes)

    # =========================
    # Aplicação
    # =========================
    def aplicar(self, df):
        df = df.copy()

        # separa apenas a categoria alvo
        mask = df["Categoria"].apply(self._categoria_valida)

        # inicializa colunas
        df["chave_pai"] = None
        df["ID_Variacao"] = None
        df["SKU_Pai"] = None
        df["Tipo"] = "PAI"

        # aplica somente nos elétricos
        df_eletrico = df[mask].copy()

        if df_eletrico.empty:
            return df

        # cria chave pai
        df_eletrico["chave_pai"] = df_eletrico.apply(self._chave_pai, axis=1)

        # ID de variação
        df_eletrico["ID_Variacao"] = df_eletrico.groupby("chave_pai").ngroup() + 1

        # SKU pai
        df_eletrico["SKU_Pai"] = df_eletrico.groupby("ID_Variacao")[self.sku_col].transform("first")

        # Tipo
        df_eletrico["Tipo"] = "FILHO"
        df_eletrico.loc[
            df_eletrico[self.sku_col] == df_eletrico["SKU_Pai"],
            "Tipo",
        ] = "PAI"

        # devolve ao df original
        df.update(df_eletrico)

        return df.sort_values(
            ["ID_Variacao", "Tipo"],
            na_position="last",
        ).reset_index(drop=True)
