import pandas as pd

COLUNAS_POR_DOMINIO = {

"ELETRICA": [
        "Descricao_Limpa",
        "Score_Dominio",
        "Amperagem",
        "Polos",
        "Diametro",
        "Comprimento",
        "Formato_Caixa",
        "Capacidade_Centrinho",
        "Cor",
        "Marca",
        "grupo_id",
    ],
    "PARAFUSOS": [
        "Descricao_Limpa",
        "Score_Dominio",
        "Tipo_Parafuso",
        "Medida",
        "Material",
    ],
}


df_final = pd.read_excel("/home/lucas-silva/auto_shopee/Teste.xlsx")

with pd.ExcelWriter(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados_Por_Dominio.xlsx",
    engine="xlsxwriter"
) as writer:

    df_final.to_excel(writer, sheet_name="GERAL", index=False)

    for dominio, colunas in COLUNAS_POR_DOMINIO.items():
        df_dom = df_final[df_final["Dominio"] == dominio].copy()

        if df_dom.empty:
            continue

        # mantém só colunas que existem
        colunas_existentes = [
            c for c in colunas if c in df_dom.columns
        ]

        df_dom[colunas_existentes].to_excel(
            writer,
            sheet_name=dominio[:31],  # limite do Excel
            index=False
        )
