class BaseVariationExtractor:
    aplica_em = []

    def aplica(self, descricao: str) -> bool:
        if not descricao:
            return False

        if not self.aplica_em:
            return True

        desc = descricao.lower()
        return any(p in desc for p in self.aplica_em)

    def extrair(self, descricao: str) -> dict:
        raise NotImplementedError
