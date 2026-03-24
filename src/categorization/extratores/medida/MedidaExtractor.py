import re


class MedidaExtractor:
    PADRAO_TEM_AXB = re.compile(
        r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)\s*(?:MM|CM|M|MT|MTS|METRO|METROS|POL|\"|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
        r"(?:\s*(?:MM|CM|M|MT|MTS|METRO|METROS|POL|\"|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?))?",
        re.IGNORECASE,
    )

    # frações válidas só de polegada, sem datas e sem 03/04
    PADRAO_POLEGADA = re.compile(
        r"(?<![\d.,])"
        r"(1/2|3/4|1/4|1/8|5/32|5/16|3/8|3/16|5/8|1\s*1/2|1 1/2|1 1/4|11/4|1|11/2)"
        r"(?![\d,./])\s*(?:POL|\"|')?\b",
        re.IGNORECASE,
    )

    # token inteiro, não só o número
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

    PADRAO_NUMERO_SOLTO = re.compile(r"\b(\d+(?:[.,]\d+)?)\b")

    CTX_ENGATE = re.compile(r"\b(ENGATE|RABICHO)\b", re.IGNORECASE)
    CTX_GRELHA = re.compile(r"\b(GRELHA)\b", re.IGNORECASE)
    CTX_TUBO_LIGACAO = re.compile(r"\b(TUBO\s+LIGA[CÇ][AÃ]O|LIGA[CÇ][AÃ]O)\b", re.IGNORECASE)

    CTX_TUBO = re.compile(r"\b(TUBO)\b", re.IGNORECASE)

    CTX_CABO = re.compile(r"\b(FIO|CABO|EXTENS[AÃ]O)\b", re.IGNORECASE)
    CTX_CONDUITE_DIAMETRO = re.compile(r"\b(CONDUITE|ELETRODUTO)\b", re.IGNORECASE)
    CTX_CONDUITE_COMPRIMENTO = re.compile(r"\b(ROLO)\b", re.IGNORECASE)

    def _limpar_match(self, s: str) -> str:
        return str(s).strip()

    def _to_float(self, s: str) -> float:
        return float(str(s).replace(" ", "").replace(",", "."))

    def _inferir_numero_por_contexto(
        self, descricao: str, ctx: re.Pattern, valor_max: float = 150
    ) -> str | None:
        if not ctx.search(descricao):
            return None

        nums = [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(descricao)]
        if not nums:
            return None

        candidato = nums[-1]
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

        # se tiver AxB/AxBxC, deixa com o MedidaAxBExtractor
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
            if self.CTX_CABO.search(descricao):
                secao = token
            else:
                diametro = token

        # polegada sem aspas
        if diametro is None:
            m = self.PADRAO_POLEGADA.search(descricao)
            if m:
                diametro = m.group(1).replace(" ", "").strip()

        # inferências
        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_ENGATE)

        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_GRELHA)

        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_TUBO_LIGACAO)

        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(
                descricao, self.CTX_CONDUITE_COMPRIMENTO
            )

        if diametro is None:
            diametro = self._inferir_numero_por_contexto(descricao, self.CTX_CABO)

        if diametro is None:
            diametro = self._inferir_numero_por_contexto(descricao, self.CTX_CONDUITE_DIAMETRO)

        if diametro is None:
            diametro = self._inferir_numero_por_contexto(descricao, self.CTX_TUBO)

        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Volume": volume,
            "Peso_Venda": peso,
            "Secao_Cabo": secao,
        }
