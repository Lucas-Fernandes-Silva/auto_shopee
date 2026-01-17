import re


class RebiteVariationExtractor:
    MODELOS_VALIDOS = {
        "412", "414", "416", "525", "314", "316", "410", "306",
        "310", "319", "408", "419", "422", "425", "514", "516",
        "530", "312"
    }

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str):
            return {}

        texto = descricao.upper()

        # 1️⃣ RM + número
        match_rm = re.search(r"\bRM\s*(\d{3})\b", texto)
        if match_rm:
            modelo = match_rm.group(1)
            if modelo in self.MODELOS_VALIDOS:
                return {
                    "Tipo_Rebite": "POP",
                    "Modelo_Rebite": modelo
                }

        # 2️⃣ Apenas número
        match_num = re.search(r"\b(\d{3})\b", texto)
        if match_num:
            modelo = match_num.group(1)
            if modelo in self.MODELOS_VALIDOS:
                return {
                    "Tipo_Rebite": "POP",
                    "Modelo_Rebite": modelo
                }

        return {}
