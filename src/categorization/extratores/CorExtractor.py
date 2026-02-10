import re


class CorExtractor:
    CORES = {
        "BRANCO": ["branco"],
        "PRETO": ["preto", "black"],
        "CINZA": ["cinza", "cinza claro"],
        "AZUL": ["azul"],
        "VERDE": ["verde"],
        "AMARELO": ["amarelo"],
        "VERMELHO": ["vermelho"],
        "TRANSPARENTE": ["transparente", "cristal"],
    }

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Cor": None}

        desc = descricao.lower()

        for cor, termos in self.CORES.items():
            for termo in termos:
                if re.search(rf"\b{termo}\b", desc):
                    return {"Cor": cor}

        return {"Cor": None}
