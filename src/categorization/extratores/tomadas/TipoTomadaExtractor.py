import re


class TipoTomadaExtractor:
    PADROES = [
        # 1️⃣ FILTRO DE LINHA
        ("filtro", re.compile(r"\b(filtro de linha|filtro|regua)\b")),
        # 2️⃣ EXTENSÃO
        ("extensao", re.compile(r"\b(extensao|extensão|prolongador)\b")),
        # 3️⃣ CONJUNTO (tomada + placa)
        (
            "conjunto",
            re.compile(r"\b(tomada\s*(c\/|com)?\s*placa|conjunto|kit tomada|tomada completa)\b"),
        ),
        # 4️⃣ PLUG MACHO
        (
            "plug",
            re.compile(
                r"\b(plug macho|pino macho|pino prensa|plug retangular|plug prensado|plug porcelana|pino adaptador)\b"
            ),
        ),
        # 5️⃣ PLUG FÊMEA
        ("plug_femea", re.compile(r"\b(plug femea|tomada femea|pino femea|conector femea)\b")),
        # 6️⃣ TOMADA (módulo ou simples)
        ("barra", re.compile(r"\b(barra)\b")),
        ("sobrepor", re.compile(r"\b(sobrepor|sistema|ilumi ret|perlex|tomada tel)\b")),
        ("tomada", re.compile(r"\b(com placa)\b")),
        ("modulo", re.compile(r"\b(modulo)\b")),
        # 7️⃣ ESPELHO / PLACA
        ("espelho", re.compile(r"\b(espelho|placa)\b")),
    ]

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Tipo_Tomada": None}

        desc = descricao.lower()

        for tipo, pattern in self.PADROES:
            if pattern.search(desc):
                return {"Tipo_Tomada": tipo}

        return {"Tipo_Tomada": None}
