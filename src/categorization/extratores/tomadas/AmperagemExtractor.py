import re


class AmperagemExtractor:

    PADRAO_20A = re.compile(r"\b20\s*(a|amp|amps)\b", re.IGNORECASE)
    PADRAO_10A = re.compile(r"\b10\s*(a|amp|amps)\b", re.IGNORECASE)

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Amperagem": None}

        desc = descricao.lower()

        # ⚠️ Ordem importa: 20A primeiro
        if self.PADRAO_20A.search(desc):
            return {"Amperagem": 20}

        if self.PADRAO_10A.search(desc):
            return {"Amperagem": 10}

        return {"Amperagem": None}
