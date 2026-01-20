import re


class AmperagemExtractor:

    AMPERAGENS_VALIDAS = [63, 50, 40, 32, 25, 20, 16, 10, 6]

    def __init__(self):
        valores = "|".join(str(a) for a in self.AMPERAGENS_VALIDAS)
        self.PADRAO = re.compile(
            rf"\b({valores})\s*(a|amp|amps)\b",
            re.IGNORECASE,
        )

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Amperagem": None}

        match = self.PADRAO.search(descricao.lower())
        if match:
            return {"Amperagem": int(match.group(1))}

        return {"Amperagem": None}
