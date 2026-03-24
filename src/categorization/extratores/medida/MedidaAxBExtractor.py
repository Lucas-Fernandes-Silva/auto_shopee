import re


class MedidaAxBExtractor:
    """
    Extrai medidas:
    - fração x número      -> 1/4X50
    - fração x fração      -> 3/4X1/2
    - número x número      -> 6,0X60
    - número x número x número -> 20X10X2M
    - medida com barra e unidade -> 38/40MM
    """

    # número simples / decimal
    NUM = r"\d+(?:[.,]\d+)?"

    # fração simples
    FRAC = r"\d+/\d+"

    # fração mista válida de polegada (evita 16 1/4, 05 3/16 etc)
    MIXED = r"(?:1|2|3|4)\s+\d+/\d+"

    # qualquer medida de eixo
    EIXO = rf"(?:{MIXED}|{FRAC}|{NUM})"

    # unidade opcional por eixo
    UN = r'(?:\s*(?:MM|CM|M|MT|MTS|METRO|METROS|POL|\"|\'))?'

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

    # medidas tipo 38/40MM
    PADRAO_BARRA_UNIDADE = re.compile(
        r"(?<![\d])(\d+(?:[.,]\d+)?/\d+(?:[.,]\d+)?\s*(?:MM|CM|M|MT|MTS|METRO|METROS))\b",
        re.IGNORECASE,
    )

    def _limpar_match(self, s: str) -> str:
        s = s.strip()
        s = s.replace("×", "X")
        s = re.sub(r'\s*(?:POL|["\'])\b', "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*[xX]\s*", "X", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _trecho_exato(self, descricao: str, match: re.Match) -> str:
        return self._limpar_match(descricao[match.start():match.end()])

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {"Medida": None}

        # 1) 3 dimensões primeiro
        m3 = self.PADRAO_3D.search(descricao)
        if m3:
            return {"Medida": self._trecho_exato(descricao, m3)}

        # 2) 2 dimensões
        m2 = self.PADRAO_2D.search(descricao)
        if m2:
            return {"Medida": self._trecho_exato(descricao, m2)}

        # 3) barra com unidade (ex: 38/40MM)
        mb = self.PADRAO_BARRA_UNIDADE.search(descricao)
        if mb:
            return {"Medida": self._limpar_match(mb.group(1))}

        return {"Medida": None}
