df["Produto_Base_ID"] = (
    df["grupo_id"].astype(str)
    + "|"
    + df["Marca"].str.upper().fillna("SEM_MARCA")
)


