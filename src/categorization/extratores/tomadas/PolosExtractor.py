import re


class PolosExtractor:

    PADRAO_2P_T = re.compile(r"\b2p\s*\+\s*t\b", re.IGNORECASE)
    PADRAO_P_T = re.compile(r"\bp\s*\+\s*t\b", re.IGNORECASE)

    PADRAO_2P = re.compile(r"\b2p\b", re.IGNORECASE)

    COM_TERRA = re.compile(r"\bcom\s+terra\b", re.IGNORECASE)
    SEM_TERRA = re.compile(r"\bsem\s+terra\b", re.IGNORECASE)

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Polos": None}

        desc = descricao.lower()

        polos = None

        # Casos explícitos completos
        if self.PADRAO_2P_T.search(desc) or self.PADRAO_P_T.search(desc):
            polos = "2P+T"
        elif self.PADRAO_2P.search(desc):
            polos = "2P"

        # Ajustes por texto complementar
        if polos and self.SEM_TERRA.search(desc):
            polos = polos.replace("+T", "")

        if polos and self.COM_TERRA.search(desc) and "+T" not in polos:
            polos = polos + "+T"

        return {"Polos": polos}
