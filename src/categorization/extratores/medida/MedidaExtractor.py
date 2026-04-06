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
        r"(?<![\d.,])("
        r"(?:\d+\s+\d+/\d+)"          # 3 1/2
        r"|(?:\d+\d/\d)"              # 31/2, 41/2
        r"|(?:\d+/\d+)"               # 1/2, 3/4, 5/16
        r")(?![\d,./])\s*(?:POL|POLEGADA|POLEGADAS|\"|')?\b",
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

    PADRAO_NUMERO_SOLTO = re.compile(r"\b(\d+(?:[.,]\d+)?)\b")

    # =========================
    # CONTEXTOS DE COMPRIMENTO
    # =========================
    CTX_ENGATE = re.compile(r"\b(ENGATE|RABICHO)\b", re.IGNORECASE)
    CTX_GRELHA = re.compile(r"\b(GRELHA)\b", re.IGNORECASE)
    CTX_TUBO_LIGACAO = re.compile(
        r"\b(TUBO\s+LIGA[CÇ][AÃ]O|LIGA[CÇ][AÃ]O)\b",
        re.IGNORECASE,
    )
    CTX_EXTENSAO = re.compile(
        r"\b(EXTENSÃO|EXTENSAO)\b",
        re.IGNORECASE,
    )
    CTX_ROLO = re.compile(
        r"\b(RL|ROLO|BOBINA)\b",
        re.IGNORECASE,
    )

    # ======================
    # CONTEXTOS DE DIÂMETRO
    # ======================
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

    CTX_CABO = re.compile(
        r"\b(FIO|CABO)\b",
        re.IGNORECASE,
    )

    def _limpar_match(self, s: str) -> str:
        return str(s).strip()

    def _to_float(self, s: str) -> float:
        return float(str(s).replace(" ", "").replace(",", "."))

    def _todos_numeros(self, descricao: str) -> list[str]:
        return [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(descricao)]

    def _inferir_numero_por_contexto(
        self,
        descricao: str,
        ctx: re.Pattern,
        valor_max: float = 100,
    ) -> str | None:
        if not ctx.search(descricao):
            return None

        nums = self._todos_numeros(descricao)
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

    def _inferir_comprimento_rolo_conduite(self, descricao: str) -> str | None:
        """
        Ex:
        - CONDUITE 25 ROLO 50 -> 50
        - ELETRODUTO CORRUGADO 20 50M -> se 50M explícito já será pego antes
        """
        if not self.CTX_ROLO.search(descricao):
            return None

        if not self.CTX_CONDUITE.search(descricao):
            return None

        nums = self._todos_numeros(descricao)
        if len(nums) < 2:
            return None

        # em geral o último número é o comprimento do rolo
        candidato = nums[-1]

        try:
            v = self._to_float(candidato)
        except Exception:
            return None

        if 1 <= v <= 1000:
            return candidato.strip()

        return None

    def _inferir_diametro_conduite(self, descricao: str) -> str | None:
        """
        Ex:
        - CONDUITE 25 ROLO 50 -> 25
        - ELETRODUTO 20 -> 20
        """
        if not self.CTX_CONDUITE.search(descricao):
            return None

        nums = self._todos_numeros(descricao)
        if not nums:
            return None

        # se tiver rolo, normalmente o primeiro número é o diâmetro
        candidato = nums[0]

        try:
            v = self._to_float(candidato)
        except Exception:
            return None

        if 0 < v <= 300:
            return candidato.strip()

        return None

    def _inferir_diametro_extensao(self, descricao: str) -> str | None:
        """
        Ex:
        - EXTENSAO 10M 1,5 -> 1,5
        - EXTENSAO 20M 2,5 -> 2,5
        """
        if not self.CTX_EXTENSAO.search(descricao):
            return None

        nums = self._todos_numeros(descricao)
        if len(nums) < 2:
            return None

        # normalmente o último número técnico é a bitola/medida
        candidato = nums[-1]

        try:
            v = self._to_float(candidato)
        except Exception:
            return None

        if 0 < v <= 50:
            return candidato.strip()

        return None

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Volume": None,
                "Peso_Venda": None,
            }

        # se tiver AxB/AxBxC, deixa com MedidaAxBExtractor
        if self.PADRAO_TEM_AXB.search(descricao):
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Volume": None,
                "Peso_Venda": None,
            }

        diametro = None
        comprimento = None
        volume = None
        peso = None

        # =================
        # EXTRAÇÃO EXPLÍCITA
        # =================
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
            diametro = self._limpar_match(m.group(1))

        # polegada explícita
        if diametro is None:
            m = self.PADRAO_POLEGADA.search(descricao)
            if m:
                diametro = self._limpar_match(m.group(1))

        # =========================
        # INFERÊNCIA DE COMPRIMENTO
        # =========================
        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_ENGATE)

        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_GRELHA)

        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_TUBO_LIGACAO)

        if comprimento is None:
            comprimento = self._inferir_comprimento_rolo_conduite(descricao)

        if comprimento is None:
            comprimento = self._inferir_numero_por_contexto(descricao, self.CTX_EXTENSAO)

        # ======================
        # INFERÊNCIA DE DIÂMETRO
        # ======================
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
            contexto_extensao = self.CTX_EXTENSAO.search(descricao) is not None

            # conduíte / eletroduto / corrugado
            if diametro is None and contexto_conduite:
                diametro = self._inferir_diametro_conduite(descricao)

            # extensão
            if diametro is None and contexto_extensao:
                diametro = self._inferir_diametro_extensao(descricao)

            # cabo / fio / hidráulica genérico
            if diametro is None and (contexto_hidraulica or contexto_cabo):
                nums = self._todos_numeros(descricao)
                if nums:
                    candidato = nums[-1]
                    try:
                        v = self._to_float(candidato)
                    except Exception:
                        v = None

                    if v is not None and 0 < v <= 999:
                        diametro = candidato.strip()

        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Volume": volume,
            "Peso_Venda": peso,
        }
