import re


class PolosDisjuntorExtractor:
    PADROES = {
        "UNIPOLAR": re.compile(r"\b(unipolar)\b", re.IGNORECASE),
        "BIPOLAR": re.compile(r"\b(bipolar)\b", re.IGNORECASE),
        "TRIPOLAR": re.compile(r"\b(tripolar)\b", re.IGNORECASE),
    }

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Polos": None}

        for polos, regex in self.PADROES.items():
            if regex.search(descricao):
                return {"Polos": polos}

        return {"Polos": None}
