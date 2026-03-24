import re


class AmperagemExtractor:
    """
    Extrai amperagem diretamente da descrição SEM lista fixa.

    Regras:
    - Aceita valores como: 6A, 06A, 6,00A, 6.00A
    - Mantém apenas o número (int)
    - Não depende de lista de amperagens válidas
    """

    def __init__(self):
        # pega número inteiro ou decimal antes de A/AMP/AMPS
        self.PADRAO = re.compile(
            r"\b(\d{1,3}(?:[\.,]\d{1,2})?)\s*(a|amp|amps)\b",
            re.IGNORECASE,
        )

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Amperagem": None}

        descricao = descricao.lower()

        match = self.PADRAO.search(descricao)

        if match:
            valor = match.group(1)

            # normalizar decimal (6,00 -> 6 | 6.00 -> 6)
            valor = valor.replace(",", ".")

            try:
                valor_float = float(valor)
                valor_int = int(valor_float)
                return {"Amperagem": f"{valor_int}A"}
            except Exception:
                return {"Amperagem": None}

        return {"Amperagem": None}
