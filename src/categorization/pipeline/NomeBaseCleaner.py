def aplicar_limpeza_nome_base(df):
    df = df.copy()

    df["Descricao_Limpa"] = df["Descricao_Limpa"].fillna("").astype(str)

    df["Descricao_Limpa"] = (
        df["Descricao_Limpa"]
        # remover quantidade comercial
        .str.replace(r"\bC/\s*\d+\b", "", regex=True)
        .str.replace(r"\b\d+\s*UN\b", "", regex=True)
        .str.replace(r"\b\d+\s*PC\b", "", regex=True)
        .str.replace(r"^((?!\bFITA\b).)*\bEMBALAGEM\b", "", regex=True)
        .str.replace(r"\bCAIXA\b(?!\s*(D'?AGUA|ACOPLADA|DE\s+(PASSAGEM|LUZ)))", "", regex=True)

        # acabamentos comerciais
        .str.replace(r"\bBICR\b", "", regex=True)
        .str.replace(r"\bBICROM\b", "", regex=True)
        .str.replace(r"\bB5\b", "", regex=True)
        .str.replace(r"\bB6\b", "", regex=True)
        .str.replace(r"\bB8\b", "", regex=True)
        .str.replace(r"\bB10\b", "", regex=True)
        # normalização
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    return df
