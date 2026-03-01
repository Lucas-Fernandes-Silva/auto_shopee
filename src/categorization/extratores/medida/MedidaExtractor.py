import re


class MedidaExtractor:
    # =========================
    # Regex base (explícitos)
    # =========================

    PADRAO_FORMATO_CAIXA = re.compile(r"\b(3x3|4x2|4x4)\b", re.IGNORECASE)

    # Polegadas (frações e inteiros comuns). Mantém simples; se precisar expande depois.
    PADRAO_POLEGADA = re.compile(r"\b(1/2|3/4|1/4|5/8|1|1\s*1/2|1,1/2|1,1/4)\s*(pol|\"|')?\b", re.IGNORECASE)

    PADRAO_DIAMETRO_MM = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(mm|milimetros?)\b", re.IGNORECASE)

    # Comprimento explícito em metros (somente com unidade)
    PADRAO_COMPRIMENTO_M = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(m|mt|metro|metros)\b",
        re.IGNORECASE
    )

    # Volume explícito (litros)
    PADRAO_VOLUME_L = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(l|lt|litro|litros)\b", re.IGNORECASE)

    # Peso explícito (kg / g)
    PADRAO_PESO = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(kg|quilo|quilos|g|grama|gramas)\b", re.IGNORECASE)

    # Seção de fio/cabo (mm² / mm2)
    PADRAO_SECAO_MM2 = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(?:mm2|mm²|milimetros?\s*quadrados?)\b",
        re.IGNORECASE
    )

    # Número solto (para inferência)
    PADRAO_NUMERO_SOLTO = re.compile(r"\b(\d+(?:[.,]\d+)?)\b")

    # =========================
    # Contextos (pra inferir unidade)
    # =========================

    # Hidráulica: quando número vem solto (ex: "TUBO PVC AGUA 50" -> 50mm)
    CTX_HIDRAULICA = re.compile(
        r"\b(tubo|cano|conexao|conexoes|joelho|t[eê]\b|luva|bucha|adaptador|niple|uni[aã]o|registro|valvula|válvula|sif[aã]o|engate|mangueira)\b",
        re.IGNORECASE
    )
    REFORCO_HIDRAULICA = re.compile(
        r"\b(pvc|cpvc|ppr|pex|agua|água|esgoto|soldavel|soldável|colavel|colável|rosca)\b",
        re.IGNORECASE
    )

    # Eletroduto / conduíte
    CTX_CONDUITE = re.compile(r"\b(conduite|eletroduto)\b", re.IGNORECASE)

    # Fio/cabo: NÃO inferir mm (aqui o que importa é mm² e comprimento em m)
    CTX_CABO = re.compile(r"\b(fio|cabo)\b", re.IGNORECASE)

    # Pistas de rolo/unidade comercial — não é medida, mas pode ajudar a evitar erro
    CTX_ROLO = re.compile(r"\b(rl|rolo|bobina)\b", re.IGNORECASE)

    def _norm_num(self, s: str) -> str:
        return s.replace(",", ".")

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

        # 2) Seção cabo (mm²) — bem importante em elétrica
        m_mm2 = self.PADRAO_SECAO_MM2.search(desc)
        if m_mm2:
            secao_cabo = self._norm_num(m_mm2.group(1)) + "mm2"

        # 3) Volume (L)
        m_vol = self.PADRAO_VOLUME_L.search(desc)
        if m_vol:
            volume = self._norm_num(m_vol.group(1)) + "L"

        # 4) Peso (kg/g)
        m_peso = self.PADRAO_PESO.search(desc)
        if m_peso:
            valor = self._norm_num(m_peso.group(1))
            un = m_peso.group(2).lower()
            if un.startswith("g"):
                peso = f"{valor}g"
            else:
                peso = f"{valor}kg"

        # 5) Diâmetro polegada (se existir)
        m_pol = self.PADRAO_POLEGADA.search(desc)
        if m_pol:
            diametro = m_pol.group(1).replace(" ", "") + '"'

        # 6) Diâmetro mm explícito (se existir)
        m_mm = self.PADRAO_DIAMETRO_MM.search(desc)
        if m_mm:
            diametro = self._norm_num(m_mm.group(1)) + "mm"

        # 7) Comprimento em metros explícito
        m_comp = self.PADRAO_COMPRIMENTO_M.search(desc)
        if m_comp:
            comprimento = self._norm_num(m_comp.group(1)) + "m"

        # =========================
        # 8) Inferência: "mm omitido"
        # =========================
        # Só tenta inferir se:
        # - ainda não achou diametro explícito
        # - NÃO é fio/cabo (pra não confundir bitola/metros)
        # - tem contexto hidráulico OU conduíte
        # - e tem reforço (no caso hidráulico)
        if diametro is None and not self.CTX_CABO.search(desc):
            contexto_conduite = self.CTX_CONDUITE.search(desc) is not None
            contexto_hid = (self.CTX_HIDRAULICA.search(desc) is not None) and (self.REFORCO_HIDRAULICA.search(desc) is not None)

            if contexto_conduite or contexto_hid:
                # pega números candidatos
                nums = [m.group(1) for m in self.PADRAO_NUMERO_SOLTO.finditer(desc)]
                if nums:
                    # heurística: geralmente a bitola/diâmetro vem no final
                    candidato = nums[-1]

                    # evita inferir mm se o número parece ser:
                    # - ano ou código muito grande (ajuste conforme seu dataset)
                    # - quantidade com "l" ou "kg" (já capturado antes)
                    v = float(self._norm_num(candidato))
                    if 0 < v <= 999:
                        # se tiver rolo, o número final às vezes é metragem; mas sem "m" explícito fica ambíguo.
                        # aqui a gente só infere mm se NÃO houver "rl/rolo/bobina" E não houver comprimento explícito.
                        if not self.CTX_ROLO.search(desc) and comprimento is None:
                            # se for inteiro, mantém sem .0
                            if v.is_integer():
                                diametro = f"{int(v)}mm"
                            else:
                                diametro = f"{self._norm_num(candidato)}mm"

        return {
            "Diametro": diametro,
            "Comprimento_Venda": comprimento,
            "Formato_Caixa": formato_caixa,
            "Volume": volume,
            "Peso": peso,
            "Secao_Cabo": secao_cabo,
        }
