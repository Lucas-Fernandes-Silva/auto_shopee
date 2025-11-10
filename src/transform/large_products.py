import re

import pandas as pd

df = pd.read_excel('/home/lucas-silva/auto_shopee/planilhas/outputs/final.xlsx')

coluna_desc = "Base"   # <-- Agora usando Base

palavras_grande = [
    r"\bporta\b", r"\btelha\b", r"\btubo\b", r"\bgabinete\b", r"\bvaso\b",
    r"\blavatorio\b", r"\bcaixa d'?agua\b", r"\btela\b", r"\bviveiro\b",
    r"\bcimento\b", r"\bargamassa\b", r"\bmassa corrida\b", r"\btinta\b",
    r"\btanque\b", r"\bpia\b", r"\bdescarga\b", r"\bpá\b", r"\benxada\b",
    r"\bforcado\b", r"\bcavadeira\b", r"\bcabo\b", r"\bcalha\b",
    r"\brodo\b", r"\bvassoura\b", r"\bextensor\b", r"\bvaral\b",
    r"\bvedatop\b", r"\bcarrinho de mão\b", r"\bescada\b",
    r"\brégua\b", r"\bcantoneira\b"
]

excecoes = [
    r"\bparafuso\b",
    r"\bsuporte\b",
    r"\bfixador\b",
    r"\bmini\b",
    r"\bkit\b"
]

regex_grande = "|".join(palavras_grande)
regex_excecao = "|".join(excecoes)

df_grande = df[
    df[coluna_desc].str.contains(regex_grande, flags=re.IGNORECASE, na=False)
    & ~df[coluna_desc].str.contains(regex_excecao, flags=re.IGNORECASE, na=False)
]

df_restante = df.drop(df_grande.index)
