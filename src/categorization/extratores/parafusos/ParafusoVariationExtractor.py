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

        # -------------------------
        # 2. MEDIDA ÚNICA (DIÂMETRO X COMPRIMENTO)
        # -------------------------
        texto_norm = texto.replace(",", ".")

        match = re.search(
            r"\b(\d+(?:\.\d+)?)\s*[Xx]\s*(\d+)\b",
            texto_norm,
        )

        if match:
            diametro = match.group(1)
            comprimento = match.group(2)
            resultado["Medida"] = f"{diametro}X{comprimento}"

        return resultado
