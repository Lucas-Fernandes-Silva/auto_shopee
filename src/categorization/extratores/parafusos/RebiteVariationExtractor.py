import re


class RebiteVariationExtractor:
    MODELOS_VALIDOS = {
        "412", "414", "416", "525", "314", "316", "410", "306",
        "310", "319", "408", "419", "422", "425", "514", "516",
        "530", "312"
    }

    PADRAO_RM = re.compile(r"\b(RM\s*\d{3})\b", re.IGNORECASE)
    PADRAO_MODELO = re.compile(r"\b(\d{3})\b")

    PALAVRAS_GUARDA = [
        "REBITE",
        "POP",
        "RM"
    ]

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {}

        texto = descricao.upper()

        # ---------- GUARDA ----------
        if not any(p in texto for p in self.PALAVRAS_GUARDA):
            return {}

        resultado = {
            "Tipo_Rebite": "POP"
        }

        # ---------- 1) PRIORIDADE: RM + MODELO ----------
        match_rm = self.PADRAO_RM.search(texto)
        if match_rm:
            modelo_completo = match_rm.group(1)  # preserva exatamente como veio

            match_num = re.search(r"\d{3}", modelo_completo)
            if match_num:
                modelo_num = match_num.group()

                if modelo_num in self.MODELOS_VALIDOS:
                    resultado["Modelo_Rebite"] = modelo_completo
                    return resultado

        # ---------- 2) FALLBACK: MODELO NUMÉRICO ----------
        candidatos = self.PADRAO_MODELO.findall(texto)

        for modelo in candidatos:
            if modelo in self.MODELOS_VALIDOS:
                resultado["Modelo_Rebite"] = modelo
                return resultado

        return {}
