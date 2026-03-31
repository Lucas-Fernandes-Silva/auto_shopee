import re


class MedidaExtractor:
    # =========================================================
    # PADRÕES GERAIS
    # =========================================================

    PADRAO_TEM_AXB = re.compile(
        r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)\s*(?:MM|CM|M|MT|MTS|METRO|METROS|POL|\"|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
        r"(?:\s*(?:MM|CM|M|MT|MTS|METRO|METROS|POL|\"|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?))?",
        re.IGNORECASE,
    )

    PADRAO_POLEGADA = re.compile(
        r"(?<![\d])"
        r"("
        r"\d+\s+\d+/\d+|"      # ex: 1 1/2
        r"\d+/\d+|"            # ex: 1/2
        r"\d+(?:[.,]\d+)?"     # ex: 1 ou 1,1
        r")"
        r"\s*(?:POL\b|\"|')",
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
        r"\b(TUBO\s+LIGA[CÇ][AÃ]O|LIGA[CÇ][AÃ]O)\b",
        re.IGNORECASE,
    )
    CTX_ROLO = re.compile(r"\b(ROLO)\b", re.IGNORECASE)

    CTX_SECAO_CABO = re.compile(
        r"\b(FIO|CABO)\b",
        re.IGNORECASE,
    )

    CTX_DIAMETRO = re.compile(
        r"\b(CONDUITE|ELETRODUTO|CORRUGADO|TUBO|MANGUEIRA)\b",
        re.IGNORECASE,
    )

    # =========================================================
    # PADRÕES CONTEXTUAIS
    # =========================================================

    PADRAO_CTX_SECAO_NUM = re.compile(
        r"\b(?:FIO|CABO)\b(?:[^\d]{0,20})(\d+(?:[.,]\d+)?)\b",
        re.IGNORECASE,
    )

    PADRAO_CTX_DIAMETRO_NUM = re.compile(
        r"\b(?:CONDUITE|ELETRODUTO|CORRUGADO|TUBO|MANGUEIRA)\b"
        r"(?:[^\d]{0,20})(\d+(?:[.,]\d+)?)\b",
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

    # =========================================================
    # CASOS ÚTEIS DE AxB
    # =========================================================

    PADRAO_AXB_POLEGADA_X_COMPRIMENTO = re.compile(
        r"(?<![\d.,])"
        r"(1\s*1/2|1\s*1/4|1\s*1/8|1\s*3/4|2\s*1/2|3\s*1/2|4\s*1/2|"
        r"1/8|1/4|3/8|1/2|5/8|3/4|7/8|1|2|3|4)"
        r"(?![\d,./])\s*(?:POL\b|\"|')?\s*[xX×]\s*"
        r"(\d+(?:[.,]\d+)?\s*(?:CM|M|MT|MTS|METRO|METROS))\b",
        re.IGNORECASE,
    )

    PADRAO_AXB_MM_X_COMPRIMENTO = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*MM)\s*[xX×]\s*"
        r"(\d+(?:[.,]\d+)?\s*(?:CM|M|MT|MTS|METRO|METROS))\b",
        re.IGNORECASE,
    )

    # =========================================================
    # HELPERS
    # =========================================================

    def _limpar_match(self, s: str) -> str:
        return str(s).strip()

    def _to_float(self, s: str) -> float:
        return float(str(s).replace(" ", "").replace(",", "."))

    def _normalizar_fracao(self, s: str) -> str:
        return re.sub(r"\s+", " ", str(s).strip())

    def _inferir_numero_proximo_contexto(
        self,
        descricao: str,
        padrao_ctx_num: re.Pattern,
        valor_max: float = 150,
        valor_min: float = 0,
    ) -> str | None:
        match = padrao_ctx_num.search(descricao)
        if not match:
            return None

        candidato = match.group(1)

        try:
            v = self._to_float(candidato)
        except Exception:
            return None

        if valor_min < v <= valor_max:
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

        tem_axb = bool(self.PADRAO_TEM_AXB.search(descricao))

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

        # =====================================================
        # 2) MM explícito → decidir se é seção ou diâmetro
        # =====================================================

        m = self.PADRAO_DIAMETRO_MM.search(descricao)
        if m:
            token = self._limpar_match(m.group(1))

            if self.CTX_SECAO_CABO.search(descricao):
                secao = token
            elif self.CTX_DIAMETRO.search(descricao):
                diametro = token
            else:
                diametro = token

        # =====================================================
        # 3) POLEGADA EXPLÍCITA
        # =====================================================

        if diametro is None:
            m = self.PADRAO_POLEGADA.search(descricao)
            if m:
                diametro = self._normalizar_fracao(m.group(1))

        # =====================================================
        # 4) CASOS AxB ÚTEIS
        # =====================================================

        if diametro is None or comprimento is None:
            m = self.PADRAO_AXB_POLEGADA_X_COMPRIMENTO.search(descricao)
            if m:
                if diametro is None:
                    diametro = self._normalizar_fracao(m.group(1))
                if comprimento is None:
                    comprimento = self._limpar_match(m.group(2))

        if (diametro is None and secao is None) or comprimento is None:
            m = self.PADRAO_AXB_MM_X_COMPRIMENTO.search(descricao)
            if m:
                token_mm = self._limpar_match(m.group(1))
                token_comp = self._limpar_match(m.group(2))

                if self.CTX_SECAO_CABO.search(descricao):
                    if secao is None:
                        secao = token_mm
                else:
                    if diametro is None:
                        diametro = token_mm

                if comprimento is None:
                    comprimento = token_comp

        # =====================================================
        # 5) INFERÊNCIA DE COMPRIMENTO (SÓ SE NÃO VEIO EXPLÍCITO)
        # =====================================================

        if comprimento is None:
            comprimento = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_ENGATE_NUM, valor_max=300
            )

        if comprimento is None:
            comprimento = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_GRELHA_NUM, valor_max=300
            )

        if comprimento is None:
            comprimento = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_ROLO_NUM, valor_max=1000
            )

        if comprimento is None:
            comprimento = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_TUBO_LIGACAO_NUM, valor_max=300
            )

        # =====================================================
        # 6) INFERÊNCIA DE DIÂMETRO / SEÇÃO
        # =====================================================

        if diametro is None and secao is None:
            candidato_secao = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_SECAO_NUM, valor_max=240
            )

            candidato_diametro = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_DIAMETRO_NUM, valor_max=300
            )

            if candidato_secao and self.CTX_SECAO_CABO.search(descricao):
                secao = candidato_secao

            elif candidato_diametro and self.CTX_DIAMETRO.search(descricao):
                diametro = candidato_diametro

        elif diametro is None:
            candidato_diametro = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_DIAMETRO_NUM, valor_max=300
            )
            if candidato_diametro:
                diametro = candidato_diametro

        elif secao is None:
            candidato_secao = self._inferir_numero_proximo_contexto(
                descricao, self.PADRAO_CTX_SECAO_NUM, valor_max=240
            )
            if candidato_secao:
                secao = candidato_secao

        # =====================================================
        # 7) HIGIENIZAÇÃO FINAL
        # =====================================================

        # evita secao errada em conduíte/eletroduto
        if secao and self.CTX_DIAMETRO.search(descricao) and not self.CTX_SECAO_CABO.search(descricao):
            if diametro is None:
                diametro = secao
            secao = None

        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Volume": volume,
            "Peso_Venda": peso,
            "Secao_Cabo": secao,
        }
