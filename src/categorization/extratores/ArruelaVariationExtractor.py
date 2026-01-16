import re


class ArruelaVariationExtractor:
    TAMANHOS_VALIDOS = {
        "1/8",
        "3/16",
        "5/32",
        "1/4",
        "5/16",
        "3/8",
        "1/2",
        "M5",
    }

    def extrair(self, descricao: str):
        descricao = descricao.upper()

        # ---------- GUARDA ----------
        if "ARRUELA" not in descricao:
            return {}

        # ⚠️ ARRUELA FAZ PARTE DO PARAFUSO → IGNORAR
        if "PARAFUSO" in descricao:
            return {}

        resultado = {}

        # ---------- TIPO ----------
        if "PRESSAO" in descricao or "PRESSÃO" in descricao:
            resultado["Tipo_Arruela"] = "PRESSAO"
        else:
            resultado["Tipo_Arruela"] = "LISA"

        # ---------- TAMANHO ----------
        fracoes = re.findall(r"\b\d+/\d+\b", descricao)
        for f in fracoes:
            if f in self.TAMANHOS_VALIDOS:
                resultado["Tamanho"] = f
                return resultado

        if "M5" in descricao:
            resultado["Tamanho"] = "M5"

        return resultado
