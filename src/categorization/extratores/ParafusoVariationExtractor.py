import re


class ParafusoVariationExtractor:
    TIPOS = {
        "DRYWALL",
        "CHIPBOARD",
        "CHIPBORD",
        "BROCANTE",
        "MAQUINA",
        "SEXTAVADO",
        "ROSCA",
        "CHATA",
        "FRANCES",
    }

    def extrair(self, descricao: str):
        descricao = descricao.upper()

        # ---------- GUARDA DE SEGURANÇA ----------
        if "PARAFUSO" not in descricao:
            return {}

        resultado = {}

        # ---------- TIPO ----------
        for tipo in self.TIPOS:
            if tipo in descricao:
                resultado["Tipo_Parafuso"] = tipo
                break

        # ---------- MEDIDAS ----------
        match = re.search(
            r"(\d+(?:[.,]\d+)?(?:/\d+)?)\s*[Xx]\s*(\d+(?:[.,]\d+)?)",
            descricao,
        )

        if match:
            resultado["Diametro"] = match.group(1)
            resultado["Comprimento"] = match.group(2)

        return resultado
