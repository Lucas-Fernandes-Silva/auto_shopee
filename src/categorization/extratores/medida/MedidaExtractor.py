import re


class MedidaExtractor:
    # formatos de caixa / espelho
    PADRAO_FORMATO_CAIXA = re.compile(
        r"\b(3x3|4x2|4x4)\b",
        re.IGNORECASE
    )

    # polegadas (conduíte, hidráulica)
    PADRAO_POLEGADA = re.compile(
        r"\b(1/2|3/4|1/4|1)\s*(pol|\"|')?\b",
        re.IGNORECASE
    )

    # diâmetro em mm
    PADRAO_DIAMETRO_MM = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(mm|milimetros?)\b",
        re.IGNORECASE
    )

    # medidas compostas (ex: 20x10)
    PADRAO_MEDIDA_COMPOSTA = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)\b",
        re.IGNORECASE
    )

    # comprimento
    PADRAO_COMPRIMENTO = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(m|mt|metro|metros)\b",
        re.IGNORECASE
    )

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {}

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

        # 3️⃣ comprimento
        match_comp = self.PADRAO_COMPRIMENTO.search(desc)
        if match_comp:
            comprimento = match_comp.group(1).replace(",", ".") + "m"

        # 4️⃣ diâmetro em mm
        match_mm = self.PADRAO_DIAMETRO_MM.search(desc)
        if match_mm:
            diametro = match_mm.group(1).replace(",", ".") + "mm"

        # 5️⃣ medida composta genérica (se não for caixa)
        match_composta = self.PADRAO_MEDIDA_COMPOSTA.search(desc)
        if match_composta and not formato_caixa:
            a = match_composta.group(1).replace(",", ".")
            b = match_composta.group(2).replace(",", ".")
            diametro = f"{a}x{b}mm"

        return {
            "Diametro": diametro,
            "Comprimento": comprimento,
            "Formato_Caixa": formato_caixa,
        }
