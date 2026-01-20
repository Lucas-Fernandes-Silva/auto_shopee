import re


class TemperaturaCorExtractor:
    PADRAO_K = re.compile(r"\b(2700|3000|4000|6500)\s*k\b", re.IGNORECASE)

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Temperatura_Cor": None}

        desc = descricao.lower()

        match = self.PADRAO_K.search(desc)
        if match:
            return {"Temperatura_Cor": f"{match.group(1)}K"}

        if "quente" in desc or "amarela" in desc:
            return {"Temperatura_Cor": "3000K"}

        if "neutra" in desc:
            return {"Temperatura_Cor": "4000K"}

        if "fria" in desc or "branca" in desc:
            return {"Temperatura_Cor": "6500K"}

        return {"Temperatura_Cor": None}
