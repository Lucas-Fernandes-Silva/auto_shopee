import re


class MedidaAxBExtractor:

    # número simples / decimal
    NUM = r"\d+(?:[.,]\d+)?"

    # fração simples
    FRAC = r"\d+/\d+"

    # fração mista com espaço: 1 1/2
    MIXED = r"\d+\s+\d+/\d+"

    # qualquer eixo possível
    EIXO = rf"(?:{MIXED}|{FRAC}|{NUM})"

    # unidade opcional
    UN = r'(?:\s*(?:MM|CM|MT|M|MTS|METRO|METROS|\"|\'))?'

    # 3 dimensões
    PADRAO_3D = re.compile(
        rf"(?<![\d/.,])"
        rf"({EIXO}){UN}\s*[xX×]\s*({EIXO}){UN}\s*[xX×]\s*({EIXO}){UN}"
        rf"(?![\d/.,])",
        re.IGNORECASE,
    )

    # 2 dimensões
    PADRAO_2D = re.compile(
        rf"(?<![\d/.,])"
        rf"({EIXO}){UN}\s*[xX×]\s*({EIXO}){UN}"
        rf"(?![\d/.,])",
        re.IGNORECASE,
    )

    # medida tipo 38/40MM
    PADRAO_BARRA_UNIDADE = re.compile(
        r"(?<![\d])(\d+(?:[.,]\d+)?/\d+(?:[.,]\d+)?\s*(?:MM|CM|M|MT|MTS|METRO|METROS))\b",
        re.IGNORECASE,
    )

    def _trecho_exato(self, descricao: str, match: re.Match) -> str:
        return descricao[match.start():match.end()].strip()

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {"Medida": None}

        # 1) AxBxC primeiro
        m3 = self.PADRAO_3D.search(descricao)
        if m3:
            return {"Medida": self._trecho_exato(descricao, m3)}

        # 2) AxB
        m2 = self.PADRAO_2D.search(descricao)
        if m2:
            return {"Medida": self._trecho_exato(descricao, m2)}

        # 3) barra com unidade
        mb = self.PADRAO_BARRA_UNIDADE.search(descricao)
        if mb:
            return {"Medida": mb.group(1).strip()}

        return {"Medida": None}
