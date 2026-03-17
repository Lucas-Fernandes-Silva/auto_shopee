import re


class ParafusoVariationExtractor:
    PADROES_CABECA = {
        "FLANGEADO": re.compile(r"\bFLANGEAD[OA]\b", re.IGNORECASE),
        "CHATA": re.compile(r"\bCHATA\b", re.IGNORECASE),
        "SEXTAVADO": re.compile(r"\bSEXTAVAD[OA]\b", re.IGNORECASE),
        "FRANCES": re.compile(r"\bFRANC[EÊ]S\b", re.IGNORECASE),
        "REDONDA": re.compile(r"\bREDOND[OA]\b", re.IGNORECASE),
        "PANELA": re.compile(r"\bPANELA\b", re.IGNORECASE),
    }

    PADROES_TIPO = {
        "CHIPBOARD": re.compile(
            r"\bCHIP(?:[\s\-]?BOARD|[\s\-]?BORD)\b", re.IGNORECASE
        ),
        "SOBERBA": re.compile(r"\bSOBERBA\b", re.IGNORECASE),
        "ROSCA METRICA": re.compile(r"\bROSCA\s+METRICA\b", re.IGNORECASE),
        "ROSCA MAQUINA": re.compile(
            r"\b(?:ROSCA\s+MAQUINA|MAQ(?:UINA)?)\b", re.IGNORECASE
        ),
        "AGULHA": re.compile(r"\bAGULHA\b", re.IGNORECASE),
        "DRYWALL": re.compile(r"\bDRYWALL\b", re.IGNORECASE),
        "TOMBETA": re.compile(r"\bTOMBETA\b", re.IGNORECASE),
        "BROCANTE": re.compile(r"\b(?:BROCANTE|ABROCANTE)\b", re.IGNORECASE),
    }

    PADRAO_MODELO_NUMERICO = re.compile(r"\b\d{4}\b")

    def _texto_para_match(self, texto: str) -> str:
        t = texto.upper().strip()

        # equivalências mínimas para matching
        t = re.sub(r"\bCHIP[\s\-]?BORD\b", "CHIPBOARD", t)
        t = re.sub(r"\bCHIP[\s\-]?BOARD\b", "CHIPBOARD", t)
        t = re.sub(r"\bABROCANTE\b", "BROCANTE", t)
        t = re.sub(r"\bFRANCÊS\b", "FRANCES", t)

        # remove códigos/modelos numéricos de 4 dígitos
        t = self.PADRAO_MODELO_NUMERICO.sub(" ", t)

        return re.sub(r"\s+", " ", t).strip()

    def _extrair_tipo_cabeca(self, texto: str) -> str | None:
        for tipo, padrao in self.PADROES_CABECA.items():
            if padrao.search(texto):
                return tipo
        return None

    def _extrair_tipo_parafuso(self, texto: str) -> str | None:
        for tipo, padrao in self.PADROES_TIPO.items():
            if padrao.search(texto):
                return tipo
        return None

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {}

        texto = self._texto_para_match(descricao)

        resultado = {}

        tipo_cabeca = self._extrair_tipo_cabeca(texto)
        if tipo_cabeca:
            resultado["Tipo_Cabeca"] = tipo_cabeca

        tipo_parafuso = self._extrair_tipo_parafuso(texto)
        if tipo_parafuso:
            resultado["Tipo_Parafuso"] = tipo_parafuso

        return resultado
