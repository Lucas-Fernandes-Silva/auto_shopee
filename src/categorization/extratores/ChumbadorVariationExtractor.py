class ChumbadorAncoraVariationExtractor:
    MEDIDAS_VALIDAS = {
        "1/4 X 2",
        "1/4 X 3",
        "5/16 X 2 1/2",
        "3/8 X 2 1/2",
        "3/8 X 3 1/2",
    }

    def extrair(self, descricao: str):
        descricao = descricao.upper()

        # ---------- GUARDA ----------
        if "CHUMBADOR" not in descricao or "ANCORA" not in descricao:
            return {}

        resultado = {
            "Tipo_Chumbador": "ANCORA"
        }

        # ---------- MEDIDA ----------
        for medida in self.MEDIDAS_VALIDAS:
            if medida in descricao:
                resultado["Medida"] = medida
                break

        return resultado
