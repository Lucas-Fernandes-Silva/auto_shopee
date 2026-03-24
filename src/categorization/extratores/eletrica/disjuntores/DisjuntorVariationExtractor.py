from src.categorization.extratores.tomadas.AmperagemExtractor import AmperagemExtractor
from src.categorization.extratores.tomadas.PolosExtractor import (
    PolosExtractor,
)


class DisjuntorVariationExtractor:
    def __init__(self):
        self.amperagem = AmperagemExtractor()
        self.polos = PolosExtractor()

    def extrair(self, descricao: str) -> dict:
        variacoes = {}

        variacoes.update(self.amperagem.extrair(descricao))
        variacoes.update(self.polos.extrair(descricao))

        return variacoes
