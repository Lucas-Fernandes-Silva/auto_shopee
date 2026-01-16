import re


class BuchaVariationExtractor:
    TAMANHOS_VALIDOS = {"06", "08", "10", "12"}

    def extrair(self, descricao: str):
        descricao = descricao.upper()

        # ---------- GUARDA ----------
        if not any(x in descricao for x in ["BUCHA", "PITAO", "PITÃO", "GANCHO", "ESCAPULA"]):
            return {}


        resultado = {}

        # ---------- TIPO ----------
        if "DRYWALL" in descricao:
            resultado["Tipo_Bucha"] = "DRYWALL"
        elif "TIJOLO" in descricao:
            resultado["Tipo_Bucha"] = "TIJOLO"
        elif (
            "FIXACAO" in descricao
            or "FIXAÇÃO" in descricao
            or "PLASTICA" in descricao
            or "PLÁSTICA" in descricao
        ):
            resultado["Tipo_Bucha"] = "COMUM"
        else:
            resultado["Tipo_Bucha"] = "COMUM"

        # ---------- ANEL ----------
        if "ANEL" in descricao:
            resultado["Anel"] = "COM ANEL"
        else:
            resultado["Anel"] = "SEM ANEL"

        # ---------- TAMANHO ----------
        numeros = re.findall(r"\b\d{2}\b", descricao)
        for n in numeros:
            if n in self.TAMANHOS_VALIDOS:
                resultado["Tamanho"] = n
                break

        return resultado
