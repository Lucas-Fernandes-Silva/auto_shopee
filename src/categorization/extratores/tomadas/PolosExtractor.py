import re


class PolosExtractor:
    PADRAO_3P_T = re.compile(r"\b3p\s*[\+\-\s]?\s*t\b", re.IGNORECASE)
    PADRAO_2P_T = re.compile(r"\b2p\s*[\+\-\s]?\s*t\b", re.IGNORECASE)
    PADRAO_P_T = re.compile(r"\bp\s*[\+\-\s]?\s*t\b", re.IGNORECASE)

    PADRAO_3P = re.compile(r"\b3p\b", re.IGNORECASE)
    PADRAO_2P = re.compile(r"\b2p\b", re.IGNORECASE)
    PADRAO_1P = re.compile(r"\b1p\b", re.IGNORECASE)

    COM_TERRA = re.compile(r"\bcom\s+terra\b", re.IGNORECASE)
    SEM_TERRA = re.compile(r"\bsem\s+terra\b", re.IGNORECASE)

    PADROES_DISJUNTOR = {
        "UNIPOLAR": re.compile(r"\bunipolar\b", re.IGNORECASE),
        "BIPOLAR": re.compile(r"\bbipolar\b", re.IGNORECASE),
        "TRIPOLAR": re.compile(r"\btripolar\b", re.IGNORECASE),
    }

    def aplica(self, descricao: str) -> bool:
        if not descricao:
            return False

        return any(
            padrao.search(descricao)
            for padrao in (
                self.PADRAO_3P_T,
                self.PADRAO_2P_T,
                self.PADRAO_P_T,
                self.PADRAO_3P,
                self.PADRAO_2P,
                self.PADRAO_1P,
                self.COM_TERRA,
                self.SEM_TERRA,
                *self.PADROES_DISJUNTOR.values(),
            )
        )

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Polos": None}

        desc = descricao.lower()
        polos = None

        # prioridade 1: padrões tipo 3P+T, 2P, 1P etc.
        if self.PADRAO_3P_T.search(desc):
            polos = "3P+T"
        elif self.PADRAO_2P_T.search(desc) or self.PADRAO_P_T.search(desc):
            polos = "2P+T"
        elif self.PADRAO_3P.search(desc):
            polos = "3P"
        elif self.PADRAO_2P.search(desc):
            polos = "2P"
        elif self.PADRAO_1P.search(desc):
            polos = "1P"

        # ajustes com terra
        if polos and self.SEM_TERRA.search(desc):
            polos = polos.replace("T", "")

        if polos and self.COM_TERRA.search(desc) and "T" not in polos:
            polos = polos + "T"

        # prioridade 2: padrões textuais de disjuntor
        if not polos:
            for valor, regex in self.PADROES_DISJUNTOR.items():
                if regex.search(descricao):
                    polos = valor
                    break

        return {"Polos": polos}
