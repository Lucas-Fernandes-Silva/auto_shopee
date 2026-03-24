import re


class PotenciaLampadaExtractor:
    PADRAO_W = re.compile(r"\b(\d{1,3})\s*(w|watts?)\b", re.IGNORECASE)

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Potencia_W": None}

        match = self.PADRAO_W.search(descricao.lower())
        if match:
            return {"Potencia_W": f"{int(match.group(1))}W"}

        return {"Potencia_W": None}
