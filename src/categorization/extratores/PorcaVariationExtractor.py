import re


class PorcaVariationExtractor:
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
        if "PORCA" not in descricao:
            return {}

        resultado = {}

        # ---------- TIPO ----------
        if "BORBOLETA" in descricao:
            resultado["Tipo_Porca"] = "BORBOLETA"
        elif "TORNEADA" in descricao:
            resultado["Tipo_Porca"] = "TORNEADA"
        else:
            resultado["Tipo_Porca"] = "SEXTAVADA"

        # ---------- TAMANHO (FRAÇÕES) ----------
        fracoes = re.findall(r"\b\d+/\d+\b", descricao)
        for f in fracoes:
            if f in self.TAMANHOS_VALIDOS:
                resultado["Tamanho"] = f
                return resultado

        # ---------- TAMANHO (MÉTRICO) ----------
        if "M5" in descricao:
            resultado["Tamanho"] = "M5"

        return resultado
