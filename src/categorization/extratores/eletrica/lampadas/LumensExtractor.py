import re


class LumensExtractor:
    PADRAO_LM = re.compile(r"\b(\d{1,5})\s*lm\b", re.IGNORECASE)

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Lumens": None}

        desc = descricao.lower()

        match = self.PADRAO_LM.search(desc)
        if match:
            return {"Lumens": f"{match.group(1)}LM"}

        return {"Lumens": None}
