def aplicar_limpeza_nome_base(df):
    df = df.copy()

    df["Descricao_Limpa"] = df["Descricao_Limpa"].fillna("").astype(str)

    # limpeza base
    df["Descricao_Limpa"] = (
        df["Descricao_Limpa"]
        # remover quantidade comercial
        .str.replace(r"\bC/\s*\d+\b", "", regex=True)
        .str.replace(r"\b\d+\s*UN\b", "", regex=True)
        .str.replace(r"\b\d+\s*PC\b", "", regex=True)


        # remover "CAIXA" quando for ruído comercial,
        # mas preservar em nomes reais de produto
        .str.replace(r"\bCAIXA\b(?!\s*(D'?AGUA|ACOPLADA|DE\s+(PASSAGEM|LUZ)))", "", regex=True)
        # acabamentos comerciais
        .str.replace(r"\bBICR\b", "", regex=True)
        .str.replace(r"\bBICROM\b", "", regex=True)
        .str.replace(r"\bB5\b", "", regex=True)
        .str.replace(r"\bB6\b", "", regex=True)
        .str.replace(r"\bB8\b", "", regex=True)
        .str.replace(r"\bB10\b", "", regex=True)
        .str.replace(r"\bEZ9X33112\b", "", regex=True)
        .str.replace(r"\bEZ9X33212\b", "", regex=True)
        .str.replace(r"\b222 - 413\b", "", regex=True)
        .str.replace(r"\b222 - 412\b", "", regex=True)
        .str.replace(r"\b221 - 412\b", "", regex=True)
        .str.replace(r"\b221 - 413\b", "", regex=True)
        .str.replace(r"\b221 - 612\b", "", regex=True)
        .str.replace(r"\b1\/2GZ\b", "", regex=True)
        .str.replace(r"\b12F210B\b", "", regex=True)




    )

    # remover EMBALAGEM apenas onde NÃO tiver FITA
    mask_sem_fita = ~df["Descricao_Limpa"].str.contains(
        r"\bFITA\b", case=False, regex=True, na=False
    )

    df.loc[mask_sem_fita, "Descricao_Limpa"] = df.loc[mask_sem_fita, "Descricao_Limpa"].str.replace(
        r"\bEMBALAGEM\b", "", regex=True
    )

    # normalização final
    df["Descricao_Limpa"] = df["Descricao_Limpa"].str.replace(r"\s+", " ", regex=True).str.strip()

    return df
