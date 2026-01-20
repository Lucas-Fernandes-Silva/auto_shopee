import re


class TipoLampadaExtractor:
    PADRAO_LED = re.compile(r"\bled\b", re.IGNORECASE)
    PADRAO_FLUOR = re.compile(r"fluorescente|cfl", re.IGNORECASE)
    PADRAO_HALOGENA = re.compile(r"halogen", re.IGNORECASE)
    PADRAO_INCAN = re.compile(r"incand", re.IGNORECASE)

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Tipo_Lampada": None}

        desc = descricao.lower()

        if self.PADRAO_LED.search(desc):
            return {"Tipo_Lampada": "LED"}

        if self.PADRAO_FLUOR.search(desc):
            return {"Tipo_Lampada": "FLUORESCENTE"}

        if self.PADRAO_HALOGENA.search(desc):
            return {"Tipo_Lampada": "HALOGENA"}

        if self.PADRAO_INCAN.search(desc):
            return {"Tipo_Lampada": "INCANDESCENTE"}

        return {"Tipo_Lampada": None}
