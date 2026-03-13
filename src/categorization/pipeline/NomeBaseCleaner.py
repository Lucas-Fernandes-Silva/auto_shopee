import re
import pandas as pd


class NomeBaseCleaner:
    TOKENS_GERAIS = [
        "EMBALAGEM",
        "EMB",
        "CAIXA",
        "UNIDADE",
        "UN",
    ]

    PADROES_GERAIS = [
        r"\bCOM\s+\d+\b",     # COM 100 / COM 200
        r"\b\d+\s*EMB\b",     # 1EMB
    ]

    TOKENS_POR_DOMINIO = {
        "PARAFUSOS": ["BICR", "B5", "B6", "B10"],
    }

    PADROES_POR_DOMINIO = {
        "PARAFUSOS": [
            r"\bC/\s*\d+\b",   # C/ 500
        ]
    }

    def limpar(self, texto: str, dominio: str = "") -> str:
        if not isinstance(texto, str) or not texto.strip():
            return ""

        t = texto.upper().strip()

        # globais
        for token in self.TOKENS_GERAIS:
            t = re.sub(rf"\b{re.escape(token)}\b", " ", t)

        for padrao in self.PADROES_GERAIS:
            t = re.sub(padrao, " ", t)

        # por domínio
        dominio = (dominio or "")

        for token in self.TOKENS_POR_DOMINIO.get(dominio, []):
            t = re.sub(rf"\b{re.escape(token)}\b", " ", t)

        for padrao in self.PADROES_POR_DOMINIO.get(dominio, []):
            t = re.sub(padrao, " ", t)

        t = re.sub(r"\s+", " ", t).strip()
        return t

def aplicar_limpeza_nome_base(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cleaner = NomeBaseCleaner()

    df["Nome_Produto_Base"] = df.apply(
        lambda row: cleaner.limpar(
            row.get("Nome_Produto_Base", ""),
            row.get("Dominio", "")
        ),
        axis=1
    )

    return df
