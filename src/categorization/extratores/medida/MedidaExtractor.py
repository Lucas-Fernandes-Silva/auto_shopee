import re


class MedidaExtractor:
    # Detecta AxB ou AxBxC (com decimais/fração/misto)
    PADRAO_TEM_AXB = re.compile(
        r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)\s*(?:mm|cm|m|\"|pol|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
        r"(?:\s*(?:mm|cm|m|\"|pol|')?\s*[xX×]\s*"
        r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?))?",
        re.IGNORECASE,
    )

    PADRAO_FORMATO_CAIXA = re.compile(r"\b(3x3|4x2|4x4)\b", re.IGNORECASE)

    # polegadas (frações e mistos)
    PADRAO_POLEGADA = re.compile(
        r"\b(1/2|3/4|1/4|1/8|5/32|5/16|3/8|3/16|5/8|1|1\s*1/2|1 1/2|1 1/4)\s*(pol|\"|')?\b",
        re.IGNORECASE,
    )

    PADRAO_DIAMETRO_MM = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(cm|mm|milimetros?)\b", re.IGNORECASE)

    # comprimento explícito em mm/cm/m (normaliza pra m)
    PADRAO_COMPRIMENTO = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(m|mt|metro|metros)\b", re.IGNORECASE)

    PADRAO_VOLUME_L = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(l|lt|litro|litros)\b", re.IGNORECASE)

    PADRAO_PESO = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(kg|quilo|quilos|g|grama|gramas|gr)\b", re.IGNORECASE
    )

    PADRAO_SECAO_MM2 = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(?:mm2|mm²|milimetros?\s*quadrados?)\b", re.IGNORECASE
    )

    PADRAO_NUMERO_SOLTO = re.compile(r"\b(\d+(?:[.,]\d+)?)\b")

    # contextos pra inferência de mm omitido
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
            # heurística pra casos tipo "0,70CM" que na prática é 0,70m (70cm)
            if v < 10:
                v_m = v
            else:
                v_m = v / 100.0
        elif u == "mm":
            v_m = v / 1000.0
        else:
            v_m = v

        return self._fmt_m(v_m)

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Formato_Caixa": None,
                "Volume": None,
                "Peso": None,
                "Secao_Cabo": None,
            }

        desc = descricao.lower()
        tem_axb = self.PADRAO_TEM_AXB.search(desc) is not None

        diametro = None
        comprimento = None
        formato_caixa = None
        volume = None
        peso = None
        secao_cabo = None

        # 1) Formato caixa
        m_caixa = self.PADRAO_FORMATO_CAIXA.search(desc)
        if m_caixa:
            formato_caixa = m_caixa.group(1)

        # 2) Seção cabo (mm²)
        m_mm2 = self.PADRAO_SECAO_MM2.search(desc)
        if m_mm2:
            secao_cabo = self._fmt_plain(self._to_float(m_mm2.group(1))) + "mm2"

        # 3) Volume (L)
        m_vol = self.PADRAO_VOLUME_L.search(desc)
        if m_vol:
            volume = self._fmt_plain(self._to_float(m_vol.group(1))) + "L"

        # 4) Peso (kg/g)
        m_peso = self.PADRAO_PESO.search(desc)
        if m_peso:
            valor = self._fmt_plain(self._to_float(m_peso.group(1)))
            un = m_peso.group(2).lower()
            peso = f"{valor}g" if un.startswith("g") else f"{valor}kg"

        # ✅ Se tem AxB/AxBxC: NÃO disputa com o MedidaAxBExtractor
        if tem_axb:
            return {
                "Diametro": None,
                "Comprimento_Venda": None,
                "Formato_Caixa": formato_caixa,
                "Volume": volume,
                "Peso": peso,
                "Secao_Cabo": secao_cabo,
            }

        # 5) Diâmetro polegada
        m_pol = self.PADRAO_POLEGADA.search(desc)
        if m_pol:
            diametro = m_pol.group(1).replace(" ", "") + '"'

        # 6) Diâmetro mm explícito
        m_mm = self.PADRAO_DIAMETRO_MM.search(desc)
        if m_mm:
            diametro = self._fmt_plain(self._to_float(m_mm.group(1))) + "mm"

        # 7) Comprimento explícito (mm/cm/m -> m)
        m_comp = self.PADRAO_COMPRIMENTO.search(desc)
        if m_comp:
            comprimento = self._normalizar_comprimento_para_m(m_comp.group(1), m_comp.group(2))

        # 8) Inferência: "mm omitido" (só quando NÃO é fio/cabo)
        if (diametro is None) and (not self.CTX_CABO.search(desc)):
            contexto_conduite = self.CTX_CONDUITE.search(desc) is not None
            contexto_hid = (self.CTX_HIDRAULICA.search(desc) is not None) and (
                self.REFORCO_HIDRAULICA.search(desc) is not None
            )

            if contexto_conduite or contexto_hid:
                nums = [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(desc)]
                if nums:
                    candidato = nums[-1]
                    v = self._to_float(candidato)
                    if 0 < v <= 999:
                        if (not self.CTX_ROLO.search(desc)) and (comprimento is None):
                            diametro = self._fmt_plain(v) + "mm"

        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Formato_Caixa": formato_caixa,
            "Volume": volume,
            "Peso": peso,
            "Secao_Cabo": secao_cabo,
        }
