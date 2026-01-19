import re

from src.categorization.extratores.tomadas.AmperagemExtractor import AmperagemExtractor
from src.categorization.extratores.tomadas.PolosExtractor import PolosExtractor


class FiltroLinhaVariationExtractor:


    PADRAO_TOMADAS = re.compile(
        r"\b(\d{1,2,3,4,5})\s*(tomadas?|t|sa[ií]das?)\b", re.IGNORECASE
    )

    def __init__(self):
        self.amperagem_extractor = AmperagemExtractor()
        self.polos_extractor = PolosExtractor()

    def extrair(self, descricao: str) -> dict:
        variacoes: dict[str, int | None] = {
            "Qtd_Tomadas": None
        }

        if not descricao:
            return variacoes

        desc = descricao.lower()

        match = self.PADRAO_TOMADAS.search(desc)
        if match:
            variacoes["Qtd_Tomadas"] = int(match.group(1))

        variacoes.update(self.amperagem_extractor.extrair(descricao))
        variacoes.update(self.polos_extractor.extrair(descricao))

        return variacoes
