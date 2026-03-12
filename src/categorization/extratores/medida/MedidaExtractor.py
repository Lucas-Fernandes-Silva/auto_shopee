import re


class MedidaExtractor:
    PADRAO_TEM_AXB = re.compile(
        r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)\s*(?:mm|cm|m|\"|pol|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
        r"(?:\s*(?:mm|cm|m|\"|pol|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?))?",
        re.IGNORECASE,
    )

    # ✅ Evita pegar o "1" de "1,50" como polegada
    PADRAO_POLEGADA = re.compile(
        r"(?<![\d.,])"
        r"(1/2|3/4|1/4|1/8|5/32|5/16|3/8|3/16|5/8|1\s*1/2|1 1/2|1 1/4|11/4|1|11/2)"
        r"(?![\d,./])\s*(pol|\"|')?\b",
        re.IGNORECASE,
    )

    PADRAO_DIAMETRO_MM = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(cm|mm|milimetros?)\b",
        re.IGNORECASE,
    )

    PADRAO_COMPRIMENTO = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(m|mt|metro|metros)\b",
        re.IGNORECASE,
    )

    PADRAO_VOLUME_L = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(l|lt|litro|litros)\b",
        re.IGNORECASE,
    )

    PADRAO_PESO_VENDA = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(kg|quilo|quilos|g|grama|gramas|gr)\b",
        re.IGNORECASE,
    )

    PADRAO_SECAO_MM2 = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(?:mm2|mm²|milimetros?\s*quadrados?)\b",
        re.IGNORECASE,
    )

    PADRAO_NUMERO_SOLTO = re.compile(r"\b(\d+(?:[.,]\d+)?)\b")

    CTX_ENGATE = re.compile(r"\b(engate|rabicho)\b", re.IGNORECASE)

    CTX_HIDRAULICA = re.compile(
        r"\b(tubo|cano|conexao|conexoes|joelho|t[eê]\b|luva|bucha|adaptador|niple|uni[aã]o|registro|valvula|válvula|sif[aã]o|engate|mangueira)\b",
        re.IGNORECASE,
    )
    REFORCO_HIDRAULICA = re.compile(
        r"\b(pvc|cpvc|ppr|pex|agua|água|esgoto|soldavel|soldável|colavel|colável|rosca)\b",
        re.IGNORECASE,
    )

    CTX_CONDUITE = re.compile(r"\b(conduite|eletroduto)\b", re.IGNORECASE)
    CTX_CABO = re.compile(r"\b(fio|cabo)\b", re.IGNORECASE)
    CTX_ROLO = re.compile(r"\b(rl|rolo|bobina)\b", re.IGNORECASE)

    # ✅ reforço opcional para cabo automotivo / flexível / paralelo etc.
    REFORCO_CABO = re.compile(
        r"\b(auto|automotivo|flexivel|flexível|paralelo|pp|silicone|cobrecom)\b",
        re.IGNORECASE,
    )

    def _to_float(self, s: str) -> float:
        s = s.strip().replace(" ", "")
        s = s.replace(",", ".")
        return float(s)

    def _fmt_plain(self, v: float) -> str:
        txt = f"{v:.6f}".rstrip("0").rstrip(".")
        return txt

    def _fmt_m(self, v_m: float) -> str:
        return f"{self._fmt_plain(v_m)}m"

    def _normalizar_comprimento_para_m(self, valor_str: str, unidade: str) -> str:
        v = self._to_float(valor_str)
        u = unidade.lower()

        if u in ("mt", "metro", "metros"):
            u = "m"

        if u == "m":
            v_m = v
        elif u == "cm":
            if v < 10:
                v_m = v
            else:
                v_m = v / 100.0
        elif u == "mm":
            v_m = v / 1000.0
        else:
            v_m = v

        return self._fmt_m(v_m)

    def _extrair_secao_cabo_omitida(self, desc: str) -> str | None:
        if not self.CTX_CABO.search(desc):
            return None

        nums = [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(desc)]
        if not nums:
            return None

        # Em cabo/fio, normalmente o primeiro número é a bitola
        candidato = nums[0]
        v = self._to_float(candidato)

        # faixa razoável para bitola
        if 0 < v <= 240:
            return self._fmt_plain(v)

        return None

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Formato_Caixa": None,
                "Volume": None,
                "Peso_Venda": None,
                "Secao_Cabo": None,
            }

        desc = descricao.lower()
        tem_axb = self.PADRAO_TEM_AXB.search(desc) is not None

        diametro = None
        comprimento = None
        formato_caixa = None
        volume = None
        peso_venda = None
        secao_cabo = None

        # 2) Seção cabo explícita (mm²)
        m_mm2 = self.PADRAO_SECAO_MM2.search(desc)
        if m_mm2:
            secao_cabo = self._fmt_plain(self._to_float(m_mm2.group(1))) + "mm2"

        # 3) Volume
        m_vol = self.PADRAO_VOLUME_L.search(desc)
        if m_vol:
            volume = self._fmt_plain(self._to_float(m_vol.group(1))) + "L"

        # 4) Peso_Venda
        m_peso = self.PADRAO_PESO_VENDA.search(desc)
        if m_peso:
            valor = self._fmt_plain(self._to_float(m_peso.group(1)))
            un = m_peso.group(2).lower()
            peso_venda = f"{valor}g" if un.startswith("g") else f"{valor}kg"

        # ✅ Se tem AxB/AxBxC: não disputa com o MedidaAxBExtractor
        if tem_axb:
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Formato_Caixa": formato_caixa,
                "Volume": volume,
                "Peso_Venda": peso_venda,
                "Secao_Cabo": secao_cabo,
            }

        # 5) Polegada
        m_pol = self.PADRAO_POLEGADA.search(desc)
        if m_pol:
            diametro = m_pol.group(1).replace(" ", "")

        # 6) mm/cm explícito
        m_mm = self.PADRAO_DIAMETRO_MM.search(desc)
        if m_mm:
            valor_mm = self._fmt_plain(self._to_float(m_mm.group(1)))

            # ✅ em fio/cabo isso é seção, não diâmetro
            if self.CTX_CABO.search(desc):
                secao_cabo = valor_mm
                diametro = None
            else:
                diametro = valor_mm + "MM"

        # 7) comprimento explícito
        m_comp = self.PADRAO_COMPRIMENTO.search(desc)
        if m_comp:
            comprimento = self._normalizar_comprimento_para_m(m_comp.group(1), m_comp.group(2))

        # 8) reforço para cabo/fio com bitola omitida
        if secao_cabo is None and self.CTX_CABO.search(desc):
            secao_cabo = self._extrair_secao_cabo_omitida(desc)

        # 9) Inferência de diâmetro omitido (somente quando NÃO é cabo/fio)
        if (
            (diametro is None)
            and (not self.CTX_CABO.search(desc))
            and (not self.CTX_ENGATE.search(desc))
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
                            diametro = self._fmt_plain(v) + "mm"

        if comprimento is None and self.CTX_ENGATE.search(desc):
            nums = [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(desc)]
            if nums:
                candidato = nums[-1]
                v = self._to_float(candidato)

                # faixa razoável para comprimento comercial de engate
                if 0 < v <= 100:
                    comprimento = self._fmt_plain(v)
        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Formato_Caixa": formato_caixa,
            "Volume": volume,
            "Peso_Venda": peso_venda,
            "Secao_Cabo": secao_cabo,
        }
