import re


class MedidaExtractor:
    PADRAO_TEM_AXB = re.compile(
        r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)\s*(?:MM|CM|M|MT|MTS|METRO|METROS|POL|\"|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
        r"(?:\s*(?:MM|CM|M|MT|MTS|METRO|METROS|POL|\"|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?))?",
        re.IGNORECASE,
    )

    PADRAO_POLEGADA = re.compile(
        r"(?<![\d.,])"
        r"(1/2|3/4|1/4|1/8|5/32|5/16|3/8|3/16|5/8|1\s*1/2|1 1/2|1 1/4|11/4|1|11/2|3\s*1/2|4\s*1/2)"
        r"(?![\d,./])\s*(?:POL|\"|')?\b",
        re.IGNORECASE,
    )

    PADRAO_DIAMETRO_MM = re.compile(
        r"(?<![/\d])(\d+(?:[.,]\d+)?\s*(?:MM|MILIMETROS?))\b",
        re.IGNORECASE,
    )

    PADRAO_COMPRIMENTO = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*(?:CM|M|MT|MTS|METRO|METROS))\b",
        re.IGNORECASE,
    )

    PADRAO_VOLUME = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*(?:L|LT|LITRO|LITROS))\b",
        re.IGNORECASE,
    )

    PADRAO_PESO = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*(?:KG|QUILO|QUILOS|G|GR|GRS|GRAMA|GRAMAS))\b",
        re.IGNORECASE,
    )

    PADRAO_SECAO_MM2 = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*(?:MM2|MM²|MILIMETROS?\s*QUADRADOS?))\b",
        re.IGNORECASE,
    )

    # ---------- CONTEXTOS ----------
    CTX_ENGATE = re.compile(r"\b(ENGATE|RABICHO)\b", re.IGNORECASE)
    CTX_GRELHA = re.compile(r"\b(GRELHA)\b", re.IGNORECASE)
    CTX_TUBO_LIGACAO = re.compile(
        r"\b(TUBO\s+LIGA[CÇ][AÃ]O|LIGA[CÇ][AÃ]O)\b",
        re.IGNORECASE,
    )

    CTX_DIAMETRO = re.compile(
        r"\b(FIO|CABO|EXTENSÃO|EXTENSAO|CONDUITE|ELETRODUTO|CORRUGADO)\b",
        re.IGNORECASE,
    )

    # ---------- PADRÕES DE INFERÊNCIA CONTEXTUAL ----------
    PADRAO_CTX_DIAMETRO = re.compile(
        r"\b(?:FIO|CABO|EXTENSÃO|EXTENSAO|CONDUITE|ELETRODUTO|CORRUGADO)\b"
        r"(?:[^\d]{0,20})"
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(?:MM|POL|\")?\b",
        re.IGNORECASE,
    )

    PADRAO_CTX_ENGATE_NUM = re.compile(
        r"\b(?:ENGATE|RABICHO)\b(?:[^\d]{0,20})(\d+(?:[.,]\d+)?)\b",
        re.IGNORECASE,
    )

    PADRAO_CTX_GRELHA_NUM = re.compile(
        r"\b(?:GRELHA)\b(?:[^\d]{0,20})(\d+(?:[.,]\d+)?)\b",
        re.IGNORECASE,
    )

    PADRAO_CTX_TUBO_LIGACAO_NUM = re.compile(
        r"\b(?:TUBO\s+LIGA[CÇ][AÃ]O|LIGA[CÇ][AÃ]O)\b(?:[^\d]{0,20})(\d+(?:[.,]\d+)?)\b",
        re.IGNORECASE,
    )

    PADRAO_CTX_ROLO_NUM = re.compile(
        r"\b(?:ROLO)\b(?:[^\d]{0,20})(\d+(?:[.,]\d+)?)\b",
        re.IGNORECASE,
    )
    def _limpar_match(self, s: str) -> str:
        return str(s).strip()

    def _to_float(self, s: str) -> float:
        return float(str(s).replace(" ", "").replace(",", "."))

    def _inferir_numero_proximo_contexto(
        self,
        descricao: str,
        padrao_ctx_num: re.Pattern,
        valor_max: float = 150,
    ) -> str | None:
        match = padrao_ctx_num.search(descricao)
        if not match:
            return None

        candidato = match.group(1)

        try:
            v = self._to_float(candidato)
        except Exception:
            return None

        if 0 < v <= valor_max:
            return candidato.strip()

        return None

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Volume": None,
                "Peso_Venda": None,
                "Secao_Cabo": None,
            }

        # se tiver AxB/AxBxC, deixa com MedidaAxBExtractor
        if self.PADRAO_TEM_AXB.search(descricao):
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Volume": None,
                "Peso_Venda": None,
                "Secao_Cabo": None,
            }

        diametro = None
        comprimento = None
        volume = None
        peso = None
        secao = None

        # ---------- EXPLÍCITOS ----------
        m = self.PADRAO_SECAO_MM2.search(descricao)
        if m:
            secao = self._limpar_match(m.group(1))

        m = self.PADRAO_VOLUME.search(descricao)
        if m:
            volume = self._limpar_match(m.group(1))

        m = self.PADRAO_PESO.search(descricao)
        if m:
            peso = self._limpar_match(m.group(1))

        m = self.PADRAO_COMPRIMENTO.search(descricao)
        if m:
            comprimento = self._limpar_match(m.group(1))

        m = self.PADRAO_DIAMETRO_MM.search(descricao)
        if m:
            token = self._limpar_match(m.group(1))
            if self.CTX_DIAMETRO.search(descricao):
                secao = token
            else:
                diametro = token

        # ---------- POLEGADA EXPLÍCITA ----------
        if diametro is None:
            m = self.PADRAO_POLEGADA.search(descricao)
            if m:
                diametro = self._limpar_match(m.group(1))

        # ---------- INFERÊNCIA DE COMPRIMENTO SOMENTE POR CONTEXTO ----------
        if comprimento is None:
            comprimento = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_ENGATE_NUM
            )

        if comprimento is None:
            comprimento = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_GRELHA_NUM
            )
        if comprimento is None:
            comprimento = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_ROLO_NUM
            )

        if comprimento is None:
            comprimento = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_TUBO_LIGACAO_NUM
            )

        # ---------- INFERÊNCIA DE DIÂMETRO SOMENTE POR CONTEXTO ----------
        if diametro is None:
            diametro = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_DIAMETRO
            )

        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Volume": volume,
            "Peso_Venda": peso,
            "Secao_Cabo": secao,
        }
