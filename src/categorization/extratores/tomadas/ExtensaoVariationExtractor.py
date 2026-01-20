import re

from src.categorization.extratores.tomadas.AmperagemExtractor import AmperagemExtractor
from src.categorization.extratores.tomadas.PolosExtractor import PolosExtractor


class ExtensaoVariationExtractor:

    PADRAO_COMPRIMENTO = re.compile(
        r"\b(\d{1,3,5,10})\s*(m|mt|mts|metro|metros)\b",
        re.IGNORECASE,
    )

    def __init__(self):
        self.amperagem_extractor = AmperagemExtractor()
        self.polos_extractor = PolosExtractor()

    def extrair(self, descricao: str) -> dict:
        variacoes: dict[str, int | None] = {
            "Comprimento_m": None
        }

        if not descricao:
            return variacoes

        desc = descricao.lower()

        match = self.PADRAO_COMPRIMENTO.search(desc)
        if match:
            variacoes["Comprimento_m"] = int(match.group(1))

        variacoes.update(self.amperagem_extractor.extrair(descricao))
        variacoes.update(self.polos_extractor.extrair(descricao))

        return variacoes
