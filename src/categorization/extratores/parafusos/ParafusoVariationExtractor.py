import re


class ParafusoVariationExtractor:
    TIPOS_PARAFUSO = {
        "SEXTAVADO": ["SEXTAVADO"],
        "CHATA_PHILIPS": ["CHATA", "PHILIPS"],
        "FRANCES": ["FRANCES", "FRANCÊS"],
        "MAQUINA": ["MAQ", "MAQUINA"],
        "ROSCA": ["ROSCA"],
        "BROcante": ["BROCANTE", "ABROCANTE"],
    }

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str):
            return {}

        texto = descricao.upper()

        resultado = {}

        # -------------------------
        # 1. TIPO DE PARAFUSO
        # -------------------------
        for tipo, palavras in self.TIPOS_PARAFUSO.items():
            if all(p in texto for p in palavras):
                resultado["Tipo_Parafuso"] = tipo
                break

        return resultado
