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
        r"(?<![/\d])(\d+(?:[.,]\d+)?\s*(?:MM|MILIMETRO|MILIMETROS))\b",
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

    # comprimento
    CTX_ENGATE = re.compile(r"\b(ENGATE|RABICHO)\b", re.IGNORECASE)
    CTX_GRELHA = re.compile(r"\b(GRELHA)\b", re.IGNORECASE)
    CTX_TUBO_LIGACAO = re.compile(
        r"\b(TUBO\s+LIGA[CÇ][AÃ]O|LIGA[CÇ][AÃ]O)\b",
        re.IGNORECASE,
    )

    # diâmetro
    CTX_HIDRAULICA = re.compile(
        r"\b(TUBO|CANO|CONEXAO|CONEXOES|JOELHO|T[EÊ]\b|LUVA|BUCHA|ADAPTADOR|NIPLE|UNIAO|UNIÃO|REGISTRO|VALVULA|VÁLVULA|SIFAO|SIFÃO|MANGUEIRA)\b",
        re.IGNORECASE,
    )
    REFORCO_HIDRAULICA = re.compile(
        r"\b(PVC|CPVC|PPR|PEX|AGUA|ÁGUA|ESGOTO|SOLDAVEL|SOLDÁVEL|COLAVEL|COLÁVEL|ROSCA)\b",
        re.IGNORECASE,
    )

    CTX_CONDUITE = re.compile(
        r"\b(CONDUITE|ELETRODUTO|CORRUGADO)\b",
        re.IGNORECASE,
    )

    CTX_CABO = re.compile(r"\b(FIO|CABO|EXTENSAO|EXTENS[ÃA]O)\b", re.IGNORECASE)
    CTX_ROLO = re.compile(r"\b(RL|ROLO|BOBINA)\b", re.IGNORECASE)

    def _limpar_match(self, s: str) -> str:
        return str(s).strip()

    def _to_float(self, s: str) -> float:
        return float(str(s).replace(" ", "").replace(",", "."))

    def _inferir_numero_por_contexto(
        self,
        descricao: str,
        ctx: re.Pattern,
        valor_max: float = 100,
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

        # explícitos
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

        # polegada explícita
        if diametro is None:
            m = self.PADRAO_POLEGADA.search(descricao)
            if m:
                diametro = self._limpar_match(m.group(1))

        # inferência de comprimento
        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_ENGATE)

        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_GRELHA)

        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_TUBO_LIGACAO)

        # inferência de diâmetro
        if (
            diametro is None
            and not self.CTX_ENGATE.search(descricao)
            and not self.CTX_GRELHA.search(descricao)
            and not self.CTX_TUBO_LIGACAO.search(descricao)
        ):
            contexto_conduite = self.CTX_CONDUITE.search(descricao) is not None
            contexto_hidraulica = (
                self.CTX_HIDRAULICA.search(descricao) is not None
                and self.REFORCO_HIDRAULICA.search(descricao) is not None
            )
            contexto_cabo = self.CTX_CABO.search(descricao) is not None

            if contexto_conduite or contexto_hidraulica or contexto_cabo:
                nums = [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(descricao)]
                if nums:
                    candidato = nums[-1]
                    try:
                        v = self._to_float(candidato)
                    except Exception:
                        v = None

                    if v is not None and 0 < v <= 999:
                        if not self.CTX_ROLO.search(descricao):
                            diametro = candidato.strip()

        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Volume": volume,
            "Peso_Venda": peso,
            "Secao_Cabo": secao,
        }
