import re


class AmperagemExtractor:

    def __init__(self):
        # 1) padrão composto: 10A/20A, 10A / 20A, 10AMP/20AMP
        self.PADRAO_COMPOSTO = re.compile(
            r"\b(\d{1,3}(?:[\.,]\d{1,2})?\s*(?:A|AMP|AMPS)\s*/\s*\d{1,3}(?:[\.,]\d{1,2})?\s*(?:A|AMP|AMPS))\b",
            re.IGNORECASE,
        )

        # 2) padrão simples: 6A, 06A, 6,00A, 6.00A
        self.PADRAO_SIMPLES = re.compile(
            r"\b(\d{1,3}(?:[\.,]\d{1,2})?)\s*(A|AMP|AMPS)\b",
            re.IGNORECASE,
        )

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Amperagem": None}

        # ---------- 1) PRIORIDADE: AMPERAGEM COMPOSTA ----------
        match_composto = self.PADRAO_COMPOSTO.search(descricao)
        if match_composto:
            valor_original = match_composto.group(1)
            return {"Amperagem": valor_original}

        # ---------- 2) FALLBACK: AMPERAGEM SIMPLES ----------
        match_simples = self.PADRAO_SIMPLES.search(descricao)
        if match_simples:
            valor_original = match_simples.group(1)
            return {"Amperagem": f"{valor_original}A"}

        return {"Amperagem": None}
