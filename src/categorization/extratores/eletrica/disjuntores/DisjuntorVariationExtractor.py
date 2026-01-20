from src.categorization.extratores.eletrica.disjuntores.PolosDisjuntorExtractor import (
    PolosDisjuntorExtractor,
)
from src.categorization.extratores.tomadas.AmperagemExtractor import AmperagemExtractor


class DisjuntorVariationExtractor:
    def __init__(self):
        self.amperagem = AmperagemExtractor()
        self.polos = PolosDisjuntorExtractor()

    def extrair(self, descricao: str) -> dict:
        variacoes = {}

        variacoes.update(self.amperagem.extrair(descricao))
        variacoes.update(self.polos.extrair(descricao))

        return variacoes
