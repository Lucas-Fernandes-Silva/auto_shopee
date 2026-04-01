import re


class MedidaExtractor:
    # =========================================================
    # PADRÕES GERAIS
    # =========================================================

    PADRAO_TEM_AXB = re.compile(
        r"(?:\d+\s+\d+/\d+|\d+[.,]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)\s*"
        r"(?:MM|CM|M|MT|MTS|METRO|METROS|POL|\"|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+[.,]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
        r"(?:\s*(?:MM|CM|M|MT|MTS|METRO|METROS|POL|\"|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+[.,]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?))?",
        re.IGNORECASE,
    )

x    # Ex.: 1/2", 3/4 POL, 1 1/2'
    PADRAO_POLEGADA = re.compile(
        r"(?<![\d])" r"(\d+\s+\d+/\d+|\d+[.,]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)" r"\s*(?:POL\b|\"|')",
        re.IGNORECASE,
    )

    # Ex.: 3/4, 31/2, 1 1/2, 1.1/4 (sem unidade)
    PADRAO_POLEGADA_FRACAO = re.compile(
        r"(?<![\d])" r"(\d+\s+\d+/\d+|\d+[.,]\d+/\d+|\d+/\d+)" r"(?![\d])",
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
        r"\b(\d+(?:[.,]\d+)?\s*(?:ML|L|LT|LITRO|LITROS))\b",
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

    # =========================================================
    # CONTEXTOS
    # =========================================================

    CTX_ENGATE = re.compile(r"\b(ENGATE|RABICHO)\b", re.IGNORECASE)
    CTX_GRELHA = re.compile(r"\b(GRELHA)\b", re.IGNORECASE)
    CTX_TUBO_LIGACAO = re.compile(
        r"\b(TUBO\s+LIGA[CÇ][AÃ]O|LIGA[CÇ][AÃ]O|TUBO)\b",
        re.IGNORECASE,
    )

    CTX_CABO = re.compile(r"\b(FIO|CABO)\b", re.IGNORECASE)

    CTX_DIAMETRO = re.compile(
        r"\b(CONDUITE|ELETRODUTO|CORRUGADO|TUBO|MANGUEIRA)\b",
        re.IGNORECASE,
    )

    CTX_POLEGADA_TECNICA = re.compile(
        r"\b("
        r"CONDUITE|ELETRODUTO|CORRUGADO|TUBO|MANGUEIRA|"
        r"JOELHO|LUVA|REGISTRO|ADAPTADOR|CURVA|TE|NIPLE|"
        r"BUCHA|UNIAO|UNIÃO|COTOVELO|REDUCAO|REDUÇÃO|"
        r"ENGATE|RABICHO|CONEXAO|CONEXÃO|"
        r"VALVULA|VÁLVULA|ARRUELA|PARAFUSO|PORCA|REBITE|HASTE"
        r")\b",
        re.IGNORECASE,
    )

    # =========================================================
    # PADRÕES DE INFERÊNCIA CONTEXTUAL
    # =========================================================

    PADRAO_CTX_DIAMETRO = re.compile(
        r"\b(?:CONDUITE|ELETRODUTO|CORRUGADO|TUBO|MANGUEIRA)\b"
        r"(?:[^\d]{0,20})"
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(?:MM|POL|\")?\b",
        re.IGNORECASE,
    )

    PADRAO_CTX_CABO = re.compile(
        r"\b(?:FIO|CABO)\b" r"(?:[^\d]{0,20})" r"(\d+(?:[.,]\d+)?)" r"\s*(?:MM|MM2|MM²)?\b",
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
        r"\b(?:TUBO\s+LIGA[CÇ][AÃ]O|LIGA[CÇ][AÃ]O|TUBO)\b(?:[^\d]{0,20})(\d+(?:[.,]\d+)?)\b",
        re.IGNORECASE,
    )

    PADRAO_CTX_ROLO_NUM = re.compile(
        r"\b(?:ROLO)\b(?:[^\d]{0,20})(\d+(?:[.,]\d+)?)\b",
        re.IGNORECASE,
    )

    # =========================================================
    # HELPERS
    # =========================================================

    def _limpar_match(self, s: str) -> str:
        return str(s).strip()

    def _normalizar_fracao(self, s: str) -> str:
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

    # =========================================================
    # EXTRAÇÃO
    # =========================================================

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Volume": None,
                "Peso_Venda": None,
                "Secao_Cabo": None,
            }

        descricao = str(descricao).strip()

        diametro = None
        comprimento = None
        volume = None
        peso = None
        secao = None

        # =====================================================
        # 1) EXPLÍCITOS
        # =====================================================

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

        # =====================================================
        # 2) POLEGADA EXPLÍCITA
        # =====================================================

        if diametro is None:
            m = self.PADRAO_POLEGADA.search(descricao)
            if m:
                diametro = self._normalizar_fracao(m.group(1))

        # =====================================================
        # 3) POLEGADA FRACIONÁRIA SEM UNIDADE
        #    Só aceita em contexto técnico
        # =====================================================

        if diametro is None and self.CTX_POLEGADA_TECNICA.search(descricao):
            m = self.PADRAO_POLEGADA_FRACAO.search(descricao)
            if m:
                diametro = self._normalizar_fracao(m.group(1))

        # =====================================================
        # 4) INFERÊNCIA DE COMPRIMENTO
        # =====================================================

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
                descricao, self.PADRAO_CTX_ROLO_NUM, valor_max=1000
            )

        if comprimento is None:
            comprimento = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_TUBO_LIGACAO_NUM
            )

        # =====================================================
        # 5) INFERÊNCIA DE DIÂMETRO / SEÇÃO
        # =====================================================

        if diametro is None and self.CTX_DIAMETRO.search(descricao):
            diametro = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_DIAMETRO, valor_max=300
            )

        if secao is None and self.CTX_CABO.search(descricao):
            secao = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_CABO, valor_max=240
            )

        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Volume": volume,
            "Peso_Venda": peso,
            "Secao_Cabo": secao,
        }
