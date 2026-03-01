import re

class MedidaAxBExtractor:
    PADRAO_AXB = re.compile(
        r"\b(\d+(?:[.,]\d+)?)(\s*(?:mm|cm|m|\"|pol|')\b)?\s*[xX×]\s*"
        r"(\d+(?:[.,]\d+)?)(\s*(?:mm|cm|m|\"|pol|')\b)?\b",
        re.IGNORECASE
    )

    CTX_PARAFUSO = re.compile(r"\b(parafuso|rosca|sextav|philips|frances|franc[eê]s|bocante|abrocante|maq|maquina)\b", re.I)

    CTX_HIDRAULICA = re.compile(
        r"\b(tubo|conexao|conexoes|joelho|t[eê]\b|luva|bucha|adaptador|niple|uni[aã]o|registro|valvula|válvula|sif[aã]o|mangueira)\b",
        re.I
    )
    REFORCO_HIDRAULICA = re.compile(r"\b(pvc|cpvc|ppr|pex|agua|água|esgoto|soldavel|soldável|colavel|colável|rosca)\b", re.I)

    CTX_DIMENSIONAL = re.compile(r"\b(caixa|cuba|pia|tanque|gabinete|espelho|porta|janela|grelha|ralo|nicho)\b", re.I)

    def _norm(self, n: str) -> str:
        return n.replace(",", ".")

    def _norm_un(self, un: str | None) -> str | None:
        if not un:
            return None
        u = un.strip().lower()
        # normaliza algumas variações
        if u in ['pol', '"', "'"]:
            return '"'
        return u

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {}

        texto = descricao.lower()
        m = self.PADRAO_AXB.search(texto)
        if not m:
            return {}

        a, ua, b, ub = m.group(1), m.group(2), m.group(3), m.group(4)
        a = self._norm(a); b = self._norm(b)
        ua = self._norm_un(ua); ub = self._norm_un(ub)

        # 1) Parafuso: diametro x comprimento (não inventa unidade)
        if self.CTX_PARAFUSO.search(texto):
            return {"Medida": f"{a}X{b}"}

        # 2) Dimensional: altura x largura (se existir unidade, mantém)
        if self.CTX_DIMENSIONAL.search(texto):
            alt = f"{a}{ua or ''}"
            larg = f"{b}{ub or ''}"
            return {"Altura": alt, "Largura": larg}

        # 3) Hidráulica: normalmente bitola1 x bitola2
        if self.CTX_HIDRAULICA.search(texto) and self.REFORCO_HIDRAULICA.search(texto):
            # se uma unidade é "m", provavelmente é comprimento, não diâmetro
            if ua == "m" and (ub in (None, "mm", "cm", '"')):
                return {"Comprimento_Venda": f"{a}m", "Diametro": f"{b}{ub or 'mm'}"}
            if ub == "m" and (ua in (None, "mm", "cm", '"')):
                return {"Comprimento_Venda": f"{b}m", "Diametro": f"{a}{ua or 'mm'}"}

            # padrão redução: devolve dois diâmetros
            d1 = f"{a}{ua or 'mm'}"
            d2 = f"{b}{ub or 'mm'}"
            return {"Diametro_1": d1, "Diametro_2": d2, "Medida": f"{d1}x{d2}"}

        # 4) Fallback: retorna só a Medida bruta pra você não “perder”
        return {"Medida": f"{a}{ua or ''}X{b}{ub or ''}"}
