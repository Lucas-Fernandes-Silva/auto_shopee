import re


class PolosDisjuntorExtractor:
    PADROES = {
        "Unipolar": re.compile(r"\b(1p|unipolar)\b", re.IGNORECASE),
        "Bipolar": re.compile(r"\b(2p|bipolar)\b", re.IGNORECASE),
        "Tripolar": re.compile(r"\b(3p|tripolar)\b", re.IGNORECASE),
    }

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Polos": None}

        for polos, regex in self.PADROES.items():
            if regex.search(descricao):
                return {"Polos": polos}

        return {"Polos": None}
