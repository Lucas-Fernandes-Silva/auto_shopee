import re


class ParafusoVariationExtractor:
    TIPOS_PARAFUSO = {
        "SEXTAVADO": ["SEXTAVADO"],
        "CHATA PHILIPS": ["CHATA", "PHILIPS","CHIPBOARD CABECA CHATA PHILIPS"],
        "FRANCES": ["FRANCES"],
        "MAQUINA": ["MAQ"],
        "ROSCA": ["ROSCA"],
        "BROCANTE": ["BROCANTE", "ABROCANTE"],
    }

    ACABAMENTOS = ["BICR", "B5", "B6", "B10"]
    TOKENS_EMBALAGEM = ["EMBALAGEM", "EMB", "CAIXA"]

    PADROES_REMOVER = [
        r"\bCOM\s+\d+\b",  # COM 100 / COM 200
        r"\bC/\s*\d+\b",  # C/ 500
        r"\b\d+\s*EMB\b",  # 1EMB
    ]

    def _normalizar_termos(self, texto: str) -> str:
        t = texto.upper().strip()

        # cabeça
        t = re.sub(r"\bC/\s*CHATA\b", "CABECA CHATA", t)
        t = re.sub(r"\bC/\s*PANELA\b", "CABECA PANELA", t)
        t = re.sub(r"\bC/\s*SEXTAVADA\b", "CABECA SEXTAVADA", t)

        # caso venha errado de normalizações antigas
        t = re.sub(r"\bCOM\s+CHATA\b", "CABECA CHATA", t)
        t = re.sub(r"\bCOM\s+PANELA\b", "CABECA PANELA", t)
        t = re.sub(r"\bCOM\s+SEXTAVADA\b", "CABECA SEXTAVADA", t)

        # grafias equivalentes
        t = re.sub(r"\bCHIP[\s\-]?BOARD\b", "CHIPBOARD", t)
        t = re.sub(r"\bCHIP[\s\-]?BORD\b", "CHIPBOARD", t)
        t = re.sub(r"\bPHILLIPS\b", "PHILIPS", t)
        t = re.sub(r"\bMAQUINA\b", "MAQ", t)
        t = re.sub(r"\bFRANC[EÊ]S\b", "FRANCES", t)

        return re.sub(r"\s+", " ", t).strip()

    def _remover_ruidos(self, texto: str) -> str:
        t = texto

        # remove acabamentos
        for token in self.ACABAMENTOS:
            t = re.sub(rf"\b{re.escape(token)}\b", " ", t)

        # remove embalagem
        for token in self.TOKENS_EMBALAGEM:
            t = re.sub(rf"\b{re.escape(token)}\b", " ", t)

        # remove padrões comerciais
        for padrao in self.PADROES_REMOVER:
            t = re.sub(padrao, " ", t)

        return re.sub(r"\s+", " ", t).strip()

    def _normalizar_base(self, texto: str) -> str:
        t = self._normalizar_termos(texto)
        t = self._remover_ruidos(t)
        return re.sub(r"\s+", " ", t).strip()

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {}

        texto = self._normalizar_termos(descricao)
        resultado = {}

        # tipo do parafuso
        for tipo, palavras in self.TIPOS_PARAFUSO.items():
            if all(p in texto for p in palavras):
                resultado["Tipo_Parafuso"] = tipo
                break

        # base normalizada
        resultado["Nome_Produto_Base_Normalizado"] = self._normalizar_base(descricao)

        return resultado
