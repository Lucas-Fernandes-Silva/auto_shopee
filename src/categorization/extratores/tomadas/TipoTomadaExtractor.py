import re


class TipoTomadaExtractor:
    """
    Extrai e normaliza o TIPO de itens relacionados a tomadas.
    """

    PADROES = [
        # 1️⃣ FILTRO DE LINHA
        ("filtro", re.compile(r"\b(filtro de linha|filtro|regua)\b")),

        # 2️⃣ EXTENSÃO
        ("extensao", re.compile(r"\b(extensao|prolongador|rabicho)\b")),

        # 3️⃣ CONJUNTO (tomada + placa)
        ("conjunto", re.compile(
            r"\b(tomada\s*(c\/|com)?\s*placa|conjunto|kit tomada|tomada completa)\b"
        )),

        # 4️⃣ PLUG MACHO
        ("plug", re.compile(
            r"\b(plug macho|pino macho|pino prensa|plug retangular|plug prensado)\b"
        )),

        # 5️⃣ PLUG FÊMEA
        ("plug_femea", re.compile(
            r"\b(plug femea|tomada femea|pino femea|conector femea)\b"
        )),

        # 6️⃣ TOMADA (módulo ou simples)
        ("tomada", re.compile(
            r"\b(tomada|modulo tomada)\b"
        )),

        # 7️⃣ ESPELHO / PLACA
        ("espelho", re.compile(
            r"\b(espelho|placa)\b"
        )),
    ]

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Tipo_Tomada": None}

        desc = descricao.lower()

        for tipo, pattern in self.PADROES:
            if pattern.search(desc):
                return {"Tipo_Tomada": tipo}

        return {"Tipo_Tomada": None}
