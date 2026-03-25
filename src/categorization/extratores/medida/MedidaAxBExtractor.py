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

    # medida tipo 38/40MM
    PADRAO_BARRA_UNIDADE = re.compile(
        r"(?<![\d])(\d+(?:[.,]\d+)?/\d+(?:[.,]\d+)?\s*(?:MM|CM|M|MT|MTS|METRO|METROS))\b",
        re.IGNORECASE,
    )

    def _limpar_match(self, s: str) -> str:
        s = s.strip()
        s = s.replace("×", "X")

        # padroniza apenas o separador X
        s = re.sub(r"\s*[xX]\s*", "X", s)

        # remove aspas antigas, se existirem
        s = s.replace('"', "").replace("'", "")

        # mantém os espaços internos importantes, como em 1 1/2
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _trecho_exato(self, descricao: str, match: re.Match) -> str:
        trecho = descricao[match.start():match.end()]
        return self._limpar_match(trecho)

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
            return {"Medida": self._limpar_match(mb.group(1))}

        return {"Medida": None}
