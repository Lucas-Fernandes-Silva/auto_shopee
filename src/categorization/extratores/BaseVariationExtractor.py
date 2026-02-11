class BaseVariationExtractor:
    aplica_em = []  # lista de palavras-chave

    def aplica(self, descricao: str) -> bool:
        desc = descricao.lower()
        return any(palavra in desc for palavra in self.aplica_em)

    def extrair(self, descricao: str) -> dict:
        raise NotImplementedError
