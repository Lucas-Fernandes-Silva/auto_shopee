import re


class MedidaExtractor:
    PADRAO_TEM_AXB = re.compile(
        r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)\s*(?:mm|cm|m|\"|pol|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
        r"(?:\s*(?:mm|cm|m|\"|pol|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?))?",
        re.IGNORECASE,
    )

    # só frações válidas; não pega 03/04
    PADRAO_POLEGADA = re.compile(
        r"(?<![\d.,])"
        r"(1/2|3/4|1/4|1/8|5/32|5/16|3/8|3/16|5/8|1\s*1/2|1 1/2|1 1/4|11/4|1|11/2)"
        r"(?![\d,./])\s*(pol|\"|')?\b",
        re.IGNORECASE,
    )

    # mantém o trecho exatamente como veio
    PADRAO_DIAMETRO_MM = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*(?:mm|milimetros?))\b",
        re.IGNORECASE,
    )

    PADRAO_COMPRIMENTO = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*(?:cm|m|mt|metro|metros))\b",
        re.IGNORECASE,
    )

    PADRAO_VOLUME_L = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*(?:l|lt|litro|litros))\b",
        re.IGNORECASE,
    )

    PADRAO_PESO_VENDA = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*(?:kg|quilo|quilos|g|grama|gramas|gr|grs))\b",
        re.IGNORECASE,
    )

    PADRAO_SECAO_MM2 = re.compile(
        r"\b(\d+(?:[.,]\d+)?\s*(?:mm2|mm²|milimetros?\s*quadrados?))\b",
        re.IGNORECASE,
    )

    PADRAO_NUMERO_SOLTO = re.compile(r"\b(\d+(?:[.,]\d+)?)\b")

    CTX_ENGATE = re.compile(r"\b(engate|rabicho)\b", re.IGNORECASE)
    CTX_GRELHA = re.compile(r"\b(grelha)\b", re.IGNORECASE)

    CTX_TUBO_LIGACAO = re.compile(
        r"\b(tubo\s+liga[cç][aã]o|liga[cç][aã]o)\b",
        re.IGNORECASE,
    )

    CTX_HIDRAULICA = re.compile(
        r"\b(tubo|cano|conexao|conexoes|joelho|t[eê]\b|luva|bucha|adaptador|niple|uni[aã]o|registro|valvula|válvula|sif[aã]o|engate|mangueira)\b",
        re.IGNORECASE,
    )
    REFORCO_HIDRAULICA = re.compile(
        r"\b(pvc|cpvc|ppr|pex|agua|água|esgoto|soldavel|soldável|colavel|colável|rosca)\b",
        re.IGNORECASE,
    )

    CTX_CONDUITE = re.compile(r"\b(conduite|eletroduto|rolo)\b", re.IGNORECASE)
    CTX_CABO = re.compile(r"\b(fio|cabo|extensao)\b", re.IGNORECASE)
    CTX_ROLO = re.compile(r"\b(rl|rolo|bobina)\b", re.IGNORECASE)

    REFORCO_CABO = re.compile(
        r"\b(auto|automotivo|flexivel|flexível|paralelo|pp|silicone|cobrecom)\b",
        re.IGNORECASE,
    )

    def _to_float(self, s: str) -> float:
        s = s.strip().replace(" ", "")
        s = s.replace(",", ".")
        return float(s)

    def _limpar_match(self, s: str) -> str:
        return str(s).strip()

    def _extrair_secao_cabo_omitida(self, desc: str) -> str | None:
        if not self.CTX_CABO.search(desc):
            return None

        nums = [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(desc)]
        if not nums:
            return None

        candidato = nums[0]
        v = self._to_float(candidato)

        if 0 < v <= 240:
            return self._limpar_match(candidato)

        return None

    def _inferir_comprimento_por_contexto(
        self,
        desc: str,
        padrao_ctx: re.Pattern,
        valor_max: float = 100,
    ) -> str | None:
        if not padrao_ctx.search(desc):
            return None

        nums = [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(desc)]
        if not nums:
            return None

        candidato = nums[-1]
        v = self._to_float(candidato)

        if 0 < v <= valor_max:
            return self._limpar_match(candidato)  # só número, sem unidade

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

        desc = descricao.lower()
        tem_axb = self.PADRAO_TEM_AXB.search(desc) is not None

        diametro = None
        comprimento = None
        volume = None
        peso_venda = None
        secao_cabo = None

        # 1) seção cabo explícita - mantém exatamente como veio
        m_mm2 = self.PADRAO_SECAO_MM2.search(descricao)
        if m_mm2:
            secao_cabo = self._limpar_match(m_mm2.group(1))

        # 2) volume - mantém exatamente como veio
        m_vol = self.PADRAO_VOLUME_L.search(descricao)
        if m_vol:
            volume = self._limpar_match(m_vol.group(1))

        # 3) peso - mantém exatamente como veio
        m_peso = self.PADRAO_PESO_VENDA.search(descricao)
        if m_peso:
            peso_venda = self._limpar_match(m_peso.group(1))

        # 4) se tem AxB, não disputa com MedidaAxBExtractor
        if tem_axb:
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Volume": volume,
                "Peso_Venda": peso_venda,
                "Secao_Cabo": secao_cabo,
            }

        # 5) polegada simples (sem aspas)
        m_pol = self.PADRAO_POLEGADA.search(descricao)
        if m_pol:
            diametro = m_pol.group(1).replace(" ", "").strip()

        # 6) diâmetro em mm explícito - mantém exatamente como veio
        m_mm = self.PADRAO_DIAMETRO_MM.search(descricao)
        if m_mm:
            valor_mm = self._limpar_match(m_mm.group(1))

            # em fio/cabo isso vira seção, não diâmetro
            if self.CTX_CABO.search(desc):
                secao_cabo = valor_mm
                diametro = None
            else:
                diametro = valor_mm

        # 7) comprimento explícito - mantém exatamente como veio
        m_comp = self.PADRAO_COMPRIMENTO.search(descricao)
        if m_comp:
            comprimento = self._limpar_match(m_comp.group(1))

        # 8) reforço para cabo/fio com bitola omitida - só número
        if secao_cabo is None and self.CTX_CABO.search(desc):
            secao_cabo = self._extrair_secao_cabo_omitida(desc)

        # 9) inferência de diâmetro omitido - só número
        if (
            (diametro is None)
            and (not self.CTX_CABO.search(desc))
            and (not self.CTX_ENGATE.search(desc))
            and (not self.CTX_GRELHA.search(desc))
            and (not self.CTX_TUBO_LIGACAO.search(desc))
        ):
            contexto_conduite = self.CTX_CONDUITE.search(desc) is not None
            contexto_hid = (
                self.CTX_HIDRAULICA.search(desc) is not None
                and self.REFORCO_HIDRAULICA.search(desc) is not None
            )

            if contexto_conduite or contexto_hid:
                nums = [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(desc)]
                if nums:
                    candidato = nums[-1]
                    v = self._to_float(candidato)

                    if 0 < v <= 999:
                        if (not self.CTX_ROLO.search(desc)) and (comprimento is None):
                            diametro = self._limpar_match(candidato)

        # 10) engate -> comprimento inferido (só número)
        if comprimento is None:
            comprimento = self._inferir_comprimento_por_contexto(
                desc,
                self.CTX_ENGATE,
                valor_max=100,
            )

        # 11) grelha -> comprimento inferido (só número)
        if comprimento is None:
            comprimento = self._inferir_comprimento_por_contexto(
                desc,
                self.CTX_GRELHA,
                valor_max=100,
            )

        if comprimento is None:
            comprimento = self._inferir_comprimento_por_contexto(
                desc,
                self.CTX_TUBO_LIGACAO,
                valor_max=100,
            )

        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Volume": volume,
            "Peso_Venda": peso_venda,
            "Secao_Cabo": secao_cabo,
        }
