import re


class TipoTomadaExtractor:
    PADROES_TIPO = [
        ("filtro", re.compile(r"\b(filtro de linha|filtro|regua|régua)\b", re.IGNORECASE)),
        ("extensao", re.compile(r"\b(extensao|extensão|prolongador)\b", re.IGNORECASE)),
        (
            "conjunto",
re.compile(
                r"\b(tomada\s*(c\/|com)?\s*placa|conjunto|kit tomada|tomada completa)\b",
re.IGNORECASE,
            ),
        ),
        (
            "plug",
re.compile(
                r"\b(plug macho|pino macho|pino prensa|plug retangular|plug prensado|plug porcelana|pino adaptador)\b",
re.IGNORECASE,
            ),
        ),
        (
            "plug_femea",
           re.compile(
                r"\b(plug femea|plug fêmea|tomada femea|tomada fêmea|pino femea|pino fêmea|conector femea|conector fêmea)\b",
               re.IGNORECASE,
            ),
        ),
        ("barra", re.compile(r"\b(barra)\b", re.IGNORECASE)),
        (
            "sobrepor",
           re.compile(r"\b(sobrepor|sistema|ilumi ret|perlex|tomada tel)\b", re.IGNORECASE),
        ),
        ("modulo", re.compile(r"\b(modulo|módulo)\b", re.IGNORECASE)),
        ("espelho", re.compile(r"\b(espelho|placa)\b", re.IGNORECASE)),
        ("interruptor", re.compile(r"\b(interruptor|int)\b", re.IGNORECASE)),
        ("tomada", re.compile(r"\b(tomada)\b", re.IGNORECASE)),
    ]

    PADRAO_INT_SIGLA = re.compile(r"\b(\d+)\s*int\b", re.IGNORECASE)
    PADRAO_INT_EXTENSO = re.compile(r"\b(\d+)\s*interruptores?\b", re.IGNORECASE)
    PADRAO_TOMADA = re.compile(r"\b(\d+)\s*tomadas?\b", re.IGNORECASE)
    PADRAO_MODULOS = re.compile(
        r"\b(\d+)\s*(modulos|módulos|modulo|módulo|postos|teclas)\b", re.IGNORECASE
    )

    PADROES_PALAVRAS_QTD = [
        (3, re.compile(r"\btriplo\b|\btripla\b", re.IGNORECASE)),
        (2, re.compile(r"\bduplo\b|\bdupla\b", re.IGNORECASE)),
        (1, re.compile(r"\bsimples\b", re.IGNORECASE)),
    ]

    def _extrair_tipo_item(self, desc: str):
        for tipo, pattern in self.PADROES_TIPO:
            if pattern.search(desc):
                return tipo
        return None

    def _extrair_qtd_interruptores(self, desc: str):
        match = self.PADRAO_INT_SIGLA.search(desc)
        if match:
            return int(match.group(1))

        match = self.PADRAO_INT_EXTENSO.search(desc)
        if match:
            return int(match.group(1))

        if re.search(r"\binterruptor\b", desc, re.IGNORECASE):
            for qtd, pattern in self.PADROES_PALAVRAS_QTD:
                if pattern.search(desc):
                    return qtd
            return 1

        return None

    def _extrair_qtd_tomadas(self, desc: str):
        match = self.PADRAO_TOMADA.search(desc)
        if match:
            return int(match.group(1))

        if re.search(r"\btomada\b", desc, re.IGNORECASE):
            for qtd, pattern in self.PADROES_PALAVRAS_QTD:
                if pattern.search(desc):
                    return qtd
            return 1

        return None

    def _extrair_qtd_modulos(self, desc: str, qtd_interruptores, qtd_tomadas):
        match = self.PADRAO_MODULOS.search(desc)
        if match:
            return int(match.group(1))

        soma = (qtd_interruptores or 0) + (qtd_tomadas or 0)

        if soma > 0:
            return soma

        if re.search(r"\b(modulo|módulo)\b", desc, re.IGNORECASE):
            return 1

        return None

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {
                "Tipo_Item": None,
                "Qtd_Interruptores": None,
                "Qtd_Tomadas": None,
                "Qtd_Modulos": None,
            }

        desc = descricao.lower()

        tipo_item = self._extrair_tipo_item(desc)
        qtd_interruptores = self._extrair_qtd_interruptores(desc)
        qtd_tomadas = self._extrair_qtd_tomadas(desc)
        qtd_modulos = self._extrair_qtd_modulos(desc, qtd_interruptores, qtd_tomadas)

        return {
            "Tipo_Item": tipo_item,
            "Qtd_Interruptores": qtd_interruptores,
            "Qtd_Tomadas": qtd_tomadas,
            "Qtd_Modulos": qtd_modulos,
        }
