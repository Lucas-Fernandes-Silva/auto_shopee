import re


class MedidaExtractor:
    # formatos de caixa / espelho
    PADRAO_FORMATO_CAIXA = re.compile(r"\b(3x3|4x2|4x4)\b", re.IGNORECASE)

    # polegadas (conduíte, elétrica)
    PADRAO_POLEGADA = re.compile(r"\b(1/2|3/4|1/4|1)\s*(pol|\"|')?\b", re.IGNORECASE)

    # diâmetro em mm
    PADRAO_DIAMETRO_MM = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(mm|milimetros?)\b", re.IGNORECASE)

    # comprimento EM METROS (obrigatório ter unidade explícita)
    PADRAO_COMPRIMENTO = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(m|mt|metro|metros)\b(?![a-z])", re.IGNORECASE
    )

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {
                "Diametro": None,
                "Comprimento": None,
                "Formato_Caixa": None,
            }

        desc = descricao.lower()

        diametro = None
        comprimento = None
        formato_caixa = None

        # 1️⃣ formato de caixa
        match_caixa = self.PADRAO_FORMATO_CAIXA.search(desc)
        if match_caixa:
            formato_caixa = match_caixa.group(1)

        # 2️⃣ polegada
        match_pol = self.PADRAO_POLEGADA.search(desc)
        if match_pol:
            diametro = match_pol.group(1) + '"'

        # 3️⃣ diâmetro em mm
        match_mm = self.PADRAO_DIAMETRO_MM.search(desc)
        if match_mm:
            diametro = match_mm.group(1).replace(",", ".") + "mm"

        # 4️⃣ comprimento (somente se tiver unidade explícita)
        match_comp = self.PADRAO_COMPRIMENTO.search(desc)
        if match_comp:
            comprimento = match_comp.group(1).replace(",", ".")

        return {
            "Diametro": diametro,
            "Comprimento": comprimento,
            "Formato_Caixa": formato_caixa,
        }
